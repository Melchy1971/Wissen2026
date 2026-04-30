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

## Neue und geaenderte Dateien in Paket 2

- `README.md`
- `backend/README.md`
- `backend/alembic.ini`
- `backend/app/api/README.md`
- `backend/app/api/health.py`
- `backend/app/core/config.py`
- `backend/app/core/database.py`
- `backend/app/db/connection.py`
- `backend/app/main.py`
- `backend/migrations/env.py`
- `backend/migrations/script.py.mako`
- `backend/migrations/versions/.gitkeep`
- `backend/requirements-dev.txt`
- `backend/requirements.txt`
- `backend/tests/README.md`
- `backend/tests/conftest.py`
- `backend/tests/test_health.py`
- `docs/prompts/README.md`
- `frontend/src/features/README.md`

## Offen

- M1 Datenmodell-Migrationen sind noch nicht erstellt.
- Workspace- und User-Felder sind vorbereitet, aber noch nicht als Datenbankschema versioniert.
- Echte Remote-PostgreSQL-Verbindung wurde lokal nicht verifiziert, weil keine Zugangsdaten im Repo liegen duerfen.
- ADR-Nummerierung ist doppelt belegt, da aeltere Kurzfassungen neben den ausfuehrlichen V1-ADRs existieren.

## Naechstes Paket

M1 Datenmodell-Migrationen.

Empfohlener Fokus:

- Ausgangsschema fuer Dokumente, Versionen und vorbereitete Workspace/User-Zuordnung definieren.
- Erste fachliche Alembic-Migration unter `backend/migrations/versions/` anlegen.
- Keine Authentifizierung und keine Vektorsuche einfuehren.
- Markdown als kanonische Textquelle und Nicht-Speicherung von Originaldateien im Schema beruecksichtigen.

## ADR-Startpunkte

- [Technische Grundentscheidung fuer V1](h:\WissenMai2026\docs\adr\0001-tech-stack-v1.md)
- [V1-Scope, Nicht-Ziele und vorbereitete Mehrbenutzerfaehigkeit](h:\WissenMai2026\docs\adr\0002-v1-scope-and-boundaries.md)
