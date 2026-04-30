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
- `app/api/health.py`: Minimaler Healthcheck ohne Fachlogik.
- `app/core/config.py`: Konfiguration ueber Umgebungsvariablen.
- `app/core/database.py`: PostgreSQL-Verbindungspruefung fuer Betrieb und Healthcheck.
- `migrations/`: Alembic-Umgebung und Revisionsdateien.
- `tests/`: Backend-spezifische Unit- und Integrationstests.
- `requirements*.txt`, `pyproject.toml`, `alembic.ini`: Abhaengigkeiten und Tooling.

## Lokale Installation

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
```

Relevante Umgebungsvariablen:

- `APP_ENV`: optionale Umgebung, Default `local`.
- `DATABASE_URL`: PostgreSQL-URL fuer Remote-DB, erforderlich fuer `/health/db` und Alembic.
- `DEFAULT_WORKSPACE_ID`: vorbereitete Workspace-ID fuer V1.
- `DEFAULT_USER_ID`: vorbereitete User-ID fuer V1.

## FastAPI-Start

```bash
cd backend
uvicorn app.main:app --reload
```

`GET /health` funktioniert ohne Datenbankkonfiguration. `GET /health/db` erwartet `DATABASE_URL`
fuer eine remote erreichbare PostgreSQL-Datenbank und gibt bei fehlender Konfiguration keinen
geheimen Verbindungsstring aus.

## Alembic

Migrationen liegen im Backend unter `migrations/` und verwenden dieselbe `DATABASE_URL` wie die
FastAPI-Anwendung. Die URL wird nicht in `alembic.ini` gespeichert.

```bash
cd backend
alembic current
alembic upgrade head
alembic revision -m "describe change"
```

Autogeneration ist nicht vorausgesetzt. SQL-nahe Migrationen koennen in den generierten Dateien
unter `migrations/versions/` manuell mit `op.execute(...)` oder Alembic-Operationen gepflegt werden.

## Testausfuehrung

```bash
cd backend
pytest
```

Die erste Testbasis prueft App-Import und Healthchecks. Lokale Tests benoetigen keine
PostgreSQL-Verbindung; fehlende DB-Konfiguration wird kontrolliert als Servicefehler erwartet.

## V1-Grenzen

- Keine Authentifizierung.
- Keine Vektorsuche.
- Keine Speicherung von Quelldateien ausserhalb abgeleiteter Inhalte und Metadaten.
