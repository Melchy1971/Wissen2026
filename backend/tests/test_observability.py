import logging

from fastapi.testclient import TestClient

from app.main import app
from app.observability.logging import metrics_registry


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
    assert observability_records[0]["event_name"] == "document_upload_started"
    assert observability_records[-1]["event_name"] == "document_upload_completed"
    assert observability_records[-1]["workspace_id"] == "00000000-0000-0000-0000-000000000001"
    assert observability_records[-1]["user_id"] == "00000000-0000-0000-0000-000000000001"
    assert observability_records[-1]["correlation_id"] == "upload-corr-1"
    assert "secret body" not in caplog.text
    assert "Do not log me" not in caplog.text
    snapshot = metrics_registry.snapshot()
    assert snapshot["document_upload_started.started"] == 1
    assert snapshot["document_upload_completed.completed"] == 1


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