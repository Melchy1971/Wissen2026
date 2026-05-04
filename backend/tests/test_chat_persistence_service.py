from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.models.documents import Base, ChatCitation, Chunk, Document, DocumentVersion
from app.services.chat.persistence_service import (
    ChatCitationPayload,
    ChatPersistenceError,
    ChatPersistenceService,
    ChatSessionNotFoundError,
)


@pytest.fixture
def chat_engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def chat_session(chat_engine):
    with Session(chat_engine) as session:
        created = datetime(2026, 5, 1, 10, 0, tzinfo=UTC)
        document = Document(
            id="doc-1",
            workspace_id="workspace-1",
            owner_user_id="user-1",
            current_version_id=None,
            title="Current Document",
            source_type="upload",
            mime_type="text/plain",
            content_hash="hash-current",
            import_status="chunked",
            created_at=created,
            updated_at=created,
        )
        version = DocumentVersion(
            id="ver-1",
            document_id="doc-1",
            version_number=1,
            normalized_markdown="# Current\n\nBody",
            markdown_hash="markdown-hash-current",
            parser_version="1.0",
            ocr_used=False,
            ki_provider=None,
            ki_model=None,
            metadata_={},
            created_at=created,
        )
        session.add_all([document, version])
        session.flush()

        document.current_version_id = "ver-1"
        chunk = Chunk(
            id="chunk-1",
            document_id="doc-1",
            document_version_id="ver-1",
            chunk_index=0,
            heading_path=["Current"],
            anchor="dv:ver-1:c0000",
            content="Chunk body text for citation support.",
            content_hash="chunk-hash-1",
            token_estimate=6,
            metadata_={"source_anchor": {"type": "text", "page": None, "paragraph": None, "char_start": 0, "char_end": 34}},
            created_at=created,
        )
        session.add_all([document, chunk])
        session.commit()
        yield session


def test_create_session_persists_chat_session(chat_session: Session) -> None:
    service = ChatPersistenceService(chat_session)

    created = service.create_session(workspace_id="workspace-1", title=" Vertragspruefung ", owner_user_id="user-1")

    assert created.workspace_id == "workspace-1"
    assert created.title == "Vertragspruefung"
    assert created.owner_user_id == "user-1"


def test_list_sessions_orders_by_updated_at_desc(chat_session: Session) -> None:
    service = ChatPersistenceService(chat_session)
    first = service.create_session(workspace_id="workspace-1", title="First", owner_user_id="user-1")
    second = service.create_session(workspace_id="workspace-1", title="Second", owner_user_id="user-1")

    sessions = service.list_sessions(workspace_id="workspace-1")

    assert [session.id for session in sessions][:2] == [second.id, first.id]


def test_create_message_persists_immutable_message_and_updates_session_timestamp(chat_session: Session) -> None:
    service = ChatPersistenceService(chat_session)
    created_session = service.create_session(workspace_id="workspace-1", title="Chat", owner_user_id="user-1")
    original_updated_at = created_session.updated_at

    first_message = service.create_message(
        session_id=created_session.id,
        role="user",
        content="Erste Frage",
        metadata={"request_id": "req-1"},
    )
    second_message = service.create_message(
        session_id=created_session.id,
        role="assistant",
        content="Erste Antwort",
        metadata={"request_id": "req-2"},
    )

    messages = service.list_messages(session_id=created_session.id)
    persisted_session = service.get_session(session_id=created_session.id)

    assert first_message.message_index == 0
    assert second_message.message_index == 1
    assert [message.content for message in messages] == ["Erste Frage", "Erste Antwort"]
    assert messages[0].metadata_ == {"request_id": "req-1"}
    assert persisted_session.updated_at >= original_updated_at

def test_create_message_persists_citations(chat_session: Session) -> None:
    service = ChatPersistenceService(chat_session)
    created_session = service.create_session(workspace_id="workspace-1", title="Chat", owner_user_id="user-1")

    message = service.create_message(
        session_id=created_session.id,
        role="assistant",
        content="Antwort mit Quelle",
        citations=[
            ChatCitationPayload(
                chunk_id="chunk-1",
                document_id="doc-1",
                source_anchor={"type": "text", "page": None, "paragraph": None, "char_start": 0, "char_end": 34},
            )
        ],
    )

    citations = service.list_citations(message_id=message.id)

    assert len(citations) == 1
    assert citations[0].chunk_id == "chunk-1"
    assert citations[0].document_id == "doc-1"


def test_delete_of_cited_document_chunk_is_restricted(chat_session: Session) -> None:
    service = ChatPersistenceService(chat_session)
    created_session = service.create_session(workspace_id="workspace-1", title="Chat", owner_user_id="user-1")
    message = service.create_message(
        session_id=created_session.id,
        role="assistant",
        content="Antwort mit Quelle",
        citations=[
            ChatCitationPayload(
                chunk_id="chunk-1",
                document_id="doc-1",
                source_anchor={"type": "text", "page": None, "paragraph": None, "char_start": 0, "char_end": 34},
            )
        ],
    )
    assert chat_session.get(ChatCitation, chat_session.scalar(select(ChatCitation.id).where(ChatCitation.message_id == message.id))) is not None

    chunk = chat_session.get(Chunk, "chunk-1")
    assert chunk is not None
    chat_session.delete(chunk)
    with pytest.raises(IntegrityError):
        chat_session.commit()
    chat_session.rollback()


def test_service_rejects_invalid_inputs(chat_session: Session) -> None:
    service = ChatPersistenceService(chat_session)

    with pytest.raises(ChatPersistenceError, match="workspace_id must not be blank"):
        service.create_session(workspace_id=" ", title="Title", owner_user_id="user-1")
    with pytest.raises(ChatPersistenceError, match="title must not be blank"):
        service.create_session(workspace_id="workspace-1", title=" ", owner_user_id="user-1")


def test_service_rejects_missing_session(chat_session: Session) -> None:
    service = ChatPersistenceService(chat_session)

    with pytest.raises(ChatSessionNotFoundError, match="chat session not found"):
        service.create_message(session_id="missing", role="user", content="Hallo")