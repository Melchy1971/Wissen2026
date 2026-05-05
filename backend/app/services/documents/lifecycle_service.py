from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.documents import Document


class DocumentLifecycleNotFoundError(LookupError):
    pass


class DocumentLifecycleConflictError(RuntimeError):
    pass


class DocumentLifecycleService:
    def __init__(self, session: Session) -> None:
        self._session = session

    @classmethod
    def from_session(cls, session: Session) -> "DocumentLifecycleService":
        return cls(session)

    def archive(self, document_id: str):
        document = self._get_active_or_archived(document_id)
        if document.lifecycle_status == "archived":
            return document
        if document.lifecycle_status != "active":
            raise DocumentLifecycleConflictError("Only active documents can be archived")

        now = datetime.now(UTC)
        document.lifecycle_status = "archived"
        document.archived_at = now
        document.deleted_at = None
        document.updated_at = now
        self._session.add(document)
        self._session.commit()
        self._session.refresh(document)
        return document

    def restore(self, document_id: str):
        document = self._get_active_or_archived(document_id)
        if document.lifecycle_status == "active":
            return document
        if document.lifecycle_status != "archived":
            raise DocumentLifecycleConflictError("Only archived documents can be restored")

        now = datetime.now(UTC)
        document.lifecycle_status = "active"
        document.archived_at = None
        document.deleted_at = None
        document.updated_at = now
        self._session.add(document)
        self._session.commit()
        self._session.refresh(document)
        return document

    def delete(self, document_id: str):
        document = self._get_active_or_archived(document_id)
        now = datetime.now(UTC)
        previous_status = document.lifecycle_status
        document.lifecycle_status = "deleted"
        if document.archived_at is None and previous_status == "archived":
            document.archived_at = now
        document.deleted_at = now
        document.updated_at = now
        self._session.add(document)
        self._session.commit()
        self._session.refresh(document)
        return document

    def _get_active_or_archived(self, document_id: str) -> Document:
        document = self._session.get(Document, document_id)
        if document is None or document.lifecycle_status == "deleted":
            raise DocumentLifecycleNotFoundError(document_id)
        return document