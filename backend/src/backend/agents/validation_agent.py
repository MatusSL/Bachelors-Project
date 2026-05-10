import json
import logging
from typing import Any, Dict, List
from backend.schemas.exceptions import AgentExecutionError
from langchain_core.runnables import Runnable

from backend.agents.runner import Runner
from backend.schemas.constants import Schema, ContextMessage


logger = logging.getLogger(__name__)


TRUTHY = {"yes", "yeah", "yep", "true", "1", "sure", "correct", "right"}
FALSY = {"no", "nope", "nah", "false", "0", "none", "not"}

MAX_CONVERSATION_TURNS = 14
CONFIDENCE_THRESHOLD = 0.8


VALIDATION_PROMPT = """You are a strict JSON extraction assistant.

CRITICAL: Only extract values the user LITERALLY said. If the user did not clearly state a value for a field, you MUST skip that field. Do NOT guess, infer, or fill in defaults. When in doubt, skip the field.

TARGET FIELDS (extract ONLY these, skip any field not addressed by the user):
{target_fields}

{conversation_sections}

EXAMPLES:

Example 1 — user answers two questions:
Target: auth.has_auth (boolean), auth.auth_types (list)
ASSISTANT: Does your app require user login?
USER: Yes, we need Google and email login.
Output:
{{"updates": [{{"field": "auth.has_auth", "value": true, "confidence": 0.95}}, {{"field": "auth.auth_types", "value": ["Google", "email"], "confidence": 0.9}}]}}

Example 2 — user only answers one of two fields:
Target: context.app_name (string), context.description (string)
ASSISTANT: What is your application called?
USER: It's called Acme.
Output:
{{"updates": [{{"field": "context.app_name", "value": "Acme", "confidence": 0.95}}]}}
NOTE: description was NOT mentioned by the user, so it is skipped entirely.

Example 3 — user says nothing relevant to target fields:
Target: ui.has_dark_mode (boolean), data.has_pagination (boolean)
ASSISTANT: Tell me about your project.
USER: It's an internal HR tool for our company.
Output:
{{"updates": []}}
NOTE: The user described the project but said nothing about dark mode or pagination. Return empty.

Example 4 — do NOT infer from context:
Target: context.is_public (boolean), ui.is_responsive (boolean)
ASSISTANT: What does your app do?
USER: It's a calendar app for students.
Output:
{{"updates": []}}
NOTE: "calendar app for students" does NOT tell us if it is public or responsive. Do NOT guess.

Example 5 — user asks a question, NOT answering:
Target: ui.has_accessibility_requirements (boolean)
ASSISTANT: Does your app have any accessibility requirements?
USER: Give me an example of accessibility requirements.
Output:
{{"updates": []}}
NOTE: The user is asking for clarification, NOT stating they have accessibility requirements. Skip.

RULES:
1. ONLY extract what the user LITERALLY said in their message. Never infer, assume, or fill in values based on what seems logical.
2. "yes"/"yeah"/"yep" = true. "no"/"nope"/"nah" = false.
3. Short replies ("yes", "no") answer the assistant's most recent question before that reply.
4. Match the type shown in parentheses for each target field.
5. If the user gave multiple answers for the same field, use the most recent one.
6. If the user did NOT clearly address a field, SKIP it. Return fewer updates rather than wrong ones.
7. If the user asks a question (e.g. "what does that mean?", "give me an example"), they are NOT answering — skip that field.
8. confidence: 0.0 to 1.0. Only include fields where confidence >= 0.8.

Return ONLY valid JSON. No explanation. No markdown fences.
{{"updates": [...]}}
"""


class ValidationService:
    def __init__(self, runner: Runner, agent: Runnable) -> None:
        self.runner = runner
        self.agent = agent

    def _path_exists(self, schema: Schema, path: str) -> bool:
        keys = path.split(".")
        current = schema
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return False
            current = current[key]
        return True

    def _infer_field_type(self, schema: Schema, path: str) -> str:
        keys = path.split(".")
        field_name = keys[-1]
        current = schema
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return "string"
        if current is None:
            if field_name.startswith("has_") or field_name.startswith("is_"):
                return "boolean"
            return "string"
        if isinstance(current, list):
            return "list"
        if isinstance(current, bool):
            return "boolean"
        return "string"

    def _coerce_value(self, value: Any, schema: Schema, path: str) -> Any:
        expected_type = self._infer_field_type(schema, path)

        if expected_type == "boolean":
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                if value.strip().lower() in TRUTHY:
                    return True
                if value.strip().lower() in FALSY:
                    return False
            return None

        if expected_type == "list":
            if isinstance(value, list):
                return value
            if isinstance(value, str):
                return [item.strip() for item in value.split(",") if item.strip()]
            return None

        # string
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, bool):
            return None
        return str(value)

    def _build_conversation_window(
        self, history: List[ContextMessage], max_turns: int = MAX_CONVERSATION_TURNS
    ) -> str:
        if not history:
            return ""

        first_user_msg = next((m for m in history if m.role == "user"), None)
        recent = history[-max_turns:]

        parts: List[str] = []
        if first_user_msg and first_user_msg not in recent:
            parts.append(f"[INITIAL MESSAGE]\nUSER: {first_user_msg.content}")

        for msg in recent:
            label = "ASSISTANT" if msg.role == "assistant" else "USER"
            parts.append(f"{label}: {msg.content}")

        return "\n\n".join(parts)

    def _split_into_sections(
        self, history: List[ContextMessage], conversation_text: str
    ) -> str:
        latest_user = None
        latest_assistant_before_user = None

        for i in range(len(history) - 1, -1, -1):
            if history[i].role == "user" and latest_user is None:
                latest_user = history[i]
            elif history[i].role == "assistant" and latest_user is not None:
                latest_assistant_before_user = history[i]
                break

        if latest_assistant_before_user and latest_user:
            latest_exchange = (
                f"ASSISTANT: {latest_assistant_before_user.content}\n"
                f"USER: {latest_user.content}"
            )
        elif latest_user:
            latest_exchange = f"USER: {latest_user.content}"
        else:
            return f"CONVERSATION:\n{conversation_text}"

        prior_lines = []
        cutoff = len(history)
        if latest_assistant_before_user:
            cutoff = history.index(latest_assistant_before_user)
        elif latest_user:
            cutoff = history.index(latest_user)

        first_user_msg = next((m for m in history if m.role == "user"), None)

        for msg in history[:cutoff]:
            label = "ASSISTANT" if msg.role == "assistant" else "USER"
            prior_lines.append(f"{label}: {msg.content}")

        if (
            first_user_msg
            and first_user_msg not in history[:cutoff]
            and first_user_msg not in history[cutoff:]
        ):
            prior_lines.insert(0, f"[INITIAL MESSAGE]\nUSER: {first_user_msg.content}")

        sections = ""
        if prior_lines:
            sections += "PRIOR CONTEXT:\n" + "\n\n".join(prior_lines) + "\n\n"
        sections += "LATEST EXCHANGE:\n" + latest_exchange

        return sections

    def _format_target_fields(
        self, missing_questions: List[Dict], schema: Schema
    ) -> str:
        lines = []
        for mq in missing_questions:
            field = mq["field"]
            hint = mq["question_hint"]
            field_type = self._infer_field_type(schema, field)
            lines.append(f"- {field} ({field_type}) — {hint}")
        return "\n".join(lines)

    def _strip_markdown(self, response: str) -> str:
        response = response.strip()
        if response.startswith("```"):
            lines = response.split("\n", 1)
            if len(lines) > 1:
                response = lines[1]
            else:
                response = response.lstrip("`").rstrip("`")
                if response.lower().startswith("json"):
                    response = response[4:]
                return response.strip()
        if response.endswith("```"):
            response = response[:-3]
        return response.strip()

    def extract_updates(
        self,
        history: List[ContextMessage],
        schema: Schema,
        missing_questions: List[Dict] | None = None,
    ) -> Schema:
        if not history or not any(m.role == "user" for m in history):
            return {}

        conversation_text = self._build_conversation_window(history)
        if not conversation_text:
            return {}

        conversation_sections = self._split_into_sections(history, conversation_text)

        if missing_questions:
            target_fields = self._format_target_fields(missing_questions, schema)
        else:
            target_fields = "N/A"

        prompt = VALIDATION_PROMPT.format(
            target_fields=target_fields,
            conversation_sections=conversation_sections,
        )

        # logger.debug(self.normalized("Full validation prompt", prompt))

        try:
            response = self.runner.invoke_agent(self.agent, prompt)
        except AgentExecutionError:
            logger.error(
                "Failed to extract updates due to agent execution error.",
            )
            raise

        # logger.debug(self.normalized("Raw LLM response", response))

        response = self._strip_markdown(response)

        target_field_set = (
            {mq["field"] for mq in missing_questions} if missing_questions else set()
        )

        try:
            raw = json.loads(response)
            updates = raw.get("updates", [])

            # logger.debug(self.normalized("Parsed updates from LLM", updates))

            normalized = {}
            for item in updates:
                value = item.get("value")
                field = item.get("field", "")
                confidence = item.get("confidence", 0)

                if value is None or value == "" or value == []:
                    logger.debug(self.normalized("Skipped for empty value", field))
                    continue

                if field not in target_field_set:
                    logger.debug(self.normalized("Skipped for not being in target fields", field))
                    continue

                if confidence < CONFIDENCE_THRESHOLD:
                    logger.debug(
                        self.normalized("Skipped for confidence {confidence} < {CONFIDENCE_THRESHOLD}", field)
                    )
                    continue

                if not self._path_exists(schema, field):
                    logger.debug(self.normalized(
                            f"Skipped {field}: path does not exist in schema",
                            field
                        )
                    )
                    continue

                coerced = self._coerce_value(value, schema, field)
                if coerced is not None and coerced != "" and coerced != []:
                    normalized[field] = coerced
                else:
                    logger.debug(self.normalized(
                        f"Skipped for failing coercion value {value}",
                        field
                        )
                    )

            return normalized

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error("Failed to parse updates from response", exc_info=e)
            return {}
    
    def normalized(self, title: str, text: str) -> str:
        markdown = "------"

        header = f"\n{markdown} {title} {markdown}\n"
        body = str(text)
        footer = f"\n{markdown}{"-" * (len(title) + 2)}{markdown}\n"

        return header + body + footer
