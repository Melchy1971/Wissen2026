# Chat/RAG API Contract

Stand: 2026-05-04

Dieser Vertrag definiert den minimalen HTTP-Vertrag fuer Chat/RAG oberhalb der bestehenden Retrieval-Basis. Er beschreibt Endpunkte, Request-/Response-Schemas und den Fehlerstandard, ohne Implementierungsdetails wie Prompting, konkrete Modellanbieter oder interne Persistenzlogik festzuschreiben.

## 1. Leitregeln

- Chat/RAG baut auf dem bestehenden Retrieval-Fundament auf.
- Keine Antwort ohne Quellen.
- Jede Quelle muss mindestens `chunk_id` enthalten.
- Der Prompt-Aufbau bleibt deterministisch fuer denselben Eingabestand.
- `retrieval_limit` begrenzt den maximalen Retrieval-Kontext explizit.
- Dieser Vertrag beschreibt die Ziel-API fuer M3c; er ist noch kein Implementierungsnachweis.

## 2. Versionierung

- Contract-Version: `v1`
- Zielpfad fuer Chat/RAG: `/api/v1/chat`

## 3. Allgemeiner Fehlerstandard

Alle Fehler folgen dem bestehenden API-Format:

```json
{
  "error": {
    "code": "LLM_UNAVAILABLE",
    "message": "LLM provider is unavailable",
    "details": {}
  }
}
```

Allgemeine Regeln:

- Fehlercodes sind stabile maschinenlesbare Konstanten.
- `message` ist ein lesbarer Kurztext.
- `details` darf Zusatzinformationen enthalten, aber keine sensitiven Geheimnisse oder kompletten Prompt-Inhalte.

## 4. Endpunkte

### `POST /chat/sessions`

Zweck:

- Eine neue Chat-Sitzung im aktuellen Workspace anlegen.

Request `application/json`:

```json
{
  "workspace_id": "workspace-id",
  "title": "Vertragspruefung"
}
```

Request-Regeln:

- `workspace_id` ist required.
- `title` ist optional; wenn nicht gesetzt, darf serverseitig ein stabiler Default vergeben werden.

Response `201`:

```json
{
  "id": "session-id",
  "workspace_id": "workspace-id",
  "title": "Vertragspruefung",
  "created_at": "2026-05-04T12:00:00Z",
  "updated_at": "2026-05-04T12:00:00Z",
  "message_count": 0
}
```

Fehler:

| Status | Code | Bedeutung |
|---:|---|---|
| `422` | `WORKSPACE_REQUIRED` | `workspace_id` fehlt oder ist leer |
| `503` | `SERVICE_UNAVAILABLE` | Persistenz oder Datenbank nicht verfuegbar |

### `GET /chat/sessions`

Zweck:

- Chat-Sitzungen eines Workspaces listen.

Query Parameter:

| Name | Typ | Required | Default | Regeln |
|---|---:|---:|---:|---|
| `workspace_id` | string | ja | - | nicht leer |
| `limit` | integer | nein | `20` | `1..100` |
| `offset` | integer | nein | `0` | `>= 0` |

Sortierung:

- `updated_at DESC`

Response `200`:

```json
[
  {
    "id": "session-id",
    "workspace_id": "workspace-id",
    "title": "Vertragspruefung",
    "created_at": "2026-05-04T12:00:00Z",
    "updated_at": "2026-05-04T12:10:00Z",
    "message_count": 2,
    "last_user_question_preview": "Welche Kuendigungsfrist gilt?"
  }
]
```

Fehler:

| Status | Code | Bedeutung |
|---:|---|---|
| `422` | `WORKSPACE_REQUIRED` | `workspace_id` fehlt oder ist leer |
| `422` | `INVALID_PAGINATION` | `limit` oder `offset` sind ungueltig |
| `503` | `SERVICE_UNAVAILABLE` | Persistenz oder Datenbank nicht verfuegbar |

### `GET /chat/sessions/{id}`

Zweck:

- Eine Chat-Sitzung mit bisherigen Nachrichten lesen.

Path Parameter:

| Name | Typ | Required |
|---|---:|---:|
| `id` | string | ja |

Response `200`:

```json
{
  "id": "session-id",
  "workspace_id": "workspace-id",
  "title": "Vertragspruefung",
  "created_at": "2026-05-04T12:00:00Z",
  "updated_at": "2026-05-04T12:10:00Z",
  "messages": [
    {
      "id": "msg-1",
      "role": "user",
      "content": "Welche Kuendigungsfrist gilt?",
      "created_at": "2026-05-04T12:05:00Z"
    },
    {
      "id": "msg-2",
      "role": "assistant",
      "content": "Nach der Probezeit gilt eine Kuendigungsfrist von vier Wochen.",
      "created_at": "2026-05-04T12:05:02Z",
      "citations": [
        {
          "chunk_id": "chunk-42",
          "document_id": "doc-1",
          "document_title": "Arbeitsvertrag Hybridmodell",
          "source_anchor": {
            "type": "text",
            "page": null,
            "paragraph": null,
            "char_start": 120,
            "char_end": 240
          },
          "quote_preview": "Nach der Probezeit gilt eine Kuendigungsfrist von vier Wochen ..."
        }
      ],
      "confidence": {
        "sufficient_context": true,
        "retrieval_score_max": 0.91,
        "retrieval_score_avg": 0.78
      }
    }
  ]
}
```

Fehler:

| Status | Code | Bedeutung |
|---:|---|---|
| `404` | `CHAT_SESSION_NOT_FOUND` | Sitzung existiert nicht |
| `503` | `SERVICE_UNAVAILABLE` | Persistenz oder Datenbank nicht verfuegbar |

### `POST /chat/sessions/{id}/messages`

Zweck:

- Eine Benutzerfrage an eine bestehende Chat-Sitzung senden und eine quellengebundene RAG-Antwort erzeugen.

Request `application/json`:

```json
{
  "workspace_id": "workspace-id",
  "question": "Welche Kuendigungsfrist gilt?",
  "retrieval_limit": 8
}
```

Request-Regeln:

- `workspace_id` ist required.
- `question` ist required und darf nicht leer sein.
- `retrieval_limit` ist optional, Default `8`.
- Empfohlene Range fuer `retrieval_limit`: `1..20`.

Response `201`:

```json
{
  "session_id": "session-id",
  "user_message": {
    "id": "msg-user-1",
    "role": "user",
    "content": "Welche Kuendigungsfrist gilt?",
    "created_at": "2026-05-04T12:05:00Z"
  },
  "assistant_message": {
    "id": "msg-assistant-1",
    "role": "assistant",
    "answer": "Nach der Probezeit gilt eine Kuendigungsfrist von vier Wochen zum Fuenfzehnten oder zum Monatsende.",
    "created_at": "2026-05-04T12:05:02Z",
    "citations": [
      {
        "chunk_id": "chunk-42",
        "document_id": "doc-1",
        "document_title": "Arbeitsvertrag Hybridmodell",
        "source_anchor": {
          "type": "text",
          "page": null,
          "paragraph": null,
          "char_start": 120,
          "char_end": 240
        },
        "quote_preview": "Nach der Probezeit gilt eine Kuendigungsfrist von vier Wochen ..."
      }
    ],
    "confidence": {
      "sufficient_context": true,
      "retrieval_score_max": 0.91,
      "retrieval_score_avg": 0.78
    }
  }
}
```

Response-Regeln:

- `answer` darf nur ausgeliefert werden, wenn mindestens eine gueltige Citation vorhanden ist.
- Jede Citation muss `chunk_id`, `document_id`, `document_title`, `source_anchor` und `quote_preview` enthalten.
- `confidence.sufficient_context` ist ein technisches Signal, kein Wahrheitsbeweis.
- `retrieval_score_max` und `retrieval_score_avg` sind technische Retrieval-Metriken, keine semantische Garantie.

Fehler:

| Status | Code | Bedeutung |
|---:|---|---|
| `404` | `CHAT_SESSION_NOT_FOUND` | Sitzung existiert nicht |
| `422` | `WORKSPACE_REQUIRED` | `workspace_id` fehlt oder ist leer |
| `422` | `QUERY_REQUIRED` | `question` fehlt oder ist leer |
| `422` | `INVALID_PAGINATION` | `retrieval_limit` verletzt die erlaubte Range |
| `422` | `INSUFFICIENT_CONTEXT` | keine belastbare Antwort mit gueltigen Quellen moeglich |
| `503` | `RETRIEVAL_FAILED` | Retrieval-Pfad nicht verfuegbar oder fehlgeschlagen |
| `503` | `LLM_UNAVAILABLE` | LLM-Provider oder Modellaufruf nicht verfuegbar |
| `503` | `SERVICE_UNAVAILABLE` | Persistenz oder anderer interner Dienst nicht verfuegbar |

## 5. Schemas

### ChatSessionSummary

```json
{
  "id": "session-id",
  "workspace_id": "workspace-id",
  "title": "Vertragspruefung",
  "created_at": "2026-05-04T12:00:00Z",
  "updated_at": "2026-05-04T12:10:00Z",
  "message_count": 2,
  "last_user_question_preview": "Welche Kuendigungsfrist gilt?"
}
```

### ChatSessionDetail

```json
{
  "id": "session-id",
  "workspace_id": "workspace-id",
  "title": "Vertragspruefung",
  "created_at": "2026-05-04T12:00:00Z",
  "updated_at": "2026-05-04T12:10:00Z",
  "messages": []
}
```

### ChatMessageUser

```json
{
  "id": "msg-user-1",
  "role": "user",
  "content": "Welche Kuendigungsfrist gilt?",
  "created_at": "2026-05-04T12:05:00Z"
}
```

### ChatMessageAssistant

```json
{
  "id": "msg-assistant-1",
  "role": "assistant",
  "answer": "...",
  "created_at": "2026-05-04T12:05:02Z",
  "citations": [],
  "confidence": {
    "sufficient_context": true,
    "retrieval_score_max": 0.91,
    "retrieval_score_avg": 0.78
  }
}
```

### Citation

```json
{
  "chunk_id": "chunk-42",
  "document_id": "doc-1",
  "document_title": "Arbeitsvertrag Hybridmodell",
  "source_anchor": {
    "type": "text",
    "page": null,
    "paragraph": null,
    "char_start": 120,
    "char_end": 240
  },
  "quote_preview": "Nach der Probezeit gilt eine Kuendigungsfrist ..."
}
```

Schema-Regeln:

- `chunk_id` ist required.
- `document_id` ist required.
- `document_title` ist required.
- `source_anchor` ist required.
- `quote_preview` ist required und soll ein kurzer, zitierbarer Textauszug sein.

### Confidence

```json
{
  "sufficient_context": true,
  "retrieval_score_max": 0.91,
  "retrieval_score_avg": 0.78
}
```

Schema-Regeln:

- `sufficient_context` ist required.
- `retrieval_score_max` ist optional nullable, wenn Retrieval nicht erfolgreich stattfand.
- `retrieval_score_avg` ist optional nullable, wenn Retrieval nicht erfolgreich stattfand.

## 6. Fehlercodes

### `CHAT_SESSION_NOT_FOUND`

- Status: `404`
- Bedeutung: Die angefragte Chat-Sitzung existiert nicht.

### `QUERY_REQUIRED`

- Status: `422`
- Bedeutung: `question` fehlt oder ist leer.

### `INSUFFICIENT_CONTEXT`

- Status: `422`
- Bedeutung: Es konnte keine belastbare Antwort mit gueltigen Quellen gebaut werden.

### `LLM_UNAVAILABLE`

- Status: `503`
- Bedeutung: Das Modell oder der Provider ist aktuell nicht verfuegbar.

### `RETRIEVAL_FAILED`

- Status: `503`
- Bedeutung: Retrieval oder Kontextaufbau ist technisch fehlgeschlagen.

## 7. Entscheidungsregeln fuer Chat/RAG

- Eine Assistant-Response gilt nur dann als erfolgreich, wenn `citations.length >= 1`.
- Jede Citation muss auf einen tatsaechlich verwendeten Chunk referenzieren.
- Eine Antwort ohne gueltige Quellen wird nicht als `200` oder `201` ausgeliefert.
- `INSUFFICIENT_CONTEXT` ist der bevorzugte fachliche Fehler, wenn die Pipeline zwar laeuft, aber keine belastbare quellengebundene Antwort moeglich ist.
- `RETRIEVAL_FAILED` und `LLM_UNAVAILABLE` sind technische Fehler und duerfen nicht als leerer inhaltlicher Erfolg maskiert werden.