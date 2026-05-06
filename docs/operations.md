# Operations

Stand: 2026-05-06

## M4c Dokument-Lifecycle im Betrieb

Dieses Dokument beschreibt nur den aktuell nachgewiesenen Betriebsstand des Dokument-Lifecycle.

## Lifecycle State Machine

- `active -> archived`
- `archived -> active`
- `active -> deleted`
- `archived -> deleted`
- `deleted` ist terminal

Nicht implementiert:

- `deleted -> active`
- `deleted -> archived`
- Hard Delete / Purge

## Search- und Reindex-Verhalten

- Search verarbeitet nur aktive Dokumente.
- Archivierte und geloeschte Dokumente muessen aus neuen Search-Treffern verschwinden.
- Reindex synchronisiert dazu die Chunk-Sichtbarkeit ueber `document_chunks.is_searchable`.
- Reindex setzt aktive Dokumente suchbar und archivierte oder geloeschte Dokumente unsuchbar.

Betriebsgrenze:

- Der Service-Slice fuer Reindex ist getestet.
- Der letzte echte PostgreSQL-Integrationslauf fuer Search und Reindex ist fehlgeschlagen, weil die konfigurierte Test-Datenbank per Connection-Timeout nicht erreichbar war.

## Chat- und Citation-Verhalten

- Neue Chat-Antworten beziehen ihre Quellen aus dem Retrieval-/Search-Pfad.
- Historische Citations bleiben im Chatverlauf sichtbar, auch wenn das referenzierte Dokument spaeter archiviert oder geloescht wurde.
- Historische Citations tragen dazu Snapshot-Felder wie `document_title`, `quote_preview` und `source_status`.

Betriebsgrenze:

- Die Historie historischer Citations ist direkt getestet.
- Ein eigener Lifecycle-Integrationstest fuer neue Chat-Antworten fehlt derzeit; der Nachweis ist indirekt ueber Retrieval gegeben.

## Soft Delete

- Soft Delete setzt `lifecycle_status = deleted` und `deleted_at`.
- Versionen, Chunks und historische Citations bleiben physisch erhalten.
- `deleted` ist im aktuellen Betrieb nicht wiederherstellbar.

## Bekannte Einschraenkungen

- keine Admin-Ansicht fuer geloeschte Dokumente
- kein Purge-/Hard-Delete-Prozess
- kein gesonderter historischer Retrieval-Modus fuer archivierte oder geloeschte Dokumente
- keine gruen verifizierte PostgreSQL-End-to-End-Abdeckung fuer Search/Reindex im letzten Lauf