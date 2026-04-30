# Projektstatus

## Abgeschlossen

Paket 1 ist abgeschlossen.

- Repo-Struktur geprueft und dokumentarisch geschaerft.
- Tech-Stack-ADR fuer V1 erstellt.
- V1-Scope-ADR fuer Grenzen, Nicht-Ziele und vorbereitete Mehrbenutzerfaehigkeit erstellt.

Paket 2 ist abgeschlossen.

- FastAPI Backend-Grundgeruest erstellt.
- Konfiguration ueber Umgebungsvariablen vorbereitet.
- Healthchecks fuer App und DB-Verbindung ergaenzt.
- Alembic im Backend-Kontext initialisiert.
- Minimale pytest-Testbasis fuer Healthchecks angelegt.

Paket 3 ist abgeschlossen.

- Initiale M1-Datenbankmigrationen erstellt.
- `workspaces` und `users` fuer spaetere Mehrbenutzerfaehigkeit vorbereitet.
- Dokumentbasis mit `documents` und `document_versions` versioniert.
- `document_chunks` mit zitierfaehigen Quellenankern ergaenzt.
- Kategorien, Tags und additive Tag-Zuordnung modelliert.
- Chat- und Analyse-Grundtabellen fuer spaetere Funktionen vorbereitet.
- Migrationstests fuer Struktur, Revisionen und optionale PostgreSQL-Testdatenbank ergaenzt.

Paket 4 ist abgeschlossen.

- Import-Service-Schnittstellen fuer Parser, OCR, KI-Provider und Normalisierung definiert.
- TXT- und Markdown-Parser als minimaler vertikaler Importpfad implementiert.
- Deterministischer Markdown-Normalizer ohne inhaltliche Interpretation implementiert.
- Chunking-Service mit Quellenankern fuer normalisierten Markdown implementiert.
- Minimaler Import-Endpunkt `POST /documents/import` fuer `.txt` und `.md` ergaenzt.
- Persistenz fuer Dokument, Dokumentversion und Chunks im Importpfad umgesetzt.

## Neue Migrationen in Paket 3

- `backend/migrations/versions/20260430_0001_initial_document_schema.py`
- `backend/migrations/versions/20260430_0002_document_chunks.py`
- `backend/migrations/versions/20260430_0003_categories_tags.py`
- `backend/migrations/versions/20260430_0004_chat_analysis.py`

## Weitere neue und geaenderte Dateien in Paket 3

- `backend/alembic.ini`
- `backend/tests/README.md`
- `backend/tests/integration/test_migrations.py`
- `docs/data-model.md`
- `docs/status.md`
- `backend/README.md`

## Neue und geaenderte Module in Paket 4

- `backend/app/api/documents.py`
- `backend/app/main.py`
- `backend/app/models/import_models.py`
- `backend/app/services/chunking_service.py`
- `backend/app/services/import_service.py`
- `backend/app/services/ki_provider.py`
- `backend/app/services/markdown_normalizer.py`
- `backend/app/services/ocr_service.py`
- `backend/app/services/parser_service.py`
- `backend/app/services/README.md`
- `backend/requirements.txt`
- `backend/tests/integration/test_documents_import.py`
- `backend/tests/test_documents_import_api.py`
- `backend/tests/unit/test_chunking_service.py`
- `backend/tests/unit/test_markdown_normalizer.py`
- `backend/tests/unit/test_text_markdown_parsers.py`
- `backend/tests/README.md`
- `docs/import-pipeline.md`
- `docs/data-model.md`
- `docs/status.md`

## Offen

- Die Migrationen wurden lokal per SQL-Rendering und Tests ohne DB geprueft; echte PostgreSQL-Ausfuehrung benoetigt `TEST_DATABASE_URL` oder `DATABASE_URL`.
- Mehrbenutzerfaehigkeit ist nur vorbereitet. Es gibt keine Authentifizierung, keine Rollen und keine Rechtepruefung.
- UUID-Erzeugung fuer neue Fachdaten muss spaeter durch Anwendung oder eine gesonderte DB-Strategie erfolgen.
- `updated_at` wird noch nicht automatisch per Trigger gepflegt.
- Konsistenzregeln fuer einige optionale Quellenbezuege muessen spaeter in Service-Logik oder gezielten Constraints geschaerft werden.
- Import unterstuetzt aktuell nur `.txt` und `.md`; DOCX, PDF und OCR sind vorbereitet, aber nicht implementiert.
- Duplikaterkennung im Importpfad ist aktuell app-seitig ueber `content_hash`, nicht per DB-Unique-Constraint abgesichert.
- Import-Integrationstests gegen PostgreSQL laufen nur mit `TEST_DATABASE_URL`.
- ADR-Nummerierung ist doppelt belegt, da aeltere Kurzfassungen neben den ausfuehrlichen V1-ADRs existieren.

## Naechstes Paket

Paket 5 ist bereit.

Empfohlener Fokus:

- Dokumentlisten- und Detail-API fuer importierte Dokumente vorbereiten.
- Chunks und Quellenanker lesbar machen, ohne Chat- oder Rankinglogik einzufuehren.
- Duplikat- und Fehlerverhalten weiter schaerfen.

## ADR-Startpunkte

- [Technische Grundentscheidung fuer V1](h:\WissenMai2026\docs\adr\0001-tech-stack-v1.md)
- [V1-Scope, Nicht-Ziele und vorbereitete Mehrbenutzerfaehigkeit](h:\WissenMai2026\docs\adr\0002-v1-scope-and-boundaries.md)
