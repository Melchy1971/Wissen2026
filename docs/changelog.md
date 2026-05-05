# Changelog

Stand: 2026-05-05

## 2026-05-05 - Upload-Dokumentation auf Auth- und Fehlervertrag aktualisiert

### Changed

- `docs/status.md`, `docs/api.md`, `docs/import.md`, `docs/frontend.md`, `docs/changelog.md` und `masterplan.md` auf den aktuellen Upload-Code abgeglichen.
- Upload-Dokumentation beschreibt jetzt explizit den auth-gebundenen Uploadpfad, den serverseitigen Auth-Kontext fuer Workspace und Benutzer sowie das entfernte Default-Workspace-/Default-User-Fallback.
- `FILE_TOO_LARGE` ist mit dem aktuellen `413`-Vertrag und den Detailfeldern `max_upload_size_bytes` und `actual_size_bytes` dokumentiert.
- Pflicht-Uploadtests und der optionale PostgreSQL-Race-Test sind getrennt dokumentiert.

### Findings

- `POST /documents/import` ist auth-gebunden und liefert ohne Auth `AUTH_REQUIRED` und im fremden Workspace `WORKSPACE_ACCESS_FORBIDDEN`.
- Der Uploadvertrag bleibt asynchron: `202 Accepted` plus Job-Polling.
- Duplicate-Sequential-Tests sind Pflicht; der echte PostgreSQL-Race-Test ist als einziger optionaler Test isoliert.
- Der PostgreSQL-Race-Test ist aktuell `skipped`, weil die zugrunde liegende Migrationskette nicht vollstaendig aufloesbar ist.

### Decision

- Die Upload-Dokumentation entspricht jetzt dem aktuellen Code- und Teststand.

## 2026-05-05 - M4c Dokumentationssync und Konsistenzpruefung

### Changed

- `docs/status.md`, `docs/api.md`, `docs/data-model.md`, `docs/retrieval.md`, `docs/rag.md`, `docs/changelog.md` und `masterplan.md` auf den nachweisbaren M4c-Stand abgeglichen.
- Lifecycle-Regeln fuer `active`, `archived` und `deleted` sowie die Auswirkungen auf Liste, Search, Chat und Citation-Historie dokumentiert.

### Findings

- Lifecycle-Felder und Constraint sind im Dokumentmodell nachweisbar.
- `GET /documents` blendet `archived` standardmaessig aus und `deleted` konsequent weg.
- Search/Retrieval akzeptiert nur `active`.
- `DELETE /documents/{document_id}` ist als Soft-Delete implementiert.
- Historische Chat-Citations bleiben fuer geloeschte Dokumente sichtbar.

### Decision

- Dokumentation fuer M4c ist aktualisiert.
- M4c ist nach dem aktuellen Repository-Stand **abgeschlossen**.

## 2026-05-05 - M4b Dokumentationssync und Konsistenzpruefung

### Changed

- `docs/status.md`, `docs/api.md`, `docs/frontend.md`, `docs/changelog.md` und `masterplan.md` auf den nachweisbaren M4b-Stand abgeglichen.
- neues Dokument `docs/import.md` fuer Upload-Flow, Importstatus, Fehlercodes, Duplicate- und OCR-Verhalten erstellt.

### Findings

- Upload-GUI und Job-Polling sind nachweisbar implementiert.
- Upload-Endpunkt antwortet asynchron mit `202 Accepted`.
- Duplicate und OCR-required sind im Backend und in Tests nachweisbar.
- Die GUI zeigt Duplicate und OCR-required noch nicht als eigene spezialisierte Ergebniszustaende.
- Es gibt keinen Direkt-Sprung in die Dokumentdetailansicht nach erfolgreichem Import.

### Decision

- Dokumentation fuer M4b ist aktualisiert.
- M4b ist nach dem aktuellen Repository-Stand **nicht abgeschlossen**.

## 2026-05-05 - M4a Dokumentationssync und Konsistenzpruefung

### Changed

- `docs/status.md`, `docs/api.md`, `docs/data-model.md`, `docs/frontend.md` und `masterplan.md` wurden auf den nachweisbaren M4a-Stand abgeglichen.
- neues Dokument `docs/security.md` fuer Auth-, Workspace- und Sicherheitslage erstellt.
- M4a-Dokumentation beschreibt jetzt explizit den Unterschied zwischen Zielbild und aktuellem Codezustand.

### Findings

- `AUTH_REQUIRED`, `ADMIN_REQUIRED` und `WORKSPACE_REQUIRED` sind nachweisbar.
- echte Login-/Logout-/Session-Endpunkte sind nicht nachweisbar.
- `workspace_memberships` und `auth_sessions` sind nicht nachweisbar.
- Dokumente und Chat verwenden weiterhin `workspace_id` aus Request oder URL-Kontext.
- Upload nutzt weiterhin `settings.default_workspace_id` und `settings.default_user_id`.

### Decision

- Dokumentation fuer M4a ist aktualisiert.
- M4a ist nach dem aktuellen Repository-Stand **nicht abgeschlossen**.

## 2026-05-05 - M3c Chat/RAG Foundation Abschluss

### Added

- Chat-HTTP-API unter `/api/v1/chat/...`:
  - `POST /api/v1/chat/sessions`
  - `GET /api/v1/chat/sessions`
  - `GET /api/v1/chat/sessions/{session_id}`
  - `POST /api/v1/chat/sessions/{session_id}/messages`
- `RagChatService` als Orchestrator fuer Persistenz, Retrieval, Context Builder, Insufficient-Context-Policy, Prompt Builder, LLM Provider, Citation Mapper und Assistant-Persistenz.
- Austauschbares LLM-Provider-Interface `generate(system_prompt, user_prompt) -> str`.
- Deterministischer `FakeLlmProvider` fuer Tests mit simulierbarem Unavailable-, Timeout-, Empty- und No-Citation-Verhalten.
- Chat-Fehlercodes:
  - `CHAT_SESSION_NOT_FOUND`
  - `CHAT_MESSAGE_INVALID`
  - `CHAT_PERSISTENCE_FAILED`
  - `RETRIEVAL_FAILED`
  - `INSUFFICIENT_CONTEXT`
  - `LLM_UNAVAILABLE`
- Frontend-ChatPage gegen den echten POST-Message-Vertrag.

### Changed

- `POST /api/v1/chat/sessions/{session_id}/messages` erwartet `workspace_id`, `question` und optional `retrieval_limit`.
- Der POST-Message-Response ist eine direkte Assistant-`ChatMessageResponse` inklusive `citations` und `confidence`.
- Die GUI ergaenzt die gesendete User-Frage lokal im Verlauf und zeigt danach die Assistant-Antwort aus der API.
- Dokumentation fuer Status, API, Datenmodell, RAG, Frontend und Masterplan wurde auf M3c-Abschluss synchronisiert.

### Validated

- Backend-Fokuslauf fuer Chat/RAG, Context, Prompt, Citation, Policy und Persistenz: `74 passed`.
- Frontend-Gesamtlauf: `14 passed`.
- Frontend-Build: erfolgreich.

### Outstanding

- Produktiver LLM Provider ist nicht Teil von M3c; aktuell ist der Provider austauschbar und im Default bewusst unkonfiguriert.
- Kein Streaming.
- Keine Agenten, kein Tool Use und keine Dokumentmutation.
- Keine Embeddings oder semantische Suche.
- Kein Browser-E2E gegen laufendes Backend; M3c ist ueber API-/Service-/Frontend-Vertragstests abgesichert.

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

### Superseded

- Dieser Zwischenstand wurde durch spaetere PostgreSQL- und Ranking-Tests ueberholt.
- M3c wurde am 2026-05-05 auf dem stabilisierten Retrieval-Vertrag abgeschlossen.

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

### Superseded

- Dieser Zwischenstand wurde durch den Abschluss vom 2026-05-05 ueberholt.
- Chat-HTTP-API, end-to-end RAG-Pfad und API-Tests sind inzwischen implementiert und verifiziert.

## 2026-05-04 - M4 Integrierter Wissensbasis-Chat

### Status

- Noch nicht implementiert.
- Start ist seit dem M3c-Abschluss vom 2026-05-05 freigegeben.

### Open

- stabile Chat-HTTP-API im Backend
- integrierter Antwortpfad ueber Retrieval, Prompting, Policy, LLM und Citations
- API- und Integrationsnachweise fuer diesen produktiven Pfad
