# Prompt 002 – Datenkonsistenz Duplicate Protection

**Phase:** Paket 5 – API-Stabilität

## Prompt

Kontext:
Dokumente werden über content_hash dedupliziert.
Aktuell besteht Race-Condition-Risiko, wenn Deduplizierung nur applikationsseitig erfolgt.

Aufgabe:
1. Alembic Migration:
   - Unique Constraint auf (workspace_id, content_hash)

2. Service Layer:
   - Insert-Konflikt abfangen
   - existierendes Dokument zurückgeben
   - kein Hard Fail

3. Fehlerbehandlung:
   - DB IntegrityError abfangen
   - deterministisches Verhalten garantieren

4. Tests:
   - parallele Inserts simulieren
   - Erwartung: nur ein Datensatz

Output:
- Alembic Migration
- Service Code
- Test Case

