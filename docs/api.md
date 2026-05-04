# API fuer M3a GUI, M3b Retrieval-UI und M3c Chat-UI

Stand: 2026-05-04

## Zweck

Dieses Dokument beschreibt die API-Abhaengigkeit der aktuellen GUI auf hoher Ebene. Verbindlicher Detailvertrag fuer die Dokument-Read-Pfade bleibt `docs/api/v1-document-api-contract.md`. Der Retrieval-Pfad fuer M3b ist in `docs/retrieval.md` und `docs/m3b-retrieval-foundation.md` beschrieben. Der Zielvertrag fuer Chat/RAG ist in `docs/chat-rag-api-contract.md` beschrieben.

## Aktuell von der GUI konsumierte Endpunkte

- M3a Dokument-GUI:
- `GET /documents`
- `GET /documents/{document_id}`
- `GET /documents/{document_id}/versions`
- `GET /documents/{document_id}/chunks`
- M3b Retrieval-Erweiterung:
- `GET /api/v1/search/chunks`
- M3c Chat-UI gegen Zielvertrag:
- `POST /api/v1/chat/sessions`
- `GET /api/v1/chat/sessions`
- `GET /api/v1/chat/sessions/{id}`
- `POST /api/v1/chat/sessions/{id}/messages`

## Von der GUI verwendete Vertragsmerkmale

- Dokumentliste mit `title`, `mime_type`, `created_at`, `updated_at`, `latest_version_id`, `import_status`, `version_count`, `chunk_count`
- Dokumentdetail mit Stammdaten, `latest_version`, `parser_metadata`, `import_status`, `chunk_summary`
- Versionen mit `id`, `version_number`, `created_at`, `content_hash`
- Chunks mit `chunk_id`, `position`, `text_preview`, `source_anchor`
- Suchtreffer mit `document_id`, `document_title`, `document_version_id`, `version_number`, `chunk_id`, `position`, `text_preview`, `source_anchor`, `rank`
- Chat-Sessions mit `id`, `workspace_id`, `title`, `created_at`, `updated_at`, `message_count`
- Assistant-Antworten mit `answer`, `citations`, `confidence`
- Citations mit `chunk_id`, `document_id`, `document_title`, `source_anchor`, `quote_preview`
- Standardisiertes Fehlerformat `error.code`, `error.message`, `error.details`

## Konsistenz zum aktuellen GUI-Stand

- Die aktuelle M3a-GUI verwendet nur dokumentierte Paket-5-Felder.
- Die M3b-GUI-Erweiterung verwendet den Search-Endpunkt nur read-only und koppelt nicht direkt an Datenbank- oder Ranking-Interna.
- Die M3c-Chat-GUI ist gegen den dokumentierten Zielvertrag implementiert, nicht gegen bereits verifizierte Backend-Endpoints.
- Die GUI fuehrt keine Schreiboperationen ein.
- Die GUI nutzt den aktuell implementierten Pfad `/documents`, nicht den noch fehlenden Alias `/api/v1/documents`.
- Der Suchpfad laeuft aktuell ueber `/api/v1/search/chunks`.
- Die Chat-GUI ist gegen den dokumentierten Vertrag `/api/v1/chat/...` implementiert.
- Ein stabiler Backend-HTTP-Nachweis fuer diesen Chat-Pfad fehlt derzeit noch.

## Offene Punkte

- Der Alias `/api/v1/documents` ist weiter nicht implementiert.
- Die GUI zeigt Versionen und Chunks aktuell innerhalb der Detailseite statt ueber eigene Routen.
- Fuer den harten Abschluss von M3b fehlt noch ein belastbarer PostgreSQL-Suchtest mit echter Trefferreihenfolge.
- Fuer den harten Abschluss von M3c fehlen stabile Chat-API-Endpoints und ein echter end-to-end RAG-Antwortpfad.