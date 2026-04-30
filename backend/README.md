# Backend

FastAPI-Anwendung fuer Wissensbasis V1.

## Zweck

- API, Anwendungslogik und Persistenz liegen ausschliesslich im Backend.
- Alembic-Migrationen bleiben im Backend-Kontext.
- V1 bleibt Single-User ohne Authentifizierung.
- Datenmodelle bereiten `workspace_id`- und `owner_user_id`-Felder fuer spaetere Mehrmandantenfaehigkeit vor.
- Originaldateien werden nicht gespeichert; kanonische Inhaltsquelle ist extrahierter Markdown.

## Struktur

- `app/`: FastAPI-Code, Services, Modelle, Schemas und Jobs.
- `migrations/`: Alembic-Umgebung und Revisionsdateien.
- `tests/`: Backend-spezifische Unit- und Integrationstests.
- `requirements*.txt`, `pyproject.toml`, `alembic.ini`: Abhaengigkeiten und Tooling.

## V1-Grenzen

- Keine Authentifizierung.
- Keine Vektorsuche.
- Keine Speicherung von Quelldateien ausserhalb abgeleiteter Inhalte und Metadaten.