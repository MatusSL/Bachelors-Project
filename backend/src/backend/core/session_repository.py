import logging
from typing import List

from httpx import HTTPError
from postgrest import APIError, APIResponse

from backend.core.session_state import SessionState
from backend.schemas.constants import AppType, ContextMessage
from backend.schemas.db import (
    Message,
    MessageModel,
    Session,
    SessionModel,
    Table
)
from backend.schemas.exceptions import DatabaseError

from backend.database.supabase_setup import get_supabase


logger = logging.getLogger(__name__)


def get_session_model_fallback() -> SessionModel:
    return SessionModel(
        id="0",
        title="",
        app_type=None,
        completed=False,
        json_schema=None
    )


def get_session_state_fallback() -> SessionState:
    return SessionState(
        app_type=AppType.UNKNOWN,
        schema={},
        history=[],
        active_agent_name="fallback",
        completed=False
    )


def is_valid_response(response: APIResponse) -> bool:
    if getattr(response, "data", None) is None:
        return False
    
    if len(response.data) == 0:
        return False
    
    return True


def create_session(user_id: str) -> SessionModel:
    try:
        response = (
            get_supabase()
                .table(Table.SESSIONS)
                .insert({Session.USER_ID: user_id})
                .execute()
        )

        if not is_valid_response(response):
            logger.error(
                "Response was empty while creating a session, no session_id found."
            )
            return get_session_model_fallback()

        return SessionModel.model_validate(response.data[0])

    except HTTPError as e:
        logger.error("Failed to connect to DB.", exc_info=e)
        raise DatabaseError() from e


    except APIError as e:
        logger.error("Failed to make new session", exc_info=e)
        raise DatabaseError() from e



def get_session_by_id(id: str, user_id: str | None = None) -> SessionModel:
    try:
        query = (
            get_supabase()
                .table(Table.SESSIONS)
                .select("*")
                .eq(Session.ID, id)
        )
        if user_id is not None:
            query = query.eq(Session.USER_ID, user_id)

        response = query.execute()

        if not is_valid_response(response):
            logger.error(
                "Response was empty while getting session by id."
            )
            return get_session_model_fallback()
        
        return SessionModel.model_validate(response.data[0])
    
    except HTTPError as e:
        logger.error(
            f"Failed to connect to DB when fetching session.{id=}.",
            exc_info=e
        )
        raise DatabaseError() from e

    except APIError as e:
        logger.error(
            f"Failed to query DB when fetching session.{id=}",
            exc_info=e
        )
        raise DatabaseError() from e


def list_sessions(user_id: str) -> List[SessionModel]:
    try:
        response = (
            get_supabase()
                .table(Table.SESSIONS)
                .select("*")
                .eq(Session.USER_ID, user_id)
                .order(Session.UPDATED_AT, desc=True)
                .execute()
        )
        if getattr(response, "data", None) is None:
            logger.error(
                f"Failed to get a valid response while fetching all sessons.\n{response=}"
            )
            return []

        return [SessionModel.model_validate(s) for s in response.data]

    except HTTPError as e:
        logger.error(
            "Failed to connect to the DB while getting all sessions.",
            exc_info=e
        )
        raise DatabaseError() from e

    except APIError as e:
        logger.error(
            "Failed to query the DB getting all sessions.",
            exc_info=e
        )
        raise DatabaseError() from e

def get_messages_by_session_id(session_id: str) -> List[MessageModel]:
    try:
        response = (
            get_supabase()
                .table(Table.MESSAGES)
                .select("*")
                .eq(Message.SESSION_ID, session_id)
                .order(Message.CREATED_AT)
                .execute()
        )

        if getattr(response, "data", None) is None:
            return [MessageModel(session_id="0", role="", content="")]

        return [MessageModel.model_validate(m) for m in response.data]
    
    except HTTPError as e:
        logger.error(
            f"Failed to connect to DB while getting messages by {session_id=}",
            exc_info=e
        )
        raise DatabaseError() from e

    except APIError as e:
        logger.error(
            f"Failed to query the DB while getting messages be {session_id=}",
            exc_info=e
        )
        raise DatabaseError() from e


def add_message(session_id: str, message: ContextMessage) -> MessageModel:
    payload = MessageModel(
        session_id=session_id,
        role=message.role,
        content=message.content
    )
    
    try:
        response = (
            get_supabase()
                .table(Table.MESSAGES)
                .insert(payload.model_dump(exclude={"created_at"}))
                .execute()
        )
        
        if not is_valid_response(response):
            return payload

        return MessageModel.model_validate(response.data[0])
    
    except HTTPError as e:
        logger.error(
            f"""
            Failed to connect to DB while adding
            message:\n{message.role}: {message.content}""",
            exc_info=e
        )
        raise DatabaseError() from e
    
    except APIError as e:
        logger.error(
            f"""
            Failed to query the DB while adding
            message:\n{message.role}: {message.content}""",
            exc_info=e
        )
        raise DatabaseError() from e


def delete_session(session_id: str, user_id: str) -> None:
    try:
        (
        get_supabase()
            .table(Table.SESSIONS)
            .delete()
            .eq(Session.ID, session_id)
            .eq(Session.USER_ID, user_id)
            .execute()
        )
    except HTTPError as e:
        logger.error(
            f"Failed to connect to DB while deleting session={session_id}",
            exc_info=e
        )
        raise DatabaseError() from e

    except APIError as e:
        logger.error(
            f"Failed to query the DB while deleting session={session_id}",
            exc_info=e
        )
        raise DatabaseError() from e


def update_session(id: str, state: SessionState) -> None:
    try:
        title = make_title_from_state(state)
        payload = SessionModel(
            id=id,
            title=title,
            app_type=state.app_type,
            completed=state.completed,
            json_schema=state.schema
        )
        (
        get_supabase()
            .table(Table.SESSIONS)
            .update(payload.model_dump(exclude={"id", "user_id"}))
            .eq(Session.ID, id)
            .execute()
        )

    except HTTPError as e:
        logger.error(
            f"Failed to connect to DB while updating session.{id=}",
            exc_info=e
        )
        raise DatabaseError() from e
    
    except APIError as e:
        logger.error(
            f"Failed to query the DB while updating session.{id=}",
            exc_info=e
        )
        raise DatabaseError() from e


def db_to_session_state(user_id: str, id: str) -> SessionState:
    session = get_session_by_id(id, user_id)
    if session.id == "0":
        return get_session_state_fallback()
    
    messages = get_messages_by_session_id(id)
    if len(messages) == 1 and messages[0].session_id == "0":
        return get_session_state_fallback()

    app_type = session.app_type or AppType.UNKNOWN
    schema = session.json_schema or {}
    history = [ContextMessage(role=m.role, content=m.content) for m in messages]

    return SessionState(
        app_type=app_type,
        schema=schema,
        history=history,
        active_agent_name=app_type,
        completed=session.completed
    )

def make_title_from_state(state: SessionState) -> str:
    app_type = state.app_type
    if app_type == AppType.UNKNOWN:
        type = ""
    else:
        type = app_type.capitalize()
    
    context = state.schema.get("context", {})
    if context == {}:
        return type
    
    type += ": "
    if app_type == AppType.API:
        suffix = "api_name"
    else:
        suffix = "app_name"

    app_name = context.get(suffix, None)
    if app_name is not None:
        return type + app_name

    return "New Conversation"
