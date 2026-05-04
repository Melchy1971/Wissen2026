# Observability: Paket 5

Stand: 2026-05-04

Ziel: Fehler, Duplicate-Verhalten und Performance der Dokument-Import- und Read-API sichtbar machen, ohne eine externe Observability-Plattform vorauszusetzen.

## Grundprinzipien

- Minimaler Overhead: strukturierte Logs und einfache Timing-Messungen reichen fuer Paket 5.
- Keine Pflicht-Abhaengigkeit auf externe Plattform.
- Logs sind JSON-kompatibel und koennen spaeter an OpenTelemetry, Prometheus, Grafana/Loki oder eine andere Plattform angebunden werden.
- Keine Volltexte, keine Dokumentinhalte und keine sensiblen Datei-Inhalte in Logs oder Metriken.
- Korrelation ueber `request_id` pro HTTP-Request.

## Logging-Konzept

### Format

Jeder relevante Logeintrag soll folgende Felder enthalten:

| Feld | Bedeutung |
|---|---|
| `timestamp` | ISO-8601 Zeitstempel |
| `level` | `INFO`, `WARNING`, `ERROR` |
| `event` | stabile Event-ID |
| `request_id` | Korrelations-ID pro HTTP-Request |
| `workspace_id` | Workspace, falls bekannt |
| `document_id` | Dokument-ID, falls bekannt |
| `version_id` | Version-ID, falls bekannt |
| `filename` | Dateiname ohne Pfad |
| `mime_type` | erkannter MIME-Type |
| `duration_ms` | Dauer des Schritts |
| `error_code` | API-/Import-Fehlercode |
| `details` | kleine strukturierte Zusatzdaten |

### Events

| Event | Level | Messpunkt | Pflichtfelder |
|---|---|---|---|
| `document_import_started` | INFO | Start von `POST /documents/import` | `request_id`, `filename`, `mime_type`, `size_bytes` |
| `document_import_parsed` | INFO | nach erfolgreichem Parser/Normalizer | `request_id`, `filename`, `mime_type`, `parser_version`, `duration_ms` |
| `document_import_completed` | INFO | nach Persistenz | `request_id`, `document_id`, `version_id`, `chunk_count`, `duration_ms`, `duplicate_status`, `import_status` |
| `document_import_failed` | ERROR | Importfehler vor erfolgreicher Persistenz | `request_id`, `filename`, `mime_type`, `error_code`, `duration_ms` |
| `document_duplicate_detected` | INFO | bestehendes Dokument per Hash gefunden oder Unique-Konflikt abgefangen | `request_id`, `workspace_id`, `document_id`, `content_hash_prefix`, `duration_ms` |
| `document_parser_failed` | WARNING | Parser wirft kontrollierten Fehler | `request_id`, `filename`, `mime_type`, `error_code`, `parser_name` |
| `document_ocr_required` | WARNING | PDF braucht OCR, OCR nicht im Scope | `request_id`, `filename`, `mime_type`, `error_code` |
| `document_db_error` | ERROR | DB-Konfiguration, Verbindung oder IntegrityError ausserhalb Duplicate-Fall | `request_id`, `operation`, `error_code` |
| `document_read_completed` | INFO | Read-Endpunkt erfolgreich | `request_id`, `endpoint`, `document_id`, `workspace_id`, `duration_ms`, `row_count` |
| `document_state_conflict` | WARNING | inkonsistenter Dokumentzustand | `request_id`, `document_id`, `error_code` |

### Log-Level-Regeln

- `INFO`: normaler Import-/Read-Erfolg und erkannte Duplikate.
- `WARNING`: erwartbare fachliche Fehler wie Parserfehler, OCR-Bedarf oder State Conflict.
- `ERROR`: DB-Fehler, unerwartete Exceptions, nicht aufloesbare Persistenzfehler.

### Datenschutz

Nicht loggen:

- `normalized_markdown`
- Chunk-`content`
- Upload-Bytes
- komplette Hashes, falls nicht notwendig
- freie Parser-Metadaten ohne Allowlist

Erlaubt:

- `content_hash_prefix`, z.B. erste 12 Zeichen fuer Debugging.
- `filename` ohne Pfad.
- Dateigroesse, MIME-Type, Parsername, Chunk-Anzahl.

## Metrikdefinition

Metriken koennen initial aus strukturierten Logs berechnet werden. Optional kann spaeter ein `/metrics`-Endpoint oder Prometheus/OpenTelemetry Exporter ergaenzt werden.

| Metrik | Typ | Definition | Labels | Quelle |
|---|---|---|---|---|
| `documents_created_total` | Counter | Anzahl neu erstellter Dokumente | `workspace_id`, `mime_type` | `document_import_completed` mit `duplicate_status=created` |
| `documents_created_per_day` | Derived | Tagesaggregation von `documents_created_total` | `workspace_id`, `date` | Logs oder DB |
| `document_import_duration_ms` | Histogram | Dauer von Upload-Annahme bis Persistenzende | `mime_type`, `duplicate_status`, `import_status` | Import-Router |
| `document_parse_duration_ms` | Histogram | Dauer Parser + Normalisierung | `mime_type`, `parser_version` | `ImportService.import_document` |
| `document_persist_duration_ms` | Histogram | Dauer Persistenz inkl. Chunks | `mime_type`, `duplicate_status` | `DocumentImportPersistenceService.persist_import` |
| `document_chunk_count` | Histogram | Anzahl Chunks pro importiertem Dokument | `mime_type`, `import_status` | Persistenzresultat |
| `document_import_failures_total` | Counter | Importfehler | `error_code`, `mime_type`, `stage` | Import-Service/Router |
| `document_parser_failures_total` | Counter | Parserfehler | `parser_name`, `mime_type`, `error_code` | Parser/Import-Service |
| `document_duplicates_total` | Counter | erkannte Duplicate-Imports | `workspace_id`, `mime_type` | Persistenz-Service |
| `document_read_duration_ms` | Histogram | Dauer der Read-Endpunkte | `endpoint` | Dokument-Router/Service |
| `document_db_errors_total` | Counter | DB-Fehler | `operation`, `error_code` | DB/Repository/Persistenz |

### Fehlerquote

Definition:

```text
import_failure_rate =
  document_import_failures_total
  / (documents_created_total + document_duplicates_total + document_import_failures_total)
```

Parser Failure Rate:

```text
parser_failure_rate =
  document_parser_failures_total
  / document_import_started_total
```

## Tracing-Konzept

Paket 5 braucht noch keine externe Trace-Plattform. Es soll aber so instrumentiert werden, dass Request-Flows eindeutig nachvollziehbar sind.

### Trace-Kontext

- Jeder HTTP-Request bekommt eine `request_id`.
- Wenn Header `X-Request-ID` vorhanden ist, wird er uebernommen.
- Sonst wird eine UUID erzeugt.
- `request_id` wird in Logs und optional in Response-Header `X-Request-ID` geschrieben.

### Minimaler Trace-Flow

`POST /documents/import`:

```text
HTTP request
  -> documents.import_document
  -> ImportService.import_document
  -> Parser.parse
  -> MarkdownNormalizer.normalize
  -> DocumentImportPersistenceService.persist_import
  -> DB insert/select
  -> response
```

Read-Endpunkte:

```text
HTTP request
  -> documents router
  -> DocumentReadService
  -> DocumentRepository
  -> DB select/projection
  -> response
```

### Span-Namen fuer optionale OpenTelemetry-Anbindung

| Span | Startpunkt |
|---|---|
| `http.POST /documents/import` | FastAPI Middleware |
| `document.import.parse` | `ImportService.import_document` |
| `document.import.persist` | `DocumentImportPersistenceService.persist_import` |
| `document.import.duplicate_lookup` | `_fetch_existing` |
| `document.import.insert_document` | `_insert_document` |
| `document.read.list` | `DocumentReadService.get_documents` |
| `document.read.detail` | `DocumentReadService.get_document_detail` |
| `document.read.versions` | `DocumentReadService.get_versions` |
| `document.read.chunks` | `DocumentReadService.get_chunks` |
| `db.documents.query` | Repository-/Persistenz-DB-Operationen |

## Alerts

Alerts koennen initial als Log-Auswertungsregeln oder periodische Checks umgesetzt werden.

| Alert | Bedingung | Schwere | Aktion |
|---|---|---|---|
| Parser Failure Rate hoch | `parser_failure_rate > 10%` ueber 15 Minuten und mindestens 10 Imports | warning | Parser-Logs pruefen, problematische MIME-Typen identifizieren |
| Parser Failure Rate kritisch | `parser_failure_rate > 25%` ueber 15 Minuten und mindestens 10 Imports | critical | Importpfad stoppen oder Parser-Rollback pruefen |
| Importdauer hoch | p95 `document_import_duration_ms > 10_000` ueber 15 Minuten | warning | Parser/DB/Chunking getrennt pruefen |
| Importdauer kritisch | p95 `document_import_duration_ms > 30_000` ueber 15 Minuten | critical | Importqueue drosseln, DB/Parser pruefen |
| Chunk-Abfrage langsam | p95 `document_read_duration_ms{endpoint=chunks} > 200` ueber 15 Minuten | warning | Query-Plan und Indexe pruefen |
| DB Errors | `document_db_errors_total > 0` ueber 5 Minuten | critical | DB-Verbindung, Migrationen, Constraints pruefen |
| Duplicate-Spike | `document_duplicates_total / document_import_started_total > 50%` ueber 30 Minuten | warning | Client-Verhalten oder Retry-Schleife pruefen |
| OCR-Bedarf hoch | `OCR_REQUIRED` > 20% ueber 1 Tag | info | OCR-Paket priorisieren |

## Konkrete Messpunkte im Code

### `backend/app/main.py`

Empfohlen:

- Middleware `RequestContextMiddleware` einfuehren.
- `X-Request-ID` lesen oder erzeugen.
- Start-/Endzeit des HTTP-Requests messen.
- Response-Header `X-Request-ID` setzen.
- Unbehandelte Exceptions mit `request_id` loggen.

Messpunkte:

- `http_request_started`
- `http_request_completed`
- `http_request_failed`

### `backend/app/api/documents.py`

Empfohlen fuer `import_document()`:

- Timer direkt am Funktionsstart starten.
- `document_import_started` nach MIME-Erkennung und `file.read()`.
- `document_import_failed` vor `OcrRequiredApiError` oder `ParserFailedApiError`.
- `document_import_completed` direkt vor Response.

Empfohlen fuer Read-Endpunkte:

- Timer pro Endpoint.
- `document_read_completed` mit `endpoint`, `row_count`, `duration_ms`.
- fachliche Fehler mit `DOCUMENT_NOT_FOUND`, `DOCUMENT_STATE_CONFLICT`, `INVALID_PAGINATION` loggen.

### `backend/app/services/import_service.py`

Empfohlen:

- Parser-Auswahl messen.
- Parserdauer messen.
- Normalisierungsdauer messen.
- Parserfehler und OCR-Bedarf als strukturierte Events loggen.

Messpunkte:

- `document_parser_started`
- `document_parser_completed`
- `document_parser_failed`
- `document_ocr_required`
- `document_normalization_completed`
- `document_normalization_failed`

### `backend/app/services/documents/import_persistence_service.py`

Empfohlen:

- `persist_import()` komplett messen.
- `_fetch_existing()` separat messen.
- `_insert_document()` separat messen.
- Duplicate-Erkennung loggen:
  - vor Insert gefunden
  - nach Unique-Constraint-Konflikt gefunden
- DB-Fehler ausserhalb `uq_documents_workspace_content_hash` als `document_db_error`.

Messpunkte:

- `document_duplicate_detected`
- `document_persist_started`
- `document_persist_completed`
- `document_db_error`

### `backend/app/services/documents/read_service.py`

Empfohlen:

- Service-Dauer pro Methode messen.
- State Conflicts mit Dokument-ID loggen.

Messpunkte:

- `document_read_service_completed`
- `document_state_conflict`

### `backend/app/repositories/documents.py`

Empfohlen:

- DB Query-Dauer pro Repository-Methode messen.
- Row Counts loggen.
- Keine SQL-Parameter mit Volltext loggen.

Messpunkte:

- `db.documents.list`
- `db.documents.detail`
- `db.documents.versions`
- `db.documents.chunks`

## Minimaler Implementierungsvorschlag

### Neue Module

- `backend/app/core/request_context.py`
  - `ContextVar` fuer `request_id`
  - Helper `get_request_id()`
- `backend/app/core/observability.py`
  - `get_logger(name)`
  - `log_event(event, **fields)`
  - `measure_ms()` Context Manager
  - optionale In-Memory-Counter fuer Tests
- `backend/app/api/middleware.py`
  - Request-ID- und Timing-Middleware

### Beispiel-Log

```json
{
  "timestamp": "2026-05-04T10:30:00Z",
  "level": "INFO",
  "event": "document_import_completed",
  "request_id": "b9f3f2d8-1b4f-4e4d-a723-3b534bfc29d4",
  "workspace_id": "00000000-0000-0000-0000-000000000001",
  "document_id": "document-id",
  "version_id": "version-id",
  "mime_type": "application/pdf",
  "duration_ms": 1834,
  "chunk_count": 12,
  "duplicate_status": "created",
  "import_status": "chunked"
}
```

## Akzeptanzkriterien

- Jeder Import erzeugt genau einen Start- und einen Abschluss- oder Fehler-Log.
- Duplicate-Imports erzeugen `document_duplicate_detected`.
- Parserfehler erzeugen `document_parser_failed` oder `document_ocr_required`.
- Jeder Read-Endpunkt loggt Dauer und Row Count.
- DB-Fehler werden als `document_db_error` sichtbar.
- Keine Logs enthalten Volltext, Upload-Bytes oder Chunk-Inhalte.
- `request_id` ist in allen Logs eines Requests identisch.
- Chunk-Endpoint kann ueber Metrik/Log gegen das `< 200ms`-Gate bewertet werden.
