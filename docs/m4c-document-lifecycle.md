# M4c Dokument-Lifecycle

Stand: 2026-05-05

## Ziel

M4c fuehrt einen expliziten Dokument-Lifecycle ein, damit Dokumente zwischen regularem Betrieb, Langzeitablage und Soft-Delete unterscheidbar werden, ohne referenzielle Integritaet fuer Versionen, Chunks und historische Chat-Zitate zu verlieren.

## Statusmodell

Erlaubte Statuswerte:

- `active`
- `archived`
- `deleted`

Persistierte Felder auf `documents`:

- `lifecycle_status`
- `archived_at`
- `deleted_at`

Regeln:

- `active`: sichtbar in Dokumentliste, Search, Retrieval und Chat.
- `archived`: sichtbar nur explizit gefiltert in der Dokumentliste, nicht suchbar, nicht retrievable fuer neue Chat-Antworten.
- `deleted`: Soft-Delete. Nicht sichtbar in Liste, nicht direkt abrufbar, nicht suchbar und nicht fuer neue Chat-Antworten nutzbar.

## Lifecycle-Regeln nach Systembereich

Dokumentliste:

- Standardansicht zeigt nur `active`.
- `archived` wird nur ueber Filter sichtbar.
- `deleted` ist nie sichtbar.

Dokument-Read-API:

- `GET /documents/{id}` liefert `active` und `archived`.
- `deleted` wird wie nicht vorhanden behandelt und liefert `404 DOCUMENT_NOT_FOUND`.
- Versionen und Chunks eines geloeschten Dokuments bleiben physisch erhalten, sind aber nicht mehr ueber die Read-API erreichbar.

Search und Retrieval:

- Suchbar und retrievable sind nur Dokumente mit `lifecycle_status = 'active'`.
- `archived` und `deleted` werden im Retrieval-Pfad konsequent ausgeschlossen.

Chat-Citations:

- Bereits gespeicherte Chat-Citations bleiben historisch sichtbar.
- Es findet keine nachtraegliche Bereinigung historischer Zitate statt.
- Dadurch bleiben alte Antworten nachvollziehbar, auch wenn das Quelldokument spaeter archiviert oder geloescht wurde.

## Transitionen

Erlaubte Transitionen:

- `active -> archived`
- `archived -> active`
- `active -> deleted`
- `archived -> deleted`

Nicht vorgesehen:

- `deleted -> active`
- `deleted -> archived`

`deleted` ist damit terminal. Eine physische Bereinigung waere ein separater spaeterer Betriebsprozess und ist nicht Teil von M4c.

## Datenmodell und Migration

Migration: `20260505_0013_document_lifecycle`

Erweiterungen:

- neues Feld `lifecycle_status` mit Check-Constraint auf `active | archived | deleted`
- neues Feld `archived_at`
- neues Feld `deleted_at`
- zusaetzlicher Index auf `(workspace_id, lifecycle_status, created_at)` fuer Listen- und Filterpfade

Versionen und Chunks bleiben unveraendert. Es gibt keine Cascade-Delete-Aenderung, damit referenzielle Beziehungen fuer historische Zitate und bestehende Versionen erhalten bleiben.