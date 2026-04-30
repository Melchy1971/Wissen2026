# ADR 0001: Tech-Stack V1

## Entscheidung

FastAPI, React/Vite, PostgreSQL und Alembic.

## Konsequenzen

- Backend-Migrationen liegen im Python-Kontext.
- SQL-direkter Zugriff bleibt erlaubt.
- Frontend bleibt lokal einfach betreibbar.
- Kein Auth-Code in V1.
