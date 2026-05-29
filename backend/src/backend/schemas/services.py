from dataclasses import dataclass
from pathlib import Path

from backend.schemas.protocols import (
    DomainRulesProtocol,
    HintsGeneratorProtocol,
    RunnerProtocol,
    RouterServiceProtocol,
    IntentDetectorProtocol,
    ConversationalAgentProtocol,
    SchemaGeneratorProtocol,
    ValidationServiceProtocol,
    SpecialistGeneratorProtocol,
    ChecklistGeneratorProtocol
)

@dataclass
class OrchestratorServices:
    runner: RunnerProtocol
    router_service: RouterServiceProtocol
    intent_detector: IntentDetectorProtocol
    conversational_agent: ConversationalAgentProtocol
    validation_service: ValidationServiceProtocol
    specialist_generator: SpecialistGeneratorProtocol
    checklist_generator: ChecklistGeneratorProtocol
    schema_dir: Path


@dataclass
class SpecialistServices:
    schema_generator: SchemaGeneratorProtocol
    hints_generator: HintsGeneratorProtocol
    domain_rules_generator: DomainRulesProtocol