from typing import Any, Protocol

from app.repositories.documents import (
    DocumentChunkRecord,
    DocumentDetailRecord,
    DocumentListRecord,
    DocumentRepository,
    DocumentVersionRecord,
)
from app.schemas.documents import (
    DocumentChunkPreview,
    DocumentChunkSourceAnchor,
    DocumentDetail,
    DocumentListItem,
    DocumentVersionSummary,
)


class DocumentNotFoundError(LookupError):
    pass


class DocumentReadRepository(Protocol):
    def get_documents(self, *, workspace_id: str, limit: int, offset: int) -> list[DocumentListRecord]: ...

    def get_document_detail(self, document_id: str) -> DocumentDetailRecord | None: ...

    def get_versions(self, document_id: str) -> list[DocumentVersionRecord]: ...

    def get_latest_version_id(self, document_id: str) -> str | None: ...

    def get_chunks(self, *, document_id: str, version_id: str, limit: int | None = None) -> list[DocumentChunkRecord]: ...

    def document_exists(self, document_id: str) -> bool: ...


class DocumentReadService:
    def __init__(self, repository: DocumentReadRepository) -> None:
        self._repository = repository

    @classmethod
    def from_session(cls, session) -> "DocumentReadService":
        return cls(DocumentRepository(session))

    def get_documents(self, *, workspace_id: str, limit: int, offset: int) -> list[DocumentListItem]:
        return [
            DocumentListItem(
                id=record.id,
                title=record.title,
                created_at=record.created_at,
                updated_at=record.updated_at,
                latest_version_id=record.latest_version_id,
            )
            for record in self._repository.get_documents(workspace_id=workspace_id, limit=limit, offset=offset)
        ]

    def get_document_detail(self, document_id: str) -> DocumentDetail:
        record = self._repository.get_document_detail(document_id)
        if record is None:
            raise DocumentNotFoundError(document_id)

        latest_version = None
        if (
            record.version_id is not None
            and record.version_number is not None
            and record.version_created_at is not None
            and record.version_content_hash is not None
        ):
            latest_version = DocumentVersionSummary(
                id=record.version_id,
                version_number=record.version_number,
                created_at=record.version_created_at,
                content_hash=record.version_content_hash,
            )

        return DocumentDetail(
            id=record.id,
            workspace_id=record.workspace_id,
            owner_user_id=record.owner_user_id,
            title=record.title,
            source_type=record.source_type,
            mime_type=record.mime_type,
            content_hash=record.content_hash,
            created_at=record.created_at,
            updated_at=record.updated_at,
            latest_version_id=record.latest_version_id,
            latest_version=latest_version,
        )

    def get_versions(self, document_id: str) -> list[DocumentVersionSummary]:
        records = self._repository.get_versions(document_id)
        if not records and not self._repository.document_exists(document_id):
            raise DocumentNotFoundError(document_id)

        return [
            DocumentVersionSummary(
                id=record.id,
                version_number=record.version_number,
                created_at=record.created_at,
                content_hash=record.content_hash,
            )
            for record in records
        ]

    def get_chunks(self, document_id: str, *, limit: int | None = None) -> list[DocumentChunkPreview]:
        latest_version_id = self._repository.get_latest_version_id(document_id)
        if latest_version_id is None:
            if not self._repository.document_exists(document_id):
                raise DocumentNotFoundError(document_id)
            return []

        return [
            DocumentChunkPreview(
                chunk_id=record.id,
                position=record.position,
                text_preview=record.text_preview,
                source_anchor=self._build_source_anchor(record.anchor, record.metadata),
            )
            for record in self._repository.get_chunks(
                document_id=document_id,
                version_id=latest_version_id,
                limit=limit,
            )
        ]

    def _build_source_anchor(self, anchor: str, metadata: dict[str, Any] | None) -> DocumentChunkSourceAnchor:
        source_metadata = metadata or {}
        nested_anchor = source_metadata.get("source_anchor")
        if isinstance(nested_anchor, dict):
            source_metadata = {**source_metadata, **nested_anchor}

        return DocumentChunkSourceAnchor(
            anchor=anchor,
            page=self._optional_int(source_metadata.get("page")),
            paragraph=self._optional_int(source_metadata.get("paragraph")),
            offset=self._optional_int(source_metadata.get("offset")),
        )

    def _optional_int(self, value: Any) -> int | None:
        if value is None or isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.strip().isdigit():
            return int(value)
        return None
