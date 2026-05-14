from __future__ import annotations

import pytest

from backend.agents.validation_agent import ValidationService
from backend.schemas.constants import ContextMessage
from backend.schemas.exceptions import AgentExecutionError


class StubRunner:
    def __init__(self, response: str = '{"updates": []}') -> None:
        self.response = response
        self.prompts: list[str] = []

    def invoke_agent(self, agent, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response


@pytest.fixture
def service() -> ValidationService:
    return ValidationService(runner=StubRunner(), agent=object())


def test_path_exists_accepts_only_real_nested_schema_paths(service, web_schema):
    assert service._path_exists(web_schema, "auth.session_management.has_session_expiry")
    assert not service._path_exists(web_schema, "auth.session_management.missing")
    assert not service._path_exists(web_schema, "auth.has_auth.child")


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("auth.has_auth", "boolean"),
        ("auth.auth_types", "list"),
        ("context.app_name", "string"),
        ("missing.has_feature", "string"),
        ("missing.value", "string"),
    ],
)
def test_infer_field_type_from_schema_value_and_field_name(service, web_schema, path, expected):
    assert service._infer_field_type(web_schema, path) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (True, True),
        (False, False),
        ("yes", True),
        ("  TRUE ", True),
        ("nope", False),
        ("0", False),
        ("maybe", None),
        (1, None),
    ],
)
def test_coerce_value_for_boolean_fields(service, web_schema, value, expected):
    assert service._coerce_value(value, web_schema, "auth.has_auth") is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (["Google", "email"], ["Google", "email"]),
        ("Chrome, Firefox, Safari", ["Chrome", "Firefox", "Safari"]),
        ("Chrome,, Firefox ,", ["Chrome", "Firefox"]),
        (False, None),
    ],
)
def test_coerce_value_for_list_fields(service, web_schema, value, expected):
    assert service._coerce_value(value, web_schema, "ui.supported_browsers") == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("  Acme  ", "Acme"),
        (42, "42"),
        (True, None),
    ],
)
def test_coerce_value_for_string_fields(service, web_schema, value, expected):
    assert service._coerce_value(value, web_schema, "context.app_name") == expected


def test_build_conversation_window_keeps_initial_message_when_recent_window_truncates_it(service):
    history = [ContextMessage("user", "initial project description")]
    for i in range(8):
        history.append(ContextMessage("assistant", f"question {i}"))
        history.append(ContextMessage("user", f"answer {i}"))

    window = service._build_conversation_window(history, max_turns=4)

    assert "[INITIAL MESSAGE]\nUSER: initial project description" in window
    assert "ASSISTANT: question 6" in window
    assert "USER: answer 7" in window
    assert "ASSISTANT: question 0" not in window


def test_split_into_sections_separates_latest_exchange_from_prior_context(service):
    history = [
        ContextMessage("user", "Build a CRM"),
        ContextMessage("assistant", "What is it called?"),
        ContextMessage("user", "Atlas"),
        ContextMessage("assistant", "Is it public?"),
        ContextMessage("user", "No"),
    ]

    sections = service._split_into_sections(history, service._build_conversation_window(history))

    assert "PRIOR CONTEXT:" in sections
    assert "USER: Build a CRM" in sections
    assert "LATEST EXCHANGE:\nASSISTANT: Is it public?\nUSER: No" in sections
    assert "ASSISTANT: What is it called?" in sections
    assert "USER: Atlas" in sections


def test_split_into_sections_handles_user_only_history(service):
    history = [ContextMessage("user", "A public dashboard")]

    assert service._split_into_sections(history, "USER: A public dashboard") == (
        "LATEST EXCHANGE:\nUSER: A public dashboard"
    )


def test_format_target_fields_includes_types_and_hints(service, web_schema):
    text = service._format_target_fields(
        [
            {"field": "context.app_name", "question_hint": "name"},
            {"field": "auth.has_auth", "question_hint": "login required"},
            {"field": "auth.auth_types", "question_hint": "auth methods"},
        ],
        web_schema,
    )

    assert "- context.app_name (string) — name" in text
    assert "- auth.has_auth (boolean) — login required" in text
    assert "- auth.auth_types (list) — auth methods" in text


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ('```json\n{"updates": []}\n```', '{"updates": []}'),
        ('```\n{"updates": []}\n```', '{"updates": []}'),
        ('  {"updates": []}  ', '{"updates": []}'),
        ("```json", ""),
    ],
)
def test_strip_markdown_handles_json_fences(service, raw, expected):
    assert service._strip_markdown(raw) == expected


def test_extract_updates_returns_empty_without_user_history(web_schema):
    runner = StubRunner('{"updates": [{"field": "context.app_name", "value": "X", "confidence": 1}]}')
    service = ValidationService(runner=runner, agent=object())

    assert service.extract_updates([], web_schema, [{"field": "context.app_name", "question_hint": "name"}]) == {}
    assert runner.prompts == []


def test_extract_updates_normalizes_only_confident_targeted_existing_non_empty_values(web_schema):
    runner = StubRunner(
        """
        ```json
        {
          "updates": [
            {"field": "context.app_name", "value": " Atlas ", "confidence": 0.99},
            {"field": "auth.has_auth", "value": "yes", "confidence": 0.95},
            {"field": "auth.auth_types", "value": "Google, email", "confidence": 0.95},
            {"field": "ui.has_dark_mode", "value": true, "confidence": 0.95},
            {"field": "context.description", "value": "ignored: not targeted", "confidence": 1.0},
            {"field": "context.target_audience", "value": "ignored: low confidence", "confidence": 0.79},
            {"field": "context.missing", "value": "ignored: missing path", "confidence": 1.0},
            {"field": "context.app_name", "value": "", "confidence": 1.0},
            {"field": "auth.has_roles", "value": "maybe", "confidence": 1.0}
          ]
        }
        ```
        """
    )
    service = ValidationService(runner=runner, agent=object())

    updates = service.extract_updates(
        history=[
            ContextMessage("assistant", "What is the app called and does it require auth?"),
            ContextMessage("user", "Atlas, yes, Google and email."),
        ],
        schema=web_schema,
        missing_questions=[
            {"field": "context.app_name", "question_hint": "name"},
            {"field": "auth.has_auth", "question_hint": "login"},
            {"field": "auth.auth_types", "question_hint": "methods"},
            {"field": "ui.has_dark_mode", "question_hint": "dark mode"},
            {"field": "context.target_audience", "question_hint": "audience"},
            {"field": "context.missing", "question_hint": "bad path"},
            {"field": "auth.has_roles", "question_hint": "roles"},
        ],
    )

    assert updates == {
        "context.app_name": "Atlas",
        "auth.has_auth": True,
        "auth.auth_types": ["Google", "email"],
        "ui.has_dark_mode": True,
    }
    assert "TARGET FIELDS" in runner.prompts[0]
    assert "LATEST EXCHANGE" in runner.prompts[0]


def test_extract_updates_returns_empty_for_invalid_json(web_schema):
    service = ValidationService(runner=StubRunner("not json"), agent=object())

    assert service.extract_updates(
        [ContextMessage("user", "Atlas")],
        web_schema,
        [{"field": "context.app_name", "question_hint": "name"}],
    ) == {}


def test_extract_updates_propagates_agent_execution_errors(web_schema):
    class FailingRunner:
        def invoke_agent(self, agent, prompt: str) -> str:
            raise AgentExecutionError()

    service = ValidationService(runner=FailingRunner(), agent=object())

    with pytest.raises(AgentExecutionError):
        service.extract_updates(
            [ContextMessage("user", "Atlas")],
            web_schema,
            [{"field": "context.app_name", "question_hint": "name"}],
        )
