# Prompt 006 – Service-Layer Entkopplung

**Phase:** Paket 5 – API-Stabilität

## Prompt

Kontext:
Router darf keine Business-Logik enthalten.

Aufgabe:
- Router: nur Request/Response Mapping
- Service: Business-Logik
- Repository: DB-Zugriff optional
- Entferne DB-Zugriffe aus Routern
- Extrahiere:
  - get_documents()
  - get_document_detail()
  - get_versions()
  - get_chunks()

Ziel:
- Testbarkeit ohne FastAPI
- Austauschbarkeit der DB

Output:
- Refactored Struktur
- Beispiel-Funktion vollständig umgesetzt

