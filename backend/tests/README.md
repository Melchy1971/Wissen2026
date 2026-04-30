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
