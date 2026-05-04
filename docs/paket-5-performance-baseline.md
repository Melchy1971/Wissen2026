# Performance-Baseline: Read-API

**Datum:** 2026-05-04  
**Referenzdaten:** 10.000 Dokumente × 5 Versionen × 200 Chunks = 10.000.000 Chunks

---

## Zielwerte

| Endpoint                      | Ziel     |
|-------------------------------|----------|
| `GET /documents`              | < 150 ms |
| `GET /documents/{id}`         | < 100 ms |
| `GET /documents/{id}/chunks`  | < 200 ms |

---

## Analysierte Queries

### `GET /documents` — Vor Optimierung

```sql
-- Aggregiert die gesamte document_versions- und document_chunks-Tabelle,
-- bevor LIMIT 20 auf Documents angewendet wird.
SELECT d.id, d.title, ...,
       COALESCE(vc.version_count, 0),
       COALESCE(lcc.chunk_count, 0)
FROM documents d
LEFT JOIN (
    SELECT document_id, COUNT(id) AS version_count
    FROM document_versions GROUP BY document_id   -- Seq Scan: 50 000 Zeilen
) vc ON vc.document_id = d.id
LEFT JOIN (
    SELECT document_id, document_version_id, COUNT(id) AS chunk_count
    FROM document_chunks GROUP BY document_id, document_version_id -- Seq Scan: 10M Zeilen
) lcc ON ...
WHERE d.workspace_id = ?   -- Seq Scan: kein Index
ORDER BY d.created_at DESC -- explizites Sort
LIMIT 20
```

**Probleme:** Seq Scan auf `document_chunks` (10M Zeilen), HashAggregate,
kein Index auf `documents.workspace_id`.  
**Erwartete Laufzeit ohne Index:** 800–1500 ms.

### `GET /documents` — Nach Optimierung (korrelierte Subqueries)

```sql
-- Subqueries laufen NUR für die 20 paginierten Docs (nach Index-Scan + LIMIT).
SELECT d.id, d.title, ...,
       COALESCE((SELECT COUNT(*) FROM document_versions WHERE document_id = d.id), 0),
       COALESCE((SELECT COUNT(*) FROM document_chunks
                 WHERE document_id = d.id AND document_version_id = d.current_version_id), 0)
FROM documents d
WHERE d.workspace_id = ?        -- Index Scan: ix_documents_workspace_created
ORDER BY d.created_at DESC      -- kein Sort nötig (Index-Reihenfolge)
LIMIT 20
```

**Mit Index:** 20 × 2 Index-Lookups. **Erwartete Laufzeit:** < 15 ms.

### `GET /documents/{id}` — 4 Scalar Subqueries

```sql
SELECT d.*, v.*,
    (SELECT COUNT(*) FROM document_chunks
     WHERE document_id = d.id AND document_version_id = d.current_version_id) AS chunk_count,
    (SELECT COALESCE(SUM(LENGTH(content)), 0) FROM document_chunks
     WHERE document_id = d.id AND document_version_id = d.current_version_id) AS total_chars,
    (SELECT id FROM document_chunks WHERE ... ORDER BY chunk_index ASC  LIMIT 1) AS first_chunk_id,
    (SELECT id FROM document_chunks WHERE ... ORDER BY chunk_index DESC LIMIT 1) AS last_chunk_id
FROM documents d
LEFT JOIN document_versions v ON v.id = d.current_version_id
WHERE d.id = ?
```

**Mit Index `(document_id, document_version_id, chunk_index)`:**  
4 × Index Scan. `total_chars` benötigt Heap-Fetch für `content`.  
**Erwartete Laufzeit:** < 30 ms.

### `GET /documents/{id}/chunks`

```sql
SELECT id, chunk_index, SUBSTR(content, 1, 200), anchor, metadata
FROM document_chunks
WHERE document_id = ? AND document_version_id = ?
ORDER BY chunk_index ASC
```

**Ohne Index:** Seq Scan 10M Zeilen → 400–800 ms.  
**Mit Index `(document_id, document_version_id, chunk_index)`:**  
Index Scan direkt in Sortierreihenfolge, 200 Rows → < 10 ms.

---

## Identifizierte Probleme

| # | Tabelle              | Problem                                              | Betroffene Endpoints          |
|---|----------------------|------------------------------------------------------|-------------------------------|
| 1 | `documents`          | Kein Index auf `workspace_id` → Seq Scan             | GET /documents                |
| 2 | `documents`          | Kein kombinierter Index `(workspace_id, created_at)` → explizites Sort | GET /documents |
| 3 | `document_versions`  | FK `document_id` ohne Index (PostgreSQL legt FK-Indizes nicht automatisch an) | GET /documents, GET /documents/{id}/versions |
| 4 | `document_chunks`    | FK `document_id` + `document_version_id` ohne Index  | Alle Chunk-Queries            |
| 5 | `get_documents()`    | Full-Table-Aggregation vor Pagination                | GET /documents                |
| 6 | `total_chars`        | `SUM(LENGTH(content))` liest Heap für alle 200 Chunks | GET /documents/{id}          |

---

## Maßnahmen

### A) Migration 0008 — Indizes

Datei: `backend/migrations/versions/20260504_0008_read_api_performance_indexes.py`

```sql
-- 1. Workspace-Liste: WHERE + ORDER BY ohne Sort
CREATE INDEX ix_documents_workspace_created
    ON documents (workspace_id, created_at DESC);

-- 2. FK-Index: Versions-Aggregation und Versions-Endpoint
CREATE INDEX ix_document_versions_document_id
    ON document_versions (document_id);

-- 3. Covering Index: alle Chunk-Queries
--    Prefix (doc_id, ver_id)       → COUNT, SUM(LENGTH) in Detail-Query
--    Triple (doc_id, ver_id, idx)  → ORDER BY in Chunks-Endpoint
CREATE INDEX ix_document_chunks_doc_ver_idx
    ON document_chunks (document_id, document_version_id, chunk_index);
```

Der dreispanige Chunk-Index übernimmt alle Chunk-Queries als Prefix-Index und
macht einen separaten `(document_id, document_version_id)`-Index überflüssig.

### B) Repository-Optimierung — `get_documents()`

Datei: `backend/app/repositories/documents.py`

Umstellung von GROUP-BY-Aggregation auf **korrelierte Scalar-Subqueries**:

```python
version_count_sq = (
    select(func.count(DocumentVersion.id))
    .where(DocumentVersion.document_id == Document.id)
    .correlate(Document)
    .scalar_subquery()
)
chunk_count_sq = (
    select(func.count(Chunk.id))
    .where(
        Chunk.document_id == Document.id,
        Chunk.document_version_id == Document.current_version_id,
    )
    .correlate(Document)
    .scalar_subquery()
)
```

**Warum:** PostgreSQL wertet SELECT-list-Subqueries erst nach LIMIT aus.
Mit `LIMIT 20` laufen nur 40 Index-Lookups statt einer Full-Table-Aggregation.

---

## Erwartete Messwerte

### Ohne Indizes (Baseline — rein analytisch)

| Endpoint                      | Mean      | P95       | Status          |
|-------------------------------|-----------|-----------|-----------------|
| `GET /documents`              | ~900 ms   | ~1.200 ms | ✗ +750 ms       |
| `GET /documents/{id}`         | ~180 ms   | ~220 ms   | ✗ +80 ms        |
| `GET /documents/{id}/chunks`  | ~650 ms   | ~800 ms   | ✗ +450 ms       |

*Seq Scans dominieren. HashAggregate auf 10M Chunk-Rows ist der Hauptblocker.*

### Nach Migration 0008 + Query-Optimierung (Erwartung)

| Endpoint                      | Mean    | P95     | Ziel     | Status   |
|-------------------------------|---------|---------|----------|----------|
| `GET /documents`              | < 15 ms | < 25 ms | < 150 ms | ✓ OK     |
| `GET /documents/{id}`         | < 30 ms | < 50 ms | < 100 ms | ✓ OK     |
| `GET /documents/{id}/chunks`  | < 10 ms | < 15 ms | < 200 ms | ✓ OK     |

*Index-Scans statt Seq-Scans. Korrelierte Subqueries laufen nur für 20 Rows.*

> **Hinweis:** Die Werte sind analytisch hergeleitet. Für gemessene Zahlen
> `seed_data.py` + `benchmark.py` ausführen (s.u.).

---

## Abweichungsanalyse

### `GET /documents` — kritischste Abweichung

Ohne Optimierungen läuft diese Query **6× über Ziel** (900 ms vs. 150 ms).  
Ursache: Die GROUP-BY-Subquery über 10M Chunks erzwingt einen HashAggregate-Plan,
der mehr als 60% der Laufzeit verbraucht.

Nach Index + Subquery-Umstellung sinkt die Laufzeit auf < 15 ms. Der
Sicherheitsabstand zum 150-ms-Ziel beträgt dann ~135 ms, was auch bei
späterem Datenwachstum (mehrere Workspaces, 100k Docs) ausreicht.

### `GET /documents/{id}` — `total_chars`-Bottleneck

Bleibt als latenter Bottleneck. `SUM(LENGTH(content))` liest 200 × Heap-Pages.
Akzeptabel bei 200-Byte-Chunks (40 KB), problematisch bei größeren Docs
(z.B. 5.000 Zeichen/Chunk × 200 Chunks = 1 MB pro Detail-Request).

**Kurzfristige Mitigation:** `token_estimate` als Proxy für `total_chars` nutzen
(`token_estimate × 4 ≈ char_count`). Keine Schema-Änderung nötig.

---

## Ausführung

```bash
# 1. Indizes anlegen
cd backend
alembic upgrade head

# 2. Referenzdaten erzeugen
# Quick (100 Docs — sekunden):
python -m tests.performance.seed_data --docs 100

# Full-Scale (10 000 Docs, 10M Chunks — 10–30 Minuten):
python -m tests.performance.seed_data

# 3. Benchmark ausführen
python -m tests.performance.benchmark

# 4. Mit abweichendem Workspace oder mehr Läufen:
python -m tests.performance.benchmark --workspace-id bench-workspace-01 --runs 20
```

Der Benchmark misst **direkt auf Repository-Ebene** (kein HTTP-Overhead) und gibt
aus: Mean, P50, P95, P99 pro Endpoint + EXPLAIN ANALYZE + Index-Status.

---

## Offene Verbesserungen (Backlog)

| # | Maßnahme                                           | Aufwand | Erwartete Wirkung                       |
|---|----------------------------------------------------|---------|-----------------------------------------|
| 1 | `total_chars` als gecachte Spalte in `document_versions` | M   | Eliminiert `SUM(LENGTH(content))`       |
| 2 | `INCLUDE (id)` auf Chunk-Index → Index-Only Scan bei COUNT | S | −5–15 ms in Detail-Query             |
| 3 | Pagination-Count via `COUNT(*) OVER()` Window-Function | S   | Vermeidet separaten Count-Query bei Bedarf |
| 4 | Connection Pooling (PgBouncer) vor API-Server      | M       | Reduziert Connection-Latenz unter Last  |
| 5 | Redis-Cache für Document-Detail (TTL 60 s)         | L       | < 1 ms bei Cache-Hit, erfordert Invalidierung |
