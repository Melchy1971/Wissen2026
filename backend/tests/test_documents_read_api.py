from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.documents import Document
from tests.conftest import DEFAULT_USER_ID, DEFAULT_WORKSPACE_ID


def test_get_documents_lists_workspace_documents_sorted_by_created_at(
    client: TestClient,
    document_fixture: dict[str, str],
) -> None:
    response = client.get(f"/documents?workspace_id={document_fixture['workspace_id']}")

    assert response.status_code == 200
    payload = response.json()
    assert [document["id"] for document in payload] == [
        document_fixture["document_id"],
        "00000000-0000-0000-0000-000000000102",
    ]
    assert payload[0]["latest_version_id"] == document_fixture["version_id"]
    assert set(payload[0]) == {"id", "title", "created_at", "updated_at", "latest_version_id"}


def test_get_document_returns_metadata_and_latest_version(
    client: TestClient,
    document_fixture: dict[str, str],
) -> None:
    response = client.get(f"/documents/{document_fixture['document_id']}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == document_fixture["document_id"]
    assert payload["title"] == "Current Document"
    assert payload["latest_version_id"] == document_fixture["version_id"]
    assert payload["latest_version"] == {
        "id": document_fixture["version_id"],
        "version_number": 1,
        "created_at": "2026-05-01T10:00:00",
        "content_hash": "markdown-hash-current",
    }


def test_get_document_returns_404_for_missing_document(
    client: TestClient,
    document_fixture: dict[str, str],
) -> None:
    response = client.get("/documents/00000000-0000-0000-0000-999999999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found"}


def test_duplicate_document_content_hash_is_rejected_by_test_database(
    db_session: Session,
    document_fixture: dict[str, str],
) -> None:
    db_session.add(
        Document(
            id="00000000-0000-0000-0000-000000000999",
            workspace_id=DEFAULT_WORKSPACE_ID,
            owner_user_id=DEFAULT_USER_ID,
            current_version_id=None,
            title="Duplicate",
            source_type="upload",
            mime_type="text/plain",
            content_hash="hash-current",
            created_at=datetime(2026, 5, 2, 10, 0, tzinfo=UTC),
            updated_at=datetime(2026, 5, 2, 10, 0, tzinfo=UTC),
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_get_latest_chunks_returns_preview_structured_anchor_and_optional_limit(
    client: TestClient,
    document_fixture: dict[str, str],
) -> None:
    response = client.get(f"/documents/{document_fixture['document_id']}/chunks?limit=1")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0] == {
        "chunk_id": document_fixture["chunk_id"],
        "position": 0,
        "text_preview": "x" * 200,
        "source_anchor": {
            "anchor": "dv:current:c0000",
            "page": 1,
            "paragraph": 2,
            "offset": 0,
        },
    }
