# Projektstatus

Stand: 2026-05-04

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

Stand des Abgleichs mit Code, Backend-Tests, Frontend-Tests und Build am 2026-05-04:

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

Noch offene Luecken vor hartem Abschluss:

- Es gibt aktuell API-Tests und Service-Tests, aber keinen belastbaren PostgreSQL-Retrieval-Integrationstest fuer echte Suchtreffer ueber `/api/v1/search/chunks`.
- Die Ranking-Baseline ist implementiert, aber nicht durch einen echten Ranking-Regressionstest mit Trefferreihenfolge abgesichert.
- Der dokumentierte Suchvertrag und die Implementierung sind jetzt grob synchronisiert, aber die Search-API ist noch nicht in einem eigenstaendigen stabilen API-Contract analog zum Dokumentvertrag formalisiert.

Abschlussbewertung:

- Score: `88/100`
- Entscheidung fuer M3b: `teilweise abgeschlossen`, aber noch kein harter Abschluss.
- Go fuer M3c Chat/RAG: `No-Go`

Begruendung:

- Der fachliche Scope von M3b ist weitgehend geliefert.
- Die harten Abschlusskriterien scheitern derzeit nicht an der GUI oder an der Indexmigration, sondern an fehlendem End-to-End-Nachweis fuer Suchqualitaet und Ranking-Stabilitaet auf dem PostgreSQL-Zielpfad.
- Ohne diesen Nachweis wuerde M3c Chat/RAG auf einem noch nicht ausreichend abgesicherten Retrieval-Fundament aufsetzen.

## M3c Chat/RAG Foundation

Stand des Abgleichs mit Code, fokussierten Backend-Tests, Frontend-Tests und Build am 2026-05-04:

- Chat-Persistenz fuer `chat_sessions`, `chat_messages` und `chat_citations` ist als Datenmodell, Migration und Service angelegt.
- Context Builder ist implementiert.
- Prompt Builder ist implementiert.
- Citation Mapper ist implementiert.
- Insufficient-Context-Policy ist implementiert.
- Chat-UI mit Sessionliste, neuer Session, Nachrichtenverlauf, Frageformular, Antwortanzeige, Quellenanzeige und Insufficient-Context-Zustand ist implementiert.
- Der Frontend-API-Client ist auf den dokumentierten Chat-Vertrag `/api/v1/chat/...` ausgerichtet.

Nicht oder nicht hart abgeschlossen:

- Es gibt noch keinen verifizierten Backend-HTTP-Pfad fuer:
  - `POST /api/v1/chat/sessions`
  - `GET /api/v1/chat/sessions`
  - `GET /api/v1/chat/sessions/{id}`
  - `POST /api/v1/chat/sessions/{id}/messages`
- Es gibt noch keinen end-to-end verdrahteten RAG-Antwortservice, der Retrieval, Context Builder, Prompt Builder, Policy, LLM-Aufruf und Citation Mapping ueber einen echten API-Pfad zusammensetzt.
- Eine stabile Retrieval-Integration fuer Chat ist damit noch nicht praktisch nachgewiesen.

Scope-Pruefung:

- Chat Sessions: teilweise vorhanden, aber nur als Persistenzservice und GUI-Vertrag, nicht als harter API-Nachweis.
- Message API: noch nicht implementiert oder verifiziert.
- Retrieval Integration: Bausteine vorhanden, aber kein vollstaendiger API-Flow.
- Context Builder: implementiert und getestet.
- Prompt Builder: implementiert und getestet.
- Citation Mapper: implementiert und getestet.
- GUI Chat: implementiert und getestet.

Nicht-Scope-Pruefung:

- keine Agenten: eingehalten.
- keine Tool-Nutzung im Produktflow: eingehalten.
- kein automatisches Bearbeiten von Dokumenten: eingehalten.

Test-Pruefung:

- Unit-Tests fuer Context Builder, Prompt Builder, Citation Mapper und Insufficient-Context-Policy: vorhanden.
- Persistenztests fuer Chat-Sessions, Messages und Citations: vorhanden.
- GUI-Tests fuer ChatPage: vorhanden.
- API-Tests fuer Chat-Endpoints: fehlen.
- End-to-End-RAG-Pipeline-Tests ueber echten Antwortpfad: fehlen.

Abschlussbewertung:

- Score: `74/100`
- Entscheidung fuer M3c: `teilweise abgeschlossen`, aber nicht hart abgeschlossen.
- Go fuer M4: `No-Go`

Begruendung:

- Die M3c-Bausteine und die Chat-GUI sind fachlich weit vorangekommen.
- Der Meilenstein scheitert derzeit nicht an UI oder Hilfsdiensten, sondern an der fehlenden stabilen Chat-API und am fehlenden end-to-end RAG-Nachweis.
- Ohne diesen Nachweis waere M4 auf ein noch nicht belastbar integriertes Chat/RAG-Fundament aufgesetzt.

## M4 Integrierter Wissensbasis-Chat

Stand des Abgleichs mit Code und Dokumentation am 2026-05-04:

- M4 ist noch nicht implementiert.
- Die dafuer benoetigte M3c-Foundation ist nur teilweise abgeschlossen.

Fehlende Integrationsbausteine vor echtem M4-Start:

- stabile Chat-HTTP-API im Backend
- verdrahteter produktiver Antwortpfad ueber Retrieval, Policy, Prompting, LLM und Citation Mapping
- API- und Integrationsnachweise fuer diesen Antwortpfad

Entscheidung:

- Status fuer M4: `missing`
- Startfreigabe: `No-Go`

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
- Der aktuelle verifizierte Standardlauf ist `42 passed, 1 skipped`; der Skip betrifft den optionalen PostgreSQL-Pfad ohne gesetzte Test-DB im Standardlauf.
- Der echte PostgreSQL-Integrationslauf mit gesetzter Test-DB ist gruen: `6 passed`.
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
- Ranking, Suche, Chat- und Analyse-Fachlogik oberhalb der vorbereiteten Tabellen.
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
- Der PostgreSQL-End-to-End-Nachweis ist erfolgt.
- Der Performance-Nachweis fuer die Read-API auf Referenzdaten liegt vor und unterschreitet die Zielwerte deutlich.

Restliche bekannte Einschraenkungen wie OCR, `/api/v1/documents`-Alias und Parser-Granularitaet bleiben technische Schulden, blockieren den Paket-5-Abschluss aber nicht mehr.

## ADR-Startpunkte

- [Technische Grundentscheidung fuer V1](h:\WissenMai2026\docs\adr\0001-tech-stack-v1.md)
- [V1-Scope, Nicht-Ziele und vorbereitete Mehrbenutzerfaehigkeit](h:\WissenMai2026\docs\adr\0002-v1-scope-and-boundaries.md)
- [Dokument-Read-API und Datenkonsistenz vor Retrieval](h:\WissenMai2026\docs\adr\0003-document-read-api-before-retrieval.md)
