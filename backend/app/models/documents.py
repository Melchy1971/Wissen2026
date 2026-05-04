from datetime import datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("workspace_id", "content_hash", name="uq_documents_workspace_content_hash"),
        CheckConstraint(
            "import_status in ('pending', 'parsing', 'parsed', 'chunked', 'failed', 'duplicate')",
            name="ck_documents_import_status_allowed",
        ),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String, nullable=False)
    owner_user_id: Mapped[str] = mapped_column(String, nullable=False)
    current_version_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("document_versions.id"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    import_status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    document_id: Mapped[str] = mapped_column(String, ForeignKey("documents.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    normalized_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    markdown_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    parser_version: Mapped[str] = mapped_column(String(64), nullable=False)
    ocr_used: Mapped[bool] = mapped_column(Boolean, nullable=False)
    ki_provider: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ki_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Chunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    document_id: Mapped[str] = mapped_column(String, ForeignKey("documents.id"), nullable=False)
    document_version_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("document_versions.id"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    heading_path: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    anchor: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR().with_variant(Text(), "sqlite"),
        nullable=True,
    )
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    token_estimate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    __table_args__ = (
        CheckConstraint("length(trim(title)) > 0", name="ck_chat_sessions_title_not_blank"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String, nullable=False)
    owner_user_id: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        CheckConstraint("message_index >= 0", name="ck_chat_messages_message_index_non_negative"),
        CheckConstraint("role in ('system', 'user', 'assistant')", name="ck_chat_messages_role_allowed"),
        CheckConstraint("length(trim(content)) > 0", name="ck_chat_messages_content_not_blank"),
        CheckConstraint(
            "basis_type in ('knowledge_base', 'general', 'mixed', 'unknown')",
            name="ck_chat_messages_basis_type_allowed",
        ),
        UniqueConstraint("session_id", "message_index", name="uq_chat_messages_session_message_index"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    message_index: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    basis_type: Mapped[str] = mapped_column(String(32), nullable=False, server_default="unknown")
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ChatCitation(Base):
    __tablename__ = "chat_citations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    message_id: Mapped[str] = mapped_column(String, ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False)
    chunk_id: Mapped[str] = mapped_column(String, ForeignKey("document_chunks.id", ondelete="RESTRICT"), nullable=False)
    document_id: Mapped[str] = mapped_column(String, ForeignKey("documents.id", ondelete="RESTRICT"), nullable=False)
    source_anchor: Mapped[dict] = mapped_column(JSON, nullable=False)
