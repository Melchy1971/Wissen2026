# Changelog

Stand: 2026-05-04

## 2026-05-04 - Paket 5 Abschlussstand

### Added

- Read-Performance-Migration `20260504_0008_read_api_performance_indexes.py`.
- Versions-Recency-Migration `20260504_0009_document_version_recency_index.py`.
- Legacy-Reparaturmigration `20260504_0010_repair_legacy_document_states.py` mit Audit-Tabelle `migration_document_repairs`.
- Dokument `docs/m3-system-boundaries.md` fuer harte Systemgrenzen vor M3.
- Review-Checkliste `docs/prompts/reviews/m3-scope-review-checklist.md`.
- Windows-Dev-Skripte `scripts/dev-backend.ps1`, `scripts/dev-frontend.ps1` und `scripts/dev-fullstack.ps1`.
- VS-Code-Tasks fuer Backend-, Frontend- und Full-Stack-Start.

### Changed

- `DocumentRepository.get_documents()` nutzt korrelierte Scalar-Subqueries statt Full-Table-Aggregationen.
- `DocumentRepository` typisiert ID-Filter jetzt backend-kompatibel fuer SQLite und PostgreSQL-UUID-Spalten.
- `DocumentImportPersistenceService` fuehrt den Dokumentstatus jetzt constraint-kompatibel ueber `pending -> parsed -> chunked`.
- `masterplan.md` markiert umgesetzte Punkte sichtbar mit `✅`.
- Status-, API- und Datenmodell-Dokumentation wurden mit dem Code- und Migrationsstand synchronisiert.
- Paket-5-Abschlussbewertung ist dokumentiert: `96/100`.

### Validated

- Fokussierter Backend-Lauf: `42 passed, 1 skipped`.
- PostgreSQL-Integrationslauf: `6 passed`.
- Read-/Import-API-Ruecklauf nach den PostgreSQL-Fixes: `19 passed`.
- Verifiziert wurden Parser, Markdown-Normalisierung, Chunking, Import-API, Read-API, Read-Service und Migrationsstruktur.
- Verifiziert wurde ausserdem ein PostgreSQL-Benchmark mit `100` Dokumenten, `300` Versionen und `6.000` Chunks.
- Gemessene Mittelwerte: `GET /documents = 3.1ms`, `GET /documents/{id} = 3.4ms`, `GET /documents/{id}/chunks = 2.1ms`.

### Outstanding

- `/api/v1/documents` ist weiter Zielpfad, aber noch kein implementierter Alias.
- OCR und feinere Source-Anchor-Granularitaet bleiben offene Folgethemen.

## 2026-05-04 - M3a GUI Foundation Prototyp

### Added

- Minimaler read-only Frontend-Prototyp fuer M3a auf React/Vite.
- Routing fuer `/documents` und `/documents/:id`.
- Getrennter API-Client fuer die Dokument-Read-Endpunkte.
- Statuskomponenten fuer Loading, Empty und Error.
- Dokumentliste, Dokumentdetail, Versionen-Anzeige und Chunk-Vorschau.
- Frontend-Dokumente `docs/frontend.md`, `docs/api.md`, `docs/m3a-viewmodels.md`, `docs/m3a-implementation-plan.md`, `docs/m3a-test-strategy.md`.

### Changed

- `frontend/src/app/App.jsx` verwendet jetzt Routing statt Platzhalterseite.
- `frontend/src/pages/DocumentsPage.jsx` rendert Dokumentliste ueber `GET /documents`.
- `frontend/src/pages/DocumentDetailPage.jsx` rendert Detail, Versionen und Chunk-Vorschau ueber die bestehenden Paket-5-Endpunkte.
- `masterplan.md` und `docs/status.md` spiegeln den M3a-Zwischenstand wider.

### Validated

- Frontend-Testlauf: `5 passed`.
- Frontend-Build: `vite build` erfolgreich.

### Outstanding

- Keine separaten Unit-Tests fuer ViewModel-Mapping und Fehlerabbildung.
- Keine eigenstaendigen API-Mock-Tests fuer `404`, `409` und API down.
- Kein E2E-Smoke-Test.
- Versionen und Chunks haben noch keine eigenen Routen, sondern leben aktuell im Detailscreen.