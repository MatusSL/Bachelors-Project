from __future__ import annotations

from dataclasses import dataclass

import pytest
from httpx import HTTPError

from backend.core import session_repository as repo
from backend.core.session_state import SessionState
from backend.schemas.constants import AppType, ContextMessage
from backend.schemas.db import Message, Session, Table
from backend.schemas.exceptions import DatabaseError


@dataclass
class Response:
    data: object


class FakeQuery:
    def __init__(self, response: Response | Exception | None = None) -> None:
        self.response = response if response is not None else Response([])
        self.operations: list[tuple] = []

    def select(self, *args):
        self.operations.append(("select", args))
        return self

    def insert(self, payload):
        self.operations.append(("insert", payload))
        return self

    def update(self, payload):
        self.operations.append(("update", payload))
        return self

    def delete(self):
        self.operations.append(("delete",))
        return self

    def eq(self, field, value):
        self.operations.append(("eq", field, value))
        return self

    def order(self, field, desc=False):
        self.operations.append(("order", field, desc))
        return self

    def execute(self):
        self.operations.append(("execute",))
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class FakeSupabase:
    def __init__(self, query: FakeQuery) -> None:
        self.query = query
        self.tables: list[Table] = []

    def table(self, table):
        self.tables.append(table)
        return self.query


def install_fake_supabase(monkeypatch, response: Response | Exception | None = None):
    query = FakeQuery(response)
    supabase = FakeSupabase(query)
    monkeypatch.setattr(repo, "get_supabase", lambda: supabase)
    return supabase, query


@pytest.mark.parametrize("response", [Response(None), Response([])])
def test_is_valid_response_rejects_missing_or_empty_data(response):
    assert repo.is_valid_response(response) is False


def test_is_valid_response_accepts_non_empty_data():
    assert repo.is_valid_response(Response([{"id": "1"}])) is True


def test_create_session_returns_created_model(monkeypatch):
    supabase, query = install_fake_supabase(
        monkeypatch,
        Response([
            {
                "id": "s1",
                "title": "",
                "app_type": "web",
                "completed": False,
                "json_schema": {"type": "web-application"},
                "user_id": "u1",
            }
        ]),
    )

    session = repo.create_session("u1")

    assert session.id == "s1"
    assert session.app_type == AppType.WEB
    assert supabase.tables == [Table.SESSIONS]
    assert ("insert", {Session.USER_ID: "u1"}) in query.operations


def test_create_session_returns_fallback_for_empty_insert_response(monkeypatch):
    install_fake_supabase(monkeypatch, Response([]))

    assert repo.create_session("u1").id == "0"


def test_get_session_by_id_filters_by_user_when_user_id_is_supplied(monkeypatch):
    _, query = install_fake_supabase(
        monkeypatch,
        Response([
            {
                "id": "s1",
                "title": "Title",
                "app_type": None,
                "completed": False,
                "json_schema": None,
            }
        ]),
    )

    session = repo.get_session_by_id("s1", "u1")

    assert session.id == "s1"
    assert ("eq", Session.ID, "s1") in query.operations
    assert ("eq", Session.USER_ID, "u1") in query.operations


def test_get_session_by_id_does_not_filter_by_user_when_omitted(monkeypatch):
    _, query = install_fake_supabase(
        monkeypatch,
        Response([
            {
                "id": "s1",
                "title": "Title",
                "app_type": None,
                "completed": False,
                "json_schema": None,
            }
        ]),
    )

    repo.get_session_by_id("s1")

    assert ("eq", Session.ID, "s1") in query.operations
    assert all(op[:2] != ("eq", Session.USER_ID) for op in query.operations)


def test_list_sessions_orders_by_updated_at_desc(monkeypatch):
    _, query = install_fake_supabase(
        monkeypatch,
        Response([
            {"id": "s2", "title": "Two", "app_type": "api", "completed": True, "json_schema": {}},
            {"id": "s1", "title": "One", "app_type": None, "completed": False, "json_schema": None},
        ]),
    )

    sessions = repo.list_sessions("u1")

    assert [s.id for s in sessions] == ["s2", "s1"]
    assert ("eq", Session.USER_ID, "u1") in query.operations
    assert ("order", Session.UPDATED_AT, True) in query.operations


def test_list_sessions_returns_empty_list_when_data_is_none(monkeypatch):
    install_fake_supabase(monkeypatch, Response(None))

    assert repo.list_sessions("u1") == []


def test_get_messages_by_session_id_returns_message_models(monkeypatch):
    _, query = install_fake_supabase(
        monkeypatch,
        Response([
            {"session_id": "s1", "role": "user", "content": "hello"},
            {"session_id": "s1", "role": "assistant", "content": "hi"},
        ]),
    )

    messages = repo.get_messages_by_session_id("s1")

    assert [(m.role, m.content) for m in messages] == [("user", "hello"), ("assistant", "hi")]
    assert ("eq", Message.SESSION_ID, "s1") in query.operations
    assert ("order", Message.CREATED_AT, False) in query.operations


def test_get_messages_by_session_id_returns_fallback_when_data_is_none(monkeypatch):
    install_fake_supabase(monkeypatch, Response(None))

    assert repo.get_messages_by_session_id("s1")[0].session_id == "0"


def test_add_message_returns_db_row_when_insert_response_has_data(monkeypatch):
    _, query = install_fake_supabase(
        monkeypatch,
        Response([{"session_id": "s1", "role": "user", "content": "hello"}]),
    )

    message = repo.add_message("s1", ContextMessage(role="user", content="hello"))

    assert message.session_id == "s1"
    assert message.role == "user"
    insert_payload = next(op[1] for op in query.operations if op[0] == "insert")
    assert insert_payload == {"session_id": "s1", "role": "user", "content": "hello"}


def test_add_message_returns_payload_fallback_when_response_is_empty(monkeypatch):
    install_fake_supabase(monkeypatch, Response([]))

    message = repo.add_message("s1", ContextMessage(role="assistant", content="fallback"))

    assert message.session_id == "s1"
    assert message.role == "assistant"
    assert message.content == "fallback"


def test_delete_session_filters_by_session_and_user(monkeypatch):
    _, query = install_fake_supabase(monkeypatch, Response([]))

    repo.delete_session("s1", "u1")

    assert ("delete",) in query.operations
    assert ("eq", Session.ID, "s1") in query.operations
    assert ("eq", Session.USER_ID, "u1") in query.operations


def test_update_session_persists_title_type_completed_and_schema(monkeypatch):
    _, query = install_fake_supabase(monkeypatch, Response([]))
    state = SessionState(
        app_type=AppType.API,
        schema={"context": {"api_name": "Billing"}},
        completed=True,
    )

    repo.update_session("s1", state)

    payload = next(op[1] for op in query.operations if op[0] == "update")
    assert payload == {
        "title": "Api: Billing",
        "app_type": AppType.API,
        "completed": True,
        "json_schema": {"context": {"api_name": "Billing"}},
    }
    assert ("eq", Session.ID, "s1") in query.operations


@pytest.mark.parametrize(
        ("state", "expected"),
        [
            (SessionState(app_type=AppType.UNKNOWN, schema={}), ""),
            (SessionState(app_type=AppType.WEB, schema={}), "Web"),
            (SessionState(app_type=AppType.WEB, schema={"context": {"app_name": "Portal"}}), "Web: Portal"),
            (SessionState(app_type=AppType.API, schema={"context": {"api_name": "Billing"}}), "Api: Billing"),
            (SessionState(app_type=AppType.API, schema={"context": {"app_name": "Wrong key"}}), "New Conversation"),
        ],
    )
def test_make_title_from_state(state, expected):
    assert repo.make_title_from_state(state) == expected


def test_db_to_session_state_returns_fallback_when_session_is_missing(monkeypatch):
    monkeypatch.setattr(repo, "get_session_by_id", lambda session_id, user_id: repo.get_session_model_fallback())

    state = repo.db_to_session_state("u1", "missing")

    assert state.active_agent_name == "fallback"
    assert state.app_type == AppType.UNKNOWN


def test_db_to_session_state_returns_fallback_when_messages_failed_to_load(monkeypatch):
    monkeypatch.setattr(
        repo,
        "get_session_by_id",
        lambda session_id, user_id: repo.SessionModel(
            id="s1",
            title="",
            app_type=AppType.WEB,
            completed=False,
            json_schema={},
        ),
    )
    monkeypatch.setattr(repo, "get_messages_by_session_id", lambda session_id: [repo.MessageModel(session_id="0", role="", content="")])

    assert repo.db_to_session_state("u1", "s1").active_agent_name == "fallback"


def test_db_to_session_state_maps_session_and_messages(monkeypatch):
    monkeypatch.setattr(
        repo,
        "get_session_by_id",
        lambda session_id, user_id: repo.SessionModel(
            id="s1",
            title="",
            app_type=AppType.WEB,
            completed=True,
            json_schema={"type": "web-application"},
        ),
    )
    monkeypatch.setattr(
        repo,
        "get_messages_by_session_id",
        lambda session_id: [
            repo.MessageModel(session_id="s1", role="user", content="hello"),
            repo.MessageModel(session_id="s1", role="assistant", content="hi"),
        ],
    )

    state = repo.db_to_session_state("u1", "s1")

    assert state.app_type == AppType.WEB
    assert state.active_agent_name == AppType.WEB
    assert state.completed is True
    assert state.schema == {"type": "web-application"}
    assert [m.content for m in state.history] == ["hello", "hi"]


@pytest.mark.parametrize(
    "operation",
    [
        lambda: repo.create_session("u1"),
        lambda: repo.get_session_by_id("s1"),
        lambda: repo.list_sessions("u1"),
        lambda: repo.get_messages_by_session_id("s1"),
        lambda: repo.add_message("s1", ContextMessage("user", "hello")),
        lambda: repo.delete_session("s1", "u1"),
        lambda: repo.update_session("s1", SessionState()),
    ],
)
def test_repository_operations_translate_http_errors_to_database_error(monkeypatch, operation):
    install_fake_supabase(monkeypatch, HTTPError("network"))

    with pytest.raises(DatabaseError):
        operation()
