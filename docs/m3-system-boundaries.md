# Systemgrenzen vor M3

Stand: 2026-05-04

Dieses Dokument fixiert die fachlichen und technischen Systemgrenzen unmittelbar vor M3. Ziel ist, Scope Creep zu verhindern und M3 nur auf einer stabilen Import-, Versions-, Chunking- und Read-API-Basis aufzusetzen.

## In Scope

### Dokument-Import

Umfang:

- Upload und Parsing fuer `.txt`, `.md`, `.docx`, `.doc` und `.pdf`.
- kontrollierte Fehler fuer nicht unterstuetzte oder nicht lesbare Dateien.
- Normalisierung in kanonischen Markdown-Inhalt.

Begruendung:

- Ohne stabilen Import gibt es keine belastbare Textgrundlage fuer spaeteres Retrieval.
- M3 darf nicht auf instabilen oder impliziten Eingangsdaten aufbauen.

Risiko bei Verletzung:

- Jede Erweiterung im Importpfad, die fachlich schon Suche, OCR-Interpretation oder Ranking vorwegnimmt, verschiebt Fehlerbilder in einen spaeter schwerer testbaren Bereich.
- Retrieval-Probleme werden dann mit Parser- oder Ingest-Problemen vermischt.

### Versionierung

Umfang:

- Persistenz von `documents` und `document_versions`.
- konsistente `current_version_id`.
- nachvollziehbare Version-Historie pro Dokument.

Begruendung:

- M3 Retrieval braucht eine eindeutige kanonische Version pro Dokument.
- Ohne saubere Versionierung sind Zitate, Reindexing und Deduplizierung instabil.

Risiko bei Verletzung:

- Suche oder Chat koennen auf veraltete oder falsche Dokumentstaende zugreifen.
- spaetere Embedding- oder Retrieval-Indizes muessen bei Dateninkonsistenzen neu gedacht werden.

### Chunking

Umfang:

- deterministische Chunk-Erzeugung aus `normalized_markdown`.
- stabile Reihenfolge ueber `chunk_index`.
- normalisierte `source_anchor`-Metadaten.

Begruendung:

- Chunking ist die letzte Datenaufbereitung vor Retrieval.
- M3 darf nur auf stabilen, reproduzierbaren Chunk-Grenzen aufbauen.

Risiko bei Verletzung:

- Retrieval-Qualitaet wird spaeter durch schwankende oder semantisch instabile Chunks begrenzt.
- Ranking- oder Embedding-Probleme werden faelschlich im Retrieval-Layer gesucht, obwohl sie aus schlechtem Chunking stammen.

### Read-API

Umfang:

- `GET /documents`
- `GET /documents/{document_id}`
- `GET /documents/{document_id}/versions`
- `GET /documents/{document_id}/chunks`
- stabiles Fehlerformat und dokumentierte Zustandskonflikte.

Begruendung:

- M3 muss auf klar lesbaren und testbaren API- und Repository-Pfaden aufsetzen.
- Diese Endpunkte bilden den vertraglichen Lesezugriff auf Import-, Versions- und Chunk-Daten.

Risiko bei Verletzung:

- Suche oder Chat bauen auf unstabilen oder ad-hoc internen Datenzugriffen auf.
- Aenderungen an Datenmodell oder Retrieval werden unnoetig an HTTP-Vertrag, UI und spaetere Features gekoppelt.

## Out of Scope

### Suche

Nicht enthalten:

- Volltextsuche als Produktfunktion.
- Query Parsing, Filterlogik, Ergebnislisten oder Such-Endpoints.

Begruendung:

- M3 soll erst starten, wenn Import-, Versionierungs-, Chunking- und Read-Pfade stabil sind.
- Suche ist der erste Konsument dieser Grundlage, nicht Teil ihrer Definition.

Risiko bei Verletzung:

- Performance- oder Relevanzprobleme werden zu frueh optimiert.
- Schema-, Index- und API-Entscheidungen werden vorschnell auf Suchszenarien verengt.

### Ranking

Nicht enthalten:

- Relevanzbewertung.
- Score-Berechnung.
- Ergebnispriorisierung nach Retrieval-Regeln.

Begruendung:

- Ranking setzt voraus, dass Dokumente, Versionen und Chunks bereits fachlich korrekt und stabil sind.

Risiko bei Verletzung:

- Schlechte Datenqualitaet wird mit Ranking-Heuristiken maskiert statt behoben.
- Teams diskutieren Retrieval-Qualitaet, obwohl die Vorstufe noch nicht belastbar ist.

### Chat

Nicht enthalten:

- Chat-Use-Cases.
- Antwortgenerierung.
- Konversationslogik.
- Quellenpflicht fuer Antworttexte als Produktverhalten.

Begruendung:

- Chat ist ein nachgelagerter Verbraucher von Retrieval und darf nicht vor stabiler Daten- und Retrieval-Basis eingebaut werden.

Risiko bei Verletzung:

- Fehler in Import, Chunking oder spaeterem Retrieval erscheinen als "Chat-Probleme".
- Scope und Fehlersuche explodieren ueber Backend, Ranking, Prompting und UI gleichzeitig.

### Embeddings

Nicht enthalten:

- Embedding-Generierung.
- Vektorindizes.
- Embedding-Refresh und Reindexing.

Begruendung:

- Embeddings frieren Daten- und Chunk-Entscheidungen technisch ein.
- Vor M3 muessen diese Entscheidungen erst stabilisiert werden.

Risiko bei Verletzung:

- spaetere Aenderungen an Chunking oder Versionlogik ziehen kostspielige Reindexing-Arbeit nach sich.
- technische Komplexitaet steigt, bevor fachliche Grenzen sauber abgesichert sind.

### OCR

Nicht enthalten:

- OCR-Ausfuehrung fuer PDFs oder Bilder.
- OCR-Qualitaetsbewertung.
- OCR-Postprocessing.

Begruendung:

- OCR ist ein eigener Qualitaets- und Betriebsstrang.
- Vor M3 reicht es, OCR-Bedarf sichtbar zu machen, nicht ihn bereits auszufuehren.

Risiko bei Verletzung:

- Parser-, OCR- und Chunking-Qualitaet werden in einem Schritt vermischt.
- instabile Textextraktion verschlechtert Chunking und spaeter Retrieval ohne klare Fehlergrenze.

## Durchsetzungsregeln

### Architekturregeln

- M3-Vorarbeit darf nur `import`, `version`, `chunk` und `read`-Pfade aendern.
- Neue Endpoints sind nur zulaessig, wenn sie bestehende Read-API-Vertraege stabilisieren, nicht wenn sie bereits Suche, Ranking oder Chat vorwegnehmen.
- Neue Tabellen oder Spalten muessen Import-, Versions-, Chunk- oder Read-Zustaende direkt begruenden. Feature-Vorbereitung fuer Suche, Ranking, Chat oder Embeddings ist vor M3 nicht zulaessig.

### API-Regeln

- Kein Such-Endpoint.
- Kein Ranking- oder Score-Feld in API-Responses.
- Kein Chat-Endpoint.
- Kein Embedding-Status, keine Vektor-Metadaten, keine Retrieval-Scores in Dokument- oder Chunk-Responses.
- OCR darf nur als sichtbarer Status wie `OCR_REQUIRED` erscheinen, nicht als still ausgefuehrter Verarbeitungsschritt.

### Datenmodellregeln

- `normalized_markdown` bleibt die kanonische Textquelle.
- `document_versions` bleiben die einzige fachliche Versionsquelle.
- `document_chunks` bleiben die einzige fachliche Chunk-Quelle.
- Keine Vektor-, Ranking- oder Chat-spezifischen Persistenzfelder als Teil der M3-Vorarbeit.

### Test- und Review-Regeln

- Jede Aenderung vor M3 muss einer der vier In-Scope-Kategorien eindeutig zugeordnet werden: Import, Versionierung, Chunking oder Read-API.
- Jeder PR oder Task mit Such-, Ranking-, Chat-, Embedding- oder OCR-Implementierung ist vor M3 als Scope-Verletzung zu markieren, ausser es handelt sich ausschliesslich um explizite Nicht-Unterstuetzungs-, Fehler- oder Statuspfade.
- Fehlerbehebungen in Out-of-Scope-Bereichen sind nur zulaessig, wenn sie bestehendes Verhalten absichern, nicht erweitern.

### Produktregel fuer Entscheidungen

- Wenn eine Aenderung nicht klar die Stabilitaet von Import, Versionierung, Chunking oder Read-API verbessert, gehoert sie nicht in den M3-Vorbereitungsumfang.
- Wenn eine Aenderung eine Relevanzentscheidung trifft, gehoert sie zu Ranking oder Suche und ist vor M3 out of scope.
- Wenn eine Aenderung Nutzerantworten erzeugt oder beeinflusst, gehoert sie zu Chat und ist vor M3 out of scope.
- Wenn eine Aenderung Text neu aus nicht extrahierbarem Material gewinnt, gehoert sie zu OCR und ist vor M3 out of scope.

## Entscheidungscheck vor Umsetzung

Vor jeder Aenderung ist mit Ja oder Nein zu beantworten:

1. Stabilisiert die Aenderung direkt Import, Versionierung, Chunking oder Read-API?
2. Fuehrt die Aenderung keine Such-, Ranking-, Chat-, Embedding- oder OCR-Logik ein?
3. Bleibt die kanonische Textquelle weiter `normalized_markdown`?
4. Bleibt die API frei von Scores, Suchergebnissen und Antwortlogik?
5. Ist der Nutzen auch ohne spaetere Retrieval- oder Chat-Features unmittelbar vorhanden?

Wenn eine Frage mit Nein beantwortet wird, ist die Aenderung vor M3 ausserhalb der Systemgrenze.

Fuer Reviews und PR-Pruefungen ist zusaetzlich die kompakte Checkliste unter `docs/prompts/reviews/m3-scope-review-checklist.md` zu verwenden.