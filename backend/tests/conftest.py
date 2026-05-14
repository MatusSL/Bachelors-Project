from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def schema_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "project-checklist-schemas"


@pytest.fixture
def web_schema(schema_dir: Path) -> dict[str, Any]:
    with (schema_dir / "web.json").open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def api_schema(schema_dir: Path) -> dict[str, Any]:
    with (schema_dir / "api.json").open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def clone_schema():
    def _clone(schema: dict[str, Any]) -> dict[str, Any]:
        return copy.deepcopy(schema)

    return _clone
