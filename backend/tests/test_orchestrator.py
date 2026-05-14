from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from backend.core import orchestrator as orchestrator_module
from backend.core.orchestrator import MAX_QUESTIONS_PER_TURN, Orchestrator
from backend.core.session_state import SessionState
from backend.schemas.constants import AppType, ContextMessage, SpecialistDefinition
from backend.schemas.db import MessageModel
from backend.schemas.exceptions import (
    DatabaseError,
    MessageSaveError,
    SessionLoadError,
    SessionUpdateError,
)
from backend.schemas.services import OrchestratorServices


class Router:
    def __init__(self, app_type: AppType) -> None:
        self.app_type = app_type
        self.inputs: list[str] = []

    def detect_app_type(self, user_input: str) -> AppType:
        self.inputs.append(user_input)
        return self.app_type


class Validation:
    def __init__(self, updates: dict[str, Any] | None = None) -> None:
        self.updates = updates or {}
        self.calls: list[dict[str, Any]] = []

    def extract_updates(self, history, schema, missing_questions=None):
        self.calls.append(
            {
                "history": history,
                "schema": schema,
                "missing_questions": missing_questions,
            }
        )
        return self.updates


class Conversation:
    def __init__(self, reply: str = "next question") -> None:
        self.reply_text = reply
        self.calls: list[dict[str, Any]] = []

    def reply(self, **kwargs):
        self.calls.append(kwargs)
        return self.reply_text


class Checklist:
    def __init__(self, reply: str = "[HIGH PRIORITY]\n- test it") -> None:
        self.reply_text = reply
        self.calls: list[dict[str, Any]] = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        return self.reply_text


class SpecialistGenerator:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def generate_specialist(self, project_description, schemas):
        self.calls.append({"project_description": project_description, "schemas": schemas})
        return SpecialistDefinition(
            schema={"type": "custom-agent", "context": {"name": ""}},
            schema_filename="custom-agent.json",
            hints_map={"context.name": "custom name"},
            domain_rules="custom domain rules",
        )


@dataclass
class Harness:
    orchestrator: Orchestrator
    router: Router
    validation: Validation
    conversation: Conversation
    checklist: Checklist
    specialist_generator: SpecialistGenerator


def build_harness(schema_dir, app_type=AppType.WEB, updates=None) -> Harness:
    router = Router(app_type)
    validation = Validation(updates)
    conversation = Conversation()
    checklist = Checklist()
    specialist_generator = SpecialistGenerator()
    services = OrchestratorServices(
        runner=object(),
        router_service=router,
        conversational_agent=conversation,
        validation_service=validation,
        specialist_generator=specialist_generator,
        checklist_generator=checklist,
        schema_dir=schema_dir,
    )
    return Harness(
        orchestrator=Orchestrator(services),
        router=router,
        validation=validation,
        conversation=conversation,
        checklist=checklist,
        specialist_generator=specialist_generator,
    )


def install_repository_fakes(monkeypatch, state: SessionState):
    saved_messages: list[ContextMessage] = []
    updated_states: list[SessionState] = []

    monkeypatch.setattr(orchestrator_module, "db_to_session_state", lambda user_id, session_id: state)

    def add_message(session_id: str, message: ContextMessage) -> MessageModel:
        saved_messages.append(message)
        return MessageModel(session_id=session_id, role=message.role, content=message.content)

    monkeypatch.setattr(orchestrator_module, "add_message", add_message)
    monkeypatch.setattr(orchestrator_module, "update_session", lambda id, state: updated_states.append(state))
    return saved_messages, updated_states


def test_handle_message_returns_fallback_response_without_writes_for_fallback_state(monkeypatch, schema_dir):
    state = SessionState(active_agent_name="fallback")
    saved_messages, updated_states = install_repository_fakes(monkeypatch, state)
    harness = build_harness(schema_dir)

    response = harness.orchestrator.handle_message("u1", "s1", "hello")

    assert response.reply_message.session_id == "0"
    assert response.reply_message.content == ""
    assert response.completed is False
    assert saved_messages == []
    assert updated_states == []


def test_handle_message_loads_static_schema_for_unknown_web_app_and_asks_next_questions(monkeypatch, schema_dir):
    state = SessionState(
        app_type=AppType.UNKNOWN,
        schema={},
        history=[ContextMessage("user", "Build a public CRM")],
    )
    saved_messages, updated_states = install_repository_fakes(monkeypatch, state)
    harness = build_harness(schema_dir, app_type=AppType.WEB)

    response = harness.orchestrator.handle_message("u1", "s1", "Build a public CRM")

    assert harness.router.inputs == ["Build a public CRM"]
    assert state.app_type == AppType.WEB
    assert state.active_agent_name == "web"
    assert state.schema["type"] == "web-application"
    assert harness.validation.calls[0]["missing_questions"][0]["field"] == "context.app_name"
    assert len(harness.conversation.calls[0]["missing_questions"]) == MAX_QUESTIONS_PER_TURN
    assert harness.conversation.calls[0]["history"] == []
    assert saved_messages == [ContextMessage(role="assistant", content="next question")]
    assert updated_states == [state]
    assert response.reply_message.content == "next question"
    assert response.completed is False


def test_handle_message_merges_updates_before_asking_for_remaining_fields(monkeypatch, schema_dir):
    state = SessionState(
        app_type=AppType.WEB,
        schema={
            "type": "web-application",
            "context": {
                "app_name": "",
                "description": "",
                "target_audience": "",
                "is_public": None,
            },
        },
        history=[
            ContextMessage("assistant", "What is the app called?"),
            ContextMessage("user", "Atlas"),
        ],
    )
    install_repository_fakes(monkeypatch, state)
    harness = build_harness(schema_dir, updates={"context.app_name": "Atlas"})

    harness.orchestrator.handle_message("u1", "s1", "Atlas")

    assert state.schema["context"]["app_name"] == "Atlas"
    asked_fields = [q["field"] for q in harness.conversation.calls[0]["missing_questions"]]
    assert "context.app_name" not in asked_fields
    assert asked_fields == ["context.description", "context.target_audience"]


def test_handle_message_generates_checklist_and_marks_session_complete_when_nothing_missing(monkeypatch, schema_dir):
    state = SessionState(
        app_type=AppType.WEB,
        schema={"type": "web-application", "notes": ""},
        history=[ContextMessage("user", "done")],
    )
    saved_messages, updated_states = install_repository_fakes(monkeypatch, state)
    harness = build_harness(schema_dir)

    response = harness.orchestrator.handle_message("u1", "s1", "done")

    assert state.completed is True
    assert harness.conversation.calls == []
    assert len(harness.checklist.calls) == 1
    assert saved_messages == [ContextMessage(role="assistant", content="[HIGH PRIORITY]\n- test it")]
    assert updated_states == [state]
    assert response.completed is True


def test_handle_message_builds_dynamic_specialist_for_other_app_type(monkeypatch, schema_dir):
    state = SessionState(
        app_type=AppType.UNKNOWN,
        schema={},
        history=[ContextMessage("user", "Build a CLI migration tool")],
    )
    install_repository_fakes(monkeypatch, state)
    harness = build_harness(schema_dir, app_type=AppType.OTHER)

    harness.orchestrator.handle_message("u1", "s1", "Build a CLI migration tool")

    assert harness.specialist_generator.calls[0]["project_description"] == "Build a CLI migration tool"
    assert len(harness.specialist_generator.calls[0]["schemas"]) == 4
    assert state.schema == {"type": "custom-agent", "context": {"name": ""}}
    assert state.active_agent_name == "custom-agent"
    specialist = harness.orchestrator.registry.get(AppType.OTHER)
    assert specialist.get_domain_rules() == "custom domain rules"
    assert specialist.get_hints_map() == {"context.name": "custom name"}


def test_handle_message_wraps_database_error_while_loading_state(monkeypatch, schema_dir):
    monkeypatch.setattr(
        orchestrator_module,
        "db_to_session_state",
        lambda user_id, session_id: (_ for _ in ()).throw(DatabaseError()),
    )
    harness = build_harness(schema_dir)

    with pytest.raises(SessionLoadError):
        harness.orchestrator.handle_message("u1", "s1", "hello")


def test_handle_message_wraps_database_error_while_saving_reply(monkeypatch, schema_dir):
    state = SessionState(app_type=AppType.WEB, schema={"type": "web-application"}, history=[ContextMessage("user", "done")])
    monkeypatch.setattr(orchestrator_module, "db_to_session_state", lambda user_id, session_id: state)
    monkeypatch.setattr(
        orchestrator_module,
        "add_message",
        lambda session_id, message: (_ for _ in ()).throw(DatabaseError()),
    )
    harness = build_harness(schema_dir)

    with pytest.raises(MessageSaveError):
        harness.orchestrator.handle_message("u1", "s1", "done")


def test_handle_message_wraps_database_error_while_updating_session(monkeypatch, schema_dir):
    state = SessionState(app_type=AppType.WEB, schema={"type": "web-application"}, history=[ContextMessage("user", "done")])
    monkeypatch.setattr(orchestrator_module, "db_to_session_state", lambda user_id, session_id: state)
    monkeypatch.setattr(
        orchestrator_module,
        "add_message",
        lambda session_id, message: MessageModel(session_id=session_id, role=message.role, content=message.content),
    )
    monkeypatch.setattr(
        orchestrator_module,
        "update_session",
        lambda id, state: (_ for _ in ()).throw(DatabaseError()),
    )
    harness = build_harness(schema_dir)

    with pytest.raises(SessionUpdateError):
        harness.orchestrator.handle_message("u1", "s1", "done")


def test_get_missing_questions_uses_default_hint_when_specialist_has_no_hint(schema_dir):
    harness = build_harness(schema_dir, app_type=AppType.OTHER)
    specialist = harness.orchestrator.registry.get(AppType.OTHER)

    assert harness.orchestrator.get_missing_questions(specialist, ["context.name"]) == [
        {"field": "context.name", "question_hint": "describe this field"}
    ]


def test_normalized_wraps_text_with_matching_title_header(schema_dir):
    harness = build_harness(schema_dir)

    assert harness.orchestrator.normalized("TITLE", "body") == (
        "\n------ TITLE ------\nbody\n-------------" "------\n"
    )
