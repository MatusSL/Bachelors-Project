from datetime import datetime, timezone
from enum import Enum

from backend.schemas.constants import AppType, Schema
from pydantic import BaseModel, Field


class Table(str, Enum):
    SESSIONS = "sessions"
    MESSAGES = "messages"
    def __str__(self) -> str:
        return self.value

class Session(str, Enum):
    ID = "id"
    TITLE = "title"
    APP_TYPE = "app_type"
    COMPLETED = "completed"
    SCHEMA = "schema"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    USER_ID = "user_id"
    def __str__(self) -> str:
        return self.value

class Message(str, Enum):
    ID = "id"
    SESSION_ID = "session_id"
    ROLE = "role"
    CONTENT = "content"
    CREATED_AT = "created_at"
    def __str__(self) -> str:
        return self.value


class SessionModel(BaseModel):
    id: str
    title: str
    app_type: AppType | None
    completed: bool
    json_schema: Schema | None
    user_id: str | None = None


class MessageModel(BaseModel):
    # id: str
    session_id: str
    role: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
