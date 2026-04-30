# Backend-Tests

Tests fuer Backend-Verhalten, Migrationen und Integrationsgrenzen.

## Struktur

- `unit/`: Kleine, isolierte Tests fuer Services, Parser und Validierung.
- `integration/`: Tests ueber API-, DB- oder Servicegrenzen hinweg.

## Hinweis

- Testdaten sollen die V1-Regeln respektieren: Markdown als kanonische Quelle, keine Originaldateispeicherung, keine Auth-Pflicht.