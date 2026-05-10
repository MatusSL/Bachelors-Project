from typing import Dict, List
from backend.schemas.constants import Hints, PriorityMap


class BaseSpecialistAgent:
    schema_file: str = ""
    hints_map: Hints = {}
    domain_rules = ""

    def get_schema_filename(self) -> str:
        return self.schema_file

    def get_hints_map(self) -> Hints:
        return self.hints_map

    def set_hints_map(self, _hints_map: Hints) -> None:
        self.hints_map = _hints_map

    def get_domain_rules(self) -> str:
        return self.domain_rules

    def set_domain_rules(self, _domain_rules: str) -> None:
        self.domain_rules = _domain_rules

    def get_risk_rules(self) -> List[Dict]:
        return []

    def get_priority_map(self) -> PriorityMap:
        return {}
