from typing import Dict

from backend.schemas.constants import AppType
from backend.agents.specialist.web_agent import WebAgent
from backend.agents.specialist.mobile_agent import MobileAgent
from backend.agents.specialist.desktop_agent import DesktopAgent
from backend.agents.specialist.api_agent import APIAgent
from backend.agents.specialist.other_agent import OtherAgent
from backend.agents.specialist.base_agent import BaseSpecialistAgent

class AgentRegistry:
    def __init__(self) -> None:
        self._agents: Dict[str, BaseSpecialistAgent] = {
            AppType.WEB: WebAgent(),
            AppType.MOBILE: MobileAgent(),
            AppType.DESKTOP: DesktopAgent(),
            AppType.API: APIAgent(),
            AppType.OTHER: OtherAgent(),
            AppType.UNKNOWN: OtherAgent(),
        }

    def get(self, app_type: AppType) -> BaseSpecialistAgent:
        return self._agents.get(app_type, self._agents[AppType.UNKNOWN])
