from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from app.core.errors import (
    ChatPersistenceFailedApiError,
    ChatSessionNotFoundApiError,
    InsufficientContextApiError,
    LlmUnavailableApiError,
    RetrievalFailedApiError,
)
from app.schemas.documents import DocumentChunkSourceAnchor
from app.schemas.search import SearchChunkResult
from app.services.chat.citation_mapper import CitationMapper
from app.services.chat.context_builder import ContextBuilder
from app.services.chat.fake_llm_provider import FakeLlmProvider
from app.services.chat.insufficient_context_policy import InsufficientContextPolicy, InsufficientContextThresholds
from app.services.chat.persistence_service import ChatCitationPayload, ChatPersistenceError, ChatSessionNotFoundError
from app.services.chat.prompt_builder import PromptBuilder
from app.services.chat.rag_chat_service import RagChatService


def make_search_result(
    *,
    chunk_id: str = "chunk-1",
    document_id: str = "doc-1",
    rank: float = 0.92,
    text_preview: str | None = None,
) -> SearchChunkResult:
    text = text_preview or (
        "Nach der Probezeit gilt eine Kuendigungsfrist von vier Wochen zum Monatsende "
        "fuer das Arbeitsverhaeltnis im Unternehmen."
    )
    return SearchChunkResult(
        document_id=document_id,
        document_title="Arbeitsvertrag Hybridmodell",
        document_created_at=datetime(2026, 5, 1, 10, 0, tzinfo=UTC),
        document_version_id=f"version-{document_id}",
        version_number=1,
        chunk_id=chunk_id,
        position=0,
        text_preview=text,
        source_anchor=DocumentChunkSourceAnchor(
            type="text",
            page=None,
            paragraph=4,
            char_start=10,
            char_end=10 + len(text),
        ),
        rank=rank,
        filters={},
    )


class FakeRetrieval:
    def __init__(self, results: list[SearchChunkResult] | None = None, *, fail: bool = False) -> None:
        self.results = results if results is not None else [make_search_result()]
        self.fail = fail
        self.calls: list[dict[str, Any]] = []

    def search_chunks(
        self,
        workspace_id: str,
        query: str,
        limit: int,
        offset: int,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchChunkResult]:
        self.calls.append(
            {
                "workspace_id": workspace_id,
                "query": query,
                "limit": limit,
                "offset": offset,
                "filters": filters,
            }
        )
        if self.fail:
            raise RuntimeError("postgres search failed")
        return self.results


class FakePersistence:
    def __init__(self, *, fail_role: str | None = None) -> None:
        self.fail_role = fail_role
        self.messages: list[dict[str, Any]] = []
        self.now = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)

    def create_message(
        self,
        *,
        session_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
        citations: list[ChatCitationPayload] | None = None,
        basis_type: str = "unknown",
    ):
        if session_id == "missing":
            raise ChatSessionNotFoundError("chat session not found: missing")
        if self.fail_role == role:
            raise ChatPersistenceError(f"{role} persistence failed")
        self.messages.append(
            {
                "session_id": session_id,
                "role": role,
                "content": content,
                "basis_type": basis_type,
                "metadata": metadata or {},
                "citations": citations or [],
            }
        )
        return SimpleNamespace(
            id=f"message-{len(self.messages)}",
            session_id=session_id,
            role=role,
            content=content,
            basis_type=basis_type,
            created_at=self.now,
        )


def make_service(
    *,
    persistence: FakePersistence | None = None,
    retrieval: FakeRetrieval | None = None,
    llm_provider: FakeLlmProvider | None = None,
    min_retrieval_score: float = 0.25,
) -> tuple[RagChatService, FakePersistence, FakeRetrieval, FakeLlmProvider]:
    fake_persistence = persistence or FakePersistence()
    fake_retrieval = retrieval or FakeRetrieval()
    fake_llm = llm_provider or FakeLlmProvider(answer="Die Frist betraegt vier Wochen zum Monatsende. Quelle: chunk-1")
    service = RagChatService(
        persistence=fake_persistence,
        retrieval=fake_retrieval,
        context_builder=ContextBuilder(max_context_chars=2000, max_context_tokens=300, min_chunk_chars=20),
        insufficient_context_policy=InsufficientContextPolicy(
            InsufficientContextThresholds(
                min_retrieval_score=min_retrieval_score,
                min_top_chunk_chars=20,
                min_question_token_length=4,
                min_question_token_overlap=1,
            )
        ),
        prompt_builder=PromptBuilder(),
        llm_provider=fake_llm,
        citation_mapper=CitationMapper(),
        retrieval_limit=5,
    )
    return service, fake_persistence, fake_retrieval, fake_llm


def test_rag_chat_service_runs_full_flow_and_persists_cited_answer() -> None:
    service, persistence, retrieval, llm = make_service()

    response = service.answer_question(
        session_id="session-1",
        workspace_id="workspace-1",
        question="Welche Kuendigungsfrist gilt nach der Probezeit?",
    )

    assert [message["role"] for message in persistence.messages] == ["user", "assistant"]
    assert retrieval.calls == [
        {
            "workspace_id": "workspace-1",
            "query": "Welche Kuendigungsfrist gilt nach der Probezeit?",
            "limit": 5,
            "offset": 0,
            "filters": None,
        }
    ]
    assert "chunk_id: chunk-1" in llm.calls[0].user_prompt
    assistant = persistence.messages[1]
    assert assistant["basis_type"] == "knowledge_base"
    assert assistant["citations"][0].chunk_id == "chunk-1"
    assert assistant["citations"][0].document_id == "doc-1"
    assert assistant["citations"][0].document_title == "Arbeitsvertrag Hybridmodell"
    assert assistant["citations"][0].quote_preview is not None
    assert assistant["citations"][0].source_status == "active"
    assert assistant["citations"][0].source_anchor["paragraph"] == 4
    assert response.role == "assistant"
    assert response.citations[0].chunk_id == "chunk-1"
    assert response.citations[0].quote_preview is not None
    assert response.confidence is not None
    assert response.confidence.sufficient_context is True
    assert response.confidence.retrieval_score_max == 0.92


def test_rag_chat_service_uses_request_retrieval_limit() -> None:
    service, _persistence, retrieval, _llm = make_service()

    service.answer_question(
        session_id="session-1",
        workspace_id="workspace-1",
        question="Welche Kuendigungsfrist gilt nach der Probezeit?",
        retrieval_limit=8,
    )

    assert retrieval.calls[0]["limit"] == 8


def test_rag_chat_service_maps_unknown_session_to_chat_session_not_found() -> None:
    service, persistence, retrieval, llm = make_service()

    with pytest.raises(ChatSessionNotFoundApiError) as exc:
        service.answer_question(
            session_id="missing",
            workspace_id="workspace-1",
            question="Welche Kuendigungsfrist gilt nach der Probezeit?",
        )

    assert exc.value.code == "CHAT_SESSION_NOT_FOUND"
    assert persistence.messages == []
    assert retrieval.calls == []
    assert llm.calls == []


def test_rag_chat_service_does_not_call_llm_or_save_answer_when_context_is_insufficient() -> None:
    retrieval = FakeRetrieval(results=[])
    service, persistence, _retrieval, llm = make_service(retrieval=retrieval)

    with pytest.raises(InsufficientContextApiError) as exc:
        service.answer_question(
            session_id="session-1",
            workspace_id="workspace-1",
            question="Welche Kuendigungsfrist gilt nach der Probezeit?",
        )

    assert exc.value.code == "INSUFFICIENT_CONTEXT"
    assert [message["role"] for message in persistence.messages] == ["user"]
    assert llm.calls == []


def test_rag_chat_service_maps_retrieval_failure() -> None:
    retrieval = FakeRetrieval(fail=True)
    service, persistence, _retrieval, llm = make_service(retrieval=retrieval)

    with pytest.raises(RetrievalFailedApiError) as exc:
        service.answer_question(
            session_id="session-1",
            workspace_id="workspace-1",
            question="Welche Kuendigungsfrist gilt nach der Probezeit?",
        )

    assert exc.value.code == "RETRIEVAL_FAILED"
    assert [message["role"] for message in persistence.messages] == ["user"]
    assert llm.calls == []


def test_rag_chat_service_maps_llm_failure_without_saving_assistant_answer() -> None:
    llm = FakeLlmProvider(unavailable=True)
    service, persistence, _retrieval, _llm = make_service(llm_provider=llm)

    with pytest.raises(LlmUnavailableApiError) as exc:
        service.answer_question(
            session_id="session-1",
            workspace_id="workspace-1",
            question="Welche Kuendigungsfrist gilt nach der Probezeit?",
        )

    assert exc.value.code == "LLM_UNAVAILABLE"
    assert [message["role"] for message in persistence.messages] == ["user"]


def test_rag_chat_service_rejects_answer_without_chunk_citations() -> None:
    llm = FakeLlmProvider(answer="Die Frist betraegt vier Wochen zum Monatsende.")
    service, persistence, _retrieval, _llm = make_service(llm_provider=llm)

    with pytest.raises(InsufficientContextApiError) as exc:
        service.answer_question(
            session_id="session-1",
            workspace_id="workspace-1",
            question="Welche Kuendigungsfrist gilt nach der Probezeit?",
        )

    assert exc.value.code == "INSUFFICIENT_CONTEXT"
    assert exc.value.details["source_chunk_ids"] == ["chunk-1"]
    assert [message["role"] for message in persistence.messages] == ["user"]


def test_rag_chat_service_maps_persistence_failure() -> None:
    persistence = FakePersistence(fail_role="assistant")
    service, _persistence, _retrieval, _llm = make_service(persistence=persistence)

    with pytest.raises(ChatPersistenceFailedApiError) as exc:
        service.answer_question(
            session_id="session-1",
            workspace_id="workspace-1",
            question="Welche Kuendigungsfrist gilt nach der Probezeit?",
        )

    assert exc.value.code == "CHAT_PERSISTENCE_FAILED"
    assert [message["role"] for message in persistence.messages] == ["user"]
