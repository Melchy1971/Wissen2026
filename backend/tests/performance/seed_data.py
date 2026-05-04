#!/usr/bin/env python3
"""
Seed benchmark data for Read-API performance tests.

Erzeugt in einem dedizierten Workspace:
  --docs     N  Dokumente        (default 10 000)
  --versions V  Versionen/Doc    (default 5)
  --chunks   C  Chunks/Version   (default 200)

Beispiel (Quick-Run für Entwicklung):
  python -m tests.performance.seed_data --docs 100

Beispiel (Full-Scale):
  python -m tests.performance.seed_data

Voraussetzung: DATABASE_URL als Umgebungsvariable gesetzt.
"""

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.core.database import get_database_url


# ── Feste Benchmark-IDs (UUID-Format, deterministisch) ──────────────────────
BENCH_WORKSPACE_ID = "b0000000-0000-0000-0000-000000000001"
BENCH_USER_ID = "00000000-0000-0000-0000-000000000001"  # default user aus Migration 0001

_CHUNK_CONTENT = "A" * 200
_HEADING_PATH = json.dumps(["Abschnitt"])
_METADATA_TEMPLATE = json.dumps(
    {
        "source_anchor": {
            "type": "text",
            "page": None,
            "paragraph": None,
            "char_start": 0,
            "char_end": 200,
        }
    }
)
_MARKDOWN = "# Benchmark\n\n" + ("Lorem ipsum dolor sit amet. " * 36) + "\n"


def doc_id(i: int) -> str:
    return f"d0000000-0000-0000-0000-{i:012x}"


def ver_id(doc_i: int, ver_i: int) -> str:
    # first segment: 'e' + ver_i (7 hex) = 8 chars
    return f"e{ver_i:07x}-0000-0000-0000-{doc_i:012x}"


def chunk_id(doc_i: int, ver_i: int, chunk_i: int) -> str:
    # first segment: 'c' + chunk_i (4 hex) + ver_i (3 hex) = 1+4+3 = 8 chars
    return f"c{chunk_i:04x}{ver_i:03x}-0000-0000-0000-{doc_i:012x}"


def _progress(label: str, done: int, total: int, elapsed: float) -> None:
    pct = 100 * done // total
    rate = done / elapsed if elapsed > 0 else 0
    print(f"\r  {label}: {done:,}/{total:,} ({pct}%)  {rate:,.0f}/s  {elapsed:.0f}s", end="", flush=True)


def seed(
    workspace_id: str,
    num_docs: int,
    versions_per_doc: int,
    chunks_per_version: int,
    batch_size: int = 2000,
) -> None:
    total_versions = num_docs * versions_per_doc
    total_chunks = num_docs * versions_per_doc * chunks_per_version
    now = datetime.now(UTC).isoformat()

    print(f"\n=== Seed-Daten: {num_docs:,} Docs × {versions_per_doc} Vers × {chunks_per_version} Chunks ===")
    print(f"    Workspace: {workspace_id}")
    print(f"    Gesamt Chunks: {total_chunks:,}\n")

    db_url = get_database_url()
    with psycopg.connect(db_url, autocommit=False) as conn:

        # ── Cleanup ────────────────────────────────────────────────────────────
        print("Bereinige bestehende Daten...")
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM document_chunks WHERE document_id IN "
                "(SELECT id FROM documents WHERE workspace_id = %s::uuid)",
                (workspace_id,),
            )
            cur.execute(
                "DELETE FROM document_versions WHERE document_id IN "
                "(SELECT id FROM documents WHERE workspace_id = %s::uuid)",
                (workspace_id,),
            )
            cur.execute("DELETE FROM documents WHERE workspace_id = %s::uuid", (workspace_id,))
            # Workspace anlegen falls nicht vorhanden
            cur.execute(
                "INSERT INTO workspaces (id, name, is_default) VALUES (%s::uuid, %s, false)"
                " ON CONFLICT (id) DO NOTHING",
                (workspace_id, "Benchmark Workspace"),
            )
        conn.commit()

        # ── Documents ──────────────────────────────────────────────────────────
        print(f"Füge {num_docs:,} Dokumente ein...")
        t0 = time.perf_counter()
        doc_rows = [
            (
                doc_id(i),
                workspace_id,
                BENCH_USER_ID,
                None,  # current_version_id, wird später gesetzt
                f"Benchmark Document {i:06d}",
                "upload",
                "text/plain",
                f"hash-bench-{i:012x}",
                "pending",
                now,
                now,
            )
            for i in range(num_docs)
        ]
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO documents "
                "(id, workspace_id, owner_user_id, current_version_id, title, source_type,"
                " mime_type, content_hash, import_status, created_at, updated_at)"
                " VALUES (%s::uuid,%s::uuid,%s::uuid,%s::uuid,%s,%s,%s,%s,%s,%s,%s)",
                doc_rows,
            )
        conn.commit()
        print(f"  ->{num_docs:,} Dokumente in {time.perf_counter()-t0:.1f}s")

        # ── Versions ───────────────────────────────────────────────────────────
        print(f"Füge {total_versions:,} Versionen ein...")
        t0 = time.perf_counter()
        latest_version: dict[int, str] = {}
        batch: list = []
        inserted = 0

        for i in range(num_docs):
            for v in range(versions_per_doc):
                vid = ver_id(i, v)
                latest_version[i] = vid
                batch.append((
                    vid,
                    doc_id(i),
                    v + 1,
                    _MARKDOWN,
                    f"mdhash-{i:012x}-{v}",
                    "bench-parser/1.0",
                    False,
                    None,
                    None,
                    json.dumps({"parser_name": "bench-parser", "source_filename": f"doc{i:06d}.txt"}),
                    now,
                ))
                if len(batch) >= batch_size:
                    with conn.cursor() as cur:
                        cur.executemany(
                            "INSERT INTO document_versions "
                            "(id, document_id, version_number, normalized_markdown, markdown_hash,"
                            " parser_version, ocr_used, ki_provider, ki_model, metadata, created_at)"
                            " VALUES (%s::uuid,%s::uuid,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)",
                            batch,
                        )
                    conn.commit()
                    inserted += len(batch)
                    batch.clear()
                    _progress("Versionen", inserted, total_versions, time.perf_counter() - t0)

        if batch:
            with conn.cursor() as cur:
                cur.executemany(
                    "INSERT INTO document_versions "
                    "(id, document_id, version_number, normalized_markdown, markdown_hash,"
                    " parser_version, ocr_used, ki_provider, ki_model, metadata, created_at)"
                    " VALUES (%s::uuid,%s::uuid,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)",
                    batch,
                )
            conn.commit()
            inserted += len(batch)
            batch.clear()

        print(f"\n  ->{inserted:,} Versionen in {time.perf_counter()-t0:.1f}s")

        # ── current_version_id setzen ──────────────────────────────────────────
        print("Setze current_version_id...")
        t0 = time.perf_counter()
        update_rows = [(latest_version[i], doc_id(i)) for i in range(num_docs)]
        for start in range(0, len(update_rows), batch_size):
            chunk = update_rows[start : start + batch_size]
            with conn.cursor() as cur:
                cur.executemany(
                    "UPDATE documents SET current_version_id = %s::uuid, import_status = 'parsed' WHERE id = %s::uuid",
                    chunk,
                )
            conn.commit()
        print(f"  ->Update in {time.perf_counter()-t0:.1f}s")

        # ── Chunks ─────────────────────────────────────────────────────────────
        print(f"Füge {total_chunks:,} Chunks ein (batch={batch_size})...")
        t0 = time.perf_counter()
        batch = []
        inserted = 0

        for i in range(num_docs):
            for v in range(versions_per_doc):
                vid = ver_id(i, v)
                did = doc_id(i)
                for c in range(chunks_per_version):
                    batch.append((
                        chunk_id(i, v, c),
                        did,
                        vid,
                        c,
                        _HEADING_PATH,
                        f"text-{c:04d}",  # unique per version (constraint: version_id + anchor)
                        _CHUNK_CONTENT,
                        f"chkhash-{i:012x}-{v}-{c:04d}",
                        40,
                        _METADATA_TEMPLATE,
                        now,
                    ))
                    if len(batch) >= batch_size:
                        with conn.cursor() as cur:
                            cur.executemany(
                                "INSERT INTO document_chunks "
                                "(id, document_id, document_version_id, chunk_index,"
                                " heading_path, anchor, content, content_hash,"
                                " token_estimate, metadata, created_at)"
                                " VALUES (%s::uuid,%s::uuid,%s::uuid,%s,"
                                "        %s::jsonb,%s,%s,%s,%s,%s::jsonb,%s)",
                                batch,
                            )
                        conn.commit()
                        inserted += len(batch)
                        batch.clear()
                        _progress("Chunks", inserted, total_chunks, time.perf_counter() - t0)

        if batch:
            with conn.cursor() as cur:
                cur.executemany(
                    "INSERT INTO document_chunks "
                    "(id, document_id, document_version_id, chunk_index,"
                    " heading_path, anchor, content, content_hash,"
                    " token_estimate, metadata, created_at)"
                    " VALUES (%s::uuid,%s::uuid,%s::uuid,%s,"
                    "        %s::jsonb,%s,%s,%s,%s,%s::jsonb,%s)",
                    batch,
                )
            conn.commit()
            inserted += len(batch)

        print(f"\n  ->{inserted:,} Chunks in {time.perf_counter()-t0:.1f}s")

        print("Setze Importstatus auf chunked...")
        t0 = time.perf_counter()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE documents SET import_status = 'chunked', updated_at = %s WHERE workspace_id = %s::uuid",
                (now, workspace_id),
            )
        conn.commit()
        print(f"  ->Statusupdate in {time.perf_counter()-t0:.1f}s")

    print(f"\nSeed abgeschlossen")
    print(f"  Workspace:      {workspace_id}")
    print(f"  Sample-Doc:     {doc_id(0)}")
    print(f"  Sample-Version: {latest_version[0]}")
    print(f"  Sample-Chunk:   {chunk_id(0, versions_per_doc - 1, 0)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Read-API Benchmark-Daten")
    parser.add_argument("--workspace-id", default=BENCH_WORKSPACE_ID)
    parser.add_argument("--docs", type=int, default=10_000, help="Anzahl Dokumente")
    parser.add_argument("--versions", type=int, default=5, help="Versionen pro Dokument")
    parser.add_argument("--chunks", type=int, default=200, help="Chunks pro Version")
    parser.add_argument("--batch-size", type=int, default=2000)
    args = parser.parse_args()

    seed(
        workspace_id=args.workspace_id,
        num_docs=args.docs,
        versions_per_doc=args.versions,
        chunks_per_version=args.chunks,
        batch_size=args.batch_size,
    )
