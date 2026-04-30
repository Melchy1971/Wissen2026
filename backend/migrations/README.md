# Alembic-Migrationen

Dieser Ordner gehoert bewusst zum Backend-Kontext.

## Zweck

- `env.py` konfiguriert die Alembic-Umgebung.
- `versions/` enthaelt schemaaendernde Revisionen.

## Leitplanken

- Migrationen muessen mit den Backend-Modellen konsistent bleiben.
- V1-Modelle sollen Felder fuer spaetere Workspace- und User-Zuordnung vorbereiten, ohne Authentifizierung zu aktivieren.