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

## Offen

- Die Migrationen wurden lokal per SQL-Rendering und Tests ohne DB geprueft; echte PostgreSQL-Ausfuehrung benoetigt `TEST_DATABASE_URL` oder `DATABASE_URL`.
- Mehrbenutzerfaehigkeit ist nur vorbereitet. Es gibt keine Authentifizierung, keine Rollen und keine Rechtepruefung.
- UUID-Erzeugung fuer neue Fachdaten muss spaeter durch Anwendung oder eine gesonderte DB-Strategie erfolgen.
- `updated_at` wird noch nicht automatisch per Trigger gepflegt.
- Konsistenzregeln fuer einige optionale Quellenbezuege muessen spaeter in Service-Logik oder gezielten Constraints geschaerft werden.
- ADR-Nummerierung ist doppelt belegt, da aeltere Kurzfassungen neben den ausfuehrlichen V1-ADRs existieren.

## Naechstes Paket

Paket 4 ist bereit.

Empfohlener Fokus:

- Backend-Zugriffsschicht und einfache Repository-/SQL-Helfer fuer das M1-Schema vorbereiten.
- Keine Importpipeline, keine Chatlogik und keine KI-Provider-Logik implementieren.
- Datenzugriffe weiterhin single-user-faehig halten und `workspace_id`/`owner_user_id` konsequent beruecksichtigen.

## ADR-Startpunkte

- [Technische Grundentscheidung fuer V1](h:\WissenMai2026\docs\adr\0001-tech-stack-v1.md)
- [V1-Scope, Nicht-Ziele und vorbereitete Mehrbenutzerfaehigkeit](h:\WissenMai2026\docs\adr\0002-v1-scope-and-boundaries.md)
