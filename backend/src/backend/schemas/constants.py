from __future__ import annotations

from typing import TYPE_CHECKING, List, Dict, Any, Literal
from dataclasses import dataclass
from enum import Enum

if TYPE_CHECKING:
    from backend.schemas.db import MessageModel


QWEN2_5_MODEL = "qwen2.5:latest"
GPT_MODEL = "gpt-oss:latest"
MISTRAL_CL = "mistral-large-3:675b-cloud"


type Schema = Dict[str, Any]
type SchemaBlock = Dict[str, Any]
type LLMResponse = Dict[str, Any]
type Messages = List[ContextMessage]
type Hints = Dict[str, str]


class AppType(str, Enum):
    WEB = "web"
    MOBILE = "mobile"
    DESKTOP = "desktop"
    API = "api"
    OTHER = "other"
    UNKNOWN = "unknown"


@dataclass
class ContextMessage:
    role: str
    content: str


@dataclass
class OrchestratorResponse:
    reply_message: MessageModel
    completed: bool


@dataclass
class AppTypeRouter:
    type: Literal["web", "mobile", "desktop", "api"]


@dataclass
class SpecialistDefinition:
    schema: Schema
    schema_filename: str
    hints_map: Hints
    domain_rules: str


class Priority(str, Enum):
    HIGH = 0
    MEDIUM = 1
    LOW = 2


type PriorityMap = Dict[Priority, List[str]]
