from __future__ import annotations

import pytest
from fastapi import HTTPException, status

from backend.routes import chat, sessions
from backend.schemas.constants import OrchestratorResponse
from backend.schemas.db import MessageModel, SessionModel
from backend.schemas.exceptions import (
    AgentExecutionError,
    DatabaseError,
    MessageSaveError,
    SessionLoadError,
    SessionUpdateError,
)


def session_model(**overrides):
    data = {
        "id": "s1",
        "title": "Session",
        "app_type": "web",
        "completed": False,
        "json_schema": {},
        "user_id": "u1",
    }
    data.update(overrides)
    return SessionModel(**data)


def message_model(role="user", content="hello", session_id="s1"):
    return MessageModel(session_id=session_id, role=role, content=content)


def test_create_session_endpoint_returns_created_session(monkeypatch):
    monkeypatch.setattr(sessions, "create_session", lambda user_id: session_model(id="new"))

    response = sessions.create_session_endpoint(user_id="u1")

    assert response.session.id == "new"


def test_create_session_endpoint_raises_503_for_fallback_session(monkeypatch):
    monkeypatch.setattr(sessions, "create_session", lambda user_id: session_model(id="0"))

    with pytest.raises(HTTPException) as exc:
        sessions.create_session_endpoint(user_id="u1")

    assert exc.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert exc.value.detail == "Failed to create session."


def test_create_session_endpoint_translates_database_error(monkeypatch):
    monkeypatch.setattr(sessions, "create_session", lambda user_id: (_ for _ in ()).throw(DatabaseError()))

    with pytest.raises(HTTPException) as exc:
        sessions.create_session_endpoint(user_id="u1")

    assert exc.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert exc.value.detail == "Database connection error."


def test_sessions_endpoint_returns_sessions(monkeypatch):
    monkeypatch.setattr(sessions, "list_sessions", lambda user_id: [session_model(id="s2")])

    assert sessions.sessions_endpoint(user_id="u1")[0].id == "s2"


def test_sessions_endpoint_translates_database_error(monkeypatch):
    monkeypatch.setattr(sessions, "list_sessions", lambda user_id: (_ for _ in ()).throw(DatabaseError()))

    with pytest.raises(HTTPException) as exc:
        sessions.sessions_endpoint(user_id="u1")

    assert exc.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert exc.value.detail == "Database unavailable."


def test_session_by_id_endpoint_returns_messages(monkeypatch):
    monkeypatch.setattr(sessions, "get_messages_by_session_id", lambda session_id: [message_model()])

    assert sessions.session_by_id_endpoint("s1")[0].content == "hello"


def test_session_by_id_endpoint_treats_fallback_message_as_database_unavailable(monkeypatch):
    monkeypatch.setattr(sessions, "get_messages_by_session_id", lambda session_id: [message_model(session_id="0", role="", content="")])

    with pytest.raises(HTTPException) as exc:
        sessions.session_by_id_endpoint("s1")

    assert exc.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


def test_delete_session_endpoint_delegates_to_repository(monkeypatch):
    calls = []
    monkeypatch.setattr(sessions, "delete_session", lambda session_id, user_id: calls.append((session_id, user_id)))

    assert sessions.delete_session_endpoint("s1", user_id="u1") is None
    assert calls == [("s1", "u1")]


def test_delete_session_endpoint_translates_database_error(monkeypatch):
    monkeypatch.setattr(sessions, "delete_session", lambda session_id, user_id: (_ for _ in ()).throw(DatabaseError()))

    with pytest.raises(HTTPException) as exc:
        sessions.delete_session_endpoint("s1", user_id="u1")

    assert exc.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert exc.value.detail == "Failed to delete session."


def test_export_session_endpoint_rejects_missing_session(monkeypatch):
    monkeypatch.setattr(sessions, "get_session_by_id", lambda session_id, user_id: session_model(id="0"))

    with pytest.raises(HTTPException) as exc:
        sessions.export_session_endpoint("s1", user_id="u1")

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_export_session_endpoint_rejects_incomplete_session(monkeypatch):
    monkeypatch.setattr(sessions, "get_session_by_id", lambda session_id, user_id: session_model(completed=False))

    with pytest.raises(HTTPException) as exc:
        sessions.export_session_endpoint("s1", user_id="u1")

    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc.value.detail == "Session checklist is not yet completed."


def test_export_session_endpoint_rejects_completed_session_without_checklist(monkeypatch):
    monkeypatch.setattr(sessions, "get_session_by_id", lambda session_id, user_id: session_model(completed=True))
    monkeypatch.setattr(sessions, "get_messages_by_session_id", lambda session_id: [message_model("assistant", "no checklist")])

    with pytest.raises(HTTPException) as exc:
        sessions.export_session_endpoint("s1", user_id="u1")

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc.value.detail == "No checklist found in this session."


def test_export_session_endpoint_streams_latest_assistant_checklist(monkeypatch):
    monkeypatch.setattr(sessions, "get_session_by_id", lambda session_id, user_id: session_model(completed=True))
    monkeypatch.setattr(
        sessions,
        "get_messages_by_session_id",
        lambda session_id: [
            message_model("assistant", "[HIGH PRIORITY]\n- old"),
            message_model("user", "thanks"),
            message_model("assistant", "[MEDIUM PRIORITY]\n- newer"),
        ],
    )
    monkeypatch.setattr(sessions, "parse_checklist", lambda content: [("MEDIUM", "newer")] if "newer" in content else [])

    class Buffer:
        pass

    monkeypatch.setattr(sessions, "generate_excel", lambda rows: Buffer())

    response = sessions.export_session_endpoint("abc", user_id="u1")

    assert response.media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert response.headers["content-disposition"] == 'attachment; filename="checklist-abc.xlsx"'


def test_chat_endpoint_rejects_missing_session(monkeypatch):
    monkeypatch.setattr(chat, "get_session_by_id", lambda session_id, user_id: session_model(id="0"))

    with pytest.raises(HTTPException) as exc:
        chat.chat_endpoint(chat.ChatRequest(session_id="missing", message="hello"), user_id="u1")

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc.value.detail == "Session not found."


def test_chat_endpoint_saves_user_message_runs_orchestrator_and_returns_response(monkeypatch):
    monkeypatch.setattr(chat, "get_session_by_id", lambda session_id, user_id: session_model(id=session_id))
    monkeypatch.setattr(chat, "add_message", lambda session_id, message: message_model(message.role, message.content, session_id))

    class Orchestrator:
        def handle_message(self, user_id, session_id, user_input):
            assert (user_id, session_id, user_input) == ("u1", "s1", "hello")
            return OrchestratorResponse(
                reply_message=message_model("assistant", "reply", "s1"),
                completed=True,
            )

    monkeypatch.setattr(chat, "active_orchestrator", Orchestrator())

    response = chat.chat_endpoint(chat.ChatRequest(session_id="s1", message="hello"), user_id="u1")

    assert response.status == 200
    assert response.user_message.role == "user"
    assert response.user_message.content == "hello"
    assert response.reply_message.content == "reply"
    assert response.completed is True


@pytest.mark.parametrize(
    ("error", "detail"),
    [
        (AgentExecutionError(), "Failed to execute agent."),
        (SessionLoadError(), "Failed to load session."),
        (MessageSaveError(), "Failed to save the message."),
        (SessionUpdateError(), "Failed to update session."),
    ],
)
def test_chat_endpoint_translates_expected_orchestrator_errors(monkeypatch, error, detail):
    monkeypatch.setattr(chat, "get_session_by_id", lambda session_id, user_id: session_model())
    monkeypatch.setattr(chat, "add_message", lambda session_id, message: message_model(message.role, message.content, session_id))

    class Orchestrator:
        def handle_message(self, user_id, session_id, user_input):
            raise error

    monkeypatch.setattr(chat, "active_orchestrator", Orchestrator())

    with pytest.raises(HTTPException) as exc:
        chat.chat_endpoint(chat.ChatRequest(session_id="s1", message="hello"), user_id="u1")

    assert exc.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert exc.value.detail == detail


def test_chat_endpoint_translates_user_message_save_database_error(monkeypatch):
    monkeypatch.setattr(chat, "get_session_by_id", lambda session_id, user_id: session_model())
    monkeypatch.setattr(chat, "add_message", lambda session_id, message: (_ for _ in ()).throw(DatabaseError()))

    with pytest.raises(HTTPException) as exc:
        chat.chat_endpoint(chat.ChatRequest(session_id="s1", message="hello"), user_id="u1")

    assert exc.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert exc.value.detail == "Failed to save message."


def test_chat_endpoint_translates_unexpected_orchestrator_error(monkeypatch):
    monkeypatch.setattr(chat, "get_session_by_id", lambda session_id, user_id: session_model())
    monkeypatch.setattr(chat, "add_message", lambda session_id, message: message_model(message.role, message.content, session_id))

    class Orchestrator:
        def handle_message(self, user_id, session_id, user_input):
            raise RuntimeError("boom")

    monkeypatch.setattr(chat, "active_orchestrator", Orchestrator())

    with pytest.raises(HTTPException) as exc:
        chat.chat_endpoint(chat.ChatRequest(session_id="s1", message="hello"), user_id="u1")

    assert exc.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert exc.value.detail == "Unexpected server error."
