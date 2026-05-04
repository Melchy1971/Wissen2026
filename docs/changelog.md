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

## 2026-05-04 - M3b Retrieval Foundation

### Added

- Search API `GET /api/v1/search/chunks`.
- `SearchService`, `SearchRepository` und Search-Response-Schema.
- Migration `20260504_0011_chunk_search_vector.py` fuer PostgreSQL `search_vector` und `GIN`-Index.
- Frontend-Suchmaske auf der Dokumentuebersicht.
- Suchergebnisliste mit Vorschau, Rank und Quellenanker.
- Dokument `docs/m3b-retrieval-foundation.md`.
- Dokument `docs/m3b-retrieval-evaluation-dataset.md`.
- Dokument `docs/retrieval.md` als Retrieval-Einstiegspunkt.

### Changed

- `docs/api.md`, `docs/frontend.md`, `docs/data-model.md`, `docs/status.md` und `masterplan.md` wurden auf den aktuellen Retrieval-Stand abgeglichen.
- GUI zeigt jetzt Such-Lade-, Leer- und Fehlerzustaende auf `/documents`.
- API-Fehlermapping kennt jetzt `INVALID_QUERY` fuer Suchanfragen.

### Validated

- Backend-Retrieval-Nachweis: `14 passed` fuer Search-Service, Search-API und Migrationspfad.
- Frontend-Such- und Screen-Nachweis: `8 passed`.
- Frontend-Build: `vite build` erfolgreich.

### Outstanding

- Kein echter PostgreSQL-Integrationsnachweis fuer Treffer, Filterung und Ranking des Suchendpunkts.
- Kein expliziter Ranking-Regressionstest fuer stabile Trefferreihenfolge.
- Daher noch kein harter Go-Status fuer M3c Chat/RAG.

## 2026-05-04 - M3c Chat/RAG Foundation

### Added

- `ContextBuilder` fuer deterministische Kontextpakete.
- `PromptBuilder` fuer dokumentgestuetzte Prompts.
- `CitationMapper` fuer maschinenlesbare Citations.
- `InsufficientContextPolicy` mit festen Schwellenwerten und No-Answer-Verhalten.
- Chat-Persistenzmodelle, Migration und Service fuer Sessions, Messages und Citations.
- Frontend-Chatseite mit Sessionliste, neuer Session, Nachrichtenverlauf, Quellenanzeige und Insufficient-Context-Zustand.
- Dokumente `docs/chat-rag-api-contract.md`, `docs/rag-dataflow.md` und `docs/rag.md`.

### Changed

- `docs/status.md`, `docs/api.md`, `docs/data-model.md`, `docs/frontend.md`, `docs/retrieval.md` und `masterplan.md` wurden auf den realen M3c-Stand abgeglichen.
- `chat_messages.source_metadata` wurde fuer den Zielvertrag auf `metadata` ausgerichtet.

### Validated

- Backend-Fokustests fuer Context Builder, Prompt Builder, Citation Mapper, Insufficient-Context-Policy und Chat-Persistenz: `37 passed`.
- Frontend-Tests inklusive ChatPage: `11 passed`.
- Frontend-Build: `vite build` erfolgreich.

### Outstanding

- Keine stabile Chat-HTTP-API im Backend nachgewiesen.
- Kein end-to-end RAG-Pipeline-Test ueber echten Antwortpfad.
- Keine belastbare Retrieval-Integration fuer Chat im produktnahen API-Flow.
- Daher noch kein harter Abschluss von M3c und kein Go fuer M4.