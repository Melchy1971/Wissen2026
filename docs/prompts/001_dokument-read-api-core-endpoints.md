# Prompt 001 – Dokument-Read-API Core Endpoints

**Phase:** Paket 5 – API-Stabilität

## Prompt

Kontext:
FastAPI Backend mit bestehenden SQLAlchemy-Modellen für Document, DocumentVersion und Chunk.
Ziel ist eine stabile Read-Schicht für Dokumente ohne Business-Logik-Ausweitung.

Aufgabe:
Implementiere:
1. GET /documents
   - Pagination: limit default 20, offset
   - Filter: workspace_id required
   - Sortierung: created_at DESC
   - Response: id, title, created_at, updated_at, latest_version_id

2. GET /documents/{id}
   - Dokument-Metadaten plus latest_version
   - 404 wenn nicht vorhanden

3. GET /documents/{id}/versions
   - alle Versionen chronologisch DESC
   - Felder: id, version_number, created_at, content_hash

4. GET /documents/{id}/chunks
   - Chunks der latest_version
   - Felder: chunk_id, position, text_preview, source_anchor

Constraints:
- Keine Business-Logik außerhalb Service Layer
- Keine direkte DB-Nutzung im Router
- Pydantic Response Models strikt definieren
- Keine impliziten Lazy Loads
- N+1 vermeiden

Output:
- Router
- Service Layer
- Schemas

