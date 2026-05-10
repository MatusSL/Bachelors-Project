from typing import Literal

from backend.schemas.db import MessageModel, SessionModel
from pydantic import BaseModel


class CreateSessionResponse(BaseModel):
    session: SessionModel


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    status: Literal[200]
    user_message: MessageModel
    reply_message: MessageModel
    completed: bool
