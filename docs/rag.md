# RAG

Stand: 2026-05-04

Dieses Dokument ist der kurze Einstiegspunkt fuer den aktuellen Stand von Chat/RAG.

Es beschreibt den Stand der M3c Chat/RAG Foundation, nicht einen bereits integrierten Produkt-Chat im Sinne von M4.

## Implementiert

- RAG-Datenfluss ist dokumentiert.
- Chat/RAG-API-Vertrag ist dokumentiert.
- Context Builder ist implementiert.
- Prompt Builder ist implementiert.
- Citation Mapper ist implementiert.
- Insufficient-Context-Policy ist implementiert.
- Chat-Persistenz fuer Sessions, Messages und Citations ist implementiert.
- Chat-UI ist gegen den dokumentierten Vertrag implementiert.

## Noch nicht hart abgeschlossen

- stabile Backend-HTTP-Endpoints fuer `/api/v1/chat/...`
- end-to-end RAG-Antwortpfad ueber Retrieval -> Kontext -> Prompt -> Policy -> LLM -> Citations -> API
- API-Tests fuer Chat-Endpunkte
- echte Integrationsnachweise fuer den Chat/RAG-Flow

## Quellenlogik

- Keine erfolgreiche dokumentgestuetzte Antwort ohne Quellen.
- Citations muessen mindestens `chunk_id`, `document_id`, `document_title`, `source_anchor` und `quote_preview` enthalten.
- Insufficient-Context-Antworten duerfen keine freie Halluzinationsantwort erzeugen.

## Referenzen

- `docs/rag-dataflow.md`
- `docs/chat-rag-api-contract.md`
- `docs/retrieval.md`

## Abschlussstand

- Fachlicher Fortschritt: deutlich
- Harter Abschluss: noch offen
- Entscheidung fuer M4: `No-Go`

## Abgrenzung zu M4

- M3c liefert Bausteine, Persistenz und GUI-Vertrag.
- M4 beginnt erst mit einer stabilen Chat-HTTP-API und einem echten integrierten Antwortpfad.