# V1 Dokument-API Contract

Stand: 2026-05-04

Dieser Vertrag ist die stabile Grundlage fuer M3 Suche/Retrieval. M3 darf nur auf die hier beschriebenen Felder, Statuscodes und Semantiken aufsetzen. Implementierungsdetails wie Tabellenname, ORM-Modell, Repository-Struktur oder Parser-Interna sind kein API-Vertrag.

## Versionierung

- Contract-Version: `v1`
- Aktuell implementierter Base Path: `/documents`
- Ziel fuer explizite Versionierung: `/api/v1/documents`

Solange `/api/v1/documents` nicht als kompatibler Alias implementiert ist, ist eine reine Verschiebung von `/documents` nach `/api/v1/documents` ein Breaking Change. M3 muss entweder den aktuell implementierten Pfad `/documents` verwenden oder erst nach Einfuehrung eines Alias auf `/api/v1/documents` wechseln.

## Allgemeine Regeln

- Alle Responses sind JSON, ausser `POST /documents/import`, das `multipart/form-data` annimmt.
- Zeitstempel werden als ISO-8601-Strings geliefert.
- IDs sind stabile String-Identifier.
- Listen werden als JSON-Arrays geliefert, nicht als Envelope-Objekte.
- Dokument-Read-Endpunkte liefern keinen Volltext ausser gekuerzten `text_preview`-Feldern im Chunk-Endpunkt.
- API-Fehler folgen dem einheitlichen Format:

```json
{
  "error": {
    "code": "DOCUMENT_NOT_FOUND",
    "message": "Document not found",
    "details": {}
  }
}
```

## Endpoint Definitionen

### `GET /documents`

Liefert Dokumente eines Workspaces.

Query Parameter:

| Name | Typ | Required | Default | Regeln |
|---|---:|---:|---:|---|
| `workspace_id` | string | ja | - | nicht leer |
| `limit` | integer | nein | `20` | `1..100` |
| `offset` | integer | nein | `0` | `>= 0` |

Sortierung:

- `created_at DESC`

Response `200`:

```json
[
  {
    "id": "document-id",
    "title": "Document title",
    "mime_type": "text/plain",
    "created_at": "2026-05-01T10:00:00",
    "updated_at": "2026-05-01T10:00:00",
    "latest_version_id": "version-id",
    "import_status": "chunked",
    "version_count": 1,
    "chunk_count": 4
  }
]
```

Schema `DocumentListItem`:

| Feld | Typ | Nullable | Contract Critical |
|---|---|---:|---:|
| `id` | string | nein | ja |
| `title` | string | nein | ja |
| `mime_type` | string | ja | ja |
| `created_at` | datetime string | nein | ja |
| `updated_at` | datetime string | nein | ja |
| `latest_version_id` | string | ja | ja |
| `import_status` | `ImportStatus` | nein | ja |
| `version_count` | integer | nein | ja |
| `chunk_count` | integer | nein | ja |

Fehler:

| Status | Code | Bedeutung |
|---:|---|---|
| `422` | `WORKSPACE_REQUIRED` | `workspace_id` fehlt oder ist leer |
| `422` | `INVALID_PAGINATION` | `limit` oder `offset` ist ausserhalb der erlaubten Grenzen |
| `503` | `SERVICE_UNAVAILABLE` | DB nicht konfiguriert oder nicht verfuegbar |

### `GET /documents/{document_id}`

Liefert Dokument-Metadaten, die aktuelle Version, Parser-Metadaten, Importstatus und Chunk-Summary.

Path Parameter:

| Name | Typ | Required |
|---|---:|---:|
| `document_id` | string | ja |

Response `200`:

```json
{
  "id": "document-id",
  "workspace_id": "workspace-id",
  "owner_user_id": "user-id",
  "title": "Document title",
  "source_type": "upload",
  "mime_type": "text/plain",
  "content_hash": "sha256-source-hash",
  "created_at": "2026-05-01T10:00:00",
  "updated_at": "2026-05-01T10:00:00",
  "latest_version_id": "version-id",
  "latest_version": {
    "id": "version-id",
    "version_number": 1,
    "created_at": "2026-05-01T10:00:00",
    "content_hash": "sha256-normalized-markdown-hash"
  },
  "parser_metadata": {
    "parser_version": "text-parser-v1",
    "ocr_used": false,
    "ki_provider": null,
    "ki_model": null,
    "metadata": {
      "mime_type": "text/plain"
    }
  },
  "import_status": "chunked",
  "chunk_summary": {
    "chunk_count": 4,
    "total_chars": 1200,
    "first_chunk_id": "chunk-1",
    "last_chunk_id": "chunk-4"
  }
}
```

Schema `DocumentDetail`:

| Feld | Typ | Nullable | Contract Critical |
|---|---|---:|---:|
| `id` | string | nein | ja |
| `workspace_id` | string | nein | ja |
| `owner_user_id` | string | nein | nein |
| `title` | string | nein | ja |
| `source_type` | string | nein | ja |
| `mime_type` | string | ja | ja |
| `content_hash` | string | nein | ja |
| `created_at` | datetime string | nein | ja |
| `updated_at` | datetime string | nein | ja |
| `latest_version_id` | string | ja | ja |
| `latest_version` | `DocumentVersionSummary` | ja | ja |
| `parser_metadata` | `DocumentParserMetadata` | ja | ja |
| `import_status` | `ImportStatus` | nein | ja |
| `chunk_summary` | `DocumentChunkSummary` | nein | ja |

Schema `DocumentParserMetadata`:

| Feld | Typ | Nullable | Contract Critical |
|---|---|---:|---:|
| `parser_version` | string | nein | ja |
| `ocr_used` | boolean | nein | ja |
| `ki_provider` | string | ja | nein |
| `ki_model` | string | ja | nein |
| `metadata` | object | nein | nein |

Schema `DocumentChunkSummary`:

| Feld | Typ | Nullable | Contract Critical |
|---|---|---:|---:|
| `chunk_count` | integer | nein | ja |
| `total_chars` | integer | nein | ja |
| `first_chunk_id` | string | ja | ja |
| `last_chunk_id` | string | ja | ja |

Fehler:

| Status | Code | Bedeutung |
|---:|---|---|
| `404` | `DOCUMENT_NOT_FOUND` | Dokument existiert nicht |
| `409` | `DOCUMENT_STATE_CONFLICT` | Dokumentzustand ist inkonsistent |
| `503` | `SERVICE_UNAVAILABLE` | DB nicht konfiguriert oder nicht verfuegbar |

### `GET /documents/{document_id}/versions`

Liefert alle Versionen eines Dokuments.

Sortierung:

- `created_at DESC`
- bei Gleichstand `version_number DESC`

Response `200`:

```json
[
  {
    "id": "version-id",
    "version_number": 1,
    "created_at": "2026-05-01T10:00:00",
    "content_hash": "sha256-normalized-markdown-hash"
  }
]
```

Schema `DocumentVersionSummary`:

| Feld | Typ | Nullable | Contract Critical |
|---|---|---:|---:|
| `id` | string | nein | ja |
| `version_number` | integer | nein | ja |
| `created_at` | datetime string | nein | ja |
| `content_hash` | string | nein | ja |

Fehler:

| Status | Code | Bedeutung |
|---:|---|---|
| `404` | `DOCUMENT_NOT_FOUND` | Dokument existiert nicht |
| `503` | `SERVICE_UNAVAILABLE` | DB nicht konfiguriert oder nicht verfuegbar |

### `GET /documents/{document_id}/chunks`

Liefert Chunks der `latest_version`.

Query Parameter:

| Name | Typ | Required | Default | Regeln |
|---|---:|---:|---:|---|
| `limit` | integer | nein | alle | `1..500` |

Sortierung:

- `position ASC`

Performance-Vertrag:

- Es werden nur Chunks der `latest_version` geliefert.
- Die Query nutzt Projektion statt Full ORM Object.
- `text_preview` ist serverseitig erzeugt und maximal 200 Zeichen lang.
- Der API-Vertrag liefert keinen Volltext-Chunk.

Response `200`:

```json
[
  {
    "chunk_id": "chunk-id",
    "position": 0,
    "text_preview": "first 200 characters",
    "source_anchor": {
      "type": "text",
      "page": null,
      "paragraph": null,
      "char_start": 0,
      "char_end": 200
    }
  }
]
```

Schema `DocumentChunkPreview`:

| Feld | Typ | Nullable | Contract Critical |
|---|---|---:|---:|
| `chunk_id` | string | nein | ja |
| `position` | integer | nein | ja |
| `text_preview` | string | nein | ja |
| `source_anchor` | `DocumentChunkSourceAnchor` | nein | ja |

Schema `DocumentChunkSourceAnchor`:

| Feld | Typ | Nullable | Contract Critical |
|---|---|---:|---:|
| `type` | `"text"`, `"pdf_page"`, `"docx_paragraph"` oder `"legacy_unknown"` | nein | ja |
| `page` | integer | ja | ja |
| `paragraph` | integer | ja | ja |
| `char_start` | integer | ja | ja |
| `char_end` | integer | ja | ja |

Fehler:

| Status | Code | Bedeutung |
|---:|---|---|
| `404` | `DOCUMENT_NOT_FOUND` | Dokument existiert nicht |
| `422` | `INVALID_PAGINATION` | `limit` ist ausserhalb der erlaubten Grenzen |
| `503` | `SERVICE_UNAVAILABLE` | DB nicht konfiguriert oder nicht verfuegbar |

### `POST /documents/import`

Importiert ein Dokument in den Default-Workspace und fuer den Default-User aus der Konfiguration.

Request:

- Content-Type: `multipart/form-data`
- Feld: `file`

Unterstuetzte Dateitypen:

- `.txt`
- `.md`
- `.docx`
- `.doc`
- `.pdf`

Response `200`:

```json
{
  "document_id": "document-id",
  "version_id": "version-id",
  "title": "Document title",
  "chunk_count": 1,
  "duplicate_status": "created",
  "import_status": "chunked"
}
```

Schema `ImportDocumentResponse`:

| Feld | Typ | Nullable | Contract Critical |
|---|---|---:|---:|
| `document_id` | string | nein | ja |
| `version_id` | string | ja | ja |
| `title` | string | nein | ja |
| `chunk_count` | integer | nein | ja |
| `duplicate_status` | `"created"` oder `"duplicate_existing"` | nein | ja |
| `import_status` | `ImportStatus` | nein | ja |

Fehler:

| Status | Code | Bedeutung |
|---:|---|---|
| `415` | `UNSUPPORTED_FILE_TYPE` | Dateityp nicht unterstuetzt |
| `422` | `OCR_REQUIRED` | PDF enthaelt keinen extrahierbaren Text und OCR ist nicht im Scope |
| `422` | `PARSER_FAILED` | Parser, Normalisierung oder Chunking fehlgeschlagen |
| `503` | `SERVICE_UNAVAILABLE` | DB nicht konfiguriert oder nicht verfuegbar |

## Gemeinsame Schemas

### `ImportStatus`

Erlaubte Werte:

- `pending`
- `parsing`
- `parsed`
- `chunked`
- `failed`
- `duplicate`

### `ApiErrorResponse`

```json
{
  "error": {
    "code": "PARSER_FAILED",
    "message": "Document parser failed",
    "details": {
      "filename": "scan.pdf"
    }
  }
}
```

Definierte Paket-5-Fehlercodes:

- `DOCUMENT_NOT_FOUND`
- `WORKSPACE_REQUIRED`
- `INVALID_PAGINATION`
- `DOCUMENT_STATE_CONFLICT`
- `DUPLICATE_DOCUMENT`
- `UNSUPPORTED_FILE_TYPE`
- `OCR_REQUIRED`
- `PARSER_FAILED`
- `SERVICE_UNAVAILABLE`

`DUPLICATE_DOCUMENT` ist als Fehlercode definiert. Der regulaere Importpfad loest Duplicate-Konflikte aber deterministisch auf und liefert `duplicate_status = duplicate_existing` statt hart fehlzuschlagen.

## Was darf sich NICHT mehr aendern?

Ohne neue API-Version oder kompatiblen Migrationspfad duerfen sich nicht aendern:

- Endpoint-Pfade und HTTP-Methoden.
- Required Query- und Path-Parameter.
- Feldnamen in Request- und Response-Schemas.
- Typen der contract-critical Felder.
- Nullable-Status der contract-critical Felder.
- Semantik von `latest_version_id`: zeigt auf die aktuelle Version.
- Semantik von `/chunks`: liefert Chunks der aktuellen Version, nicht aller Versionen.
- Sortierung von `/documents`, `/versions` und `/chunks`.
- Bedeutung von `import_status`.
- Bedeutung von `duplicate_status`.
- Fehlerformat `{"error": {"code": "...", "message": "...", "details": {...}}}`.
- 404-Code `DOCUMENT_NOT_FOUND` fuer fehlende Dokumente.

## Contract-Critical Felder

Fuer M3 Suche/Retrieval sind besonders kritisch:

- Dokumentidentitaet: `id`, `document_id`
- Workspace-Grenze: `workspace_id`
- Versionierung: `latest_version_id`, `version_id`, `version_number`
- Deduplizierung/Nachvollziehbarkeit: `content_hash`
- Importzustand: `import_status`
- Chunk-Zusammenfassung: `chunk_count`, `total_chars`, `first_chunk_id`, `last_chunk_id`
- Chunk-Referenz: `chunk_id`, `position`, `source_anchor`
- Quellenaufloesung: `source_anchor.type`, `source_anchor.page`, `source_anchor.paragraph`, `source_anchor.char_start`, `source_anchor.char_end`
- User-Anzeige und Debugging: `title`, `created_at`, `updated_at`, `mime_type`
- Importverhalten: `duplicate_status`

## Breaking Change Regeln

Ein Breaking Change ist jede Aenderung, die bestehende M3-Clients ohne Codeaenderung brechen kann. Dazu gehoeren:

- Entfernen oder Umbenennen eines Feldes.
- Aendern eines Feldtyps.
- Aendern von nullable zu non-nullable oder umgekehrt bei contract-critical Feldern.
- Aendern der Sortierung.
- Aendern der Bedeutung von IDs, Hashes, Versionen oder Importstatus.
- Aendern von Fehlercodes fuer dokumentierte Fehlerfaelle.
- Verschieben von `/documents` nach `/api/v1/documents`, solange kein kompatibler Alias existiert.

Nicht-breaking sind:

- Neue optionale Felder in Responses.
- Neue Endpoints.
- Neue optionale Query-Parameter mit identischem Default-Verhalten.
- Zusaetzliche Fehlerdetails in `details`, sofern Code, Statuscode und Grundsemantik stabil bleiben.

Breaking Changes muessen:

1. in einer neuen API-Version landen, z.B. `/api/v2`,
2. mit Migrationshinweisen dokumentiert werden,
3. mindestens eine Uebergangsphase mit parallelem v1/v2-Betrieb erhalten,
4. durch Contract-Tests abgesichert werden.

## Contract Tests

Mindestens folgende Tests muessen fuer v1 dauerhaft gruen bleiben:

- `GET /documents` liefert sortierte Liste mit stabilen Feldern.
- `GET /documents/{document_id}` liefert Metadaten, `latest_version`, Parser-Metadaten, Importstatus und Chunk-Summary.
- `GET /documents/{document_id}/versions` liefert Versionen in absteigender Chronologie.
- `GET /documents/{document_id}/chunks` liefert nur Chunks der aktuellen Version, sortiert nach `position ASC`.
- Duplicate Import liefert bei Konflikt kein Hard-Fail, sondern `duplicate_existing`.
- Paket-5-Fehler verwenden das einheitliche Error-Envelope.
