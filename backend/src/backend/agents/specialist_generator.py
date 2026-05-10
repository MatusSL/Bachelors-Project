from typing import List

from backend.schemas.constants import Schema, SpecialistDefinition
from backend.schemas.services import SpecialistServices


class SpecialistGenerator:
    def __init__(self, services: SpecialistServices) -> None:
        self.hints_generator = services.hints_generator
        self.schema_generator = services.schema_generator
        self.domain_rules_generator = services.domain_rules_generator

    def generate_specialist(self, project_description: str, schemas: List[Schema]) -> SpecialistDefinition:
        new_schema = self.schema_generator.generate_schema(schemas, project_description)
        hints_map = self.hints_generator.generate_hints(new_schema)
        domain_rules = self.domain_rules_generator.generate(
            new_schema, project_description
        )

        filename = new_schema["type"] + ".json"

        return SpecialistDefinition(
            schema=new_schema,
            schema_filename=filename,
            hints_map=hints_map,
            domain_rules=domain_rules,
        )
