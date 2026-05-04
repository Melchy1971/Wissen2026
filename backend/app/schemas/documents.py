from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


ImportStatus = Literal["pending", "parsing", "parsed", "chunked", "failed", "duplicate"]


class DocumentListItem(BaseModel):
    model_config = ConfigDict(strict=True)

    id: str
    title: str
    mime_type: str | None
    created_at: datetime
    updated_at: datetime
    latest_version_id: str | None
    import_status: ImportStatus
    version_count: int
    chunk_count: int


class DocumentVersionSummary(BaseModel):
    model_config = ConfigDict(strict=True)

    id: str
    version_number: int
    created_at: datetime
    content_hash: str


class DocumentParserMetadata(BaseModel):
    model_config = ConfigDict(strict=True)

    parser_version: str
    ocr_used: bool
    ki_provider: str | None
    ki_model: str | None
    metadata: dict[str, Any]


class DocumentChunkSummary(BaseModel):
    model_config = ConfigDict(strict=True)

    chunk_count: int
    total_chars: int
    first_chunk_id: str | None
    last_chunk_id: str | None


class DocumentDetail(BaseModel):
    model_config = ConfigDict(strict=True)

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
    latest_version: DocumentVersionSummary | None
    parser_metadata: DocumentParserMetadata | None
    import_status: ImportStatus
    chunk_summary: DocumentChunkSummary


class DocumentChunkSourceAnchor(BaseModel):
    model_config = ConfigDict(strict=True)

    type: Literal["text", "pdf_page", "docx_paragraph", "legacy_unknown"]
    page: int | None = None
    paragraph: int | None = None
    char_start: int | None = None
    char_end: int | None = None


class DocumentChunkPreview(BaseModel):
    model_config = ConfigDict(strict=True)

    chunk_id: str
    position: int
    text_preview: str
    source_anchor: DocumentChunkSourceAnchor
