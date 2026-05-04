# Projektstatus

Stand: 2026-05-04

## Ground Truth = Code, nicht Dokumentation

Diese Datei beschreibt den aktuellen Stand nach bestem Abgleich mit dem Code.
Bei Widerspruechen gilt immer der Code als Ground Truth, nicht diese Dokumentation.

Vor Statusaenderungen sollen mindestens die betroffenen Module und Tests geprueft werden:

- Backend-Code unter `backend/app`
- Alembic-Migrationen unter `backend/migrations/versions`
- Tests unter `backend/tests`

## Implemented

### Backend-Grundlage

- FastAPI-App mit Healthchecks.
- Konfiguration ueber Umgebungsvariablen.
- Alembic-Setup im Backend-Kontext.
- pytest-Testbasis mit Unit- und optionalen PostgreSQL-Integrationstests.

### Datenmodell und Migrationen

- `workspaces` und `users` als vorbereitete Mehrbenutzer-Basis.
- `documents` und `document_versions` fuer versionierte Dokumente.
- `document_chunks` fuer chunkbasierte Weiterverarbeitung und Quellenanker.
- Kategorien, Tags und additive Tag-Zuordnung.
- Chat- und Analyse-Grundtabellen.
- Harte DB-Deduplizierung fuer Dokumentimporte ueber Unique Constraint auf `(workspace_id, content_hash)`.

Relevante Migrationen:

- `backend/migrations/versions/20260430_0001_initial_document_schema.py`
- `backend/migrations/versions/20260430_0002_document_chunks.py`
- `backend/migrations/versions/20260430_0003_categories_tags.py`
- `backend/migrations/versions/20260430_0004_chat_analysis.py`
- `backend/migrations/versions/20260504_0005_document_content_hash_unique.py`

### Import-Pipeline

- Import-Service fuer Parser-Auswahl, Normalisierung und Import-Ergebnis.
- Deterministischer Markdown-Normalizer ohne inhaltliche Interpretation.
- Chunking-Service fuer normalisierten Markdown.
- Persistenz-Service fuer Importergebnisse mit Dokument, Version und Chunks.
- Duplicate Handling im Service Layer:
  - Vorab-Pruefung auf vorhandenes Dokument.
  - DB-Unique-Constraint als harte Sicherung.
  - `IntegrityError` auf den Content-Hash-Constraint wird abgefangen.
  - Bei Konflikt wird deterministisch das bestehende Dokument zurueckgegeben.

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
  - Markiert OCR-Bedarf ueber `ocr_required`, fuehrt aber kein OCR aus.

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
  - Response mit `latest_version_id`

- `GET /documents/{document_id}`
  - Dokument-Metadaten plus `latest_version`
  - 404 bei nicht vorhandenem Dokument

- `GET /documents/{document_id}/versions`
  - Versionen chronologisch absteigend
  - Projektion auf API-Felder

- `GET /documents/{document_id}/chunks`
  - Nur Chunks der `latest_version`
  - Sortierung `position ASC`
  - Optionales `limit`
  - Projektion statt Full ORM Object
  - `text_preview` wird serverseitig erzeugt
  - `source_anchor` wird strukturiert als `anchor`, `page`, `paragraph`, `offset` ausgegeben, soweit Metadaten vorhanden sind.

## Partial

- PostgreSQL-Integrationstests sind vorhanden, laufen aber nur mit gesetzter `TEST_DATABASE_URL`.
- PDF-Import erkennt OCR-Bedarf, besitzt aber noch keine OCR-Ausfuehrung.
- DOC-Import funktioniert nur, wenn LibreOffice lokal verfuegbar ist.
- Parser-Metadaten sind vorhanden, aber Quellenpositionen sind nur teilweise strukturiert. Chunks koennen `page`, `paragraph` und `offset` aus Metadaten ausgeben, die aktuellen Parser fuellen diese Felder aber noch nicht konsistent.
- Mehrbenutzerfaehigkeit ist datenmodellseitig vorbereitet, aber ohne Authentifizierung, Rollen und Rechtepruefung.
- `updated_at` wird teilweise explizit gesetzt, aber nicht generell per DB-Trigger oder ORM-Event gepflegt.

## Missing

- OCR-Engine fuer gescannte PDFs oder Bilder.
- Authentifizierung und Autorisierung.
- Benutzer- und Workspace-Verwaltung als echte Produktfunktion.
- Vollstaendige Quellenpositions-Erfassung pro Chunk.
- Ranking, Suche, Chat- und Analyse-Fachlogik oberhalb der vorbereiteten Tabellen.
- Einheitliche Parser-Qualitaetsmetriken und Parser-Confidence.
- Produktionsreife Fehlerklassifikation fuer alle Importpfade.

## Known Limitations

- OCR fehlt. PDFs mit wenig oder keinem extrahierbaren Text werden nur mit `ocr_required=True` markiert.
- Parser-Qualitaet ist uneinheitlich:
  - TXT/MD sind robust, aber semantisch flach.
  - DOCX deckt grundlegende Paragraphen, Headings, Listen und Tabellen ab, aber nicht alle Word-Layout- und Formatierungsdetails.
  - PDF-Textextraktion haengt stark von der PDF-Struktur ab.
  - DOC haengt von LibreOffice und dessen Konvertierungsqualitaet ab.
- Duplicate Race Condition ist im aktuellen Code adressiert, setzt aber voraus, dass die Migration `20260504_0005_document_content_hash_unique.py` angewendet wurde.
- Integrationstests mit echter Datenbank werden ohne `TEST_DATABASE_URL` uebersprungen.
- ADR-Nummerierung ist historisch doppelt belegt, weil aeltere Kurzfassungen neben den ausfuehrlichen V1-ADRs existieren.

## Naechster sinnvoller Fokus

- OCR-Implementierung oder klare OCR-Auslagerungsentscheidung.
- Parser-Qualitaet und Quellenpositions-Metadaten verbessern.
- Read-API mit realen Integrationstests gegen PostgreSQL absichern.
- Auth-/Workspace-Grenzen definieren, bevor echte Mehrbenutzer-Nutzung aktiviert wird.

## ADR-Startpunkte

- [Technische Grundentscheidung fuer V1](h:\WissenMai2026\docs\adr\0001-tech-stack-v1.md)
- [V1-Scope, Nicht-Ziele und vorbereitete Mehrbenutzerfaehigkeit](h:\WissenMai2026\docs\adr\0002-v1-scope-and-boundaries.md)
