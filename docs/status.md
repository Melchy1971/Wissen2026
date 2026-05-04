# Projektstatus

Stand: 2026-05-04

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
- Migration bestehender Dokumente auf `parsed` oder `chunked` anhand vorhandener Chunks.
- Normalisierung von `document_chunks.metadata.source_anchor`.
- Bewahrung alter Source-Anchor-Daten in `metadata.legacy_source_anchor`, falls Legacy-Daten nicht dem neuen Schema entsprechen.

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

## Partial

- PostgreSQL-Integrationstests sind vorhanden, laufen aber nur mit gesetzter `TEST_DATABASE_URL`.
- PDF-Import erkennt OCR-Bedarf, besitzt aber keine OCR-Ausfuehrung.
- DOC-Import funktioniert nur, wenn LibreOffice lokal verfuegbar ist.
- Quellenanker sind API-seitig normalisiert, aber Parser liefern noch nicht fuer alle Formate vollstaendige `page`, `paragraph`, `char_start` und `char_end`-Werte.
- DOCX-Quellenanker sind als `docx_paragraph` typisiert, Paragraphenpositionen sind aber noch nicht durchgehend granular gefuellt.
- Mehrbenutzerfaehigkeit ist datenmodellseitig vorbereitet, aber ohne Authentifizierung, Rollen und Rechtepruefung.
- `updated_at` wird teilweise explizit gesetzt, aber nicht generell per DB-Trigger oder ORM-Event gepflegt.
- `/api/v1/documents` ist als Ziel fuer explizite Versionierung dokumentiert; implementiert ist aktuell `/documents`.
- Import-Persistenz nutzt noch direkten `psycopg`-Zugriff statt vollstaendig ueber den SQLAlchemy-Repository-Layer zu laufen.

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

## ADR-Startpunkte

- [Technische Grundentscheidung fuer V1](h:\WissenMai2026\docs\adr\0001-tech-stack-v1.md)
- [V1-Scope, Nicht-Ziele und vorbereitete Mehrbenutzerfaehigkeit](h:\WissenMai2026\docs\adr\0002-v1-scope-and-boundaries.md)
- [Dokument-Read-API und Datenkonsistenz vor Retrieval](h:\WissenMai2026\docs\adr\0003-document-read-api-before-retrieval.md)
