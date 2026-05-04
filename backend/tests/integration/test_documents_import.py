import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock

import psycopg
import pytest
from alembic import command
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services.documents.import_persistence_service import DocumentImportPersistenceService
from tests.integration.test_migrations import make_alembic_config, psycopg_url


@pytest.fixture
def test_database_url() -> str:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is not set; skipping document import integration test")
    return database_url


def test_txt_import_persists_document_version_chunks_and_duplicate_status(
    test_database_url,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "database_url", test_database_url)
    config = make_alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    try:
        client = TestClient(app)
        files = {"file": ("notes.txt", b"# Notes\n\nHello world\n", "text/plain")}

        response = client.post("/documents/import", files=files)

        assert response.status_code == 200
        payload = response.json()
        assert payload["title"] == "notes"
        assert payload["chunk_count"] == 1
        assert payload["duplicate_status"] == "created"
        assert payload["import_status"] == "chunked"
        assert payload["document_id"]
        assert payload["version_id"]

        with psycopg.connect(psycopg_url(test_database_url)) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select d.current_version_id, d.mime_type, d.import_status, v.normalized_markdown, count(c.id)
                    from documents d
                    join document_versions v on v.document_id = d.id
                    left join document_chunks c on c.document_version_id = v.id
                    where d.id = %s
                    group by d.current_version_id, d.mime_type, d.import_status, v.normalized_markdown
                    """,
                    (payload["document_id"],),
                )
                row = cursor.fetchone()

            assert row is not None
            assert str(row[0]) == payload["version_id"]
            assert row[1:] == ("text/plain", "chunked", "# Notes\n\nHello world\n", 1)

        duplicate_response = client.post("/documents/import", files=files)

        assert duplicate_response.status_code == 200
        duplicate_payload = duplicate_response.json()
        assert duplicate_payload["document_id"] == payload["document_id"]
        assert duplicate_payload["version_id"] == payload["version_id"]
        assert duplicate_payload["chunk_count"] == 1
        assert duplicate_payload["duplicate_status"] == "duplicate_existing"
        assert duplicate_payload["import_status"] == "duplicate"
    finally:
        command.downgrade(config, "base")


def test_markdown_import_preserves_table_in_persisted_chunk(test_database_url, monkeypatch) -> None:
    monkeypatch.setattr(settings, "database_url", test_database_url)
    config = make_alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    try:
        client = TestClient(app)
        markdown = b"# Table\n\n| Name | Wert |\n| --- | ---: |\n| Alpha | 42 |\n"

        response = client.post(
            "/documents/import",
            files={"file": ("table.md", markdown, "text/markdown")},
        )

        assert response.status_code == 200
        payload = response.json()

        with psycopg.connect(psycopg_url(test_database_url)) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select content, anchor
                    from document_chunks
                    where document_id = %s
                    order by chunk_index
                    """,
                    (payload["document_id"],),
                )
                rows = cursor.fetchall()

        assert len(rows) == 1
        assert "| Name | Wert |\n| --- | ---: |\n| Alpha | 42 |" in rows[0][0]
        assert rows[0][1].startswith(f"dv:{payload['version_id']}:c")
    finally:
        command.downgrade(config, "base")


def test_parallel_duplicate_imports_create_single_document(test_database_url, monkeypatch) -> None:
    monkeypatch.setattr(settings, "database_url", test_database_url)
    config = make_alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    original_fetch_existing = DocumentImportPersistenceService._fetch_existing
    barrier = Barrier(2)
    lock = Lock()
    empty_fetch_count = 0

    def wait_after_initial_empty_fetch(self, connection, *, workspace_id, content_hash):
        nonlocal empty_fetch_count
        existing = original_fetch_existing(
            self,
            connection,
            workspace_id=workspace_id,
            content_hash=content_hash,
        )
        if existing is None:
            with lock:
                empty_fetch_count += 1
                should_wait = empty_fetch_count <= 2
            if should_wait:
                barrier.wait(timeout=10)
        return existing

    monkeypatch.setattr(
        DocumentImportPersistenceService,
        "_fetch_existing",
        wait_after_initial_empty_fetch,
    )

    def post_document() -> dict:
        client = TestClient(app)
        response = client.post(
            "/documents/import",
            files={"file": ("race.txt", b"# Race\n\nSame content\n", "text/plain")},
        )
        assert response.status_code == 200
        return response.json()

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            payloads = list(executor.map(lambda _: post_document(), range(2)))

        assert {payload["document_id"] for payload in payloads}
        assert len({payload["document_id"] for payload in payloads}) == 1
        assert sorted(payload["duplicate_status"] for payload in payloads) == [
            "created",
            "duplicate_existing",
        ]

        with psycopg.connect(psycopg_url(test_database_url)) as connection:
            with connection.cursor() as cursor:
                cursor.execute("select count(*) from documents")
                assert cursor.fetchone() == (1,)

                cursor.execute("select count(*) from document_versions")
                assert cursor.fetchone() == (1,)

                cursor.execute("select count(*) from document_chunks")
                assert cursor.fetchone() == (1,)
    finally:
        command.downgrade(config, "base")
