# M3 Scope Review Checklist

Diese Checkliste dient dazu, Aenderungen vor M3 gegen die festgelegten Systemgrenzen zu pruefen.

## Pflichtfragen

Jede Frage muss mit `Ja` beantwortet werden. Ein `Nein` bedeutet Scope-Verletzung oder Eskalationsbedarf.

1. Verbessert die Aenderung direkt Import, Versionierung, Chunking oder Read-API?
2. Fuehrt die Aenderung keine Such-, Ranking-, Chat-, Embedding- oder OCR-Logik ein?
3. Bleibt `normalized_markdown` die kanonische Textquelle?
4. Bleiben `document_versions` die einzige fachliche Versionsquelle und `document_chunks` die einzige fachliche Chunk-Quelle?
5. Bleibt die API frei von Such-Endpoints, Score-Feldern, Chat-Endpoints und Embedding-Metadaten?
6. Bleibt OCR auf sichtbare Status- oder Fehlerpfade begrenzt und wird nicht still ausgefuehrt?
7. Fuehrt die Aenderung keine neuen Tabellen oder Spalten ein, die primaer Suche, Ranking, Chat oder Embeddings vorbereiten?
8. Ist der Nutzen der Aenderung auch ohne spaeteres Retrieval oder Chat unmittelbar gegeben?

## Review-Entscheidung

- `Freigabe`: Alle Pflichtfragen sind `Ja`.
- `Blockiert`: Mindestens eine Pflichtfrage ist `Nein`.
- `Eskalation erforderlich`: Die Aenderung liegt zwischen Stabilisierung und Feature-Vorwegnahme und braucht explizite Scope-Entscheidung.

## Typische Scope-Verletzungen

- neuer Such-Endpoint oder Query-Parsing vor M3
- Score-, Ranking- oder Relevanzfelder in API-Responses
- Embedding-Erzeugung, Vektorindex oder Reindexing-Pfade
- Chat- oder Antwortlogik auf Basis von Dokumentdaten
- OCR-Ausfuehrung statt reinem `OCR_REQUIRED`-Status
- Datenmodell-Erweiterungen, die primaer spaetere Retrieval- oder Chat-Funktionen vorbereiten

## Zulassige Ausnahmen

- explizite Fehler- oder Statuspfade, die Out-of-Scope-Funktionen sichtbar als nicht implementiert markieren
- Bugfixes in bestehenden Randbereichen, sofern sie keine neue Fachlogik einfuehren
- Refactorings ohne neue Produktfunktion und ohne Aufweichung der Systemgrenzen