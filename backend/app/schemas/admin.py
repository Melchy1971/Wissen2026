from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SearchIndexRebuildResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    workspace_id: str | None
    reindexed_chunk_count: int
    reindexed_document_count: int
    index_name: str
    index_action: str
    status: str


class SearchIndexInconsistencyBucket(BaseModel):
    model_config = ConfigDict(strict=True)

    count: int
    status: str
    sample_chunk_ids: list[str]
    sample_document_ids: list[str]
    note: str | None = None


class SearchIndexInconsistencyReportResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    workspace_id: str | None
    checked_at: datetime
    index_name: str
    status: str
    searchable_chunk_count: int
    missing_index_entries: SearchIndexInconsistencyBucket
    orphan_index_entries: SearchIndexInconsistencyBucket
    deleted_documents_in_index: SearchIndexInconsistencyBucket
    archived_documents_in_active_index: SearchIndexInconsistencyBucket