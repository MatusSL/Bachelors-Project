from pathlib import Path
from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langchain.chat_models import BaseChatModel

from backend.agents.checklist_generator import ChecklistGenerator
from backend.agents.domain_rules_generator import DomainRulesGenerator
from backend.agents.hints_generator import HintsGenerator
from backend.agents.runner import Runner
from backend.agents.conversation_agent import ConversationalAgent
from backend.agents.schema_generator import SchemaGenerator
from backend.agents.specialist_generator import SpecialistGenerator
from backend.agents.validation_agent import ValidationService
from backend.agents.router_agent import RouterService
from backend.agents.intent_detector import IntentDetector
from backend.core.orchestrator import Orchestrator
from backend.schemas.constants import QWEN2_5_MODEL, GPT_MODEL
from backend.schemas.services import OrchestratorServices, SpecialistServices


def resolve_schema_dir() -> Path:
    current = Path(__file__).resolve()
    while not (current / "project-checklist-schemas").exists():
        current = current.parent
    return current / "project-checklist-schemas"


def create_conversational_agent(runner: Runner, model: BaseChatModel) -> ConversationalAgent:
    return ConversationalAgent(runner=runner, model=model)


def create_router_service(runner: Runner, model: BaseChatModel) -> RouterService:
    agent = create_agent(model=model)
    return RouterService(runner=runner, router_agent=agent)


def create_intent_detector(runner: Runner, model: BaseChatModel) -> IntentDetector:
    agent = create_agent(model=model)
    return IntentDetector(runner=runner, agent=agent)


def create_validation_service(runner: Runner, model: BaseChatModel) -> ValidationService:
    agent = create_agent(model=model)
    return ValidationService(runner=runner, agent=agent)


def create_domain_rules_generator(runner: Runner, model: BaseChatModel) -> DomainRulesGenerator:
    agent = create_agent(model=model)
    return DomainRulesGenerator(runner=runner, agent=agent)


def create_schema_generator(runner: Runner, model: BaseChatModel) -> SchemaGenerator:
    agent = create_agent(model=model)
    return SchemaGenerator(runner=runner, agent=agent)


def create_hints_generator(runner: Runner, model: BaseChatModel) -> HintsGenerator:
    agent = create_agent(model=model)
    return HintsGenerator(runner=runner, agent=agent)


def create_specialist_generator(runner: Runner) -> SpecialistGenerator:    
    HINTS_GENERATOR_MODEL = ChatOllama(model=QWEN2_5_MODEL, temperature=0)
    DOMAIN_RULES_GENERATOR_MODEL = ChatOllama(model=QWEN2_5_MODEL, temperature=0)
    SCHEMA_GENERATOR_MODEL = ChatOllama(model=GPT_MODEL, temperature=0)
    
    schema_generator = create_schema_generator(runner, SCHEMA_GENERATOR_MODEL)
    hints_generator = create_hints_generator(runner, HINTS_GENERATOR_MODEL)
    domain_rules_generator = create_domain_rules_generator(runner, DOMAIN_RULES_GENERATOR_MODEL)
    
    services = SpecialistServices(
        schema_generator=schema_generator,
        hints_generator=hints_generator,
        domain_rules_generator=domain_rules_generator,
    )
    return SpecialistGenerator(services=services)


def create_checklist_generator(runner: Runner, model: BaseChatModel) -> ChecklistGenerator:
    return ChecklistGenerator(runner=runner, model=model)


def build_orchestrator() -> Orchestrator:
    ROUTER_MODEL = ChatOllama(model=QWEN2_5_MODEL, temperature=0)
    INTENT_MODEL = ChatOllama(model=QWEN2_5_MODEL, temperature=0)
    CONVERSATIONAL_MODEL = ChatOllama(model=QWEN2_5_MODEL, temperature=0.3)

    VALIDATION_MODEL = ChatOllama(model=GPT_MODEL, temperature=0)
    CHECKLIST_GENERATOR_MODEL = ChatOllama(model=GPT_MODEL, temperature=0.3)

    runner = Runner()
    
    router_service = create_router_service(runner, ROUTER_MODEL)
    intent_detector = create_intent_detector(runner, INTENT_MODEL)

    validation_service = create_validation_service(runner, VALIDATION_MODEL)
    conversational_agent = create_conversational_agent(runner,CONVERSATIONAL_MODEL)

    checklist_generator = create_checklist_generator(runner, CHECKLIST_GENERATOR_MODEL)
    specialist_generator = create_specialist_generator(runner)

    schema_dir = resolve_schema_dir()

    services = OrchestratorServices(
        runner=runner,
        router_service=router_service,
        intent_detector=intent_detector,
        conversational_agent=conversational_agent,
        validation_service=validation_service,
        specialist_generator=specialist_generator,
        checklist_generator=checklist_generator,
        schema_dir=schema_dir,
    )

    return Orchestrator(services)
