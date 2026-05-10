from typing import Dict, List, Protocol

from backend.schemas.constants import (
    AppType,
    ContextMessage,
    Hints,
    Messages,
    PriorityMap,
    Schema,
    SpecialistDefinition
)
from langchain_core.runnables import Runnable

class RunnerProtocol(Protocol):
    def invoke_agent(self, agent: Runnable, user_input: str) -> str: ...


class RouterServiceProtocol(Protocol):
    def detect_app_type(self, user_input: str) -> AppType: ...


class ConversationalAgentProtocol(Protocol):
    def reply(
        self,
        domain_rules: str,
        schema: Dict,
        missing_questions: List[Dict],
        history: List[ContextMessage],
        user_input: str,
    ) -> str: ...


class ValidationServiceProtocol(Protocol):
    def extract_updates(self, history: Messages, schema: Schema, missing_questions: List[Dict] | None = None) -> Schema: ...


class SchemaGeneratorProtocol(Protocol):
    def generate_schema(
        self, schemas: List[Schema], project_description: str
    ) -> Schema: ...


class HintsGeneratorProtocol(Protocol):
    def generate_hints(self, new_schema: Schema) -> Hints: ...


class DomainRulesProtocol(Protocol):
    def generate(self, new_schema: Schema, project_description: str) -> str: ...


class SpecialistGeneratorProtocol(Protocol):
    def generate_specialist(
        self, project_description: str, schemas: List[Schema]
    ) -> SpecialistDefinition: ...


class ChecklistGeneratorProtocol(Protocol):
    def generate(
        self,
        schema: Schema,
        domain_rules: str,
        risk_rules: List[Dict],
        priority_map: PriorityMap,
    ) -> str: ...