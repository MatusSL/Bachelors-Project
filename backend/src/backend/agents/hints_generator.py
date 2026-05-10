import json
import logging

from backend.schemas.exceptions import AgentExecutionError
from langchain_core.runnables import Runnable

from backend.agents.runner import Runner
from backend.schemas.constants import Hints, Schema

from backend.agents.specialist.api_agent import api_hints_map
from backend.agents.specialist.desktop_agent import desktop_hints_map
from backend.agents.specialist.mobile_agent import mobile_hints_map
from backend.agents.specialist.web_agent import web_hints_map


logger = logging.getLogger(__name__)


def _strip_markdown_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text[: text.rfind("```")]
    return text.strip()


class HintsGenerator:
    def __init__(self, agent: Runnable, runner: Runner) -> None:
        self.runner = runner
        self.agent = agent

    def generate_hints(self, new_schema: Schema) -> Hints:
        existing_hints = [
            api_hints_map,
            desktop_hints_map,
            mobile_hints_map,
            web_hints_map,
        ]

        prompt = f"""
            You are a system that generates field-level hints for a JSON schema.

            Existing hints (reference patterns):
            {json.dumps(existing_hints, indent=2)}

            New schema:
            {json.dumps(new_schema, indent=2)}

            Task:
            Generate a hints map for the new schema.

            Requirements:
            - Output ONLY valid JSON
            - The output must be a flat dictionary: field_path -> description
            - Field paths must use dot notation (e.g., "context.app_name", "auth.type")
            - Each value must be a short, clear description of what the field represents
            - Reuse naming and style patterns from existing hints where possible
            - Cover all relevant fields in the schema

            Return format:
            {{
                "field.path": "description",
                ...
            }}
            """

        try:
            response = self.runner.invoke_agent(self.agent, prompt)
        except AgentExecutionError:
            logger.error(
                "Failed to generate hints due to agent execution error.",
            )
            raise

        try:
            return json.loads(_strip_markdown_json(response))
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse hints JSON: {response}") from e
