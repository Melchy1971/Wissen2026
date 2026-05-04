from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.documents import Chunk, Document, DocumentVersion


@dataclass(frozen=True)
class DocumentListRecord:
    id: str
    title: str
    mime_type: str | None
    created_at: datetime
    updated_at: datetime
    latest_version_id: str | None
    import_status: str
    version_count: int
    chunk_count: int


@dataclass(frozen=True)
class DocumentDetailRecord:
    id: str
    workspace_id: str
    owner_user_id: str
    title: str
    source_type: str
    mime_type: str | None
    content_hash: str
    created_at: datetime
    updated_at: datetime
    latest_version_id: str | None
    import_status: str
    version_id: str | None
    version_number: int | None
    version_created_at: datetime | None
    version_content_hash: str | None
    parser_version: str | None
    ocr_used: bool | None
    ki_provider: str | None
    ki_model: str | None
    version_metadata: dict[str, Any] | None
    chunk_count: int
    total_chars: int
    first_chunk_id: str | None
    last_chunk_id: str | None


@dataclass(frozen=True)
class DocumentVersionRecord:
    id: str
    version_number: int
    created_at: datetime
    content_hash: str


@dataclass(frozen=True)
class DocumentChunkRecord:
    id: str
    position: int
    text_preview: str
    anchor: str
    metadata: dict[str, Any] | None


class DocumentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_documents(self, *, workspace_id: str, limit: int, offset: int) -> list[DocumentListRecord]:
        version_counts = (
            select(
                DocumentVersion.document_id.label("document_id"),
                func.count(DocumentVersion.id).label("version_count"),
            )
            .group_by(DocumentVersion.document_id)
            .subquery()
        )
        latest_chunk_counts = (
            select(
                Chunk.document_id.label("document_id"),
                Chunk.document_version_id.label("document_version_id"),
                func.count(Chunk.id).label("chunk_count"),
            )
            .group_by(Chunk.document_id, Chunk.document_version_id)
            .subquery()
        )

        rows = self._session.execute(
            select(
                Document.id,
                Document.title,
                Document.mime_type,
                Document.created_at,
                Document.updated_at,
                Document.current_version_id.label("latest_version_id"),
                Document.import_status,
                func.coalesce(version_counts.c.version_count, 0).label("version_count"),
                func.coalesce(latest_chunk_counts.c.chunk_count, 0).label("chunk_count"),
            )
            .outerjoin(version_counts, version_counts.c.document_id == Document.id)
            .outerjoin(
                latest_chunk_counts,
                (latest_chunk_counts.c.document_id == Document.id)
                & (latest_chunk_counts.c.document_version_id == Document.current_version_id),
            )
            .where(Document.workspace_id == workspace_id)
            .order_by(desc(Document.created_at))
            .limit(limit)
            .offset(offset)
        ).all()

        return [
            DocumentListRecord(
                id=row.id,
                title=row.title,
                mime_type=row.mime_type,
                created_at=row.created_at,
                updated_at=row.updated_at,
                latest_version_id=row.latest_version_id,
                import_status=row.import_status,
                version_count=row.version_count,
                chunk_count=row.chunk_count,
            )
            for row in rows
        ]

    def get_document_detail(self, document_id: str) -> DocumentDetailRecord | None:
        chunk_count = (
            select(func.count(Chunk.id))
            .where(Chunk.document_id == Document.id, Chunk.document_version_id == Document.current_version_id)
            .scalar_subquery()
        )
        total_chars = (
            select(func.coalesce(func.sum(func.length(Chunk.content)), 0))
            .where(Chunk.document_id == Document.id, Chunk.document_version_id == Document.current_version_id)
            .scalar_subquery()
        )
        first_chunk_id = (
            select(Chunk.id)
            .where(Chunk.document_id == Document.id, Chunk.document_version_id == Document.current_version_id)
            .order_by(Chunk.chunk_index.asc())
            .limit(1)
            .scalar_subquery()
        )
        last_chunk_id = (
            select(Chunk.id)
            .where(Chunk.document_id == Document.id, Chunk.document_version_id == Document.current_version_id)
            .order_by(Chunk.chunk_index.desc())
            .limit(1)
            .scalar_subquery()
        )

        row = self._session.execute(
            select(
                Document.id,
                Document.workspace_id,
                Document.owner_user_id,
                Document.title,
                Document.source_type,
                Document.mime_type,
                Document.content_hash,
                Document.created_at,
                Document.updated_at,
                Document.current_version_id.label("latest_version_id"),
                Document.import_status,
                DocumentVersion.id.label("version_id"),
                DocumentVersion.version_number,
                DocumentVersion.created_at.label("version_created_at"),
                DocumentVersion.markdown_hash.label("version_content_hash"),
                DocumentVersion.parser_version,
                DocumentVersion.ocr_used,
                DocumentVersion.ki_provider,
                DocumentVersion.ki_model,
                DocumentVersion.metadata_,
                chunk_count.label("chunk_count"),
                total_chars.label("total_chars"),
                first_chunk_id.label("first_chunk_id"),
                last_chunk_id.label("last_chunk_id"),
            )
            .outerjoin(DocumentVersion, Document.current_version_id == DocumentVersion.id)
            .where(Document.id == document_id)
        ).one_or_none()

        if row is None:
            return None

        return DocumentDetailRecord(
            id=row.id,
            workspace_id=row.workspace_id,
            owner_user_id=row.owner_user_id,
            title=row.title,
            source_type=row.source_type,
            mime_type=row.mime_type,
            content_hash=row.content_hash,
            created_at=row.created_at,
            updated_at=row.updated_at,
            latest_version_id=row.latest_version_id,
            import_status=row.import_status,
            version_id=row.version_id,
            version_number=row.version_number,
            version_created_at=row.version_created_at,
            version_content_hash=row.version_content_hash,
            parser_version=row.parser_version,
            ocr_used=row.ocr_used,
            ki_provider=row.ki_provider,
            ki_model=row.ki_model,
            version_metadata=row.metadata_,
            chunk_count=row.chunk_count,
            total_chars=row.total_chars,
            first_chunk_id=row.first_chunk_id,
            last_chunk_id=row.last_chunk_id,
        )

    def get_versions(self, document_id: str) -> list[DocumentVersionRecord]:
        rows = self._session.execute(
            select(
                DocumentVersion.id,
                DocumentVersion.version_number,
                DocumentVersion.created_at,
                DocumentVersion.markdown_hash.label("content_hash"),
            )
            .where(DocumentVersion.document_id == document_id)
            .order_by(desc(DocumentVersion.created_at), desc(DocumentVersion.version_number))
        ).all()

        return [
            DocumentVersionRecord(
                id=row.id,
                version_number=row.version_number,
                created_at=row.created_at,
                content_hash=row.content_hash,
            )
            for row in rows
        ]

    def get_latest_version_id(self, document_id: str) -> str | None:
        return self._session.execute(
            select(Document.current_version_id).where(Document.id == document_id)
        ).scalar_one_or_none()

    def get_chunks(self, *, document_id: str, version_id: str, limit: int | None = None) -> list[DocumentChunkRecord]:
        query = (
            select(
                Chunk.id,
                Chunk.chunk_index,
                func.substr(Chunk.content, 1, 200).label("text_preview"),
                Chunk.anchor,
                Chunk.metadata_,
            )
            .where(Chunk.document_id == document_id, Chunk.document_version_id == version_id)
            .order_by(Chunk.chunk_index.asc())
        )
        if limit is not None:
            query = query.limit(limit)

        rows = self._session.execute(query).all()

        return [
            DocumentChunkRecord(
                id=row.id,
                position=row.chunk_index,
                text_preview=row.text_preview,
                anchor=row.anchor,
                metadata=row.metadata_,
            )
            for row in rows
        ]

    def document_exists(self, document_id: str) -> bool:
        return (
            self._session.execute(select(Document.id).where(Document.id == document_id).limit(1)).scalar_one_or_none()
            is not None
        )
