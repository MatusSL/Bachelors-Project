import json
import logging

from backend.schemas.exceptions import AgentExecutionError
from langchain_core.runnables import Runnable

from backend.schemas.constants import Schema


logger = logging.getLogger(__name__)


class DomainRulesGenerator:
    def __init__(self, runner, agent: Runnable) -> None:
        self.runner = runner
        self.agent = agent

    def generate(self, new_schema: Schema, project_description: str) -> str:
        prompt = f"""
            You are a system that generates domain-specific guidance for requirement gathering agents.

            New schema:
            {json.dumps(new_schema, indent=2)}

            User project description:
            {project_description}

            Task:
            Generate DOMAIN RULES that guide an agent on how to ask questions and what to focus on.

            Requirements:
            - Output ONLY plain text (no JSON, no markdown)
            - Keep it concise (3-6 sentences)
            - Describe:
            - what aspects of the system are most important
            - what kinds of questions the agent should prioritize
            - any domain-specific concerns (e.g., performance, UX, security, workflows)
            - Align with the structure of the schema
            - Be specific to the domain implied by the schema and project description

            Example style:
            "Focus on command structure, argument handling, execution environment, and user workflows. Prioritize clarity of inputs and expected outputs. Ensure error handling and usability of the interface are well defined."

            Return only the domain rules text.
            """

        try:
            response = self.runner.invoke_agent(self.agent, prompt)
        except AgentExecutionError:
            logger.error(
                "Failed to generate domain rules due to agent execution error.",
            )
            raise

        text = response.strip()
        if text.startswith("```"):
            text = text.strip("`")
        return text.strip()
