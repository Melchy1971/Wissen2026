from io import BytesIO
from types import SimpleNamespace

from fastapi.testclient import TestClient
from pypdf import PdfWriter


def test_import_enqueues_job_and_returns_accepted(client: TestClient) -> None:
    response = client.post(
        "/documents/import",
        files={"file": ("notes.txt", b"# Notes\n\nHello world\n", "text/plain")},
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["job_type"] == "document_import"
    assert payload["status"] == "queued"
    assert payload["filename"] == "notes.txt"
    assert payload["result"] is None
    assert payload["error_code"] is None


def test_import_job_status_returns_completed_result_after_background_processing(client: TestClient) -> None:
    from app.models.import_models import ImportResult, NormalizedDocument
    from app.services.documents import import_executor

    class StubImportService:
        def import_document(self, request):
            return ImportResult(
                success=True,
                filename=request.filename,
                mime_type=request.mime_type,
                source_content_hash="hash-1",
                document=NormalizedDocument(
                    normalized_markdown="# Notes\n\nHello world\n",
                    markdown_hash="markdown-hash-1",
                    metadata={
                        "parser_name": "txt-parser",
                        "mime_type": request.mime_type,
                    },
                    parser_version="1.0",
                    ocr_used=False,
                ),
                errors=[],
                metadata={"filename": request.filename, "mime_type": request.mime_type},
            )

    class StubPersistenceService:
        def persist_import(self, **kwargs):
            return SimpleNamespace(
                document_id="doc-1",
                version_id="ver-1",
                title="notes",
                chunk_count=1,
                duplicate_existing=False,
                import_status="chunked",
            )

    original_build_import_service = import_executor.build_import_service
    original_persistence_service = import_executor.DocumentImportPersistenceService
    import_executor.build_import_service = lambda: StubImportService()
    import_executor.DocumentImportPersistenceService = lambda: StubPersistenceService()

    try:
        enqueue_response = client.post(
            "/documents/import",
            files={"file": ("notes.txt", b"# Notes\n\nHello world\n", "text/plain")},
        )

        assert enqueue_response.status_code == 202
        job_id = enqueue_response.json()["id"]

        response = client.get(f"/documents/import-jobs/{job_id}")
    finally:
        import_executor.build_import_service = original_build_import_service
        import_executor.DocumentImportPersistenceService = original_persistence_service

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["result"]["document_id"]
    assert payload["result"]["version_id"] is not None
    assert payload["result"]["import_status"] == "chunked"
    assert payload["result"]["duplicate_of_document_id"] is None
    assert payload["result"]["chunk_count"] >= 1
    assert payload["result"]["parser_type"] == "txt-parser"
    assert payload["result"]["warnings"] == []


def test_generic_job_status_endpoint_returns_import_job(client: TestClient) -> None:
    response = client.post(
        "/documents/import",
        files={"file": ("notes.txt", b"# Notes\n\nHello world\n", "text/plain")},
    )

    assert response.status_code == 202
    job_id = response.json()["id"]

    job_response = client.get(f"/api/v1/jobs/{job_id}")

    assert job_response.status_code == 200
    payload = job_response.json()
    assert payload["id"] == job_id
    assert payload["job_type"] == "document_import"


def test_import_rejects_unsupported_file_type(client: TestClient) -> None:
    response = client.post(
        "/documents/import",
        files={"file": ("scan.rtf", b"{\\rtf1 unsupported}", "application/rtf")},
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"
    assert response.json()["error"]["message"] == "Only .txt, .md, .docx, .doc and .pdf uploads are supported"


def test_import_rejects_file_above_configured_max_size(monkeypatch, client: TestClient) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "max_upload_file_size_bytes", 4)

    response = client.post(
        "/documents/import",
        files={"file": ("notes.txt", b"12345", "text/plain")},
    )

    assert response.status_code == 413
    payload = response.json()
    assert payload["error"]["code"] == "FILE_TOO_LARGE"
    assert payload["error"]["details"]["max_file_size_bytes"] == 4
    assert payload["error"]["details"]["received_file_size_bytes"] == 5


def test_import_job_status_surfaces_parser_failures_as_job_failure(client: TestClient) -> None:
    enqueue_response = client.post(
        "/documents/import",
        files={"file": ("broken.pdf", b"%PDF-1.7", "application/pdf")},
    )

    assert enqueue_response.status_code == 202
    job_id = enqueue_response.json()["id"]

    response = client.get(f"/documents/import-jobs/{job_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "failed"
    assert payload["error_code"] == "PARSER_FAILED"
    assert payload["result"] is None


def test_import_job_status_surfaces_ocr_requirement_as_job_failure(client: TestClient) -> None:
    buffer = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(buffer)

    enqueue_response = client.post(
        "/documents/import",
        files={"file": ("scan.pdf", buffer.getvalue(), "application/pdf")},
    )

    assert enqueue_response.status_code == 202
    job_id = enqueue_response.json()["id"]

    response = client.get(f"/documents/import-jobs/{job_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "failed"
    assert payload["error_code"] == "OCR_REQUIRED"
    assert payload["result"] is None


def test_import_job_returns_404_for_unknown_job(client: TestClient) -> None:
    response = client.get("/documents/import-jobs/00000000-0000-0000-0000-999999999999")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "JOB_NOT_FOUND",
            "message": "Background job not found",
            "details": {"job_id": "00000000-0000-0000-0000-999999999999"},
        }
    }


def test_generic_job_status_returns_404_for_unknown_job(client: TestClient) -> None:
    response = client.get("/api/v1/jobs/00000000-0000-0000-0000-999999999999")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "JOB_NOT_FOUND",
            "message": "Background job not found",
            "details": {"job_id": "00000000-0000-0000-0000-999999999999"},
        }
    }
