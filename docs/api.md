# API fuer M3a GUI

Stand: 2026-05-04

## Zweck

Dieses Dokument beschreibt die API-Abhaengigkeit der M3a-GUI auf hoher Ebene. Verbindlicher Detailvertrag bleibt `docs/api/v1-document-api-contract.md`.

## Von M3a konsumierte Endpunkte

- `GET /documents`
- `GET /documents/{document_id}`
- `GET /documents/{document_id}/versions`
- `GET /documents/{document_id}/chunks`

## Von der GUI verwendete Vertragsmerkmale

- Dokumentliste mit `title`, `mime_type`, `created_at`, `updated_at`, `latest_version_id`, `import_status`, `version_count`, `chunk_count`
- Dokumentdetail mit Stammdaten, `latest_version`, `parser_metadata`, `import_status`, `chunk_summary`
- Versionen mit `id`, `version_number`, `created_at`, `content_hash`
- Chunks mit `chunk_id`, `position`, `text_preview`, `source_anchor`
- Standardisiertes Fehlerformat `error.code`, `error.message`, `error.details`

## Konsistenz zum aktuellen GUI-Stand

- Die aktuelle M3a-GUI verwendet nur dokumentierte Paket-5-Felder.
- Die GUI fuehrt keine Schreiboperationen ein.
- Die GUI nutzt den aktuell implementierten Pfad `/documents`, nicht den noch fehlenden Alias `/api/v1/documents`.

## Offene Punkte

- Der Alias `/api/v1/documents` ist weiter nicht implementiert.
- Die GUI zeigt Versionen und Chunks aktuell innerhalb der Detailseite statt ueber eigene Routen.
- Fuer den harten Abschluss fehlen noch vollstaendige Unit-, API-Mock- und E2E-Nachweise.