import json
import logging
from typing import List

from backend.schemas.exceptions import AgentExecutionError
from langchain_core.runnables import Runnable

from backend.agents.runner import Runner
from backend.schemas.constants import Schema


logger = logging.getLogger(__name__)


def _strip_markdown_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text[: text.rfind("```")]
    return text.strip()


class SchemaGenerator:
    def __init__(self, agent: Runnable, runner: Runner) -> None:
        self.runner = runner
        self.agent = agent

    def generate_schema(
        self, schemas: List[Schema], project_description: str
    ) -> Schema:
        prompt = f"""
            You are a system that generates JSON schemas.

            Existing schemas:
            {json.dumps(schemas, indent=2)}

            User project description:
            {project_description}

            Task:
            Create a new schema following the same structure.

            Rules:
            - Output ONLY valid JSON
            - Include "type" field
            - Match structure of existing schemas
            """
        try:
            response = self.runner.invoke_agent(self.agent, prompt)
        except AgentExecutionError:
            logger.error(
                "Failed to generate schema due to agent execution error.",
            )
            raise


        try:
            return json.loads(_strip_markdown_json(response))
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON returned by model: {response}")
