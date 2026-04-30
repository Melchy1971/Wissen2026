# Backend-Tests

Tests fuer Backend-Verhalten, Migrationen und Integrationsgrenzen.

## Struktur

- `unit/`: Kleine, isolierte Tests fuer Services, Parser und Validierung.
- `integration/`: Tests ueber API-, DB- oder Servicegrenzen hinweg.

## Hinweis

- Testdaten sollen die V1-Regeln respektieren: Markdown als kanonische Quelle, keine Originaldateispeicherung, keine Auth-Pflicht.
- Lokale Tests duerfen keine remote PostgreSQL-Datenbank voraussetzen.
- DB-nahe Tests muessen fehlende Konfiguration kontrolliert behandeln oder explizit uebersprungen werden.

## Ausfuehrung

```bash
cd backend
pytest
```

## Migrationstests

Die Strukturtests fuer Alembic laufen ohne Datenbank. Der echte Upgrade-/Downgrade-Test wird nur
ausgefuehrt, wenn `TEST_DATABASE_URL` gesetzt ist:

```bash
cd backend
$env:TEST_DATABASE_URL="postgresql+psycopg://user:password@host:5432/test_database"
pytest tests/integration/test_migrations.py
```

`TEST_DATABASE_URL` muss auf eine dedizierte PostgreSQL-Testdatenbank zeigen. Der Integrationstest
setzt die Migrationen auf `base` zurueck, migriert auf `head`, prueft Defaultdaten und Constraints
und fuehrt anschliessend wieder ein Downgrade auf `base` aus. Die URL wird im Test nicht ausgegeben.

Der optionale Import-Integrationstest nutzt dieselbe Voraussetzung und prueft `POST /documents/import`
fuer TXT/Markdown inklusive Dokumentversionen, Chunks und Duplikaterkennung. Auch dieser Test setzt
die Testdatenbank zurueck.
