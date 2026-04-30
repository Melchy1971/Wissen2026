# Wissensbasis V1

Produktionsnahe Startstruktur fuer eine lokale/remote-faehige Wissensbasis.

## Stack

- Backend: FastAPI
- Frontend: React/Vite
- Datenbank: PostgreSQL remote, lokal testbar
- Migrationen: Alembic im Backend-Kontext
- Auth: nicht in V1
- Persistenz: extrahierter Markdown, Metadaten, Versionen, Chunks, Tags

## Start

```bash
cp .env.example .env
cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt
cd ../frontend && npm install
```
