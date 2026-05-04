from datetime import UTC, datetime

import pytest

from app.repositories.documents import DocumentDetailRecord
from app.services.documents.read_service import DocumentNotFoundError, DocumentReadService


class FakeDocumentRepository:
    def __init__(self, detail: DocumentDetailRecord | None) -> None:
        self.detail = detail

    def get_documents(self, *, workspace_id: str, limit: int, offset: int):
        return []

    def get_document_detail(self, document_id: str) -> DocumentDetailRecord | None:
        return self.detail

    def get_versions(self, document_id: str):
        return []

    def get_latest_version_id(self, document_id: str) -> str | None:
        return None

    def get_chunks(self, *, document_id: str, version_id: str, limit: int | None = None):
        return []

    def document_exists(self, document_id: str) -> bool:
        return self.detail is not None


def test_get_document_detail_maps_repository_record_without_fastapi_or_database() -> None:
    created_at = datetime(2026, 5, 1, 10, 0, tzinfo=UTC)
    service = DocumentReadService(
        FakeDocumentRepository(
            DocumentDetailRecord(
                id="document-1",
                workspace_id="workspace-1",
                owner_user_id="user-1",
                title="Title",
                source_type="upload",
                mime_type="text/plain",
                content_hash="content-hash",
                created_at=created_at,
                updated_at=created_at,
                latest_version_id="version-1",
                version_id="version-1",
                version_number=1,
                version_created_at=created_at,
                version_content_hash="markdown-hash",
            )
        )
    )

    detail = service.get_document_detail("document-1")

    assert detail.id == "document-1"
    assert detail.latest_version is not None
    assert detail.latest_version.id == "version-1"
    assert detail.latest_version.content_hash == "markdown-hash"


def test_get_document_detail_raises_not_found_without_fastapi() -> None:
    service = DocumentReadService(FakeDocumentRepository(None))

    with pytest.raises(DocumentNotFoundError):
        service.get_document_detail("missing")
