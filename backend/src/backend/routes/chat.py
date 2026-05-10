import logging

from fastapi import APIRouter, Depends, HTTPException, status

from backend.core.auth import get_current_user_id
from backend.schemas.constants import ContextMessage
from backend.schemas.api import ChatRequest, ChatResponse
from backend.core.build_orchestrator import build_orchestrator
from backend.core.session_repository import add_message, get_session_by_id
from backend.schemas.exceptions import (
    AgentExecutionError,
    DatabaseError,
    SessionLoadError,
    SessionUpdateError,
    MessageSaveError
)

logger = logging.getLogger(__name__)

router = APIRouter()

active_orchestrator = build_orchestrator()

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, user_id: str = Depends(get_current_user_id)) -> ChatResponse:
    session = get_session_by_id(request.session_id, user_id)
    if session.id == "0":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found."
        )

    try:
        user_message = add_message(
            session_id=request.session_id,
            message=ContextMessage(role="user", content=request.message)
        )
    except DatabaseError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to save message."
        )
    
    try:
        response = active_orchestrator.handle_message(
            user_id=user_id,
            session_id=request.session_id,
            user_input=request.message
        )
    
    except AgentExecutionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to execute agent."
        )

    except SessionLoadError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to load session."
        )
    
    except MessageSaveError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to save the message."
        )
    
    except SessionUpdateError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to update session."
        )

    except Exception:
        logger.exception("Unexpected error in chat_endpoint.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected server error."
        )

    return ChatResponse(
        status=status.HTTP_200_OK,
        user_message=user_message,
        reply_message=response.reply_message,
        completed=response.completed,
    )