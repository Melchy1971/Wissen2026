from __future__ import annotations

import logging

from sqlalchemy import cast, distinct, func, select, text, update
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from app.core.errors import ServiceUnavailableApiError
from app.models.documents import Chunk, Document


logger = logging.getLogger(__name__)

SEARCH_VECTOR_INDEX = "ix_document_chunks_search_vector"


class SearchIndexRebuildService:
    def __init__(self, session: Session) -> None:
        self._session = session

    @classmethod
    def from_session(cls, session: Session) -> "SearchIndexRebuildService":
        return cls(session)

    def rebuild_search_index(self, workspace_id: str | None = None) -> dict[str, int | str | None]:
        bind = self._session.get_bind()
        if bind is None or bind.dialect.name != "postgresql":
            raise ServiceUnavailableApiError(message="Search index rebuild requires PostgreSQL")

        normalized_workspace_id = workspace_id.strip() if workspace_id else None
        conditions = [Document.lifecycle_status == "active"]
        if normalized_workspace_id:
            conditions.append(Document.workspace_id == self._uuid_param(normalized_workspace_id))

        chunk_count = int(
            self._session.scalar(
                select(func.count(Chunk.id)).join(Document, Document.id == Chunk.document_id).where(*conditions)
            )
            or 0
        )
        document_count = int(
            self._session.scalar(select(func.count(distinct(Document.id))).where(*conditions)) or 0
        )

        logger.info(
            "search index rebuild started workspace_id=%s active_documents=%s active_chunks=%s",
            normalized_workspace_id or "ALL",
            document_count,
            chunk_count,
        )

        document_ids = select(Document.id).where(*conditions)
        updated = self._session.execute(
            update(Chunk)
            .where(Chunk.document_id.in_(document_ids))
            .values(content=Chunk.content)
        )

        index_exists = bool(
            self._session.execute(
                text(
                    "SELECT EXISTS ("
                    "SELECT 1 FROM pg_indexes "
                    "WHERE schemaname = current_schema() AND indexname = :index_name"
                    ")"
                ),
                {"index_name": SEARCH_VECTOR_INDEX},
            ).scalar()
        )

        if index_exists:
            self._session.execute(text(f"REINDEX INDEX {SEARCH_VECTOR_INDEX}"))
            index_action = "reindexed"
        else:
            self._session.execute(
                text(
                    f"CREATE INDEX {SEARCH_VECTOR_INDEX} "
                    "ON document_chunks USING gin (search_vector)"
                )
            )
            index_action = "created"

        self._session.commit()

        logger.info(
            "search index rebuild finished workspace_id=%s updated_chunks=%s index_action=%s",
            normalized_workspace_id or "ALL",
            updated.rowcount or 0,
            index_action,
        )

        return {
            "workspace_id": normalized_workspace_id,
            "reindexed_chunk_count": int(updated.rowcount or 0),
            "reindexed_document_count": document_count,
            "index_name": SEARCH_VECTOR_INDEX,
            "index_action": index_action,
            "status": "completed",
        }

    def _uuid_param(self, value: str):
        bind = self._session.get_bind()
        if bind is not None and bind.dialect.name == "postgresql":
            return cast(value, postgresql.UUID(as_uuid=False))
        return value