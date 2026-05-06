import logging
from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.main import app
from app.models.import_models import NormalizedDocument
from app.observability.logging import bind_observability_context, metrics_registry
from app.services.chunking_service import MarkdownChunk


def test_correlation_id_middleware_sets_response_header() -> None:
    client = TestClient(app)

    response = client.get("/health", headers={"x-correlation-id": "corr-123"})

    assert response.status_code == 200
    assert response.headers["x-correlation-id"] == "corr-123"


def test_upload_logs_structured_context_without_document_content(monkeypatch, caplog, client: TestClient) -> None:
    from app.services.documents import import_executor

    class StubImportService:
        def import_document(self, request):
            from app.models.import_models import ImportResult, NormalizedDocument

            return ImportResult(
                success=True,
                filename=request.filename,
                mime_type=request.mime_type,
                source_content_hash="hash-1",
                document=NormalizedDocument(
                    normalized_markdown="# Secret\n\nDo not log me\n",
                    markdown_hash="markdown-hash-1",
                    metadata={"parser_name": "txt-parser", "mime_type": request.mime_type},
                    parser_version="1.0",
                    ocr_used=False,
                ),
                errors=[],
                metadata={"filename": request.filename, "mime_type": request.mime_type},
            )

    class StubPersistenceService:
        def persist_import(self, **kwargs):
            from types import SimpleNamespace

            from app.observability.logging import log_import_event

            log_import_event(
                "chunking_started",
                document_id="doc-1",
                workspace_id=kwargs["workspace_id"],
                duration_ms=0,
                parser_type="txt-parser",
                chunk_count=0,
                status="started",
            )
            log_import_event(
                "chunking_completed",
                document_id="doc-1",
                workspace_id=kwargs["workspace_id"],
                duration_ms=1,
                parser_type="txt-parser",
                chunk_count=1,
                status="completed",
            )
            log_import_event(
                "indexing_started",
                document_id="doc-1",
                workspace_id=kwargs["workspace_id"],
                duration_ms=0,
                parser_type="txt-parser",
                chunk_count=1,
                status="started",
            )
            log_import_event(
                "indexing_completed",
                document_id="doc-1",
                workspace_id=kwargs["workspace_id"],
                duration_ms=1,
                parser_type="txt-parser",
                chunk_count=1,
                status="completed",
            )

            return SimpleNamespace(
                document_id="doc-1",
                version_id="ver-1",
                title="notes",
                chunk_count=1,
                duplicate_existing=False,
                import_status="chunked",
            )

    metrics_registry.reset()
    monkeypatch.setattr(import_executor, "build_import_service", lambda: StubImportService())
    monkeypatch.setattr(import_executor, "DocumentImportPersistenceService", lambda: StubPersistenceService())

    with caplog.at_level(logging.INFO, logger="app.observability.events"):
        response = client.post(
            "/documents/import",
            headers={"x-correlation-id": "upload-corr-1"},
            files={"file": ("notes.txt", b"secret body", "text/plain")},
        )

    assert response.status_code == 202
    observability_records = [record.observability for record in caplog.records if hasattr(record, "observability")]
    assert [record["event_name"] for record in observability_records] == [
        "upload_received",
        "parsing_started",
        "parsing_completed",
        "chunking_started",
        "chunking_completed",
        "indexing_started",
        "indexing_completed",
    ]
    for record in observability_records:
        assert set(record) == {
            "event_name",
            "document_id",
            "workspace_id",
            "duration_ms",
            "parser_type",
            "chunk_count",
            "error_code",
            "correlation_id",
            "status",
        }
        assert record["workspace_id"] == "00000000-0000-0000-0000-000000000001"
        assert record["correlation_id"] == "upload-corr-1"
    assert observability_records[0]["parser_type"] == "txt-parser"
    assert observability_records[0]["chunk_count"] == 0
    assert observability_records[-1]["document_id"] == "doc-1"
    assert observability_records[-1]["chunk_count"] == 1
    assert "secret body" not in caplog.text
    assert "Do not log me" not in caplog.text
    snapshot = metrics_registry.snapshot()
    assert snapshot["upload_received.received"] == 1
    assert snapshot["parsing_started.started"] == 1
    assert snapshot["parsing_completed.completed"] == 1
    assert snapshot["chunking_started.started"] == 1
    assert snapshot["chunking_completed.completed"] == 1
    assert snapshot["indexing_started.started"] == 1
    assert snapshot["indexing_completed.completed"] == 1


def test_chat_observability_logs_context_without_full_question(caplog) -> None:
    from app.services.chat.rag_chat_service import RagChatService
    from tests.test_rag_chat_service import FakePersistence, FakeRetrieval, make_service

    metrics_registry.reset()
    retrieval = FakeRetrieval(results=[])
    service, _persistence, _retrieval, _llm = make_service(retrieval=retrieval)

    with caplog.at_level(logging.INFO, logger="app.observability.events"):
        try:
            service.answer_question(
                session_id="session-1",
                workspace_id="workspace-1",
                question="Sehr geheime Frage nach internen Vertragsdetails",
            )
        except Exception:
            pass

    observability_records = [record.observability for record in caplog.records if hasattr(record, "observability")]
    assert observability_records[-1]["event_name"] == "rag_insufficient_context"
    assert observability_records[-1]["workspace_id"] == "workspace-1"
    assert observability_records[-1]["error_code"] == "INSUFFICIENT_CONTEXT"
    assert "Sehr geheime Frage" not in caplog.text
    snapshot = metrics_registry.snapshot()
    assert snapshot["rag_insufficient_context.failed"] == 1


def test_persistence_logs_chunking_and_indexing_events(monkeypatch, caplog) -> None:
    from app.services.documents import import_persistence_service

    class FakeCursor:
        def execute(self, *_args, **_kwargs):
            return None

        def executemany(self, *_args, **_kwargs):
            return None

        def fetchone(self):
            return None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

        def rollback(self):
            return None

    @contextmanager
    def fake_get_connection():
        yield FakeConnection()

    class StubChunkingService:
        def chunk(self, normalized_markdown, document_version_id, source_anchor_type):
            assert normalized_markdown == "# Title\n\nBody\n"
            assert document_version_id
            assert source_anchor_type == "text"
            return [
                MarkdownChunk(
                    chunk_index=0,
                    heading_path=["Title"],
                    anchor="dv:test:c0000",
                    content="# Title\n\nBody\n",
                    content_hash="chunk-hash-1",
                    token_estimate=4,
                    metadata={"source_anchor": {"type": "text"}},
                )
            ]

    metrics_registry.reset()
    bind_observability_context(workspace_id="workspace-1")
    monkeypatch.setattr(import_persistence_service, "get_connection", fake_get_connection)
    service = import_persistence_service.DocumentImportPersistenceService(chunking_service=StubChunkingService())

    with caplog.at_level(logging.INFO, logger="app.observability.events"):
        persisted = service.persist_import(
            workspace_id="workspace-1",
            owner_user_id="user-1",
            title="Title",
            mime_type="text/plain",
            content_hash="content-hash-1",
            document=NormalizedDocument(
                normalized_markdown="# Title\n\nBody\n",
                markdown_hash="markdown-hash-1",
                metadata={"parser_name": "txt-parser", "mime_type": "text/plain"},
                parser_version="1.0",
                ocr_used=False,
            ),
        )

    assert persisted.chunk_count == 1
    observability_records = [record.observability for record in caplog.records if hasattr(record, "observability")]
    assert [record["event_name"] for record in observability_records] == [
        "chunking_started",
        "chunking_completed",
        "indexing_started",
        "indexing_completed",
    ]
    assert all(record["document_id"] == persisted.document_id for record in observability_records)
    assert all(record["workspace_id"] == "workspace-1" for record in observability_records)
    assert all(record["parser_type"] == "txt-parser" for record in observability_records)
    assert observability_records[0]["chunk_count"] == 0
    assert observability_records[1]["chunk_count"] == 1
    assert observability_records[3]["chunk_count"] == 1