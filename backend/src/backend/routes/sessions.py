from typing import List

from backend.schemas.exceptions import DatabaseError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse


from backend.core.auth import get_current_user_id

from backend.schemas.db import MessageModel
from backend.schemas.api import CreateSessionResponse, SessionModel
from backend.core.checklist_parser import parse_checklist
from backend.core.excel_export import generate_excel
from backend.core.session_repository import (
    create_session,
    delete_session,
    get_messages_by_session_id,
    get_session_by_id,
    list_sessions
)


router = APIRouter()


@router.post("/sessions", response_model=CreateSessionResponse)
def create_session_endpoint(user_id: str = Depends(get_current_user_id)) -> CreateSessionResponse:
    try:
        session = create_session(user_id)
        if session.id == "0":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to create session."
            )

        return CreateSessionResponse(session=session)

    except DatabaseError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection error."
        )


@router.get("/sessions", response_model=List[SessionModel])
def sessions_endpoint(user_id: str = Depends(get_current_user_id)) -> List[SessionModel]:
    try:
        return list_sessions(user_id)

    except DatabaseError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable."
        )


@router.get("/sessions/{id}", response_model=List[MessageModel])
def session_by_id_endpoint(id: str) -> List[MessageModel]:
    try:
        messages = get_messages_by_session_id(id)
        if len(messages) == 1 and messages[0].session_id == "0":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database unavailable."
            )

        return messages
    
    except DatabaseError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable."
        )


@router.delete("/sessions/{id}")
def delete_session_endpoint(id: str, user_id: str = Depends(get_current_user_id)):
    try:
        delete_session(id, user_id)

    except DatabaseError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to delete session."
        )


@router.get("/sessions/{id}/export")
def export_session_endpoint(id: str, user_id: str = Depends(get_current_user_id)):
    try:
        session = get_session_by_id(id, user_id)
    except DatabaseError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable."
        )

    if session.id == "0":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found."
        )

    if not session.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session checklist is not yet completed."
        )

    try:
        messages = get_messages_by_session_id(id)
    except DatabaseError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable."
        )

    checklist_message = next(
        (
            m for m in reversed(messages)
            if m.role == "assistant"
            and ("[HIGH PRIORITY]" in m.content or "[MEDIUM PRIORITY]" in m.content)
        ),
        None,
    )

    if checklist_message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No checklist found in this session."
        )

    rows = parse_checklist(checklist_message.content)
    buffer = generate_excel(rows)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=\"checklist-{id}.xlsx\""},
    )
