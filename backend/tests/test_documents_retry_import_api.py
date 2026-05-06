from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.documents import Chunk, Document, DocumentVersion
from tests.conftest import DEFAULT_USER_ID, DEFAULT_WORKSPACE_ID


def test_retry_import_recovers_parser_failed_document_without_creating_duplicate_versions(
    client: TestClient,
    db_session: Session,
) -> None:
    created_at = datetime(2026, 5, 6, 9, 0, tzinfo=UTC)
    document = Document(
        id="00000000-0000-0000-0000-000000000801",
        workspace_id=DEFAULT_WORKSPACE_ID,
        owner_user_id=DEFAULT_USER_ID,
        current_version_id=None,
        title="Parser Failed",
        source_type="upload",
        mime_type="text/plain",
        content_hash="parser-failed-doc",
        import_status="failed",
        lifecycle_status="active",
        created_at=created_at,
        updated_at=created_at,
    )
    version = DocumentVersion(
        id="00000000-0000-0000-0000-000000000802",
        document_id=document.id,
        version_number=1,
        normalized_markdown="# Title\n\nRecovery text",
        markdown_hash="parser-failed-markdown",
        parser_version="1.0",
        ocr_used=False,
        ki_provider=None,
        ki_model=None,
        metadata_={"mime_type": "text/plain"},
        created_at=created_at,
    )
    db_session.add_all([document, version])
    db_session.commit()

    response = client.post(f"/documents/{document.id}/retry-import")

    assert response.status_code == 200
    assert response.json() == {
        "document_id": document.id,
        "import_status": "chunked",
        "current_version_id": version.id,
        "chunk_count": 1,
        "recovery_action": "retry_parsing",
    }
    recovered_document = db_session.get(Document, document.id)
    assert recovered_document is not None
    assert recovered_document.current_version_id == version.id
    assert recovered_document.import_status == "chunked"
    versions = db_session.scalars(select(DocumentVersion).where(DocumentVersion.document_id == document.id)).all()
    assert [item.id for item in versions] == [version.id]


def test_retry_import_recovers_indexing_failed_document_without_duplicate_chunks(
    client: TestClient,
    db_session: Session,
    document_fixture: dict[str, str],
) -> None:
    document = db_session.get(Document, document_fixture["document_id"])
    chunk = db_session.get(Chunk, document_fixture["chunk_id"])
    assert document is not None
    assert chunk is not None
    document.import_status = "chunked"
    chunk.is_searchable = False
    db_session.add(document)
    db_session.add(chunk)
    db_session.commit()

    before_chunk_ids = [
        row[0]
        for row in db_session.query(Chunk.id).filter(Chunk.document_id == document.id).order_by(Chunk.id.asc()).all()
    ]

    response = client.post(f"/documents/{document.id}/retry-import")

    assert response.status_code == 200
    assert response.json() == {
        "document_id": document.id,
        "import_status": "chunked",
        "current_version_id": document_fixture["version_id"],
        "chunk_count": 2,
        "recovery_action": "retry_indexing",
    }
    after_chunks = db_session.scalars(select(Chunk).where(Chunk.document_id == document.id).order_by(Chunk.id.asc())).all()
    assert [item.id for item in after_chunks] == before_chunk_ids
    assert all(item.is_searchable is True for item in after_chunks)


def test_retry_import_recovers_partial_import_by_rebuilding_chunks(
    client: TestClient,
    db_session: Session,
    document_fixture: dict[str, str],
) -> None:
    document = db_session.get(Document, document_fixture["document_id"])
    version = db_session.get(DocumentVersion, document_fixture["version_id"])
    assert document is not None
    assert version is not None
    document.import_status = "failed"
    db_session.query(Chunk).filter(Chunk.document_version_id == version.id).delete()
    db_session.add(document)
    db_session.commit()

    response = client.post(f"/documents/{document.id}/retry-import")

    assert response.status_code == 200
    assert response.json() == {
        "document_id": document.id,
        "import_status": "chunked",
        "current_version_id": version.id,
        "chunk_count": 1,
        "recovery_action": "retry_chunking",
    }
    rebuilt_chunks = db_session.scalars(
        select(Chunk).where(Chunk.document_version_id == version.id).order_by(Chunk.chunk_index.asc())
    ).all()
    assert len(rebuilt_chunks) == 1
    assert [chunk.chunk_index for chunk in rebuilt_chunks] == [0]
    assert len({chunk.id for chunk in rebuilt_chunks}) == 1
