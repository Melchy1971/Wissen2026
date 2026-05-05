# M4 Performance-Haertung

Stand: 2026-05-05

## Referenzlast

- 50.000 Dokumente
- 10.000.000 Chunks
- 5 gleichzeitige Nutzer
- lokale PostgreSQL-Instanz

## Zielwerte

| Pfad | Zielwert |
|---|---|
| Dokumentliste | < 300 ms |
| Suche | < 500 ms |
| Chat Retrieval vor LLM | < 800 ms |
| Upload grosser Dateien | parser-abhaengig, aber Engpass transparent dokumentiert |

## Messplan

### 1. Datensatz vorbereiten

- Basisdaten mit [backend/tests/performance/seed_data.py](H:/WissenMai2026/backend/tests/performance/seed_data.py) erzeugen.
- Fuer M4 die Seed-Konfiguration auf 50.000 Dokumente und 10.000.000 Chunks hochfahren.
- Messungen gegen lokale PostgreSQL-Instanz nur nach `alembic upgrade head`.

### 2. Warm-up und Messregeln

- 3 Warm-up-Laeufe pro Query oder Endpunkt.
- 10 bis 20 Messlaeufe pro Szenario.
- Mean, P50, P95 und P99 erfassen.
- Immer getrennt messen:
  - Repository-Ebene ohne HTTP-Overhead
  - API-Ebene mit FastAPI + JSON-Serialisierung

### 3. Zu pruefende Pfade

#### Dokumentliste

- `GET /documents?workspace_id=...&limit=20&offset=0`
- Lastprofil:
  - Workspace mit 50k Dokumenten
  - Standardfall `lifecycle_status=active`
  - Parallel: 5 Nutzer x 5 Requests hintereinander

#### Dokumentdetail

- `GET /documents/{id}`
- Referenzdokument mit 200 Chunks in aktueller Version
- Zusaetzlich grosses Dokument mit langen Chunks fuer `total_chars`

#### Chunkansicht

- `GET /documents/{id}/chunks`
- Varianten mit `limit=50`, `limit=200`, ohne Limit

#### Suche

- `GET /api/v1/search/chunks?workspace_id=...&q=...`
- Query-Klassen:
  - haeufige Standardbegriffe
  - seltene Begriffe
  - mehrwortige Anfragen
- Messung immer mit aktivem FTS-Index und dokumentierter `EXPLAIN ANALYZE`

#### Chat Retrieval vor LLM

- messen bis einschliesslich:
  - SearchRepository/SearchService
  - ContextBuilder
  - InsufficientContextPolicy
  - PromptBuilder
- LLM-Aufruf explizit ausklammern
- Query-Sets mit ausreichendem und unzureichendem Kontext

#### Upload grosser Dateien

- TXT, MD, DOCX und PDF separat messen
- Dateiklassen:
  - klein: < 1 MB
  - mittel: 5 bis 20 MB
  - gross: > 20 MB
- Messpunkte:
  - Upload lesen
  - Parser + Normalisierung
  - Chunking
  - Persistenz
- Ergebnis nicht als starre SLA werten, sondern als groessenabhaengigen Verlauf dokumentieren

## Indexpruefung

### Bereits vorhanden und relevant

| Index | Zweck | Status |
|---|---|---|
| `ix_documents_workspace_created` | Dokumentliste nach Workspace + Recency | vorhanden |
| `ix_documents_workspace_lifecycle_created_at` | aktive/archivierte Dokumentliste | vorhanden |
| `ix_document_versions_document_id` | Version-Count und Versionsliste | vorhanden |
| `ix_document_chunks_doc_ver_idx` | Chunkliste, Chunk-Count, first/last chunk | vorhanden |
| `ix_document_chunks_search_vector` | PostgreSQL FTS | vorhanden |
| `ix_chat_sessions_workspace_updated_at` | Sessionliste pro Workspace ohne zusaetzlichen Sort | neu in 0014 |
| `ix_chat_messages_session_message_index_desc` | letztes Message-Index-Lookup, geordnete Nachrichten | neu in 0014 |

### Pruef-SQL

```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname IN (
    'ix_documents_workspace_created',
    'ix_documents_workspace_lifecycle_created_at',
    'ix_document_versions_document_id',
    'ix_document_chunks_doc_ver_idx',
    'ix_document_chunks_search_vector',
    'ix_chat_sessions_workspace_updated_at',
    'ix_chat_messages_session_message_index_desc'
  )
ORDER BY indexname;
```

## Bottleneck-Liste

### 1. Upload-Persistenz grosser Dateien

- Vorher: ein `INSERT` pro Chunk im Python-Loop
- Wirkung: viele DB-Roundtrips bei grossen Dokumenten und PDFs
- Massnahme: Chunk-Inserts auf `executemany(...)` gebuendelt

### 2. Chat-Nachrichtenindex unter Parallelitaet

- Vorher: `_next_message_index()` ueber `MAX(message_index)`
- Wirkung: unnötige Aggregation pro Nachricht und schlechtere Planstabilitaet unter 5 parallelen Nutzern
- Massnahme:
  - Lookup ueber `ORDER BY message_index DESC LIMIT 1`
  - neuer Index `ix_chat_messages_session_message_index_desc`

### 3. Chat-Session-Liste

- Vorher: Filter `workspace_id` plus Sort `updated_at DESC` nur mit Einzelindizes
- Wirkung: zusaetzliche Sort-Operation moeglich
- Massnahme: neuer Composite-Index `ix_chat_sessions_workspace_updated_at`

### 4. Dokumentdetail `total_chars`

- Aktuell: `SUM(LENGTH(content))` ueber alle Chunks der aktuellen Version
- Wirkung: heap-lastig bei grossen Dokumenten
- Status: bleibt M4-Restbottleneck
- Folgeoptionen:
  - gecachte Zeichenzahl pro Version
  - naehere Approximation ueber `token_estimate * 4`

### 5. Suche auf 10 Mio Chunks

- Hauptabhaengig von:
  - GIN-Index-Gesundheit
  - `VACUUM ANALYZE`
  - Rank-Sort bei grossen Treffermengen
- M4-Pruefpunkt:
  - `EXPLAIN ANALYZE` fuer haeufige und seltene Suchbegriffe sichern
  - Rebuild-Runbook fuer `ix_document_chunks_search_vector` vorhanden halten

### 6. Chat Retrieval vor LLM

- technisch dominiert durch Suche + Kontextaufbau
- kritischer Pfad:
  - FTS-Trefferzahl
  - Anzahl uebernommener Chunks in den Kontext
  - String-Verarbeitung im PromptBuilder
- M4-Ziel nur erreichbar, wenn Suche unter Ziel bleibt und Kontext groessenbegrenzt bleibt

## Umgesetzte Optimierungen

### Code

- [backend/app/services/documents/import_persistence_service.py](H:/WissenMai2026/backend/app/services/documents/import_persistence_service.py)
  - Chunk-Persistenz von Einzel-`INSERT`s auf gebuendelte `executemany(...)`-Writes umgestellt
- [backend/app/services/chat/persistence_service.py](H:/WissenMai2026/backend/app/services/chat/persistence_service.py)
  - `_next_message_index()` auf geordneten Top-1-Lookup umgestellt

### Datenbank

- [backend/migrations/versions/20260505_0014_m4_performance_indexes.py](H:/WissenMai2026/backend/migrations/versions/20260505_0014_m4_performance_indexes.py)
  - `ix_chat_sessions_workspace_updated_at`
  - `ix_chat_messages_session_message_index_desc`

## Bewertung gegen Zielwerte

### Erwartung nach aktueller Haertung

| Pfad | Erwartung | Bewertung |
|---|---|---|
| Dokumentliste | deutlich unter 300 ms | realistisch |
| Dokumentdetail | deutlich unter 300 ms | realistisch, ausser `total_chars` bei Extremfaellen |
| Chunkansicht | deutlich unter 300 ms | realistisch |
| Suche | unter 500 ms mit gesundem GIN-Index | plausibel, messen |
| Chat Retrieval vor LLM | unter 800 ms bei begrenztem Kontext | plausibel, messen |
| Upload grosser Dateien | parser- und dateitypabhaengig | keine harte SLA, aber jetzt geringerer Persistenz-Overhead |

## Empfohlene Messreihenfolge

1. Repository-Benchmark fuer Dokumentliste, Detail und Chunks
2. FTS-Messung mit `EXPLAIN ANALYZE` fuer Suche
3. Chat-Retrieval ohne LLM gegen reale Search-Daten
4. Upload-Messung getrennt nach TXT, DOCX, PDF
5. 5-Nutzer-Paralleltest lokal mit fixer Datenbasis und gleicher Postgres-Konfiguration

## Offene M4-Nachzuege

1. Benchmark-Skript von Read-API auf Search, Chat-Retrieval und Upload erweitern
2. `document_versions.total_chars` oder aequivalente Cache-Spalte pruefen
3. Upload fuer sehr grosse Dateien spaeter in asynchronen Jobpfad verschieben, falls lokale Parserzeiten kritisch werden