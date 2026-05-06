# Prompt 005 – Test-Härtung

**Phase:** Paket 5 – API-Stabilität

## Prompt

Kontext:
Tests schlagen fehl wegen fehlender Dependencies.

Aufgabe:
1. requirements.txt / pyproject prüfen:
   - psycopg hinzufügen
   - optional asyncpg falls async stack

2. Test Setup:
   - separate Test DB
   - Fixtures für workspace, document, version, chunks

3. Tests:
   - GET /documents
   - GET /documents/{id}
   - Duplicate Insert
   - Chunk Retrieval

Ziel:
Tests laufen ohne manuelle Setup-Schritte.

Output:
- Dependency Fix
- pytest Setup
- Test Cases

