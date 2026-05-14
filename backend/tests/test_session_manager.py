from __future__ import annotations

import json

import pytest

from backend.core.session_manager import SessionManager


def test_get_schema_returns_none_for_dynamic_other_schema(schema_dir):
    manager = SessionManager(schema_dir)

    assert manager.get_schema("other.json") is None


def test_load_all_schemas_loads_supported_static_schema_files(schema_dir):
    manager = SessionManager(schema_dir)

    schemas = manager.load_all_schemas()

    assert [schema["type"] for schema in schemas] == [
        "desktop-application",
        "web-application",
        "api",
        "mobile-application",
    ]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, True),
        ("", True),
        ([], True),
        ({}, False),
        (False, False),
        (0, False),
        ("value", False),
        ([0], False),
    ],
)
def test_is_missing_only_flags_unanswered_schema_values(schema_dir, value, expected):
    manager = SessionManager(schema_dir)

    assert manager.is_missing(value) is expected


def test_find_missing_fields_skips_private_metadata_and_dependency_children(schema_dir, web_schema):
    manager = SessionManager(schema_dir)
    web_schema["context"] = {
        "app_name": "Planner",
        "description": "Team planning",
        "target_audience": "Managers",
        "is_public": False,
    }
    web_schema["ui"]["has_browser_constraints"] = False
    web_schema["ui"]["has_device_constraints"] = False

    missing = manager.find_missing_fields(web_schema["ui"], "ui")

    assert "_depends_on" not in missing
    assert "ui.supported_browsers" not in missing
    assert "ui.supported_devices" not in missing
    assert "ui.is_responsive" in missing
    assert "ui.has_dark_mode" in missing


def test_find_missing_fields_skips_entire_block_when_its_gate_is_false(schema_dir):
    manager = SessionManager(schema_dir)
    block = {
        "has_auth": False,
        "auth_types": [],
        "roles": [],
        "nested": {"empty": ""},
    }

    assert manager.find_missing_fields(block, "auth") == []


def test_block_has_missing_values_returns_false_when_block_gate_is_disabled(schema_dir):
    manager = SessionManager(schema_dir)
    block = {
        "has_payments": False,
        "provider": "",
        "currency": None,
    }

    assert manager.block_has_missing_values(block, "payments") is False


def test_block_has_missing_values_respects_nested_dependency_gates(schema_dir):
    manager = SessionManager(schema_dir)
    block = {
        "has_api": False,
        "api_type": "",
        "_depends_on": {"api_type": "has_api"},
        "has_third_party_services": True,
        "third_party_services": [],
    }

    assert manager.block_has_missing_values(block, "integrations") is True

    block["third_party_services"] = ["Stripe"]
    assert manager.block_has_missing_values(block, "integrations") is False


def test_get_next_block_uses_declared_order_before_later_missing_sections(schema_dir, web_schema):
    manager = SessionManager(schema_dir)
    web_schema["context"] = {
        "app_name": "Planner",
        "description": "Team planning",
        "target_audience": "Managers",
        "is_public": False,
    }

    assert manager.get_next_block(web_schema) == {"ui": web_schema["ui"]}


def test_get_next_block_returns_extra_schema_blocks_after_known_order_is_complete(schema_dir):
    manager = SessionManager(schema_dir)
    schema = {
        "type": "web-application",
        "context": {"app_name": "A", "description": "B", "target_audience": "C", "is_public": True},
        "notes": "",
        "custom": {"field": ""},
    }

    assert manager.get_next_block(schema) == {"custom": {"field": ""}}


def test_get_next_block_returns_empty_dict_when_schema_has_no_missing_values(schema_dir):
    manager = SessionManager(schema_dir)
    schema = {
        "type": "web-application",
        "context": {"app_name": "A", "description": "B", "target_audience": "C", "is_public": True},
        "notes": "",
    }

    assert manager.get_next_block(schema) == {}


def test_merge_updates_changes_nested_values_in_place(schema_dir, web_schema):
    manager = SessionManager(schema_dir)

    result = manager.merge_updates(
        web_schema,
        {
            "context.app_name": "Roadmap",
            "ui.has_dark_mode": True,
            "auth.session_management.has_session_expiry": False,
        },
    )

    assert result is web_schema
    assert web_schema["context"]["app_name"] == "Roadmap"
    assert web_schema["ui"]["has_dark_mode"] is True
    assert web_schema["auth"]["session_management"]["has_session_expiry"] is False


def test_merge_updates_raises_for_unknown_nested_path(schema_dir, web_schema):
    manager = SessionManager(schema_dir)

    with pytest.raises(KeyError):
        manager.merge_updates(web_schema, {"context.missing.value": "x"})


def test_save_schema_uses_type_as_filename(tmp_path):
    manager = SessionManager(tmp_path)
    schema = {"type": "generated.json", "context": {"name": "Generated"}}

    manager.save_schema(schema)

    assert json.loads((tmp_path / "generated.json").read_text()) == schema
