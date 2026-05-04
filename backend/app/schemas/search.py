from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas.documents import DocumentChunkSourceAnchor


class SearchChunkResult(BaseModel):
    model_config = ConfigDict(strict=True)

    document_id: str
    document_title: str
    document_created_at: datetime
    document_version_id: str
    version_number: int
    chunk_id: str
    position: int
    text_preview: str
    source_anchor: DocumentChunkSourceAnchor
    rank: float
    filters: dict[str, Any] = {}