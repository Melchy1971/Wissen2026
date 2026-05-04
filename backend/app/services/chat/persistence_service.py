from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.documents import ChatCitation, ChatMessage, ChatSession


CHAT_ROLES = {"system", "user", "assistant"}


class ChatPersistenceError(ValueError):
    pass


class ChatSessionNotFoundError(ChatPersistenceError):
    pass


@dataclass(frozen=True)
class ChatCitationPayload:
    chunk_id: str
    document_id: str
    source_anchor: dict


class ChatPersistenceService:
    def __init__(self, session: Session) -> None:
        self._session = session

    @classmethod
    def from_session(cls, session: Session) -> "ChatPersistenceService":
        return cls(session)

    def create_session(
        self,
        *,
        workspace_id: str,
        title: str,
        owner_user_id: str | None = None,
    ) -> ChatSession:
        normalized_workspace_id = workspace_id.strip()
        normalized_title = title.strip()
        normalized_owner_user_id = (owner_user_id or settings.default_user_id).strip()

        if not normalized_workspace_id:
            raise ChatPersistenceError("workspace_id must not be blank")
        if not normalized_title:
            raise ChatPersistenceError("title must not be blank")
        if not normalized_owner_user_id:
            raise ChatPersistenceError("owner_user_id must not be blank")

        now = datetime.now(UTC)
        chat_session = ChatSession(
            id=str(uuid4()),
            workspace_id=normalized_workspace_id,
            owner_user_id=normalized_owner_user_id,
            title=normalized_title,
            created_at=now,
            updated_at=now,
        )
        self._session.add(chat_session)
        self._session.commit()
        self._session.refresh(chat_session)
        return chat_session

    def list_sessions(self, *, workspace_id: str, limit: int = 20, offset: int = 0) -> list[ChatSession]:
        normalized_workspace_id = workspace_id.strip()
        if not normalized_workspace_id:
            raise ChatPersistenceError("workspace_id must not be blank")
        if limit < 1 or limit > 100:
            raise ChatPersistenceError("limit must be between 1 and 100")
        if offset < 0:
            raise ChatPersistenceError("offset must be non-negative")

        return list(
            self._session.scalars(
                select(ChatSession)
                .where(ChatSession.workspace_id == normalized_workspace_id)
                .order_by(ChatSession.updated_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )

    def get_session(self, *, session_id: str) -> ChatSession:
        chat_session = self._session.get(ChatSession, session_id)
        if chat_session is None:
            raise ChatSessionNotFoundError(f"chat session not found: {session_id}")
        return chat_session

    def list_messages(self, *, session_id: str) -> list[ChatMessage]:
        self.get_session(session_id=session_id)
        return list(
            self._session.scalars(
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.message_index.asc(), ChatMessage.created_at.asc(), ChatMessage.id.asc())
            )
        )

    def list_citations(self, *, message_id: str) -> list[ChatCitation]:
        return list(
            self._session.scalars(
                select(ChatCitation)
                .where(ChatCitation.message_id == message_id)
                .order_by(ChatCitation.id.asc())
            )
        )

    def create_message(
        self,
        *,
        session_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
        citations: list[ChatCitationPayload] | None = None,
        basis_type: str = "unknown",
    ) -> ChatMessage:
        chat_session = self.get_session(session_id=session_id)
        normalized_role = role.strip()
        normalized_content = content.strip()
        if normalized_role not in CHAT_ROLES:
            raise ChatPersistenceError("role must be one of: assistant, system, user")
        if not normalized_content:
            raise ChatPersistenceError("content must not be blank")

        next_index = self._next_message_index(session_id=session_id)
        now = datetime.now(UTC)
        chat_message = ChatMessage(
            id=str(uuid4()),
            session_id=session_id,
            message_index=next_index,
            role=normalized_role,
            content=normalized_content,
            basis_type=basis_type,
            metadata_=metadata or {},
            created_at=now,
        )
        self._session.add(chat_message)
        self._session.flush()

        for citation in citations or []:
            self._validate_citation_payload(citation)
            self._session.add(
                ChatCitation(
                    id=str(uuid4()),
                    message_id=chat_message.id,
                    chunk_id=citation.chunk_id,
                    document_id=citation.document_id,
                    source_anchor=citation.source_anchor,
                )
            )

        chat_session.updated_at = now
        self._session.add(chat_session)
        self._session.commit()
        self._session.refresh(chat_message)
        return chat_message

    def _next_message_index(self, *, session_id: str) -> int:
        current_max = self._session.scalar(
            select(func.max(ChatMessage.message_index)).where(ChatMessage.session_id == session_id)
        )
        return 0 if current_max is None else int(current_max) + 1

    def _validate_citation_payload(self, citation: ChatCitationPayload) -> None:
        if not citation.chunk_id.strip():
            raise ChatPersistenceError("citation chunk_id must not be blank")
        if not citation.document_id.strip():
            raise ChatPersistenceError("citation document_id must not be blank")
        if not isinstance(citation.source_anchor, dict):
            raise ChatPersistenceError("citation source_anchor must be a dict")