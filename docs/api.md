# API fuer M3a GUI, M3b Retrieval-UI und M3c Chat/RAG

Stand: 2026-05-05

## Zweck

Dieses Dokument beschreibt die API-Abhaengigkeit der aktuellen GUI auf hoher Ebene und finalisiert den stabilen Vertrag fuer M3b Search sowie M3c Chat/RAG. Verbindlicher Detailvertrag fuer die Dokument-Read-Pfade bleibt `docs/api/v1-document-api-contract.md`. Der Retrieval-Vertrag fuer M3b ist zusaetzlich in `docs/retrieval.md` beschrieben.

## Aktuell implementierte Endpunkte

M3a Dokument-GUI:

- `GET /documents`
- `GET /documents/{document_id}`
- `GET /documents/{document_id}/versions`
- `GET /documents/{document_id}/chunks`

M3b Retrieval:

- `GET /api/v1/search/chunks`

M3c Chat:

- `POST /api/v1/chat/sessions`
- `GET /api/v1/chat/sessions`
- `GET /api/v1/chat/sessions/{session_id}`
- `POST /api/v1/chat/sessions/{session_id}/messages`

## M3b Search Contract

### `GET /api/v1/search/chunks`

Sucht in Chunks ueber PostgreSQL Full Text Search.

Query Parameter:

| Name | Typ | Required | Default | Limit / Regel |
|---|---|---:|---:|---|
| `workspace_id` | string | ja | - | `min_length=1` |
| `q` | string | ja | - | `min_length=1`, wird im Service getrimmt |
| `limit` | integer | nein | `20` | `1..100` |
| `offset` | integer | nein | `0` | `>= 0` |

Request-Beispiel:

```text
GET /api/v1/search/chunks?workspace_id=e1000000-0000-0000-0000-000000000001&q=rankingterm%20orderterm&limit=20&offset=0
```

Response `200`:

```json
[
  {
    "document_id": "document-id",
    "document_title": "Document title",
    "document_created_at": "2026-05-01T10:00:00Z",
    "document_version_id": "version-id",
    "version_number": 1,
    "chunk_id": "chunk-id",
    "position": 0,
    "text_preview": "First 200 characters of chunk content",
    "source_anchor": {
      "type": "text",
      "page": null,
      "paragraph": null,
      "char_start": 0,
      "char_end": 200
    },
    "rank": 0.123,
    "filters": {}
  }
]
```

Response Schema `SearchChunkResult`:

| Feld | Typ | Nullable | Hinweis |
|---|---|---:|---|
| `document_id` | string | nein | Dokument-ID |
| `document_title` | string | nein | Dokumenttitel |
| `document_created_at` | datetime string | nein | fuer Sortier-Tie-Breaker relevant |
| `document_version_id` | string | nein | aktuelle Version des Dokuments |
| `version_number` | integer | nein | Versionsnummer |
| `chunk_id` | string | nein | stabile Chunk-ID |
| `position` | integer | nein | entspricht `chunk_index` |
| `text_preview` | string | nein | serverseitig auf 200 Zeichen projiziert |
| `source_anchor` | `DocumentChunkSourceAnchor` | nein | normalisiertes Quellenanker-Schema |
| `rank` | float | nein | PostgreSQL `ts_rank` |
| `filters` | object | nein | aktuell immer `{}`, kein Query-Filtervertrag |

Schema `DocumentChunkSourceAnchor`:

| Feld | Typ | Nullable |
|---|---|---:|
| `type` | `"text"`, `"pdf_page"`, `"docx_paragraph"` oder `"legacy_unknown"` | nein |
| `page` | integer | ja |
| `paragraph` | integer | ja |
| `char_start` | integer | ja |
| `char_end` | integer | ja |

## Search-Verhalten

PostgreSQL-Abhaengigkeit:

- Search funktioniert nur mit PostgreSQL.
- Der Repository-Code verlangt PostgreSQL, weil `search_vector`, `plainto_tsquery`, `ts_rank` und GIN-Index genutzt werden.
- SQLite ist fuer diesen Endpoint kein unterstuetztes Search-Backend.
- Bei SQLite oder anderem Nicht-PostgreSQL-Dialect liefert der Endpoint `503 SERVICE_UNAVAILABLE`.

Index-/FTS-Verhalten:

- `document_chunks.search_vector` ist eine PostgreSQL `tsvector` Generated Column.
- Der GIN-Index `ix_document_chunks_search_vector` wird fuer Full Text Search vorbereitet.
- Query-Ausdruck: `plainto_tsquery('simple', q)`.
- Ranking: `ts_rank(document_chunks.search_vector, ts_query)`.

Filterverhalten:

- Es werden nur Chunks aus dem angefragten `workspace_id` geliefert.
- Es werden nur Chunks der aktuellen Dokumentversion geliefert.
- Dokumente mit `import_status in ('parsed', 'chunked')` sind suchbar.
- `pending`, `failed`, `duplicate` und andere Statuswerte werden nicht als Suchtreffer geliefert.

Sortierlogik:

1. `rank DESC`
2. `document.created_at DESC`
3. `chunk_index ASC`
4. `chunk_id ASC`

Diese Reihenfolge ist Teil des stabilen M3b-Vertrags.

## Fehlercodes

Alle Fehler folgen dem Standardformat:

```json
{
  "error": {
    "code": "INVALID_QUERY",
    "message": "Invalid search query",
    "details": {}
  }
}
```

| HTTP Status | Code | Ursache |
|---:|---|---|
| `422` | `WORKSPACE_REQUIRED` | `workspace_id` fehlt oder ist leer |
| `422` | `INVALID_QUERY` | `q` fehlt oder ist leer |
| `422` | `INVALID_PAGINATION` | `limit` oder `offset` ist ausserhalb der Grenzen |
| `503` | `SERVICE_UNAVAILABLE` | Search-Backend ist nicht verfuegbar oder nicht PostgreSQL |
| `500` | `INTERNAL_ERROR` | unerwarteter interner Fehler oder fehlende DB-Konfiguration ausserhalb des Search-Backend-Checks |

## M3c Chat Contract

### `POST /api/v1/chat/sessions`

Erstellt eine Chat-Session.

Request:

```json
{
  "workspace_id": "workspace-1",
  "title": "Arbeitsvertrag"
}
```

Response `201` `ChatSessionSummary`:

```json
{
  "id": "session-id",
  "workspace_id": "workspace-1",
  "title": "Arbeitsvertrag",
  "created_at": "2026-05-01T12:00:00Z",
  "updated_at": "2026-05-01T12:00:00Z"
}
```

### `GET /api/v1/chat/sessions`

Listet Sessions eines Workspaces.

Query Parameter:

| Name | Typ | Required | Default | Limit / Regel |
|---|---|---:|---:|---|
| `workspace_id` | string | ja | - | `min_length=1` |
| `limit` | integer | nein | `20` | `1..100` |
| `offset` | integer | nein | `0` | `>= 0` |

Response `200`:

```json
[
  {
    "id": "session-id",
    "workspace_id": "workspace-1",
    "title": "Arbeitsvertrag",
    "created_at": "2026-05-01T12:00:00Z",
    "updated_at": "2026-05-01T12:00:00Z"
  }
]
```

### `GET /api/v1/chat/sessions/{session_id}`

Liefert Session-Metadaten mit Messages.

Response `200` `ChatSessionDetail`:

```json
{
  "id": "session-id",
  "workspace_id": "workspace-1",
  "title": "Arbeitsvertrag",
  "created_at": "2026-05-01T12:00:00Z",
  "updated_at": "2026-05-01T12:10:00Z",
  "messages": [
    {
      "id": "message-id",
      "session_id": "session-id",
      "role": "assistant",
      "content": "Antwort mit Quelle chunk-1.",
      "basis_type": "knowledge_base",
      "created_at": "2026-05-01T12:10:00Z",
      "citations": [
        {
          "chunk_id": "chunk-1",
          "document_id": "document-1",
          "source_anchor": {
            "type": "text",
            "page": null,
            "paragraph": 4,
            "char_start": 10,
            "char_end": 130
          },
          "quote_preview": null
        }
      ],
      "confidence": null
    }
  ]
}
```

### `POST /api/v1/chat/sessions/{session_id}/messages`

Fuehrt den M3c-RAG-Flow aus. Der Endpoint speichert zuerst die User-Frage, fuehrt Retrieval und RAG-Orchestrierung aus und speichert bei ausreichendem Kontext eine Assistant-Antwort mit Citations.

Request:

```json
{
  "workspace_id": "workspace-1",
  "question": "Welche Kuendigungsfrist gilt nach der Probezeit?",
  "retrieval_limit": 8
}
```

Felder:

| Feld | Typ | Required | Default | Limit / Regel |
|---|---|---:|---:|---|
| `workspace_id` | string | ja | - | `min_length=1` |
| `question` | string | ja | - | `min_length=1` |
| `retrieval_limit` | integer | nein | `8` | `1..100` |

Response `201` `ChatMessageResponse` fuer die Assistant-Antwort:

```json
{
  "id": "assistant-message-id",
  "session_id": "session-id",
  "role": "assistant",
  "content": "Die Frist betraegt vier Wochen zum Monatsende. Quelle: chunk-1",
  "basis_type": "knowledge_base",
  "created_at": "2026-05-01T12:10:00Z",
  "citations": [
    {
      "chunk_id": "chunk-1",
      "document_id": "document-1",
      "source_anchor": {
        "type": "text",
        "page": null,
        "paragraph": 4,
        "char_start": 10,
        "char_end": 130
      },
      "quote_preview": "Nach der Probezeit gilt eine Kuendigungsfrist von vier Wochen zum Monatsende."
    }
  ],
  "confidence": {
    "sufficient_context": true,
    "retrieval_score_max": 0.92,
    "retrieval_score_avg": 0.92
  }
}
```

Wichtig:

- Der Response enthaelt nicht die User-Message. Die User-Frage wird serverseitig persistiert; die GUI ergaenzt sie lokal im Verlauf und kann die Session danach erneut laden.
- Eine erfolgreiche Assistant-Antwort muss mindestens eine Citation mit `chunk_id` enthalten.
- Bei unzureichendem Kontext wird keine freie Assistant-Antwort erzeugt.

## M3c Fehlercodes

Alle Chat/RAG-Fehler verwenden das gleiche Standardformat:

```json
{
  "error": {
    "code": "INSUFFICIENT_CONTEXT",
    "message": "no_retrieval_hits",
    "details": {
      "session_id": "session-id"
    }
  }
}
```

| HTTP Status | Code | Ursache |
|---:|---|---|
| `404` | `CHAT_SESSION_NOT_FOUND` | Session existiert nicht |
| `422` | `WORKSPACE_REQUIRED` | `workspace_id` fehlt oder ist leer |
| `422` | `CHAT_MESSAGE_INVALID` | `question` oder `retrieval_limit` ungueltig |
| `422` | `INSUFFICIENT_CONTEXT` | Retrieval-/Kontextlage reicht nicht fuer belegte Antwort |
| `500` | `CHAT_PERSISTENCE_FAILED` | Speichern von Session, Message oder Citation fehlgeschlagen |
| `502` | `RETRIEVAL_FAILED` | Retrieval-Service fehlgeschlagen |
| `503` | `LLM_UNAVAILABLE` | LLM Provider nicht verfuegbar oder leere Antwort |

## Nicht-Scope fuer M3b Search

- kein Chat
- keine LLM-Antwort
- keine Embeddings
- keine semantische Suche
- kein Re-Ranking
- keine Query-Filter ausser `workspace_id`, `q`, `limit`, `offset`
- keine Schreiboperationen

## Von der GUI verwendete Vertragsmerkmale

- Dokumentliste mit `title`, `mime_type`, `created_at`, `updated_at`, `latest_version_id`, `import_status`, `version_count`, `chunk_count`
- Dokumentdetail mit Stammdaten, `latest_version`, `parser_metadata`, `import_status`, `chunk_summary`
- Versionen mit `id`, `version_number`, `created_at`, `content_hash`
- Chunks mit `chunk_id`, `position`, `text_preview`, `source_anchor`
- Suchtreffer mit `document_id`, `document_title`, `document_created_at`, `document_version_id`, `version_number`, `chunk_id`, `position`, `text_preview`, `source_anchor`, `rank`, `filters`
- Chat-Sessions mit `id`, `workspace_id`, `title`, `created_at`, `updated_at`
- Chat-Assistant-Antworten mit `content`, `citations`, `confidence`
- Standardisiertes Fehlerformat `error.code`, `error.message`, `error.details`

## Offene Punkte

- Der Alias `/api/v1/documents` ist weiter nicht implementiert.
- M3b Search hat PostgreSQL-Integrationstests, wird aber ohne `TEST_DATABASE_URL` geskippt.
- M3c nutzt aktuell einen austauschbaren LLM-Provider-Vertrag; ein produktiver LLM-Provider ist M4-Scope.
- Streaming, Agenten, Tool Use, Embeddings und Dokumentmutation sind nicht Teil von M3c.
