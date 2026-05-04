#!/usr/bin/env python3
"""
Performance-Baseline: Read-API

Misst die drei Read-Endpoints direkt auf Repository-Ebene (kein HTTP-Overhead)
und analysiert die Query-Pläne via EXPLAIN ANALYZE.

Voraussetzung:
  1. DATABASE_URL gesetzt
  2. Benchmark-Daten vorhanden (seed_data.py ausführen)
  3. Alembic-Migration 0008 ausgeführt (alembic upgrade head)

Aufruf:
  python -m tests.performance.benchmark
  python -m tests.performance.benchmark --workspace-id bench-workspace-01 --runs 20
"""

import argparse
import statistics
import sys
import time
from pathlib import Path

import psycopg
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.core.database import get_database_url, get_sqlalchemy_database_url
from app.repositories.documents import DocumentRepository

# ── Zielwerte ─────────────────────────────────────────────────────────────────
TARGETS = {
    "GET /documents": 150,
    "GET /documents/{id}": 100,
    "GET /documents/{id}/chunks": 200,
}

WARMUP = 3
RUNS = 10


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _ms(seconds: float) -> str:
    return f"{seconds * 1000:.1f}ms"


def _status(mean_ms: float, target_ms: int) -> str:
    if mean_ms <= target_ms:
        return f"✓ OK"
    diff = mean_ms - target_ms
    return f"✗ +{diff:.0f}ms"


def _percentile(data: list[float], p: float) -> float:
    data = sorted(data)
    k = (len(data) - 1) * p
    f, c = int(k), min(int(k) + 1, len(data) - 1)
    return data[f] + (data[c] - data[f]) * (k - f)


def measure(fn, warmup: int, runs: int) -> list[float]:
    for _ in range(warmup):
        fn()
    timings = []
    for _ in range(runs):
        t0 = time.perf_counter()
        fn()
        timings.append(time.perf_counter() - t0)
    return timings


# ── EXPLAIN ANALYZE ────────────────────────────────────────────────────────────

def explain(conn: psycopg.Connection, sql: str, params: tuple) -> str:
    with conn.cursor() as cur:
        cur.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) {sql}", params)
        rows = cur.fetchall()
    return "\n".join(r[0] for r in rows)


def _detect_seq_scans(plan: str) -> list[str]:
    issues = []
    for line in plan.splitlines():
        if "Seq Scan" in line:
            table = line.split("Seq Scan on ")[-1].split()[0].rstrip("(")
            issues.append(f"Seq Scan auf {table}")
    return issues


def _detect_sort(plan: str) -> list[str]:
    issues = []
    for line in plan.splitlines():
        if "Sort" in line and "Index" not in line:
            issues.append("Explizites Sort (kein Index-Scan in Order-Reihenfolge)")
            break
    return issues


def _extract_execution_time(plan: str) -> str:
    for line in plan.splitlines():
        if "Execution Time:" in line:
            return line.strip()
    return ""


# ── Benchmark-Queries (entspricht exakt den Repository-Methoden) ──────────────

SQL_LIST_DOCS = """
SELECT d.id, d.title, d.mime_type, d.created_at, d.updated_at,
       d.current_version_id, d.import_status,
       COALESCE((
           SELECT COUNT(v.id) FROM document_versions v
           WHERE v.document_id = d.id
       ), 0) AS version_count,
       COALESCE((
           SELECT COUNT(c.id) FROM document_chunks c
           WHERE c.document_id = d.id AND c.document_version_id = d.current_version_id
       ), 0) AS chunk_count
FROM documents d
WHERE d.workspace_id = %s::uuid
ORDER BY d.created_at DESC
LIMIT 20 OFFSET 0
"""

SQL_DOCUMENT_DETAIL = """
SELECT
    d.id, d.workspace_id, d.owner_user_id, d.title, d.source_type,
    d.mime_type, d.content_hash, d.created_at, d.updated_at,
    d.current_version_id, d.import_status,
    v.id AS version_id, v.version_number, v.created_at AS version_created_at,
    v.markdown_hash AS version_content_hash,
    v.parser_version, v.ocr_used, v.ki_provider, v.ki_model, v.metadata,
    (SELECT COUNT(c.id) FROM document_chunks c
     WHERE c.document_id = d.id AND c.document_version_id = d.current_version_id
    ) AS chunk_count,
    (SELECT COALESCE(SUM(LENGTH(c.content)), 0) FROM document_chunks c
     WHERE c.document_id = d.id AND c.document_version_id = d.current_version_id
    ) AS total_chars,
    (SELECT c.id FROM document_chunks c
     WHERE c.document_id = d.id AND c.document_version_id = d.current_version_id
     ORDER BY c.chunk_index ASC LIMIT 1
    ) AS first_chunk_id,
    (SELECT c.id FROM document_chunks c
     WHERE c.document_id = d.id AND c.document_version_id = d.current_version_id
     ORDER BY c.chunk_index DESC LIMIT 1
    ) AS last_chunk_id
FROM documents d
LEFT JOIN document_versions v ON v.id = d.current_version_id
WHERE d.id = %s::uuid
"""

SQL_CHUNKS = """
SELECT c.id, c.chunk_index,
       SUBSTR(c.content, 1, 200) AS text_preview,
       c.anchor, c.metadata
FROM document_chunks c
WHERE c.document_id = %s::uuid AND c.document_version_id = %s::uuid
ORDER BY c.chunk_index ASC
"""


# ── Hauptroutine ──────────────────────────────────────────────────────────────

def run_benchmark(
    workspace_id: str,
    sample_doc_id: str,
    sample_ver_id: str,
    warmup: int,
    runs: int,
) -> None:
    engine = create_engine(get_sqlalchemy_database_url(), pool_pre_ping=True)
    db_url = get_database_url()

    # ── Datenmenge ermitteln ───────────────────────────────────────────────────
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM documents WHERE workspace_id = %s::uuid", (workspace_id,))
            num_docs = cur.fetchone()[0]
            cur.execute(
                "SELECT COUNT(*) FROM document_versions WHERE document_id IN "
                "(SELECT id FROM documents WHERE workspace_id = %s::uuid)",
                (workspace_id,),
            )
            num_versions = cur.fetchone()[0]
            cur.execute(
                "SELECT COUNT(*) FROM document_chunks WHERE document_id IN "
                "(SELECT id FROM documents WHERE workspace_id = %s::uuid)",
                (workspace_id,),
            )
            num_chunks = cur.fetchone()[0]

    print("\n" + "=" * 70)
    print("PERFORMANCE-BASELINE: READ-API")
    print("=" * 70)
    print(f"Workspace:      {workspace_id}")
    print(f"Dokumente:      {num_docs:,}")
    print(f"Versionen:      {num_versions:,}")
    print(f"Chunks:         {num_chunks:,}")
    print(f"Warm-up:        {warmup}  |  Messläufe: {runs}")
    print()

    results: dict[str, list[float]] = {}

    with Session(engine) as session:
        repo = DocumentRepository(session)

        # [1] GET /documents
        label = "GET /documents"
        print(f"[1] {label} (workspace={num_docs:,} Docs, limit=20)...")
        timings = measure(
            lambda: repo.get_documents(workspace_id=workspace_id, limit=20, offset=0),
            warmup, runs,
        )
        results[label] = timings

        # [2] GET /documents/{id}
        label = "GET /documents/{id}"
        print(f"[2] {label} (doc={sample_doc_id})...")
        timings = measure(
            lambda: repo.get_document_detail(sample_doc_id),
            warmup, runs,
        )
        results[label] = timings

        # [3] GET /documents/{id}/chunks
        label = "GET /documents/{id}/chunks"
        print(f"[3] {label} (version={sample_ver_id})...")
        timings = measure(
            lambda: repo.get_chunks(
                document_id=sample_doc_id, version_id=sample_ver_id
            ),
            warmup, runs,
        )
        results[label] = timings

    # ── Ergebnistabelle ────────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("MESSWERTE")
    print("=" * 70)
    header = f"{'Endpoint':<30} {'Ziel':>7} {'Mean':>8} {'P50':>8} {'P95':>8} {'P99':>8}  Status"
    print(header)
    print("-" * 70)

    slow_endpoints: list[tuple[str, float, str]] = []

    for label, timings in results.items():
        target = TARGETS[label]
        mean_s = statistics.mean(timings)
        p50_s = _percentile(timings, 0.50)
        p95_s = _percentile(timings, 0.95)
        p99_s = _percentile(timings, 0.99)
        mean_ms = mean_s * 1000
        status = _status(mean_ms, target)

        print(
            f"{label:<30} {f'<{target}ms':>7}"
            f" {_ms(mean_s):>8} {_ms(p50_s):>8} {_ms(p95_s):>8} {_ms(p99_s):>8}"
            f"  {status}"
        )

        if mean_ms > target:
            slow_endpoints.append((label, mean_s, status))

    print()

    # ── EXPLAIN ANALYZE ────────────────────────────────────────────────────────
    with psycopg.connect(db_url) as conn:
        print("=" * 70)
        print("EXPLAIN ANALYZE (Datenbankpläne)")
        print("=" * 70)

        # Plan 1: Document-Liste
        print("\n[1] GET /documents")
        plan1 = explain(conn, SQL_LIST_DOCS, (workspace_id,))
        print(plan1)
        seq_scans = _detect_seq_scans(plan1) + _detect_sort(plan1)
        if seq_scans:
            print(f"\n  ⚠ Probleme: {', '.join(seq_scans)}")
        et = _extract_execution_time(plan1)
        if et:
            print(f"  → {et}")

        # Plan 2: Document-Detail
        print(f"\n[2] GET /documents/{{id}}")
        plan2 = explain(conn, SQL_DOCUMENT_DETAIL, (sample_doc_id,))
        print(plan2)
        seq_scans = _detect_seq_scans(plan2) + _detect_sort(plan2)
        if seq_scans:
            print(f"\n  ⚠ Probleme: {', '.join(seq_scans)}")
        et = _extract_execution_time(plan2)
        if et:
            print(f"  → {et}")

        # Plan 3: Chunks
        print(f"\n[3] GET /documents/{{id}}/chunks")
        plan3 = explain(conn, SQL_CHUNKS, (sample_doc_id, sample_ver_id))
        print(plan3)
        seq_scans = _detect_seq_scans(plan3) + _detect_sort(plan3)
        if seq_scans:
            print(f"\n  ⚠ Probleme: {', '.join(seq_scans)}")
        et = _extract_execution_time(plan3)
        if et:
            print(f"  → {et}")

        # ── Index-Check ────────────────────────────────────────────────────────
        print()
        print("=" * 70)
        print("INDEX-STATUS")
        print("=" * 70)
        expected_indexes = [
            "ix_documents_workspace_created",
            "ix_document_versions_document_created",
            "ix_document_chunks_doc_ver_idx",
        ]
        with conn.cursor() as cur:
            cur.execute(
                "SELECT indexname FROM pg_indexes "
                "WHERE schemaname = 'public' AND indexname = ANY(%s)",
                (expected_indexes,),
            )
            found = {r[0] for r in cur.fetchall()}

        for idx in expected_indexes:
            mark = "✓" if idx in found else "✗ FEHLT"
            print(f"  {mark}  {idx}")

        missing = [i for i in expected_indexes if i not in found]
        if missing:
            print()
            print("  Fehlende Indizes anlegen:")
            index_ddl = {
                "ix_documents_workspace_created": (
                    "CREATE INDEX ix_documents_workspace_created "
                    "ON documents (workspace_id, created_at DESC);"
                ),
                "ix_document_versions_document_created": (
                    "CREATE INDEX ix_document_versions_document_created "
                    "ON document_versions (document_id, created_at DESC);"
                ),
                "ix_document_chunks_doc_ver_idx": (
                    "CREATE INDEX ix_document_chunks_doc_ver_idx "
                    "ON document_chunks (document_id, document_version_id, chunk_index);"
                ),
            }
            for idx in missing:
                print(f"    {index_ddl[idx]}")
            print()
            print("  Oder via Alembic:")
            print("    alembic upgrade head  (Migration 0008)")

    # ── Zusammenfassung ────────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("ZUSAMMENFASSUNG")
    print("=" * 70)

    if not slow_endpoints:
        print("✓ Alle Endpoints innerhalb der Zielwerte.")
    else:
        print("Abweichungen:")
        for label, mean_s, status in slow_endpoints:
            mean_ms = mean_s * 1000
            target = TARGETS[label]
            print(f"  {label}: {mean_ms:.0f}ms (Ziel {target}ms, {status})")

    print()
    print("Optimierungsmaßnahmen (priorisiert):")
    print("  1. alembic upgrade head  → Migration 0008 (Indizes)")
    print("  2. Repository: get_documents nutzt korrelierte Subqueries (bereits angewendet)")
    print("  3. Bei total_chars-Bottleneck: token_estimate-Spalte als Proxy nutzen")
    print("     statt SUM(LENGTH(content)) über alle Chunks zu berechnen")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-API Performance-Baseline")
    parser.add_argument("--workspace-id", default="b0000000-0000-0000-0000-000000000001")
    parser.add_argument(
        "--doc-id",
        default=None,
        help="Sample-Dokument-ID (default: erster Doc im Workspace)",
    )
    parser.add_argument("--warmup", type=int, default=WARMUP)
    parser.add_argument("--runs", type=int, default=RUNS)
    args = parser.parse_args()

    db_url = get_database_url()
    with psycopg.connect(db_url) as conn:
        # Sample-Doc und -Version ermitteln
        with conn.cursor() as cur:
            if args.doc_id:
                sample_doc = args.doc_id
            else:
                cur.execute(
                    "SELECT id FROM documents WHERE workspace_id = %s::uuid LIMIT 1",
                    (args.workspace_id,),
                )
                row = cur.fetchone()
                if not row:
                    print(
                        f"Keine Daten in workspace '{args.workspace_id}'.\n"
                        "Bitte zuerst seed_data.py ausführen.",
                        file=sys.stderr,
                    )
                    sys.exit(1)
                sample_doc = row[0]

            cur.execute(
                "SELECT current_version_id FROM documents WHERE id = %s",
                (sample_doc,),
            )
            row = cur.fetchone()
            sample_ver = row[0] if row else None
            if not sample_ver:
                print(
                    f"Dokument {sample_doc} hat keine current_version_id.",
                    file=sys.stderr,
                )
                sys.exit(1)

    run_benchmark(
        workspace_id=args.workspace_id,
        sample_doc_id=sample_doc,
        sample_ver_id=sample_ver,
        warmup=args.warmup,
        runs=args.runs,
    )


if __name__ == "__main__":
    main()
