from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.documents import Document, DocumentVersion
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
    assert payload[0] == {
        "id": document_fixture["document_id"],
        "title": "Current Document",
        "mime_type": "text/plain",
        "created_at": "2026-05-01T10:00:00",
        "updated_at": "2026-05-01T11:00:00",
        "latest_version_id": document_fixture["version_id"],
        "import_status": "chunked",
        "lifecycle_status": "active",
        "archived_at": None,
        "deleted_at": None,
        "version_count": 1,
        "chunk_count": 2,
    }
    assert payload[1]["version_count"] == 1
    assert payload[1]["chunk_count"] == 0


def test_get_documents_requires_workspace_id(client: TestClient) -> None:
    response = client.get("/documents")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "WORKSPACE_REQUIRED"


def test_get_documents_rejects_limit_above_100(client: TestClient, document_fixture: dict[str, str]) -> None:
    response = client.get(f"/documents?workspace_id={document_fixture['workspace_id']}&limit=101")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_PAGINATION"


def test_get_document_returns_metadata_and_latest_version(
    client: TestClient,
    document_fixture: dict[str, str],
) -> None:
    response = client.get(f"/documents/{document_fixture['document_id']}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == document_fixture["document_id"]
    assert payload["title"] == "Current Document"
    assert payload["import_status"] == "chunked"
    assert payload["lifecycle_status"] == "active"
    assert payload["archived_at"] is None
    assert payload["deleted_at"] is None
    assert payload["latest_version_id"] == document_fixture["version_id"]
    assert payload["latest_version"] == {
        "id": document_fixture["version_id"],
        "version_number": 1,
        "created_at": "2026-05-01T10:00:00",
        "content_hash": "markdown-hash-current",
    }
    assert payload["parser_metadata"] == {
        "parser_version": "1.0",
        "ocr_used": False,
        "ki_provider": None,
        "ki_model": None,
        "metadata": {"parser_name": "txt-parser", "source_filename": "current.txt"},
    }
    assert payload["chunk_summary"] == {
        "chunk_count": 2,
        "total_chars": 272,
        "first_chunk_id": document_fixture["chunk_id"],
        "last_chunk_id": "00000000-0000-0000-0000-000000000302",
    }


def test_get_document_returns_404_for_missing_document(
    client: TestClient,
    document_fixture: dict[str, str],
) -> None:
    response = client.get("/documents/00000000-0000-0000-0000-999999999999")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "DOCUMENT_NOT_FOUND",
            "message": "Document not found",
            "details": {"document_id": "00000000-0000-0000-0000-999999999999"},
        }
    }


def test_get_documents_excludes_archived_by_default_and_shows_with_filter(
    client: TestClient,
    db_session: Session,
    document_fixture: dict[str, str],
) -> None:
    archived_id = "00000000-0000-0000-0000-000000000405"
    archived_time = datetime(2026, 5, 2, 10, 0, tzinfo=UTC)
    db_session.add(
        Document(
            id=archived_id,
            workspace_id=document_fixture["workspace_id"],
            owner_user_id=DEFAULT_USER_ID,
            current_version_id=None,
            title="Archived Doc",
            source_type="upload",
            mime_type="text/plain",
            content_hash="archived-doc",
            import_status="chunked",
            lifecycle_status="archived",
            archived_at=archived_time,
            deleted_at=None,
            created_at=archived_time,
            updated_at=archived_time,
        )
    )
    db_session.commit()

    response_default = client.get(f"/documents?workspace_id={document_fixture['workspace_id']}")
    response_filtered = client.get(
        f"/documents?workspace_id={document_fixture['workspace_id']}&lifecycle_status=archived"
    )

    assert response_default.status_code == 200
    assert archived_id not in [document["id"] for document in response_default.json()]
    assert response_filtered.status_code == 200
    assert [document["id"] for document in response_filtered.json()] == [archived_id]


def test_deleted_document_is_not_retrievable(
    client: TestClient,
    db_session: Session,
    document_fixture: dict[str, str],
) -> None:
    deleted_id = "00000000-0000-0000-0000-000000000406"
    deleted_time = datetime(2026, 5, 2, 11, 0, tzinfo=UTC)
    db_session.add(
        Document(
            id=deleted_id,
            workspace_id=document_fixture["workspace_id"],
            owner_user_id=DEFAULT_USER_ID,
            current_version_id=None,
            title="Deleted Doc",
            source_type="upload",
            mime_type="text/plain",
            content_hash="deleted-doc",
            import_status="chunked",
            lifecycle_status="deleted",
            archived_at=None,
            deleted_at=deleted_time,
            created_at=deleted_time,
            updated_at=deleted_time,
        )
    )
    db_session.commit()

    response = client.get(f"/documents/{deleted_id}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DOCUMENT_NOT_FOUND"


def test_archive_document_updates_lifecycle_status(
    client: TestClient,
    document_fixture: dict[str, str],
) -> None:
    response = client.patch(f"/documents/{document_fixture['document_id']}/archive")

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"] == document_fixture["document_id"]
    assert payload["lifecycle_status"] == "archived"
    assert payload["archived_at"] is not None
    assert payload["deleted_at"] is None


def test_restore_document_moves_archived_document_back_to_active(
    client: TestClient,
    document_fixture: dict[str, str],
) -> None:
    archive_response = client.patch(f"/documents/{document_fixture['document_id']}/archive")
    assert archive_response.status_code == 200

    response = client.patch(f"/documents/{document_fixture['document_id']}/restore")

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"] == document_fixture["document_id"]
    assert payload["lifecycle_status"] == "active"
    assert payload["archived_at"] is None
    assert payload["deleted_at"] is None


def test_delete_document_soft_deletes_document(
    client: TestClient,
    document_fixture: dict[str, str],
) -> None:
    response = client.delete(f"/documents/{document_fixture['document_id']}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"] == document_fixture["document_id"]
    assert payload["lifecycle_status"] == "deleted"
    assert payload["deleted_at"] is not None

    get_response = client.get(f"/documents/{document_fixture['document_id']}")
    assert get_response.status_code == 404


def test_get_document_returns_409_when_document_has_no_version(
    client: TestClient,
    db_session: Session,
) -> None:
    document_id = "00000000-0000-0000-0000-000000000401"
    db_session.add(
        Document(
            id=document_id,
            workspace_id=DEFAULT_WORKSPACE_ID,
            owner_user_id=DEFAULT_USER_ID,
            current_version_id=None,
            title="Broken",
            source_type="upload",
            mime_type="text/plain",
            content_hash="broken-no-version",
            import_status="chunked",
            created_at=datetime(2026, 5, 2, 10, 0, tzinfo=UTC),
            updated_at=datetime(2026, 5, 2, 10, 0, tzinfo=UTC),
        )
    )
    db_session.commit()

    response = client.get(f"/documents/{document_id}")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DOCUMENT_STATE_CONFLICT"
    assert response.json()["error"]["message"] == "Document exists without a latest version"


def test_get_document_returns_pending_document_without_version(
    client: TestClient,
    db_session: Session,
) -> None:
    document_id = "00000000-0000-0000-0000-000000000404"
    db_session.add(
        Document(
            id=document_id,
            workspace_id=DEFAULT_WORKSPACE_ID,
            owner_user_id=DEFAULT_USER_ID,
            current_version_id=None,
            title="Pending",
            source_type="upload",
            mime_type="text/plain",
            content_hash="pending-document",
            import_status="pending",
            created_at=datetime(2026, 5, 2, 10, 0, tzinfo=UTC),
            updated_at=datetime(2026, 5, 2, 10, 0, tzinfo=UTC),
        )
    )
    db_session.commit()

    response = client.get(f"/documents/{document_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["import_status"] == "pending"
    assert payload["latest_version"] is None
    assert payload["parser_metadata"] is None
    assert payload["chunk_summary"] == {
        "chunk_count": 0,
        "total_chars": 0,
        "first_chunk_id": None,
        "last_chunk_id": None,
    }


def test_get_document_returns_409_when_completed_version_has_no_chunks(
    client: TestClient,
    db_session: Session,
) -> None:
    document_id = "00000000-0000-0000-0000-000000000402"
    version_id = "00000000-0000-0000-0000-000000000403"
    created_at = datetime(2026, 5, 2, 10, 0, tzinfo=UTC)
    document = Document(
        id=document_id,
        workspace_id=DEFAULT_WORKSPACE_ID,
        owner_user_id=DEFAULT_USER_ID,
        current_version_id=None,
        title="Broken Chunks",
        source_type="upload",
        mime_type="text/plain",
        content_hash="broken-no-chunks",
        import_status="chunked",
        created_at=created_at,
        updated_at=created_at,
    )
    db_session.add(document)
    db_session.flush()
    db_session.add(
        DocumentVersion(
            id=version_id,
            document_id=document_id,
            version_number=1,
            normalized_markdown="# Broken\n",
            markdown_hash="broken-markdown",
            parser_version="1.0",
            ocr_used=False,
            ki_provider=None,
            ki_model=None,
            metadata_={},
            created_at=created_at,
        )
    )
    db_session.flush()
    document.current_version_id = version_id
    db_session.commit()

    response = client.get(f"/documents/{document_id}")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DOCUMENT_STATE_CONFLICT"
    assert response.json()["error"]["message"] == "Document import is chunked but latest version has no chunks"


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
            import_status="chunked",
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
            "type": "text",
            "page": None,
            "paragraph": None,
            "char_start": 0,
            "char_end": 260,
        },
    }
