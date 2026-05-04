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
- `TEST_DATABASE_URL`: optionale PostgreSQL-Testdatenbank fuer echte Migrationstests.
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

## Import-Endpunkt

Der minimale Importpfad unterstuetzt TXT, Markdown und DOCX:

- `.txt`
- `.md`
- `.docx`

Endpunkt:

```text
POST /documents/import
```

Beispiel:

```bash
curl -F "file=@notes.md" http://127.0.0.1:8000/documents/import
```

Beispielantwort:

```json
{
  "document_id": "00000000-0000-0000-0000-000000000000",
  "version_id": "00000000-0000-0000-0000-000000000000",
  "title": "notes",
  "chunk_count": 3,
  "duplicate_status": "created"
}
```

Bei gleichem `content_hash` wird kein stilles Duplikat erzeugt. Die API gibt
`duplicate_status = "duplicate_existing"` und die bestehende Dokument-/Versionsreferenz zurueck.

Originaldateien werden nicht gespeichert. Persistiert werden Dokument-Metadaten, normalisierter
Markdown, Hashes und Chunks mit Quellenankern.

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

Aktueller M1-Migrationsstand:

- `20260430_0001_initial_document_schema.py`: Workspaces, Users, Documents, DocumentVersions.
- `20260430_0002_document_chunks.py`: versionierte Chunks mit Quellenankern.
- `20260430_0003_categories_tags.py`: Kategorien, Tags und additive DocumentTags.
- `20260430_0004_chat_analysis.py`: Chat- und Analyse-Grundtabellen.

Migration gegen eine konfigurierte PostgreSQL-Datenbank ausfuehren:

```bash
cd backend
alembic upgrade head
```

Aktuellen Stand pruefen:

```bash
cd backend
alembic current
```

## Testausfuehrung

```bash
cd backend
pytest
```

Die erste Testbasis prueft App-Import und Healthchecks. Lokale Tests benoetigen keine
PostgreSQL-Verbindung; fehlende DB-Konfiguration wird kontrolliert als Servicefehler erwartet.

Migrationstests ohne DB pruefen Alembic-Struktur und eindeutige Revisionen. Mit
`TEST_DATABASE_URL` wird ein echter Upgrade-/Downgrade-Lauf gegen PostgreSQL ausgefuehrt:

```bash
cd backend
$env:TEST_DATABASE_URL="postgresql+psycopg://user:password@host:5432/test_database"
pytest tests/integration/test_migrations.py
```

`TEST_DATABASE_URL` muss auf eine dedizierte Testdatenbank zeigen, da der Test auf `base`
downgradet und Tabellen entfernt.

Import-Integrationstests nutzen dieselbe Voraussetzung und pruefen `POST /documents/import` fuer
TXT/Markdown inklusive Dokumentversionen, Chunks und Duplikaterkennung:

```bash
cd backend
pytest tests/integration/test_documents_import.py
```

## V1-Grenzen

- Keine Authentifizierung.
- Mehrbenutzerfaehigkeit ist nur ueber Workspace-/User-Felder vorbereitet.
- Keine Vektorsuche.
- Keine Speicherung von Quelldateien ausserhalb abgeleiteter Inhalte und Metadaten.
