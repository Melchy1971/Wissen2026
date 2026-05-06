# M4d - Admin- und Diagnoseansicht

Stand: 2026-05-05

## Realer Status am 2026-05-06

- Real implementiert sind aktuell die Search-Index-Rebuild-Aktion, der Inconsistency-Report, Health-Endpunkte und Observability-Slices.
- Die Frontend-Seite `/admin/diagnostics` existiert, bildet derzeit aber nur den Rebuild-/Resultat-Flow ab.
- Nicht real implementiert ist ein aggregierter Backend-Endpunkt `GET /api/v1/admin/diagnostics` mit den unten beschriebenen Statuskarten.
- Dieses Dokument beschreibt daher gemischt aus Ist-Stand und Zielvertrag; der Zielvertrag ist noch nicht freigegeben.

## Ziel

M4d macht den operativen Systemzustand fuer Administratoren sichtbar, ohne fachliche Inhalte oder sensible Daten offenzulegen. Die Diagnoseansicht ist eine Betriebsoberflaeche fuer Verfuegbarkeit, Datenqualitaet, Importstabilitaet, Search-Bereitschaft und Chat-/RAG-Stabilitaet.

Die Ansicht ist explizit kein allgemeines Reporting-Dashboard und keine Entwicklerkonsole.

## Scope

In Scope:

- Backend-Diagnose-Endpunkt fuer aggregierte Systemkennzahlen
- Admin-Seite unter `/admin/diagnostics`
- Statuskarten fuer Kernkomponenten
- Fehlerliste mit redigierten technischen Details
- kopierbare technische Details fuer Support und Betrieb

Nicht in Scope:

- Dokumentinhalte oder Chunk-Texte
- Roh-Stacktraces in der UI
- Benutzerbezogene personenbezogene Details
- freie SQL- oder Admin-Operations
- Mandantenuebergreifende Detail-Exporte

## Sicherheits- und Datenschutzregeln

Admin-Zugriff:

- Zugriff nur fuer authentifizierte Benutzer mit Admin-Berechtigung.
- Enforcement serverseitig ueber M4a-Auth- und Membership-Kontext.
- Frontend darf Admin-Zugriff nicht nur ueber Routing oder UI-Verstecken modellieren.

Datensparsamkeit:

- Keine Dokumenttitel, keine Dokumenttexte, keine Chunk-Texte.
- Keine Prompt-Inhalte, keine Chat-Nachrichten, keine Dateinamen einzelner fehlgeschlagener Uploads.
- Keine rohen Connection-Strings, Secrets, Tokens oder Dateisystempfade.

Zulaessig sind nur aggregierte Kennzahlen, redigierte Fehlercodes und redigierte technische Hinweise.

## Backend Diagnostics API

Status:

- Zielvertrag, derzeit nicht real implementiert.

### Endpoint

- `GET /api/v1/admin/diagnostics`

Zweck:

- Liefert eine redigierte Systemdiagnose fuer die Admin-Oberflaeche.

### Auth und Autorisierung

Anforderungen:

- authentifizierte Session erforderlich
- aktiver Workspace-Kontext serverseitig aufgeloest
- Membership-Rolle `admin` oder `owner` erforderlich

Fehler:

| Status | Code | Bedeutung |
|---:|---|---|
| `401` | `AUTH_REQUIRED` | keine gueltige Session |
| `403` | `ADMIN_REQUIRED` | Benutzer ist kein Admin/Owner |
| `503` | `SERVICE_UNAVAILABLE` | Diagnose kann wegen Infrastrukturfehler nicht vollstaendig aufgebaut werden |

### Response `200`

```json
{
  "generated_at": "2026-05-05T14:00:00Z",
  "workspace_scope": "workspace-1",
  "overall_status": "degraded",
  "cards": {
    "database": {
      "status": "ok",
      "label": "DB erreichbar",
      "details": {
        "reachable": true,
        "latency_ms": 18
      }
    },
    "migrations": {
      "status": "ok",
      "label": "Migration Head aktuell",
      "details": {
        "current_revision": "20260505_0013",
        "head_revision": "20260505_0013",
        "at_head": true
      }
    },
    "documents": {
      "status": "ok",
      "label": "Dokumente und Chunks",
      "details": {
        "document_count": 128,
        "chunk_count": 6421,
        "archived_document_count": 12,
        "deleted_document_count": 3
      }
    },
    "imports": {
      "status": "warning",
      "label": "Import-Stabilitaet",
      "details": {
        "parser_error_rate_24h": 0.083,
        "successful_imports_24h": 44,
        "failed_imports_24h": 4,
        "last_imports": [
          {
            "import_id": "imp-1",
            "finished_at": "2026-05-05T13:42:00Z",
            "status": "failed",
            "error_code": "PARSER_FAILED"
          },
          {
            "import_id": "imp-2",
            "finished_at": "2026-05-05T13:40:00Z",
            "status": "chunked",
            "error_code": null
          }
        ]
      }
    },
    "search": {
      "status": "ok",
      "label": "Search Index",
      "details": {
        "backend": "postgresql_fts",
        "index_ready": true,
        "missing_search_vectors": 0,
        "stale_current_documents": 0
      }
    },
    "chat_rag": {
      "status": "warning",
      "label": "Chat/RAG",
      "details": {
        "chat_error_rate_24h": 0.041,
        "retrieval_error_rate_24h": 0.018,
        "llm_unavailable_rate_24h": 0.006
      }
    }
  },
  "errors": [
    {
      "id": "diag-1",
      "severity": "warning",
      "source": "imports",
      "code": "PARSER_FAILED",
      "message": "Parser-Fehlerquote der letzten 24h liegt ueber dem Grenzwert.",
      "technical_details": {
        "window_hours": 24,
        "failed_imports": 4,
        "successful_imports": 44,
        "threshold": 0.05
      }
    }
  ]
}
```

### Response-Felder

Top-Level:

| Feld | Typ | Nullable | Hinweis |
|---|---|---:|---|
| `generated_at` | datetime string | nein | serverseitiger Erstellungszeitpunkt |
| `workspace_scope` | string | nein | aktiver Workspace-Kontext, nicht frei vom Client gesetzt |
| `overall_status` | `ok` \| `warning` \| `degraded` \| `error` | nein | aggregierter Gesamtzustand |
| `cards` | object | nein | gruppierte Statuskarten |
| `errors` | array | nein | redigierte Fehlerliste |

Statuskarte:

| Feld | Typ | Nullable | Hinweis |
|---|---|---:|---|
| `status` | `ok` \| `warning` \| `degraded` \| `error` | nein | Ampelzustand |
| `label` | string | nein | UI-Label |
| `details` | object | nein | redigierte Kennzahlen |

Fehlerliste:

| Feld | Typ | Nullable | Hinweis |
|---|---|---:|---|
| `id` | string | nein | stabile Diagnose-ID |
| `severity` | `info` \| `warning` \| `error` | nein | Sortierung und UI-Farbe |
| `source` | string | nein | `database`, `migrations`, `imports`, `search`, `chat_rag` |
| `code` | string | nein | technischer Fehlercode |
| `message` | string | nein | redigierte menschenlesbare Meldung |
| `technical_details` | object | nein | kopierbare, aber redigierte Betriebshinweise |

## Definition der Kennzahlen

DB erreichbar:

- einfacher Lese- oder Ping-Check gegen die aktive Datenbank
- optional `latency_ms`
- keine DSN-Ausgabe

Migration Head aktuell:

- Vergleich zwischen aktueller Alembic-Revision und Head-Revision
- nur Revisionskennungen ausgeben, keine Dateipfade

Dokumentanzahl:

- Anzahl `active` plus `archived` Dokumente im aktiven Workspace
- getrennte Zaehlung fuer `archived` und `deleted` erlaubt

Chunkanzahl:

- Anzahl persistierter Chunks im aktiven Workspace
- keine Detailverteilung nach Dokument in M4d erforderlich

Parser-Fehlerquote:

- Anteil fehlgeschlagener Importe im letzten 24h-Fenster
- Grundlage: Import-Status und importbezogene Fehlercodes
- keine Dateinamen einzelner Fehlerfaelle anzeigen

Search Index Status:

- Backend-Typ, z. B. `postgresql_fts`
- Index bereit oder nicht bereit
- Anzahl Dokumente mit fehlender Search-Indexierbarkeit fuer aktuelle Versionen

Letzte Imports:

- nur redigierte Metadaten
- `import_id`, `finished_at`, `status`, `error_code`
- keine Dateinamen, keine Dokumenttitel, keine Inhalte

Chat/RAG Fehlerquote:

- Fehleranteile fuer Chat-Persistenz, Retrieval und LLM-Verfuegbarkeit im letzten 24h-Fenster
- keine Prompts, keine Antworten, keine Zitateinhalte

## UI-Spezifikation

### Route

- `/admin/diagnostics`

### Page-Zweck

- Admins sehen die Betriebsbereitschaft des Systems auf einen Blick.
- Die Seite dient als Startpunkt fuer Diagnose und Support, nicht fuer fachliche Datenanalyse.

### Layout

Bereiche:

- Kopfbereich mit Seitentitel `Systemdiagnose`
- Statuskarten-Raster
- Fehlerliste
- Bereich `Technische Details` mit kopierbarem JSON oder Key-Value-Block

### Statuskarten

Pflichtkarten:

- `DB erreichbar`
- `Migration Head aktuell`
- `Dokumente und Chunks`
- `Import-Stabilitaet`
- `Search Index`
- `Chat/RAG`

Verhalten:

- Jede Karte zeigt genau einen Status und 2 bis 5 Kernkennzahlen.
- Status-Farblogik: gruen, gelb, orange, rot fuer `ok`, `warning`, `degraded`, `error`.
- Keine expandierten Rohdaten in der Karte selbst.

### Fehlerliste

Inhalt pro Zeile:

- Severity-Badge
- Quelle
- Fehlercode
- kurze menschenlesbare Meldung
- Aktion `Technische Details kopieren`

Sortierung:

- zuerst `error`, dann `warning`, dann `info`
- innerhalb derselben Severity nach Aktualitaet

Leerer Zustand:

- Hinweis `Keine aktuellen Diagnosefehler`

### Technische Details

Zweck:

- Support-faehige Informationen kopierbar machen, ohne sensible Daten freizugeben.

Darstellung:

- kompakter Monospace-Block oder JSON-Viewer
- Button `Kopieren`
- nur redigierte Werte aus `technical_details`

Explizit verboten:

- Dokumenttext
- Chunk-Preview
- Prompt- oder Antworttexte
- Stacktraces mit lokalen Pfaden
- Secrets oder Header-Werte

### Loading, Error und Access States

Loading:

- Skeletons fuer Karten und Fehlerliste

403 State:

- klare Meldung `Kein Admin-Zugriff`
- kein Fallback auf technische Rohantwort im UI

503 State:

- degradierter Diagnosehinweis `Diagnosedaten konnten nicht vollstaendig geladen werden`
- wenn vorhanden, partielle Karten weiter anzeigen

## Frontend-ViewModels

### `DiagnosticsOverviewVM`

Felder:

- `generatedAt`
- `workspaceScope`
- `overallStatus`
- `cards`
- `errors`
- `hasBlockingError`

### `DiagnosticsCardVM`

Felder:

- `id`
- `title`
- `status`
- `primaryMetric`
- `secondaryMetrics`
- `copyPayload`

### `DiagnosticsErrorItemVM`

Felder:

- `id`
- `severity`
- `source`
- `code`
- `message`
- `technicalDetails`
- `copyText`

## Teststrategie

### Backend-Tests

Contract-Tests:

- `GET /api/v1/admin/diagnostics` liefert stabile Top-Level-Felder
- Kartenstruktur bleibt stabil, auch wenn einzelne Teilchecks `warning` oder `error` sind
- Response enthaelt keine Dokumenttitel, keine Dateinamen, keine Dokumenttexte

Auth-Tests:

- `401 AUTH_REQUIRED` ohne Session
- `403 ADMIN_REQUIRED` fuer Nicht-Admin
- `200` fuer Admin

Metric-Tests:

- DB-Check mappt erreichbar versus nicht erreichbar korrekt
- Migration-Check erkennt `at_head` korrekt
- archivierte und geloeschte Dokumente verfremden die Sichtbarkeit nicht, aber die Zaehlung bleibt konsistent
- Search-Index-Status erkennt fehlende oder stale Indexierung
- Parser-Fehlerquote und Chat/RAG-Fehlerquote werden fuer ein definiertes Zeitfenster korrekt berechnet

Redaction-Tests:

- keine Dokumenttexte im Payload
- keine Prompt-/Antworttexte im Payload
- keine Secrets oder Connection-Strings im Payload

### Frontend-Tests

Routing:

- `/admin/diagnostics` ist nur fuer Admin-Nutzer erreichbar
- Nicht-Admin sieht den `403`-State

Rendering:

- alle Pflichtkarten werden gerendert
- Fehlerliste zeigt Severity, Code und Meldung
- leere Fehlerliste zeigt Empty State

Copy-Interaktion:

- `Technische Details kopieren` kopiert nur redigierte Details
- kopierter Inhalt enthaelt keine Dokumentinhalte

Resilienz:

- partielle Backend-Fehler fuehren nicht zum Komplettabsturz der Seite
- `503` und Netzwerkfehler haben klaren Fallback-State

## Akzeptanzkriterien

- Admin sieht auf einer Seite die Betriebsbereitschaft von DB, Migration, Import, Search und Chat/RAG.
- Nicht-Admin kann die Diagnoseansicht weder direkt noch indirekt nutzen.
- Die UI zeigt keine sensiblen Inhalte und keine Dokumenttexte.
- Technische Details sind kopierbar, aber redigiert.
- Backend- und Frontend-Tests decken Auth, Vertragsstabilitaet, Redaction und Fehlerfaelle ab.