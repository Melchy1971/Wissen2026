# Prompt 003 – Chunk-Read-Optimierung

**Phase:** Paket 5 – API-Stabilität

## Prompt

Kontext:
Chunks existieren, werden aber potenziell ineffizient geladen.

Aufgabe:
- Query nur für latest_version
- ORDER BY position ASC
- optionales Limit
- Projection statt Full ORM Object
- text_preview serverseitig erzeugen
- source_anchor strukturiert zurückgeben

Output:
- optimierte Query
- Service Methode
- Response Schema

