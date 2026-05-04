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
    created_at: datetime
    updated_at: datetime
    latest_version_id: str | None


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
    version_id: str | None
    version_number: int | None
    version_created_at: datetime | None
    version_content_hash: str | None


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
        rows = self._session.execute(
            select(
                Document.id,
                Document.title,
                Document.created_at,
                Document.updated_at,
                Document.current_version_id.label("latest_version_id"),
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
                created_at=row.created_at,
                updated_at=row.updated_at,
                latest_version_id=row.latest_version_id,
            )
            for row in rows
        ]

    def get_document_detail(self, document_id: str) -> DocumentDetailRecord | None:
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
                DocumentVersion.id.label("version_id"),
                DocumentVersion.version_number,
                DocumentVersion.created_at.label("version_created_at"),
                DocumentVersion.markdown_hash.label("version_content_hash"),
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
            version_id=row.version_id,
            version_number=row.version_number,
            version_created_at=row.version_created_at,
            version_content_hash=row.version_content_hash,
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
