from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.documents import Chunk, Document, DocumentVersion
from app.services.chunking_service import MarkdownChunkingService
from app.services.search_index_service import SearchIndexRebuildService


class DocumentImportRecoveryNotFoundError(LookupError):
    pass


class DocumentImportRecoveryConflictError(RuntimeError):
    pass


class DocumentImportRecoveryService:
    def __init__(
        self,
        session: Session,
        *,
        chunking_service: MarkdownChunkingService | None = None,
    ) -> None:
        self._session = session
        self._chunking_service = chunking_service or MarkdownChunkingService()

    @classmethod
    def from_session(cls, session: Session) -> "DocumentImportRecoveryService":
        return cls(session)

    def retry_import(self, *, document_id: str, workspace_id: str) -> dict[str, object]:
        document = self._session.scalar(
            select(Document).where(Document.id == document_id, Document.workspace_id == workspace_id)
        )
        if document is None or document.lifecycle_status == "deleted":
            raise DocumentImportRecoveryNotFoundError(document_id)
        if document.import_status == "duplicate":
            raise DocumentImportRecoveryConflictError("Duplicate documents cannot be retried")

        latest_version = self._session.scalar(
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document.id)
            .order_by(DocumentVersion.version_number.desc(), DocumentVersion.created_at.desc(), DocumentVersion.id.desc())
            .limit(1)
        )

        if document.import_status == "chunked":
            if document.current_version_id is None:
                raise DocumentImportRecoveryConflictError("Chunked document exists without a current version")
            chunk_count = self._count_chunks(document.current_version_id)
            if chunk_count == 0:
                raise DocumentImportRecoveryConflictError("Chunked document has no chunks to reindex")
            self._repair_indexing(document)
            return self._build_result(document=document, recovery_action="retry_indexing")

        if latest_version is None:
            raise DocumentImportRecoveryConflictError("Import recovery requires a persisted version")

        recovery_action = "retry_parsing" if document.current_version_id is None else "retry_chunking"
        document.current_version_id = latest_version.id

        regenerated_chunks = self._chunking_service.chunk(
            latest_version.normalized_markdown,
            document_version_id=latest_version.id,
            source_anchor_type=self._source_anchor_type(document.mime_type, latest_version.parser_version),
        )

        self._session.execute(delete(Chunk).where(Chunk.document_version_id == latest_version.id))
        now = datetime.now(UTC)
        is_searchable = document.lifecycle_status == "active"
        for chunk in regenerated_chunks:
            self._session.add(
                Chunk(
                    id=str(uuid4()),
                    document_id=document.id,
                    document_version_id=latest_version.id,
                    chunk_index=chunk.chunk_index,
                    heading_path=chunk.heading_path,
                    anchor=chunk.anchor,
                    content=chunk.content,
                    is_searchable=is_searchable,
                    content_hash=chunk.content_hash,
                    token_estimate=chunk.token_estimate,
                    metadata_=chunk.metadata,
                    created_at=now,
                )
            )

        document.import_status = "chunked"
        document.updated_at = now
        self._session.add(document)
        self._session.flush()
        self._repair_indexing(document, commit=False)
        self._session.commit()
        self._session.refresh(document)

        return self._build_result(document=document, recovery_action=recovery_action)

    def _repair_indexing(self, document: Document, *, commit: bool = True) -> None:
        is_searchable = document.lifecycle_status == "active"
        chunks = list(
            self._session.scalars(select(Chunk).where(Chunk.document_id == document.id).order_by(Chunk.chunk_index.asc(), Chunk.id.asc()))
        )
        for chunk in chunks:
            chunk.is_searchable = is_searchable
            self._session.add(chunk)

        bind = self._session.get_bind()
        if bind is not None and bind.dialect.name == "postgresql":
            SearchIndexRebuildService.from_session(self._session).rebuild_search_index(workspace_id=document.workspace_id)
            return

        if commit:
            self._session.commit()
            self._session.refresh(document)

    def _count_chunks(self, version_id: str) -> int:
        return int(self._session.scalar(select(func.count(Chunk.id)).where(Chunk.document_version_id == version_id)) or 0)

    def _build_result(self, *, document: Document, recovery_action: str) -> dict[str, object]:
        chunk_count = 0
        if document.current_version_id is not None:
            chunk_count = self._count_chunks(document.current_version_id)
        return {
            "document_id": document.id,
            "import_status": document.import_status,
            "current_version_id": document.current_version_id,
            "chunk_count": chunk_count,
            "recovery_action": recovery_action,
        }

    def _source_anchor_type(self, mime_type: str | None, parser_version: str | None) -> str:
        normalized_mime_type = (mime_type or "").strip().lower()
        if normalized_mime_type == "application/pdf":
            return "pdf_page"
        if normalized_mime_type in {
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        }:
            return "docx_paragraph"
        if normalized_mime_type.startswith("text/") or parser_version:
            return "text"
        return "legacy_unknown"