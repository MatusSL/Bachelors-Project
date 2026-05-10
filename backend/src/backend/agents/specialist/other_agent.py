from backend.agents.specialist.base_agent import BaseSpecialistAgent
from backend.schemas.constants import AppType, Hints


class OtherAgent(BaseSpecialistAgent):
    app_type = AppType.OTHER
    schema_file = "other.json"
    hints_map = {}
    domain_rules = ""

    def get_domain_rules(self) -> str:
        return self.domain_rules

    def set_domain_rules(self, _domain_rules: str) -> None:
        self.domain_rules = _domain_rules

    def set_hints_map(self, _hints_map: Hints) -> None:
        self.hints_map = _hints_map
