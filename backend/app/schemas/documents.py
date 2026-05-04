from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentListItem(BaseModel):
    model_config = ConfigDict(strict=True)

    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    latest_version_id: str | None


class DocumentVersionSummary(BaseModel):
    model_config = ConfigDict(strict=True)

    id: str
    version_number: int
    created_at: datetime
    content_hash: str


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


class DocumentChunkSourceAnchor(BaseModel):
    model_config = ConfigDict(strict=True)

    anchor: str
    page: int | None = None
    paragraph: int | None = None
    offset: int | None = None


class DocumentChunkPreview(BaseModel):
    model_config = ConfigDict(strict=True)

    chunk_id: str
    position: int
    text_preview: str
    source_anchor: DocumentChunkSourceAnchor
