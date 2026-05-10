import logging
from typing import Dict, List

from backend.agents.specialist.base_agent import BaseSpecialistAgent
from backend.core.agent_registry import AgentRegistry
from backend.core.session_manager import SessionManager
from backend.core.session_state import SessionState
from backend.schemas.constants import (
    AppType,
    ContextMessage,
    OrchestratorResponse,
    Schema,
)
from backend.schemas.db import MessageModel
from backend.core.session_repository import (
    db_to_session_state,
    update_session,
    add_message,
)
from backend.schemas.exceptions import (
    DatabaseError,
    SessionUpdateError,
    MessageSaveError,
    SessionLoadError,
)
from backend.schemas.services import OrchestratorServices


logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self, services: OrchestratorServices) -> None:
        self.runner = services.runner
        self.router_service = services.router_service
        self.conversational_agent = services.conversational_agent
        self.validation_service = services.validation_service
        self.specialist_generator = services.specialist_generator
        self.checklist_generator = services.checklist_generator
        self.registry = AgentRegistry()
        self.session_manager = SessionManager(services.schema_dir)

    def handle_message(self, user_id: str, session_id: str, user_input: str) -> OrchestratorResponse:
        try:
            state = db_to_session_state(user_id, session_id)

        except DatabaseError as e:
            raise SessionLoadError() from e

        if state.active_agent_name == "fallback":
            return self.get_orchestrator_response_fallback()

        if state.app_type == AppType.UNKNOWN:
            self.handle_unknown_app(user_input, state)

        specialist = self.registry.get(state.app_type)

        prev_block = self.session_manager.get_next_block(state.schema)
        prev_missing_fields = self.session_manager.find_missing_fields(prev_block)
        prev_missing_questions = self.get_missing_questions(
            specialist, prev_missing_fields
        )

        # logger.debug(f"\n{prev_missing_questions=}\n")

        updates = self.get_updates(state, prev_missing_questions)

        logger.debug(self.normalized("UPDATES", str(updates)))

        self.merge_updates_with_schema(state, updates)

        next_block = self.session_manager.get_next_block(state.schema)
        missing_fields = self.session_manager.find_missing_fields(next_block)
        missing_questions = self.get_missing_questions(specialist, missing_fields)

        logger.debug(self.normalized("MISSING QUESTIONS", str(missing_questions)))

        if not missing_questions:
            state.completed = True
            reply = self.checklist_generator.generate(
                schema=state.schema,
                domain_rules=specialist.get_domain_rules(),
                risk_rules=specialist.get_risk_rules(),
                priority_map=specialist.get_priority_map(),
            )
        else:
            history_without_last_user = (
                state.history[:-1]
                if state.history and state.history[-1].role == "user"
                else state.history
            )
            reply = self.conversational_agent.reply(
                domain_rules=specialist.get_domain_rules(),
                schema=state.schema,
                missing_questions=missing_questions,
                history=history_without_last_user,
                user_input=user_input,
            )

        reply_message = ContextMessage(role="assistant", content=reply)
        try:
            response = add_message(session_id, reply_message)

        except DatabaseError as e:
            raise MessageSaveError() from e

        try:
            update_session(id=session_id, state=state)

        except DatabaseError as e:
            raise SessionUpdateError() from e

        return OrchestratorResponse(reply_message=response, completed=state.completed)

    def handle_unknown_app(self, user_input: str, state: SessionState) -> None:
        app_type = self.router_service.detect_app_type(user_input)
        state.app_type = app_type
        logger.debug(f"\n{app_type=}\n")

        specialist = self.registry.get(app_type)
        schema = self.session_manager.get_schema(specialist.schema_file)

        if schema is None:
            new_specialist_definition = self.specialist_generator.generate_specialist(
                project_description=user_input,
                schemas=self.session_manager.load_all_schemas(),
            )

            state.schema = new_specialist_definition.schema
            state.active_agent_name = state.schema["type"]
            specialist.set_domain_rules(new_specialist_definition.domain_rules)
            specialist.set_hints_map(new_specialist_definition.hints_map)

        else:
            state.schema = schema
            state.active_agent_name = app_type.value

    def get_updates(
        self, state: SessionState, missing_questions: List[Dict] | None = None
    ) -> Schema:
        updates = self.validation_service.extract_updates(
            history=state.history,
            schema=state.schema,
            missing_questions=missing_questions,
        )

        return updates

    def merge_updates_with_schema(self, state: SessionState, updates: Schema) -> None:
        state.schema = self.session_manager.merge_updates(
            schema=state.schema,
            updates=updates,
        )

    def get_missing_questions(
        self, specialist: BaseSpecialistAgent, missing_fields: List[str]
    ):
        return [
            {
                "field": field,
                "question_hint": specialist.get_hints_map().get(
                    field, "describe this field"
                ),
            }
            for field in missing_fields
        ]

    def get_orchestrator_response_fallback(self) -> OrchestratorResponse:
        return OrchestratorResponse(
            reply_message=MessageModel(
                session_id="0",
                role="",
                content="",
            ),
            completed=False,
        )
    
    def normalized(self, title: str, text: str) -> str:
        markdown = "------"

        header = f"\n{markdown} {title} {markdown}\n"
        body = str(text)
        footer = f"\n{markdown}{"-" * (len(title) + 2)}{markdown}\n"

        return header + body + footer
