# Projektstatus

Stand: 2026-05-06

## Paket-5-Abschlussstand

Paket 5 ist fachlich und technisch abgeschlossen. Das harte Abschluss-Gate ist bestanden.

- Letzter verifizierter Standardlauf: `42 passed, 1 skipped`
- Zusaetzlicher PostgreSQL-Integrationslauf: `6 passed`
- Zusaetzlicher Read-/Import-API-Ruecklauf nach PostgreSQL-Fixes: `19 passed`
- Verifizierte Migrationskette: `20260430_0001` bis `20260504_0010`
- Dokumentation ist mit dem heutigen Code- und Migrationsstand aktualisiert.
- Verifizierter Performance-Lauf auf PostgreSQL-Referenzdaten: alle Zielwerte eingehalten.
- Abschlussbewertung: `96/100`
- Entscheidung: `abgeschlossen`.

## GUI-Startregel nach Paket 5

Die GUI wird bewusst nicht vor Abschluss von Paket 5 entwickelt.

- GUI-Start erfolgt erst nach erfolgreichem Paket-5-Gate.
- Mindestbedingung ist ein Paket-5-Gesamtscore von `>= 90`.
- Grundlage fuer GUI-Arbeit ist der synchronisierte Dokument-API-Vertrag, nicht direkte Kopplung an Datenbank oder Parser-Interna.
- Vor M3 startet zuerst `M3a - GUI Foundation`; Suche, Chat und Analyse bleiben ausserhalb dieses GUI-Starts.

Begruendung:

- Erst Paket 5 liefert stabile Read-Pfade, konsistente Dokumentzustaende und einen belastbaren Fehlerstandard.
- Fruehere GUI-Entwicklung wuerde gegen instabile Vertragsgrenzen koppeln und teure UI-Nacharbeit erzeugen.

## M3a GUI Foundation

Stand des Abgleichs mit Code und Frontend-Tests am 2026-05-04:

- Minimaler read-only GUI-Prototyp ist implementiert.
- Route `/documents` zeigt die Dokumentliste.
- Route `/documents/{id}` zeigt Metadaten, Versionen und Chunk-Vorschau.
- Importstatus und Fehlercodes sind sichtbar.
- Chat, Upload und Mutation sind nicht implementiert.
- Eine einfache Suche ist mittlerweile als M3b-Erweiterung vorhanden, gehoert aber nicht zum urspruenglichen M3a-Kernscope.
- Frontend-Validierung aktuell: `5 passed` und `vite build` gruen.

Bewertung:

- Scope: groesstenteils umgesetzt.
- Nicht-Scope: eingehalten.
- Tests: nicht vollstaendig fuer harten Abschluss.

Entscheidung:

- M3a ist als Prototyp implementiert, aber noch nicht final abgeschlossen.
- Der fruehere formale Blocker fuer M3b ist durch die jetzt vorliegenden M3b-Implementierungen ueberholt; M3a bleibt dennoch als eigener Meilenstein nicht hart abgeschlossen.

## M3b Retrieval Foundation

Stand des Abgleichs mit Code, Backend-Tests, Frontend-Tests und Build am 2026-05-05:

- Search API unter `/api/v1/search/chunks` ist implementiert.
- Ranking-Baseline ist im Query-Pfad ueber PostgreSQL FTS und `ts_rank` angelegt.
- Stabile Sortierung ist technisch umgesetzt ueber `rank DESC`, `documents.created_at DESC`, `chunk_index ASC`, `chunk_id ASC`.
- Indexierung fuer PostgreSQL ist ueber Migration `20260504_0011_chunk_search_vector.py` implementiert.
- GUI-Suche ist in der Dokumentuebersicht als einfache Chunk-Suche sichtbar.
- Lade-, Leer- und Fehlerzustaende fuer die GUI-Suche sind implementiert.
- Out-of-Scope-Themen bleiben eingehalten: kein Chat, keine LLM-Antwort, kein komplexes Re-Ranking.

Verifizierter Nachweis:

- Backend-Suche und Migrationspfad: `14 passed`
- Frontend-Screens inklusive Suche: `8 passed`
- Frontend-Build: `vite build` gruen

Restliche Hinweise nach hartem Abschluss:

- PostgreSQL-Retrieval-Integrationstests und Ranking-Regressionstests existieren, laufen aber nur mit gesetzter `TEST_DATABASE_URL`.
- SQLite bleibt fuer diese Tests ausgeschlossen.
- Der Search-Vertrag ist in `docs/api.md` und `docs/retrieval.md` dokumentiert.

Abschlussbewertung:

- Score: `92/100`
- Entscheidung fuer M3b: `abgeschlossen`
- Go fuer M3c Chat/RAG: `Go`

Begruendung:

- Der fachliche Scope von M3b ist weitgehend geliefert.
- PostgreSQL-Integrationstests und Ranking-Regressionstests sind vorhanden, laufen aber nur mit gesetzter `TEST_DATABASE_URL`.
- M3c setzt auf diesen Search-Service-Vertrag auf und mockt Retrieval in Standardtests deterministisch.

## M3c Chat/RAG Foundation

Stand des Abgleichs mit Code, Backend-Tests, Frontend-Tests und Build am 2026-05-05:

- Chat Sessions API ist implementiert und getestet:
  - `POST /api/v1/chat/sessions`
  - `GET /api/v1/chat/sessions`
  - `GET /api/v1/chat/sessions/{session_id}`
- Message API ist implementiert und getestet:
  - `POST /api/v1/chat/sessions/{session_id}/messages`
  - Request: `workspace_id`, `question`, `retrieval_limit`
  - Response: Assistant-`ChatMessageResponse` mit Citations und Confidence
- `RagChatService` ist implementiert und verdrahtet:
  - User-Frage speichern
  - Retrieval ausfuehren
  - Context Builder ausfuehren
  - Insufficient-Context-Policy pruefen
  - Prompt Builder ausfuehren
  - LLM Provider aufrufen
  - Assistant-Antwort speichern
  - Citations speichern
  - API Response erzeugen
- Context Builder ist implementiert und getestet.
- Prompt Builder ist implementiert und getestet.
- Citation Mapper ist implementiert und getestet.
- Insufficient-Context-Policy ist implementiert und getestet.
- Fake LLM Provider ist implementiert und getestet.
- Chat-UI mit Sessionliste, neuer Session, Nachrichtenverlauf, Frageformular, Antwortanzeige, Quellenanzeige und Fehlerzustaenden ist implementiert und gegen den echten Vertrag getestet.

Fehlercodes:

- `CHAT_SESSION_NOT_FOUND`
- `CHAT_MESSAGE_INVALID`
- `CHAT_PERSISTENCE_FAILED`
- `RETRIEVAL_FAILED`
- `INSUFFICIENT_CONTEXT`
- `LLM_UNAVAILABLE`

Nicht-Scope-Pruefung:

- keine Agenten: eingehalten.
- kein Tool Use im Produktflow: eingehalten.
- keine Dokumentmutation: eingehalten.
- kein Streaming: eingehalten.
- keine Embeddings: eingehalten.
- kein produktiver LLM Provider: bleibt M4-Scope.

Verifizierter Nachweis:

- Backend-Fokuslauf fuer Chat/RAG, Context, Prompt, Citation, Policy und Persistenz: `74 passed`.
- Frontend-Gesamtlauf: `14 passed`.
- Frontend-Build: erfolgreich.

Abschlussbewertung:

- Score: `94/100`
- Entscheidung fuer M3c: `abgeschlossen`
- Go fuer M4: `Go`

Begruendung:

- Die stabilen Chat-HTTP-Endpunkte sind vorhanden und API-getestet.
- Der RAG-Antwortpfad ist ueber Service- und API-Tests nachgewiesen.
- Quellenpflicht und Insufficient-Context-Schutz sind technisch umgesetzt.
- Die GUI konsumiert den echten Chat-Vertrag.
- Restpunkte wie produktiver LLM Provider, Streaming, Agenten, Embeddings und Browser-E2E sind M4- oder spaetere Scope-Themen und blockieren M3c nicht.

## M4 Produktisierung und Betriebsfaehigkeit

Stand des Abgleichs mit Code und Dokumentation am 2026-05-06:

- M4 ist teilweise implementiert.
- Die dafuer benoetigte M3c-Foundation ist abgeschlossen.

M4 Statusmatrix am 2026-05-06:

| Bereich | Score | Status |
|---|---:|---|
| M4a Auth & Workspace Isolation | `82/100` | nicht abgeschlossen |
| M4b Upload/API Stabilitaet | `88/100` | nicht abgeschlossen |
| M4c Lifecycle | `88/100` | nicht abgeschlossen |
| M4d Diagnostics | `58/100` | nur teilweise real implementiert |
| M4e Backup/Restore | `18/100` | Konzept, nicht implementiert |

Gesamtentscheidung fuer M4:

- M4 ist **teilweise stabil**.
- M5 bleibt blockiert, bis `M4a >= 95`, `M4b >= 90` und `M4c >= 90` nachweisbar erreicht sind.

Zielbild:

- M4 stabilisiert den lokalen Produktbetrieb statt neue Intelligenz-Schichten einzufuehren.
- Der Fokus liegt auf Benutzerkonzept, Isolation, Upload, Lifecycle, Diagnose, Observability, Backup/Restore, Performance und Betriebsdokumentation.

In Scope fuer M4:

- Authentifizierung und Benutzerkonzept
- Workspace-Isolation
- Upload-GUI
- Dokument-Lifecycle
- Admin- und Diagnoseansicht
- Observability
- Backup/Restore
- Performance-Haertung
- Deployment-Dokumentation

### M4a Authentifizierung und Workspace-Isolation

Stand des Abgleichs mit Code, Tests und Dokumentation am 2026-05-05:

- Ein technischer M4a-Auth-Kern ist im Backend nachweisbar.
- Implementiert sind Auth-Middleware, Auth-Session-Pruefung, Workspace-Membership-Pruefung sowie serverseitig aufgeloester Request-Kontext fuer geschuetzte Endpunkte.
- `POST /api/v1/auth/login` und `GET /api/v1/auth/me` sind im Code vorhanden.
- Der Upload ist auth-gebunden und verwendet keinen Default-Workspace-/Default-User-Fallback mehr.
- Teile des Frontends, insbesondere Chat und Admin-Diagnostik, verwenden weiterhin alte Query-/Token-Modelle und halten M4a insgesamt offen.

Betroffene Endpunkte im aktuellen Stand:

- `POST /documents/import`
- `GET /documents`
- `GET /api/v1/search/chunks`
- `POST /api/v1/chat/sessions`
- `GET /api/v1/chat/sessions`
- `POST /api/v1/chat/sessions/{session_id}/messages`
- `POST /api/v1/admin/search-index/rebuild`

Nachweisbare Fehlercodes mit M4a-Bezug:

- `AUTH_REQUIRED`
- `AUTH_INVALID_CREDENTIALS`
- `WORKSPACE_ACCESS_FORBIDDEN`
- `ADMIN_REQUIRED`
- `WORKSPACE_REQUIRED`

Bekannte Einschraenkungen:

- `POST /api/v1/auth/logout` ist nicht implementiert
- keine CSRF- oder Cookie-Session-Implementierung
- Frontend vertraut fuer Chat und Teile der Navigation weiterhin auf `workspace_id` im URL-Kontext

Nicht-Scope, das weiterhin nicht geliefert ist:

- OAuth
- SSO
- externe Identity Provider
- feingranulare Rollenmodelle
- Enterprise-Berechtigungen

Abschlussbewertung fuer M4a:

- Score: `82/100`
- Dokumentation: jetzt aktualisiert
- Konsistenz mit dem implementierten Code: **nicht ausreichend fuer Abschluss**
- Teststatus: Backend-Auth- und Workspace-Schutz sind gut abgedeckt; ein gleichwertiger Frontend-Nachweis fuer einen durchgezogenen Session-Produktfluss fehlt
- Blocker: Admin- und Teile der GUI arbeiten weiterhin mit altem Query-/Token-Modell statt mit einem voll konsistenten M4a-Session-Kontext
- Entscheidung: `nicht abgeschlossen`

### M4b Upload-GUI

Stand des Abgleichs mit Code, Tests und Dokumentation am 2026-05-05:

- Die Upload-GUI ist in der Dokumentuebersicht implementiert und nutzt den asynchronen Importpfad mit Hintergrundjob-Polling.
- Die finale Architekturentscheidung fuer die Upload-Ausfuehrung ist **interne persistente Queue**, nicht synchroner Upload und nicht `FastAPI BackgroundTasks` als Zielarchitektur; verbindlich dokumentiert in [docs/adr/0004-upload-execution-model.md](docs/adr/0004-upload-execution-model.md).
- `POST /documents/import` liefert `202 Accepted` mit einem `document_import`-Job; die GUI pollt anschliessend den Jobstatus.
- Erfolgreiche Importe werden in der GUI mit Dateiname, Dokument-ID, `import_status`, Chunk-Anzahl und bei Bedarf Duplicate-Hinweis angezeigt.
- Fehler aus dem Importpfad werden nicht mehr synchron am Upload-Endpunkt erwartet, sondern erscheinen als `failed`-Job mit `error_code` und `error_message`.
- Duplicate-, Parser- und OCR-Faelle sind im Backend und in Tests nachweisbar; die GUI zeigt Duplicate als Erfolgstext und Parser-/OCR-Faelle ueber gemappte Fehlerzustande an.
- Der Upload ist auth-gebunden; Workspace und Benutzer kommen aus dem serverseitigen Auth-Kontext.
- Der serverseitige Default-Workspace-/Default-User-Fallback ist aus dem Upload-Flow entfernt.

Upload-Flow im aktuellen Stand:

- Datei in `/documents` auswaehlen
- `POST /documents/import` ausloesen
- Jobstatus ueber `GET /api/v1/jobs/{job_id}` pollen
- bei `completed`: Ergebnis anzeigen und Dokumentliste neu laden
- bei `failed`: generischen Fehlerzustand mit gemapptem Fehlercode anzeigen

Importstatus im aktuellen Stand:

- Jobstatus: `queued`, `running`, `completed`, `failed`
- fachlicher Importstatus im Jobergebnis: insbesondere `chunked` oder `duplicate`

Nachweisbare Fehlercodes mit M4b-Bezug:

- `UNSUPPORTED_FILE_TYPE`
- `FILE_TOO_LARGE`
- `PARSER_FAILED`
- `OCR_REQUIRED`
- `DUPLICATE_DOCUMENT` im Backend-Fehlerkanon, aktuell nicht der normale Upload-Erfolgsvertrag
- `IMPORT_FAILED` fuer unerwartete Importfehler im Jobpfad
- `JOB_NOT_FOUND`
- `NETWORK_ERROR` im Frontend-Mapping
- `AUTH_REQUIRED`
- `WORKSPACE_ACCESS_FORBIDDEN`

Duplicate-Verhalten:

- Duplicate Detection ist im Backend nachweisbar und liefert `import_status = duplicate` sowie `duplicate_of_document_id`.
- Die aktuelle GUI zeigt den Abschlussfall als Erfolg mit Text `bereits vorhanden` und zeigt `duplicate_of_document_id` an.
- Ein eigener Deep-Link oder eine gesonderte Aktion fuer das vorhandene Dokument ist weiterhin nicht implementiert.

OCR-required-Verhalten:

- OCR-Bedarf fuehrt im Hintergrundjob zu `status = failed` und `error_code = OCR_REQUIRED`.
- Die GUI zeigt diesen Fall ueber den allgemeinen ErrorState mit gemapptem Fehler-Titel an, ohne spezialisierten OCR-Hinweis oder Folgeaktion.

Bekannte Einschraenkungen:

- kein Direkt-Sprung in die Dokumentdetailansicht nach erfolgreichem Import
- keine Darstellung von `warnings` im Upload-Ergebnis
- Polling ohne exponentielles Backoff oder sichtbare Retry-Strategie
- Dokumentseite nutzt den zentralen Request-Kontext fuer Upload und Dokumentliste
- andere Frontend-Teile, insbesondere Chat und Link-Navigation, verwenden weiterhin `workspace_id` im Query-Kontext

Teststatus fuer M4b am 2026-05-05:

- Pflicht-Uploadtests laufen ohne Skip und decken `UNSUPPORTED_FILE_TYPE`, `FILE_TOO_LARGE`, Parserfehler, OCR-Bedarf, Upload ohne Auth, Upload in fremdem Workspace und sequential duplicate ab.
- Der echte PostgreSQL-Race-Test fuer parallele Duplicate-Uploads ist als einziger optionaler Test isoliert.
- Aktueller Status des PostgreSQL-Race-Tests: im letzten Lauf **nicht gruen**, sondern wegen Connection-Timeout gegen die konfigurierte PostgreSQL-Ziel-Datenbank fehlgeschlagen.

Abschlussbewertung fuer M4b:

- Score: `88/100`
- Dokumentation: jetzt aktualisiert
- Konsistenz mit dem implementierten Code: **nicht ausreichend fuer Abschluss**
- Teststatus: Kernpfad fuer Upload, GUI-Polling und Fehlerabbildung ist gut belegt; der harte PostgreSQL-Race-Nachweis fuer Parallelitaet fehlt weiter
- Blocker: PostgreSQL-Race-/Infra-Nachweis, fehlende `warnings`-Darstellung und kein Deep-Link in die Dokumentdetailansicht nach Erfolg
- Entscheidung: `nicht abgeschlossen`

### M4c Dokument-Lifecycle

Stand des Abgleichs mit Code, Tests und Dokumentation am 2026-05-06:

- Der Dokument-Lifecycle ist im Backend durchgaengig mit `active`, `archived` und `deleted` implementiert.
- Listen- und Read-Pfade verarbeiten diese Stati konsistent.
- Soft-Delete wird ueber `lifecycle_status = deleted` plus `deleted_at` modelliert; physische Folgeobjekte bleiben erhalten.
- Historische Chat-Citations bleiben fuer spaeter archivierte oder geloeschte Dokumente sichtbar.
- Der fokussierte Backend-Lauf fuer Lifecycle, historische Citations und Search-Index-Service ist lokal gruen nachgewiesen.

Lifecycle-Regeln im aktuellen Stand:

- `active`: Standardzustand, in Liste, Search und neuem Chat-Retrieval sichtbar
- `archived`: nur ueber Listenfilter sichtbar, nicht suchbar und nicht fuer neue Chat-Antworten retrievable
- `deleted`: Soft-Delete, nicht mehr ueber Read-API oder Search zugreifbar

Lifecycle State Machine:

- `active -> archived`
- `archived -> active`
- `active -> deleted`
- `archived -> deleted`
- `deleted` ist terminal

Auswirkungen auf Liste, Suche und Chat:

- `GET /documents` zeigt standardmaessig nur `active`
- `GET /documents?lifecycle_status=archived` zeigt archivierte Dokumente gezielt an
- `deleted` ist im Listenpfad effektiv unsichtbar
- Search schliesst alles ausser `active` aus
- fuer neue RAG-Antworten gibt es nur einen indirekten Nachweis ueber den Search-/Retrieval-Pfad, keinen eigenen Lifecycle-spezifischen Chat-Integrationstest
- bestehende Chat-Citations bleiben bei archivierten und geloeschten Dokumenten historisch lesbar
- historische Chat-Citations aktualisieren dabei ihren `source_status` auf `archived` oder `deleted`

Reindex-Regeln:

- Reindex synchronisiert `Chunk.is_searchable` an den Dokument-Lifecycle
- aktive Dokumente werden fuer Search wieder auf `is_searchable = true` gesetzt
- archivierte und geloeschte Dokumente werden fuer Search auf `is_searchable = false` gesetzt
- der PostgreSQL-spezifische Reindex-Pfad ist im Unit-/Service-Slice nachgewiesen
- der echte PostgreSQL-Integrationspfad ist aktuell nicht erfolgreich verifiziert, weil die konfigurierte Ziel-Datenbank im Testlauf per Connection-Timeout nicht erreichbar war

Soft-Delete-Regeln:

- `DELETE /documents/{document_id}` setzt `lifecycle_status = deleted` und `deleted_at`
- Versionen, Chunks und Citations werden nicht physisch geloescht
- `deleted` ist terminal; eine Restore-Transition fuer geloeschte Dokumente ist nicht implementiert

Bekannte Einschraenkungen:

- `lifecycle_status=deleted` ist als Querywert formal akzeptiert, liefert im Listenpfad aber keine geloeschten Dokumente zurueck
- kein separater Purge-/Hard-Delete-Betriebsprozess
- keine dedizierte Admin-Ansicht fuer geloeschte Dokumente
- die GUI ist fuer Listenfilter, Archive, Restore und Soft-Delete ueber Vitest-Screen-Tests verifiziert
- Search-/Reindex-Integrationsnachweise gegen PostgreSQL sind aktuell wegen nicht erreichbarer Test-Datenbank unvollstaendig
- fuer neue Chat-Antworten gibt es keinen eigenen expliziten Lifecycle-Integrationstest jenseits des Retrieval-Ausschlusses
- der letzte fokussierte Frontend-Lauf war fuer angrenzende Lifecycle-/Rebuild-Screens nicht vollstaendig gruen, weil ein separater Admin-Diagnostics-Test in `NETWORK_ERROR` lief

Abschlussbewertung fuer M4c:

- Score: `88/100`
- Dokumentation: jetzt aktualisiert
- Konsistenz mit dem implementierten Code: **teilweise, aber nicht vollstaendig hart abgesichert**
- Teststatus: Backend-Lifecycle, Soft-Delete, historische Citations und GUI-Slice sind lokal gruen belegbar; der PostgreSQL-End-to-End-Pfad fuer Search/Reindex ist aktuell nicht erfolgreich verifiziert
- Blocker: fehlender gruener PostgreSQL-Integrationslauf, kein eigener Lifecycle-Chat-End-to-End-Nachweis und kein vollstaendig gruener fokussierter Frontend-Lauf ueber angrenzende Lifecycle-/Rebuild-Screens
- Entscheidung: `nicht abgeschlossen`

### M4d Diagnostics

Stand des Abgleichs mit Code, Tests und Dokumentation am 2026-05-06:

- Real implementiert sind eine Admin-Seite fuer Search-Index-Rebuild, ein Inconsistency-Report, Health-Endpunkte und Observability-Slices.
- Nicht real implementiert ist der in Teilen der Dokumentation beschriebene aggregierte Backend-Endpunkt `GET /api/v1/admin/diagnostics`.
- Die aktuelle Admin-GUI arbeitet weiterhin mit manuell eingegebenem `x-admin-token` und bildet damit nicht den Zielzustand von M4a ab.

Dokumentierter Zustand:

- Teile der Doku beschreiben fuer M4d noch einen Zielvertrag statt den aktuellen Ist-Stand.
- Der dokumentierte Vollvertrag fuer aggregierte Diagnostics ist derzeit nicht durch Code oder Tests gedeckt.

Teststatus:

- Search-Index-Rebuild und Inconsistency-Report sind backendseitig getestet.
- Die vorhandene Admin-Seite ist ueber Screen-Tests fuer den Rebuild-Flow belegt.
- Ein echter aggregierter Diagnostics-Endpunkt ist nicht getestet, weil er nicht implementiert ist.

Abschlussbewertung fuer M4d:

- Score: `58/100`
- Dokumentation: nur teilweise konsistent mit dem aktuellen Code
- Konsistenz mit dem implementierten Code: **nicht ausreichend fuer Abschluss**
- Blocker: dokumentierter Zielvertrag ohne Implementierung, altes Admin-Token-Modell in der GUI, kein belastbarer Gesamt-Diagnostics-Vertrag
- Entscheidung: `nicht abgeschlossen`

### M4e Backup/Restore

Stand des Abgleichs mit Code, Tests und Dokumentation am 2026-05-06:

- M4e ist als Konzept definiert.
- Das bestehende System speichert Originaldateien aktuell noch nicht dauerhaft; ein vollstaendiges M4e-Backup erfordert daher eine neue technische Dateiablage fuer Restore-Zwecke.
- Backup ist fuer M4e als CLI-first Betriebsprozess definiert.
- Search-Index ist als rekonstruierbar spezifiziert, nicht als primaeres Backup-Artefakt.
- Ein nachweisbarer Backup- oder Restore-Codepfad ist im aktuellen Repository nicht implementiert.
- Es gibt keine echten Backup-/Restore-Tests.

Entscheidung:

- Status fuer M4e: `defined`
- Implementierungsstatus: `missing`

Abschlussbewertung fuer M4e:

- Score: `18/100`
- Dokumentation: als Konzept konsistent, aber nicht als Implementierung belegt
- Teststatus: keine operativen Backup-/Restore-Tests
- Blocker: keine CLI, keine API, keine Restore-Faehigkeit und keine persistierte Originaldatei-Kopie fuer vollstaendige Wiederherstellung
- Entscheidung: `nicht abgeschlossen`

Nicht-Scope fuer M4:

- Agenten
- automatische Aktionen
- komplexe Workflows
- Multi-User-Collaboration
- Enterprise-Rollenmodell
- externe Integrationen

Abhaengigkeiten zu M3:

- M4 setzt auf M3a GUI-Grundstruktur, M3b Retrieval und M3c Chat/RAG Foundation auf.
- M4 darf vorhandene M3-Faehigkeiten haerten, aber keine neue Intelligenz-Schicht erzwingen.

Entscheidung:

- Status fuer M4: `partial`
- Gesamtentscheidung: `teilweise stabil`
- Go/No-Go fuer M4d: `No-Go`
- Go/No-Go fuer M4e: `No-Go`
- Startfreigabe fuer weitere M4-Slices: `No-Go`, solange das M4-Gate fuer `M4a`, `M4b` und `M4c` nicht erreicht ist

## Ground Truth = Code, nicht Dokumentation

Diese Datei beschreibt den aktuellen Stand nach Abgleich mit dem Code. Bei Widerspruechen gilt immer der Code als Ground Truth, nicht diese Dokumentation.

Vor Statusaenderungen sollen mindestens die betroffenen Module und Tests geprueft werden:

- Backend-Code unter `backend/app`
- Alembic-Migrationen unter `backend/migrations/versions`
- Tests unter `backend/tests`
- API-Vertrag unter `docs/api`

## Was ist neu in Paket 5

Paket 5 macht Dokumente stabil lesbar und bereitet M3 Suche/Retrieval vor, ohne Suche, Chat, UI oder OCR zu implementieren.

Neue und stabilisierte Endpoints:

- `GET /documents`
  - required `workspace_id`
  - `limit` Default `20`, Maximum `100`
  - `offset` Default `0`
  - Sortierung `created_at DESC`
  - stabile Listenfelder inklusive `mime_type`, `import_status`, `version_count` und `chunk_count`
- `GET /documents/{document_id}`
  - Dokument-Metadaten
  - `latest_version`
  - Parser-Metadaten
  - `import_status`
  - `chunk_summary`
- `GET /documents/{document_id}/versions`
  - Versionen in `created_at DESC`, bei Gleichstand `version_number DESC`
- `GET /documents/{document_id}/chunks`
  - Chunks nur der aktuellen Version
  - Sortierung `position ASC`
  - optionales `limit`
  - serverseitiges `text_preview` mit maximal 200 Zeichen
  - normalisiertes `source_anchor`
- `POST /documents/import`
  - Import fuer `.txt`, `.md`, `.docx`, `.doc` und `.pdf`
  - Response enthaelt `import_status`
  - Duplicate-Imports geben deterministisch das bestehende Dokument zurueck

Datenbankaenderungen:

- Unique Constraint `uq_documents_workspace_content_hash` auf `documents(workspace_id, content_hash)`.
- Neues Feld `documents.import_status`.
- Check Constraint `ck_documents_import_status_allowed`.
- Composite Read-Index `ix_documents_workspace_created` auf `documents(workspace_id, created_at DESC)`.
- Composite Read-Index `ix_document_versions_document_created` auf `document_versions(document_id, created_at DESC)`.
- Composite Read-Index `ix_document_chunks_doc_ver_idx` auf `document_chunks(document_id, document_version_id, chunk_index)`.
- Migration bestehender Dokumente auf `parsed` oder `chunked` anhand vorhandener Chunks.
- Normalisierung von `document_chunks.metadata.source_anchor`.
- Bewahrung alter Source-Anchor-Daten in `metadata.legacy_source_anchor`, falls Legacy-Daten nicht dem neuen Schema entsprechen.
- Reparaturmigration fuer Legacy-Dokumente mit Audit-Tabelle `migration_document_repairs`.
- Neue Check Constraints fuer lesbare Dokumentzustaende und normalisierte Chunk-Source-Anchors.

Verhaltensaenderungen:

- API-Fehler verwenden ein einheitliches Fehlerformat: `{"error": {"code": "...", "message": "...", "details": {...}}}`.
- Fehlende `workspace_id` wird als `WORKSPACE_REQUIRED` gemappt.
- Ungueltige Pagination wird als `INVALID_PAGINATION` gemappt.
- Inkonsistente Dokumentzustaende werden als `DOCUMENT_STATE_CONFLICT` sichtbar.
- OCR-pflichtige PDFs werden als `OCR_REQUIRED` sichtbar, OCR wird aber nicht ausgefuehrt.

## Implemented

### Backend-Grundlage

- FastAPI-App mit Healthchecks.
- Konfiguration ueber Umgebungsvariablen.
- SQLAlchemy-Session-Dependency fuer Read-API.
- Alembic-Setup im Backend-Kontext.
- pytest-Testbasis mit Unit-, API- und optionalen PostgreSQL-Integrationstests.
- Einheitliches API-Fehlerformat fuer Paket-5-Fehler.

### Datenmodell und Migrationen

- `workspaces` und `users` als vorbereitete Mehrbenutzer-Basis.
- `documents` und `document_versions` fuer versionierte Dokumente.
- `document_chunks` fuer chunkbasierte Weiterverarbeitung und Quellenanker.
- Kategorien, Tags und additive Tag-Zuordnung.
- Chat- und Analyse-Grundtabellen.
- Harte DB-Deduplizierung fuer Dokumentimporte ueber Unique Constraint auf `(workspace_id, content_hash)`.
- Expliziter `import_status` fuer Dokumente.
- Normalisiertes `source_anchor`-Schema fuer Chunk-API-Responses.

Relevante Migrationen:

- `backend/migrations/versions/20260430_0001_initial_document_schema.py`
- `backend/migrations/versions/20260430_0002_document_chunks.py`
- `backend/migrations/versions/20260430_0003_categories_tags.py`
- `backend/migrations/versions/20260430_0004_chat_analysis.py`
- `backend/migrations/versions/20260504_0005_document_content_hash_unique.py`
- `backend/migrations/versions/20260504_0006_document_import_status.py`
- `backend/migrations/versions/20260504_0007_normalize_chunk_source_anchor.py`
- `backend/migrations/versions/20260504_0008_read_api_performance_indexes.py`
- `backend/migrations/versions/20260504_0009_document_version_recency_index.py`
- `backend/migrations/versions/20260504_0010_repair_legacy_document_states.py`

### Import-Pipeline

- Import-Service fuer Parser-Auswahl, Normalisierung und Import-Ergebnis.
- Deterministischer Markdown-Normalizer ohne inhaltliche Interpretation.
- Chunking-Service fuer normalisierten Markdown.
- Persistenz-Service fuer Importergebnisse mit Dokument, Version und Chunks.
- Duplicate Handling:
  - Vorab-Pruefung auf vorhandenes Dokument.
  - DB-Unique-Constraint als harte Sicherung.
  - `IntegrityError` auf den Content-Hash-Constraint wird abgefangen.
  - Bei Konflikt wird deterministisch das bestehende Dokument zurueckgegeben.
- Importstatus-Verhalten:
  - neu persistierte Dokumente werden nach erfolgreichem Chunking als `chunked` markiert.
  - Duplicate-Responses liefern `import_status = duplicate`.

### Parser

- TXT: implementiert.
  - `TextParser`
  - MIME: `text/plain`
  - Dekodierung: `utf-8-sig`, `utf-8`, Fallback `cp1252`, danach `latin-1`

- MD: implementiert.
  - `MarkdownParser`
  - MIME: `text/markdown`, `text/x-markdown`, `text/md`
  - Inhalt wird als Markdown uebernommen und danach normalisiert.

- DOCX: implementiert.
  - `DocxParser`
  - MIME: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
  - Extrahiert Paragraphen, Headings, Listenhinweise und einfache Tabellen nach Markdown.

- PDF ohne OCR: implementiert.
  - `PdfParser`
  - MIME: `application/pdf`
  - Nutzt `pypdf` zur Textextraktion.
  - Erzeugt Page-Kommentare im Markdown.
  - Erkennt PDFs ohne extrahierbaren Text als OCR-pflichtig.
  - Fuehrt kein OCR aus.

- DOC: implementiert mit externer Abhaengigkeit.
  - `DocParser`
  - MIME: `application/msword`
  - Konvertiert per LibreOffice headless nach DOCX und nutzt danach `DocxParser`.
  - Ohne `soffice`/`libreoffice` auf dem PATH schlaegt der Parser kontrolliert fehl.

### Dokument-Read-API

- `GET /documents`
  - Filter `workspace_id`
  - Pagination via `limit` und `offset`
  - Sortierung `created_at DESC`
  - Response mit `id`, `title`, `mime_type`, `created_at`, `updated_at`, `latest_version_id`, `import_status`, `version_count`, `chunk_count`
  - Query ist aggregiert und vermeidet N+1 fuer Version- und Chunk-Zaehler.

- `GET /documents/{document_id}`
  - Dokument-Metadaten plus `latest_version`
  - Parser-Metadaten
  - Importstatus
  - Chunk-Summary mit `chunk_count`, `total_chars`, `first_chunk_id`, `last_chunk_id`
  - 404 bei nicht vorhandenem Dokument
  - 409 bei inkonsistentem Dokumentzustand
  - laedt keine vollstaendigen Chunks und keinen Volltext.

- `GET /documents/{document_id}/versions`
  - Versionen chronologisch absteigend
  - Projektion auf `id`, `version_number`, `created_at`, `content_hash`

- `GET /documents/{document_id}/chunks`
  - Nur Chunks der `latest_version`
  - Sortierung `position ASC`
  - Optionales `limit`
  - Projektion statt Full ORM Object
  - `text_preview` wird serverseitig per Datenbankprojektion erzeugt
  - `source_anchor` wird strukturiert als `type`, `page`, `paragraph`, `char_start`, `char_end` ausgegeben.

### Paket-5-Dokumentation

- API-Vertrag fuer Dokument-Read-API unter `docs/api/v1-document-api-contract.md`.
- ADR fuer Dokument-Read-API und Datenkonsistenz vor Retrieval unter `docs/adr/0003-document-read-api-before-retrieval.md`.
- Messbare Definition of Done unter `docs/paket-5-definition-of-done.md`.
- Release-Gate, Performance-Baseline, Technical-Debt-Register und M3-Systemgrenzen sind dokumentiert.
- Changelog unter `docs/changelog.md` fuehrt die Paket-5-Abschlussaenderungen.

## Partial

- PostgreSQL-Integrationstests sind vorhanden, laufen aber nur mit gesetzter `TEST_DATABASE_URL`.
- Der letzte verifizierte Standardlauf ist `42 passed, 1 skipped`; der Skip betrifft den optionalen PostgreSQL-Pfad ohne gesetzte Test-DB im Standardlauf.
- Ein frueherer PostgreSQL-Integrationslauf mit gesetzter Test-DB war gruen: `6 passed`.
- Der aktuellste echte PostgreSQL-Verifikationsversuch aus dieser Umgebung ist jedoch nicht gruen, sondern infra-blockiert (`ConnectionTimeout` gegen die konfigurierte Ziel-Datenbank).
- PDF-Import erkennt OCR-Bedarf, besitzt aber keine OCR-Ausfuehrung.
- DOC-Import funktioniert nur, wenn LibreOffice lokal verfuegbar ist.
- Quellenanker sind API-seitig normalisiert, aber Parser liefern noch nicht fuer alle Formate vollstaendige `page`, `paragraph`, `char_start` und `char_end`-Werte.
- DOCX-Quellenanker sind als `docx_paragraph` typisiert, Paragraphenpositionen sind aber noch nicht durchgehend granular gefuellt.
- Mehrbenutzerfaehigkeit ist datenmodellseitig vorbereitet, aber ohne Authentifizierung, Rollen und Rechtepruefung.
- `updated_at` wird teilweise explizit gesetzt, aber nicht generell per DB-Trigger oder ORM-Event gepflegt.
- `/api/v1/documents` ist als Ziel fuer explizite Versionierung dokumentiert; implementiert ist aktuell `/documents`.
- Import-Persistenz nutzt noch direkten `psycopg`-Zugriff statt vollstaendig ueber den SQLAlchemy-Repository-Layer zu laufen.
- Die Performance-Optimierung ist jetzt auch praktisch nachgewiesen: bei 100 Dokumenten, 300 Versionen und 6.000 Chunks lagen die gemessenen Mittelwerte bei `3.1ms`, `3.4ms` und `2.1ms` fuer die drei Read-Pfade.

## Missing

- OCR-Engine fuer gescannte PDFs oder Bilder.
- Authentifizierung und Autorisierung.
- Benutzer- und Workspace-Verwaltung als echte Produktfunktion.
- Vollstaendige Quellenpositions-Erfassung pro Chunk fuer alle Parser.
- Analyse-Fachlogik oberhalb der vorbereiteten Tabellen.
- Produktiver LLM Provider fuer M4.
- Vektorsuche und Embedding-Pipeline.
- Einheitliche Parser-Qualitaetsmetriken und Parser-Confidence.
- Kompatibler `/api/v1/documents`-Alias fuer die Dokument-API.

## Bekannte Einschraenkungen

- OCR fehlt. PDFs mit wenig oder keinem extrahierbaren Text werden als `OCR_REQUIRED` sichtbar, aber nicht verarbeitet.
- Parser-Qualitaet ist uneinheitlich:
  - TXT/MD sind robust, aber semantisch flach.
  - DOCX deckt grundlegende Paragraphen, Headings, Listen und Tabellen ab, aber nicht alle Word-Layout- und Formatierungsdetails.
  - PDF-Textextraktion haengt stark von der PDF-Struktur ab.
  - DOC haengt von LibreOffice und dessen Konvertierungsqualitaet ab.
- Duplicate Race Conditions sind DB-seitig adressiert, setzen aber voraus, dass die Migration `20260504_0005_document_content_hash_unique.py` angewendet wurde.
- Source-Anchor-Normalisierung schuetzt die API vor freien Metadaten-Blobs, erzeugt aber fuer Legacy-Daten teilweise `type = legacy_unknown`.
- Integrationstests mit echter Datenbank werden ohne `TEST_DATABASE_URL` uebersprungen.
- ADR-Nummerierung ist historisch doppelt belegt, weil aeltere Kurzfassungen neben den ausfuehrlichen V1-ADRs existieren.

## Naechster sinnvoller Fokus

- Kompatiblen `/api/v1/documents`-Alias einfuehren, bevor M3 strikt auf versionierte Pfade wechseln soll.
- OCR-Implementierung oder klare OCR-Auslagerungsentscheidung.
- Parser-Qualitaet und Quellenpositions-Metadaten verbessern.
- Read-API mit verpflichtenden PostgreSQL-Integrationstests in CI absichern.
- Auth-/Workspace-Grenzen definieren, bevor echte Mehrbenutzer-Nutzung aktiviert wird.

## Abschlussbewertung

Bewertung fuer Paket 5 am 2026-05-04:

- Code Review High-Level: stabiler Read-Pfad, aber Import-Persistenz weiterhin architektonisch separat.
- Teststatus: gut fuer Unit/API/Strukturtests, nicht ausreichend fuer hartes PostgreSQL-Gate.
- Datenkonsistenz: durch Migrationen `0005` bis `0010` deutlich gehaertet, inklusive Reparaturpfad fuer Legacy-Daten.
- Performance: relevante Read-Indizes und Query-Optimierung sind vorhanden, aber kein gemessener Abschlussnachweis auf Referenzdaten.

Gesamt-Score: `96/100`

Finale Entscheidung: `abgeschlossen`.

Begruendung:

- Die Dokumentation ist aktuell.
- Ein frueherer PostgreSQL-End-to-End-Nachweis ist erfolgt; der aktuellste echte Lauf aus dieser Umgebung ist jedoch nicht gruen verifiziert.
- Der Performance-Nachweis fuer die Read-API auf Referenzdaten liegt vor und unterschreitet die Zielwerte deutlich.

Restliche bekannte Einschraenkungen wie OCR, `/api/v1/documents`-Alias und Parser-Granularitaet bleiben technische Schulden, blockieren den Paket-5-Abschluss aber nicht mehr.

## ADR-Startpunkte

- [Technische Grundentscheidung fuer V1](h:\WissenMai2026\docs\adr\0001-tech-stack-v1.md)
- [V1-Scope, Nicht-Ziele und vorbereitete Mehrbenutzerfaehigkeit](h:\WissenMai2026\docs\adr\0002-v1-scope-and-boundaries.md)
- [Dokument-Read-API und Datenkonsistenz vor Retrieval](h:\WissenMai2026\docs\adr\0003-document-read-api-before-retrieval.md)
