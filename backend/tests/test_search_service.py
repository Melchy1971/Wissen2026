from datetime import UTC, datetime

import pytest

from app.repositories.search import SearchChunkRecord
from app.services.search_service import InvalidSearchQueryError, SearchService


class FakeSearchRepository:
    def __init__(self, records: list[SearchChunkRecord] | None = None) -> None:
        self.records = records or []
        self.calls: list[dict] = []

    def search_chunks(self, *, workspace_id: str, query: str, limit: int, offset: int, filters=None):
        self.calls.append(
            {
                "workspace_id": workspace_id,
                "query": query,
                "limit": limit,
                "offset": offset,
                "filters": filters,
            }
        )
        return self.records


def test_search_chunks_validates_and_maps_results() -> None:
    created_at = datetime(2026, 5, 1, 10, 0, tzinfo=UTC)
    repository = FakeSearchRepository(
        [
            SearchChunkRecord(
                document_id="document-1",
                document_title="Current Document",
                document_created_at=created_at,
                document_version_id="version-1",
                version_number=2,
                chunk_id="chunk-1",
                position=3,
                text_preview="Preview",
                anchor="dv:current:c0003",
                metadata={
                    "source_anchor": {
                        "type": "text",
                        "page": None,
                        "paragraph": None,
                        "char_start": "120",
                        "char_end": "240",
                    }
                },
                rank=0.73,
            )
        ]
    )
    service = SearchService(repository)

    results = service.search_chunks(
        workspace_id=" workspace-1 ",
        query="  chunk query  ",
        limit=20,
        offset=0,
        filters={"mime_type": "text/plain"},
    )

    assert repository.calls == [
        {
            "workspace_id": "workspace-1",
            "query": "chunk query",
            "limit": 20,
            "offset": 0,
            "filters": {"mime_type": "text/plain"},
        }
    ]
    assert len(results) == 1
    assert results[0].document_id == "document-1"
    assert results[0].document_title == "Current Document"
    assert results[0].source_anchor.char_start == 120
    assert results[0].source_anchor.char_end == 240
    assert results[0].rank == 0.73


@pytest.mark.parametrize(
    ("workspace_id", "query", "limit", "offset", "message"),
    [
        (" ", "query", 20, 0, "workspace_id is required"),
        ("workspace-1", "   ", 20, 0, "query must not be blank"),
        ("workspace-1", "query", 0, 0, "limit must be between 1 and 100"),
        ("workspace-1", "query", 101, 0, "limit must be between 1 and 100"),
        ("workspace-1", "query", 20, -1, "offset must be non-negative"),
    ],
)
def test_search_chunks_rejects_invalid_input(
    workspace_id: str,
    query: str,
    limit: int,
    offset: int,
    message: str,
) -> None:
    service = SearchService(FakeSearchRepository())

    with pytest.raises(InvalidSearchQueryError, match=message):
        service.search_chunks(workspace_id=workspace_id, query=query, limit=limit, offset=offset, filters=None)