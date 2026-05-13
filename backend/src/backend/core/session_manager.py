import json
from pathlib import Path
from typing import Any, List
from backend.schemas.constants import Schema, SchemaBlock


EXCLUDED_BLOCKS = {"type", "notes"}

BLOCK_ORDER = {
    "web-application": [
        "context", "ui", "auth", "data", "integrations",
        "non_functional", "environment",
    ],
    "mobile-application": [
        "context", "distribution", "ui", "auth", "device_features",
        "data", "integrations", "non_functional", "environment",
    ],
    "desktop-application": [
        "context", "installation", "ui", "auth", "data",
        "os_integration", "integrations", "non_functional", "environment",
    ],
    "api": [
        "context", "auth", "endpoints", "data", "response_behavior",
        "non_functional", "integrations", "security", "environment",
    ],
}


class SessionManager:
    def __init__(self, schema_dir: Path) -> None:
        self.schema_dir = schema_dir

    def get_schema(self, filename: str) -> Schema | None:
        if filename == "other.json":
            return None

        return self.load_schema(filename)

    def load_schema(self, filename: str) -> Schema:
        path = self.schema_dir / filename
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_all_schemas(self) -> List[Schema]:
        schema_types = ["desktop", "web", "api", "mobile"]

        schemas: List[Schema] = []
        for schema_type in schema_types:
            filename = schema_type + ".json"
            schema = self.load_schema(filename)
            schemas.append(schema)

        return schemas

    def save_schema(self, schema: Schema) -> None:
        filename = schema["type"]
        path = self.schema_dir / filename

        with open(path, "w") as file:
            file.write(json.dumps(schema))

    def is_missing(self, value: Any) -> bool:
        return value is None or value == "" or value == []

    def _build_skip_set(self, block: SchemaBlock) -> set:
        skipped = set()

        depends_on = block.get("_depends_on", {})
        if isinstance(depends_on, dict):
            for field, gate_flag in depends_on.items():
                if block.get(gate_flag) is False:
                    skipped.add(field)

        for key, value in block.items():
            if key.startswith("has_") and value is False:
                skipped.add(key[4:])
        return skipped

    def block_has_missing_values(
        self, block: SchemaBlock, block_name: str = ""
    ) -> bool:
        gate = f"has_{block_name}"
        if gate in block and block[gate] is False:
            return False

        skipped = self._build_skip_set(block)

        for key, value in block.items():
            if key.startswith("_"):
                continue
            if key in skipped:
                continue
            if isinstance(value, dict):
                if self.block_has_missing_values(value, key):
                    return True
            elif self.is_missing(value):
                return True
        return False

    def find_missing_fields(self, schema: Schema, prefix: str = "") -> List[str]:
        missing: List[str] = []

        dict_name = prefix.split(".")[-1] if prefix else ""
        gate = f"has_{dict_name}" if dict_name else ""
        if gate and gate in schema and schema[gate] is False:
            return missing

        skipped = self._build_skip_set(schema)

        for key, value in schema.items():
            path = f"{prefix}.{key}" if prefix else key

            if key.startswith("_"):
                continue
            if key in skipped:
                continue

            if isinstance(value, dict):
                missing.extend(self.find_missing_fields(value, path))
            elif self.is_missing(value):
                missing.append(path)

        return missing

    def get_next_block(self, schema: Schema) -> Schema:
        schema_type = schema.get("type", "")
        order = BLOCK_ORDER.get(schema_type, [])

        for block_name in order:
            if block_name in schema:
                block = schema[block_name]
                if isinstance(block, dict) and self.block_has_missing_values(
                    block, block_name
                ):
                    return {block_name: block}

        for block_name, block in schema.items():
            if block_name in EXCLUDED_BLOCKS or block_name in order:
                continue
            if isinstance(block, dict) and self.block_has_missing_values(
                block, block_name
            ):
                return {block_name: block}

        return {}

    def set_nested_value(self, data: Schema, path: str, value: Any) -> None:
        keys = path.split(".")
        current = data
        for key in keys[:-1]:
            current = current[key]
        current[keys[-1]] = value

    def merge_updates(self, schema: Schema, updates: Schema) -> Schema:
        for path, value in updates.items():
            self.set_nested_value(schema, path, value)
        return schema


if __name__ == "__main__":

    def resolve_schema_dir() -> Path:
        current = Path(__file__).resolve()
        while not (current / "project-checklist-schemas").exists():
            current = current.parent

        schema_dir = current / "project-checklist-schemas"
        return schema_dir

    sm = SessionManager(resolve_schema_dir())
    schemas = sm.load_all_schemas()
