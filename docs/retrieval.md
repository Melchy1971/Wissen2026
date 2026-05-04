# Retrieval

Stand: 2026-05-04

Dieses Dokument ist der kurze Einstiegspunkt fuer den aktuellen Retrieval-Stand.

## Implementiert

- read-only Search API unter `/api/v1/search/chunks`
- PostgreSQL-FTS auf Chunk-Ebene
- Ranking-Baseline ueber `ts_rank`
- stabile Sortierung mit Tie-Breakern
- GUI-Suche auf der Dokumentuebersicht
- sichtbare Lade-, Leer- und Fehlerzustaende
- Failure-Mode-Matrix und minimales Evaluation-Dataset

## Nicht im Scope

- voll integrierte Chat-API
- voll integrierte LLM-Antwortgenerierung
- komplexes Re-Ranking
- semantische Suche / Embeddings

## Referenzen

- `docs/m3b-retrieval-foundation.md`
- `docs/m3b-retrieval-evaluation-dataset.md`
- `docs/rag-dataflow.md`
- `docs/chat-rag-api-contract.md`
- `docs/api.md`

## Abschlussstand

- Fachlicher Scope: weitgehend umgesetzt
- Harter Abschluss: noch offen
- Hauptgrund: fehlender echter PostgreSQL-Retrieval- und Ranking-Nachweis fuer den Query-Pfad
- Entscheidung fuer harten M3c-Chat/RAG-Abschluss: `No-Go`, bis Retrieval und Chat-API end-to-end belegt sind