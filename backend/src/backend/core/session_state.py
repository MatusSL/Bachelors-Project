from dataclasses import dataclass, field
from typing import List

from backend.schemas.constants import AppType, ContextMessage, Schema


@dataclass
class SessionState:
    app_type: AppType = AppType.UNKNOWN
    schema: Schema = field(default_factory=dict)
    history: List[ContextMessage] = field(default_factory=list)
    active_agent_name: str = "router"
    completed: bool = False
