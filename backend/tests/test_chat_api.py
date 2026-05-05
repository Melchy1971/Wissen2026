from datetime import UTC, datetime
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.error_handlers import register_exception_handlers
from app.api.v1.chat import get_chat_service, get_rag_chat_service
from app.core.errors import (
    ChatSessionNotFoundApiError,
    InsufficientContextApiError,
    LlmUnavailableApiError,
    RetrievalFailedApiError,
)
from app.main import app
from app.schemas.chat import ChatMessageResponse
from app.services.chat.persistence_service import ChatPersistenceError, ChatSessionNotFoundError


def source_anchor() -> dict[str, int | str | None]:
    return {
        "type": "text",
        "page": None,
        "paragraph": 3,
        "char_start": 10,
        "char_end": 42,
    }


class FakeChatService:
    def __init__(self) -> None:
        self.created_sessions: list[dict[str, str]] = []
        self.list_call: dict[str, int | str] | None = None
        self.created_messages: list[dict[str, str]] = []
        self.now = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)
        self.session = SimpleNamespace(
            id="session-1",
            workspace_id="workspace-1",
            title="Research",
            created_at=self.now,
            updated_at=self.now,
        )
        self.message = SimpleNamespace(
            id="message-1",
            session_id="session-1",
            role="user",
            content="Was steht im Dokument?",
            basis_type="unknown",
            metadata_={"raw_internal": "not exposed"},
            created_at=self.now,
        )
        self.citation = SimpleNamespace(
            id="citation-1",
            message_id="message-1",
            chunk_id="chunk-1",
            document_id="document-1",
            source_anchor=source_anchor(),
        )

    def create_session(self, *, workspace_id: str, title: str, owner_user_id: str | None = None):
        self.created_sessions.append({"workspace_id": workspace_id, "title": title})
        return SimpleNamespace(
            id="session-created",
            workspace_id=workspace_id,
            title=title,
            created_at=self.now,
            updated_at=self.now,
        )

    def list_sessions(self, *, workspace_id: str, limit: int = 20, offset: int = 0):
        if workspace_id == "persistence-fail":
            raise ChatPersistenceError("database write failed")
        self.list_call = {"workspace_id": workspace_id, "limit": limit, "offset": offset}
        return [self.session]

    def get_session(self, *, session_id: str):
        if session_id == "missing":
            raise ChatSessionNotFoundError("chat session not found: missing")
        return self.session

    def list_messages(self, *, session_id: str):
        return [self.message]

    def list_citations(self, *, message_id: str):
        return [self.citation] if message_id == "message-1" else []

    def create_message(
        self,
        *,
        session_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
        citations: list | None = None,
        basis_type: str = "unknown",
    ):
        if session_id == "missing":
            raise ChatSessionNotFoundError("chat session not found: missing")
        if content == "invalid":
            raise ChatPersistenceError("content must not be blank")
        self.created_messages.append(
            {
                "session_id": session_id,
                "role": role,
                "content": content,
                "basis_type": basis_type,
            }
        )
        return SimpleNamespace(
            id="message-created",
            session_id=session_id,
            role=role,
            content=content,
            basis_type=basis_type,
            metadata_={},
            created_at=self.now,
        )


def install_fake_service(service: FakeChatService) -> None:
    app.dependency_overrides[get_chat_service] = lambda: service


class FakeRagChatService:
    def __init__(self) -> None:
        self.calls: list[dict[str, int | str]] = []
        self.now = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)

    def answer_question(
        self,
        *,
        session_id: str,
        workspace_id: str,
        question: str,
        retrieval_limit: int | None = None,
    ) -> ChatMessageResponse:
        self.calls.append(
            {
                "session_id": session_id,
                "workspace_id": workspace_id,
                "question": question,
                "retrieval_limit": retrieval_limit or 8,
            }
        )
        if session_id == "missing":
            raise ChatSessionNotFoundApiError(details={"session_id": session_id})
        if question == "insufficient":
            raise InsufficientContextApiError(message="no_retrieval_hits", details={"session_id": session_id})
        if question == "retrieval failed":
            raise RetrievalFailedApiError(message="postgres search failed", details={"workspace_id": workspace_id})
        if question == "llm unavailable":
            raise LlmUnavailableApiError(message="provider unavailable")
        return ChatMessageResponse(
            id="assistant-message-1",
            session_id=session_id,
            role="assistant",
            content="Die Antwort basiert auf chunk-1.",
            basis_type="knowledge_base",
            created_at=self.now,
            citations=[
                {
                    "chunk_id": "chunk-1",
                    "document_id": "document-1",
                    "source_anchor": source_anchor(),
                    "quote_preview": "Quelle aus dem Dokument",
                }
            ],
            confidence={
                "sufficient_context": True,
                "retrieval_score_max": 0.91,
                "retrieval_score_avg": 0.81,
            },
        )


def install_fake_rag_service(service: FakeRagChatService) -> None:
    app.dependency_overrides[get_rag_chat_service] = lambda: service


def assert_error_response(
    body: dict,
    *,
    code: str,
    message: str,
    details: dict,
) -> None:
    assert body == {
        "error": {
            "code": code,
            "message": message,
            "details": details,
        }
    }


def test_create_chat_session_persists_session_and_returns_summary() -> None:
    service = FakeChatService()
    install_fake_service(service)
    try:
        response = TestClient(app).post(
            "/api/v1/chat/sessions",
            json={"workspace_id": "workspace-1", "title": "Research"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert service.created_sessions == [{"workspace_id": "workspace-1", "title": "Research"}]
    assert response.json() == {
        "id": "session-created",
        "workspace_id": "workspace-1",
        "title": "Research",
        "created_at": "2026-05-01T12:00:00Z",
        "updated_at": "2026-05-01T12:00:00Z",
    }


def test_list_chat_sessions_requires_workspace_id() -> None:
    service = FakeChatService()
    install_fake_service(service)
    try:
        response = TestClient(app).get("/api/v1/chat/sessions")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "WORKSPACE_REQUIRED"


def test_list_chat_sessions_uses_pagination_and_stable_response_shape() -> None:
    service = FakeChatService()
    install_fake_service(service)
    try:
        response = TestClient(app).get("/api/v1/chat/sessions?workspace_id=workspace-1&limit=10&offset=5")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert service.list_call == {"workspace_id": "workspace-1", "limit": 10, "offset": 5}
    assert response.json() == [
        {
            "id": "session-1",
            "workspace_id": "workspace-1",
            "title": "Research",
            "created_at": "2026-05-01T12:00:00Z",
            "updated_at": "2026-05-01T12:00:00Z",
        }
    ]


def test_chat_persistence_error_uses_standard_error_format() -> None:
    service = FakeChatService()
    install_fake_service(service)
    try:
        response = TestClient(app).get("/api/v1/chat/sessions?workspace_id=persistence-fail")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "CHAT_PERSISTENCE_FAILED",
            "message": "database write failed",
            "details": {},
        }
    }


def test_get_chat_session_detail_returns_messages_and_filtered_citations() -> None:
    service = FakeChatService()
    install_fake_service(service)
    try:
        response = TestClient(app).get("/api/v1/chat/sessions/session-1")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["messages"] == [
        {
            "id": "message-1",
            "session_id": "session-1",
            "role": "user",
            "content": "Was steht im Dokument?",
            "basis_type": "unknown",
            "created_at": "2026-05-01T12:00:00Z",
            "citations": [
                {
                    "chunk_id": "chunk-1",
                    "document_id": "document-1",
                    "source_anchor": source_anchor(),
                    "quote_preview": None,
                }
            ],
            "confidence": None,
        }
    ]
    assert "metadata" not in body["messages"][0]
    assert "metadata_" not in body["messages"][0]


def test_get_chat_session_detail_keeps_historical_citations_visible_for_deleted_documents() -> None:
    service = FakeChatService()
    service.citation = SimpleNamespace(
        id="citation-deleted-1",
        message_id="message-1",
        chunk_id="chunk-deleted-1",
        document_id="document-deleted-1",
        source_anchor=source_anchor(),
    )
    install_fake_service(service)
    try:
        response = TestClient(app).get("/api/v1/chat/sessions/session-1")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    citations = response.json()["messages"][0]["citations"]
    assert citations == [
        {
            "chunk_id": "chunk-deleted-1",
            "document_id": "document-deleted-1",
            "source_anchor": source_anchor(),
            "quote_preview": None,
        }
    ]


def test_get_chat_session_detail_returns_404_for_unknown_session() -> None:
    service = FakeChatService()
    install_fake_service(service)
    try:
        response = TestClient(app).get("/api/v1/chat/sessions/missing")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CHAT_SESSION_NOT_FOUND"


def test_create_chat_message_runs_rag_pipeline_and_returns_assistant_response() -> None:
    service = FakeRagChatService()
    install_fake_rag_service(service)
    try:
        response = TestClient(app).post(
            "/api/v1/chat/sessions/session-1/messages",
            json={
                "workspace_id": "workspace-1",
                "question": "Bitte zusammenfassen.",
                "retrieval_limit": 3,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert service.calls == [
        {
            "session_id": "session-1",
            "workspace_id": "workspace-1",
            "question": "Bitte zusammenfassen.",
            "retrieval_limit": 3,
        }
    ]
    assert response.json() == {
        "id": "assistant-message-1",
        "session_id": "session-1",
        "role": "assistant",
        "content": "Die Antwort basiert auf chunk-1.",
        "basis_type": "knowledge_base",
        "created_at": "2026-05-01T12:00:00Z",
        "citations": [
            {
                "chunk_id": "chunk-1",
                "document_id": "document-1",
                "source_anchor": source_anchor(),
                "quote_preview": "Quelle aus dem Dokument",
            }
        ],
        "confidence": {
            "sufficient_context": True,
            "retrieval_score_max": 0.91,
            "retrieval_score_avg": 0.81,
        },
    }


def test_create_chat_message_endpoint_can_run_real_rag_service_with_fake_llm() -> None:
    from tests.test_rag_chat_service import make_service as make_rag_service

    rag_service, persistence, retrieval, _llm = make_rag_service()
    app.dependency_overrides[get_rag_chat_service] = lambda: rag_service
    try:
        response = TestClient(app).post(
            "/api/v1/chat/sessions/session-1/messages",
            json={
                "workspace_id": "workspace-1",
                "question": "Welche Kuendigungsfrist gilt nach der Probezeit?",
                "retrieval_limit": 8,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert [message["role"] for message in persistence.messages] == ["user", "assistant"]
    assert persistence.messages[0]["content"] == "Welche Kuendigungsfrist gilt nach der Probezeit?"
    assert persistence.messages[1]["basis_type"] == "knowledge_base"
    assert persistence.messages[1]["citations"][0].chunk_id == "chunk-1"
    assert retrieval.calls[0]["limit"] == 8
    assert response.json() == {
        "id": "message-2",
        "session_id": "session-1",
        "role": "assistant",
        "content": "Die Frist betraegt vier Wochen zum Monatsende. Quelle: chunk-1",
        "basis_type": "knowledge_base",
        "created_at": "2026-05-01T12:00:00Z",
        "citations": [
            {
                "chunk_id": "chunk-1",
                "document_id": "doc-1",
                "source_anchor": {
                    "type": "text",
                    "page": None,
                    "paragraph": 4,
                    "char_start": 10,
                    "char_end": 130,
                },
                "quote_preview": (
                    "Nach der Probezeit gilt eine Kuendigungsfrist von vier Wochen zum Monatsende "
                    "fuer das Arbeitsverhaeltnis im Unternehmen."
                ),
            }
        ],
        "confidence": {
            "sufficient_context": True,
            "retrieval_score_max": 0.92,
            "retrieval_score_avg": 0.92,
        },
    }


def test_create_chat_message_returns_404_for_unknown_session() -> None:
    service = FakeRagChatService()
    install_fake_rag_service(service)
    try:
        response = TestClient(app).post(
            "/api/v1/chat/sessions/missing/messages",
            json={"workspace_id": "workspace-1", "question": "Bitte zusammenfassen."},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert_error_response(
        response.json(),
        code="CHAT_SESSION_NOT_FOUND",
        message="Chat session not found",
        details={"session_id": "missing"},
    )


def test_create_chat_message_validation_uses_standard_error_format() -> None:
    service = FakeRagChatService()
    install_fake_rag_service(service)
    try:
        response = TestClient(app).post(
            "/api/v1/chat/sessions/session-1/messages",
            json={"workspace_id": "workspace-1", "question": ""},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "CHAT_MESSAGE_INVALID"
    assert body["error"]["message"] == "Chat message is invalid"
    assert set(body["error"]) == {"code", "message", "details"}
    assert body["error"]["details"]["errors"][0]["type"] == "string_too_short"
    assert body["error"]["details"]["errors"][0]["loc"] == ["body", "question"]


def test_create_chat_message_maps_insufficient_context() -> None:
    service = FakeRagChatService()
    install_fake_rag_service(service)
    try:
        response = TestClient(app).post(
            "/api/v1/chat/sessions/session-1/messages",
            json={"workspace_id": "workspace-1", "question": "insufficient"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert_error_response(
        response.json(),
        code="INSUFFICIENT_CONTEXT",
        message="no_retrieval_hits",
        details={"session_id": "session-1"},
    )


def test_create_chat_message_maps_retrieval_failure() -> None:
    service = FakeRagChatService()
    install_fake_rag_service(service)
    try:
        response = TestClient(app).post(
            "/api/v1/chat/sessions/session-1/messages",
            json={"workspace_id": "workspace-1", "question": "retrieval failed"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502
    assert_error_response(
        response.json(),
        code="RETRIEVAL_FAILED",
        message="postgres search failed",
        details={"workspace_id": "workspace-1"},
    )


def test_create_chat_message_maps_llm_unavailable() -> None:
    service = FakeRagChatService()
    install_fake_rag_service(service)
    try:
        response = TestClient(app).post(
            "/api/v1/chat/sessions/session-1/messages",
            json={"workspace_id": "workspace-1", "question": "llm unavailable"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert_error_response(
        response.json(),
        code="LLM_UNAVAILABLE",
        message="provider unavailable",
        details={},
    )


def test_rag_error_classes_are_registered_with_standard_error_format() -> None:
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/retrieval-failed")
    def retrieval_failed() -> None:
        raise RetrievalFailedApiError(details={"stage": "search"})

    @test_app.get("/insufficient-context")
    def insufficient_context() -> None:
        raise InsufficientContextApiError(details={"hits": 0})

    @test_app.get("/llm-unavailable")
    def llm_unavailable() -> None:
        raise LlmUnavailableApiError(details={"provider": "local"})

    client = TestClient(test_app)

    retrieval_response = client.get("/retrieval-failed")
    context_response = client.get("/insufficient-context")
    llm_response = client.get("/llm-unavailable")

    assert retrieval_response.status_code == 502
    assert retrieval_response.json() == {
        "error": {
            "code": "RETRIEVAL_FAILED",
            "message": "Retrieval failed",
            "details": {"stage": "search"},
        }
    }
    assert context_response.status_code == 422
    assert context_response.json()["error"]["code"] == "INSUFFICIENT_CONTEXT"
    assert llm_response.status_code == 503
    assert llm_response.json()["error"]["code"] == "LLM_UNAVAILABLE"
