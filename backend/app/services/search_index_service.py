from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import Text as SqlText
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
        self._require_postgresql("Search index rebuild requires PostgreSQL")

        normalized_workspace_id = workspace_id.strip() if workspace_id else None
        active_conditions = [Document.lifecycle_status == "active"]
        scoped_conditions: list = []
        if normalized_workspace_id:
            workspace_condition = Document.workspace_id == self._uuid_param(normalized_workspace_id)
            active_conditions.append(workspace_condition)
            scoped_conditions.append(workspace_condition)

        chunk_count = int(
            self._session.scalar(
                select(func.count(Chunk.id)).join(Document, Document.id == Chunk.document_id).where(*active_conditions)
            )
            or 0
        )
        document_count = int(
            self._session.scalar(select(func.count(distinct(Document.id))).where(*active_conditions)) or 0
        )

        logger.info(
            "search index rebuild started workspace_id=%s active_documents=%s active_chunks=%s",
            normalized_workspace_id or "ALL",
            document_count,
            chunk_count,
        )

        active_document_ids = select(Document.id).where(*active_conditions)
        inactive_document_conditions = list(scoped_conditions)
        inactive_document_conditions.append(Document.lifecycle_status != "active")
        inactive_document_ids = select(Document.id).where(*inactive_document_conditions)

        self._session.execute(
            update(Chunk)
            .where(Chunk.document_id.in_(active_document_ids))
            .values(is_searchable=True)
        )
        self._session.execute(
            update(Chunk)
            .where(Chunk.document_id.in_(inactive_document_ids))
            .values(is_searchable=False)
        )

        updated = self._session.execute(
            update(Chunk)
            .where(Chunk.document_id.in_(select(Document.id).where(*scoped_conditions)) if scoped_conditions else text("TRUE"))
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

    def inspect_inconsistencies(self, workspace_id: str | None = None) -> dict[str, object]:
        self._require_postgresql("Search index consistency checks require PostgreSQL")

        normalized_workspace_id = workspace_id.strip() if workspace_id else None
        scoped_conditions: list = []
        if normalized_workspace_id:
            scoped_conditions.append(Document.workspace_id == self._uuid_param(normalized_workspace_id))

        searchable_chunk_count = int(
            self._session.scalar(
                select(func.count(Chunk.id))
                .join(Document, Document.id == Chunk.document_id)
                .where(*scoped_conditions, Chunk.is_searchable.is_(True))
            )
            or 0
        )

        missing_index_predicate = [
            *scoped_conditions,
            Chunk.is_searchable.is_(True),
            ((Chunk.search_vector.is_(None)) | (cast(Chunk.search_vector, SqlText) == "")),
        ]
        deleted_index_predicate = [
            *scoped_conditions,
            Document.lifecycle_status == "deleted",
            ((Chunk.is_searchable.is_(True)) | (Chunk.search_vector.is_not(None))),
        ]
        archived_index_predicate = [
            *scoped_conditions,
            Document.lifecycle_status == "archived",
            ((Chunk.is_searchable.is_(True)) | (Chunk.search_vector.is_not(None))),
        ]

        missing_index_entries = self._build_bucket(
            predicates=missing_index_predicate,
            note_ok="All searchable chunks have an indexable search vector.",
        )
        deleted_documents_in_index = self._build_bucket(
            predicates=deleted_index_predicate,
            note_ok="No deleted documents are present in the active search index.",
        )
        archived_documents_in_active_index = self._build_bucket(
            predicates=archived_index_predicate,
            note_ok="No archived documents are present in the active search index.",
        )

        bucket_statuses = {
            missing_index_entries["status"],
            deleted_documents_in_index["status"],
            archived_documents_in_active_index["status"],
        }

        return {
            "workspace_id": normalized_workspace_id,
            "checked_at": datetime.now(UTC),
            "index_name": SEARCH_VECTOR_INDEX,
            "status": "inconsistent" if "inconsistent" in bucket_statuses else "ok",
            "searchable_chunk_count": searchable_chunk_count,
            "missing_index_entries": missing_index_entries,
            "orphan_index_entries": {
                "count": 0,
                "status": "not_applicable",
                "sample_chunk_ids": [],
                "sample_document_ids": [],
                "note": "GIN index entries are derived from document_chunks.search_vector and cannot be enumerated as standalone rows.",
            },
            "deleted_documents_in_index": deleted_documents_in_index,
            "archived_documents_in_active_index": archived_documents_in_active_index,
        }

    def _build_bucket(self, *, predicates: list, note_ok: str) -> dict[str, object]:
        count = int(
            self._session.scalar(
                select(func.count(Chunk.id)).join(Document, Document.id == Chunk.document_id).where(*predicates)
            )
            or 0
        )
        sample_chunk_ids = list(
            self._session.scalars(
                select(Chunk.id)
                .join(Document, Document.id == Chunk.document_id)
                .where(*predicates)
                .order_by(Chunk.id.asc())
                .limit(10)
            )
        )
        sample_document_ids = list(
            self._session.scalars(
                select(distinct(Document.id))
                .join(Chunk, Chunk.document_id == Document.id)
                .where(*predicates)
                .order_by(Document.id.asc())
                .limit(10)
            )
        )

        return {
            "count": count,
            "status": "inconsistent" if count else "ok",
            "sample_chunk_ids": sample_chunk_ids,
            "sample_document_ids": sample_document_ids,
            "note": None if count else note_ok,
        }

    def _require_postgresql(self, message: str) -> None:
        bind = self._session.get_bind()
        if bind is None or bind.dialect.name != "postgresql":
            raise ServiceUnavailableApiError(message=message)

    def _uuid_param(self, value: str):
        bind = self._session.get_bind()
        if bind is not None and bind.dialect.name == "postgresql":
            return cast(value, postgresql.UUID(as_uuid=False))
        return value