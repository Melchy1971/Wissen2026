# M3b - Retrieval Foundation

Stand: 2026-05-04

Kontext:

- Paket 5 liefert stabile Read-Pfade fuer Dokumente, Versionen und Chunks.
- M3a hat die read-only GUI-Grundlage geschaffen.
- M3b fuehrt die erste Such- und Retrieval-Basis auf Chunk-Ebene ein.

## 1. Zielbild

M3b schafft eine belastbare Retrieval-Grundlage auf Chunk-Ebene, ohne bereits Chat, LLM-Antworten oder semantische Suche einzufuehren.

Das Zielbild fuer M3b ist:

- Nutzer koennen ueber Chunk-Inhalte eine Volltextsuche ausfuehren.
- Suchergebnisse zeigen immer den Dokumentbezug mit Dokument-ID, Titel, Version und Chunk.
- Jedes Ergebnis enthaelt einen normalisierten Quellenanker.
- Ergebnisse sind mindestens nach einer nachvollziehbaren Ranking-Baseline sortiert.
- Die Query API ist auf den Retrieval-Anwendungsfall zugeschnitten und strikt read-only.
- Die Suche ist auf `workspace_id` begrenzbar.

Nicht Ziel von M3b ist es, bereits semantische oder generative Antwortqualitaet zu liefern. M3b definiert die erste robuste technische und fachliche Retrieval-Stufe.

## 2. API-Endpunkte

### Neuer Endpunkt

- Implementierter Pfad: `GET /api/v1/search/chunks`

Zweck:

- Volltextsuche ueber Chunks des aktuellen, lesbaren Dokumentbestands.

Query Parameter:

| Name | Typ | Required | Default | Regeln |
|---|---:|---:|---:|---|
| `workspace_id` | string | ja | - | nicht leer |
| `q` | string | ja | - | nicht leer |
| `limit` | integer | nein | `20` | `1..100` |
| `offset` | integer | nein | `0` | `>= 0` |

Antwortschema `200`:

```json
[
  {
    "document_id": "doc-1",
    "document_title": "Titel",
    "document_created_at": "2026-05-01T10:00:00Z",
    "document_version_id": "ver-1",
    "version_number": 2,
    "chunk_id": "chunk-7",
    "position": 6,
    "text_preview": "...",
    "source_anchor": {
      "type": "text",
      "page": null,
      "paragraph": null,
      "char_start": 120,
      "char_end": 240
    },
    "rank": 0.74,
    "filters": {}
  }
]
```

Fehler:

| Status | Code | Bedeutung |
|---:|---|---|
| `422` | `WORKSPACE_REQUIRED` | `workspace_id` fehlt oder ist leer |
| `422` | `INVALID_QUERY` | `q` fehlt, ist leer oder ungueltig |
| `422` | `INVALID_PAGINATION` | `limit` oder `offset` sind ungueltig |
| `503` | `SERVICE_UNAVAILABLE` | DB oder Suchfunktion nicht verfuegbar |

### API-Regeln

- Ergebnisse liefern keine generierten Zusammenfassungen.
- Ergebnisse liefern keinen LLM-Output.
- `rank` ist eine technische Ranking-Baseline, kein semantischer Relevanzbeweis.
- Responses bleiben read-only und enthalten nur Retrieval-relevante Felder.
- `document_created_at` ist ein auslieferbares Hilfsfeld fuer stabile Sortierung und UI-nahe Anzeige, nicht fuer semantische Interpretation.

## 3. Ranking-Strategie

M3b verwendet eine einfache, nachvollziehbare Ranking-Baseline.

Baseline:

- PostgreSQL-Fulltext-Suche ueber Chunk-Inhalte.
- Ranking ueber `ts_rank` oder eine vergleichbare native Volltext-Rangfunktion.
- Primaere Sortierung nach `rank DESC`.
- Sekundaere Sortierung fuer Stabilitaet:
  - `documents.created_at DESC`
  - `document_chunks.chunk_index ASC`

Ranking-Ziele:

- reproduzierbare Reihenfolge bei gleicher Query
- robuste technische Grundlage fuer spaeteres Re-Ranking
- keine verdeckte Heuristik, die Datenqualitaetsprobleme maskiert

Explizit nicht enthalten:

- komplexes Re-Ranking
- Cross-Encoder oder LLM-basiertes Ranking
- Embedding-basierte semantische Aehnlichkeit, solange Embeddings nicht stabil eingefuehrt sind

## 4. Datenmodelländerungen

M3b soll moeglichst wenig neue fachliche Komplexitaet einbringen.

Bevorzugte Aenderungen:

- Erweiterung der Suchfaehigkeit auf Basis bestehender `document_chunks`.
- PostgreSQL-spezifischer Volltextindex auf Chunk-Inhalt.
- Optional materialisierte Suchspalte oder generierter TSVECTOR-Ausdruck fuer Chunk-Content.

Minimal notwendige technische Aenderungen:

- Index oder Suchvektor fuer `document_chunks.content`.
- Query-Pfad, der nur lesbare Dokumente durchsucht.
- Ausschluss nicht lesbarer Stati wie `failed`, `pending` oder OCR-pflichtiger Fehlerzustaende.

Explizit nicht vorgesehen:

- neue Embedding-Tabellen
- Vektorindizes
- Chat- oder Antworttabellen
- Zusammenfassungs- oder Cachetabellen fuer LLM-Antworten

## 4a. Search-Index-Strategie

### Bewertete Optionen

| Option | Implementierungsaufwand | Skalierbarkeit | Ranking-Qualitaet | Migrationsrisiko | Kompatibilitaet mit bestehendem Datenmodell |
|---|---|---|---|---|---|
| PostgreSQL Full Text Search | mittel | gut fuer M3b-Zielgroesse | gut fuer keyword-basierte Baseline | niedrig bis mittel | sehr hoch |
| SQLite FTS5 fuer lokale Entwicklung | mittel bis hoch, weil zweiter Suchpfad | begrenzt | ausreichend lokal, aber nicht zielsystemgleich | mittel bis hoch | mittel |
| spaeterer Wechsel auf Vektorindex | hoch | hoch fuer semantische Suche | spaeter potenziell hoch | hoch, wenn zu frueh eingefuehrt | aktuell bewusst niedrig |

### Entscheidung

M3b startet mit **PostgreSQL Full Text Search**.

Begruendung:

- PostgreSQL ist bereits das Zielsystem des Produkts.
- Das bestehende Datenmodell mit `documents`, `document_versions` und `document_chunks` passt direkt auf einen chunk-basierten Volltextpfad.
- Die Ranking-Baseline fuer M3b ist keyword- und phrase-orientiert; dafuer ist PostgreSQL FTS ausreichend und betrieblich einfacher als ein frueher Vektorpfad.
- Embeddings bleiben explizit eine spaetere Erweiterung und werden in M3b nicht vorgezogen.

SQLite FTS5 wird fuer M3b **nicht** als gleichwertiger Produktpfad eingefuehrt. Lokale Entwicklung kann weiterhin ueber vereinfachte Tests, Mocking oder begrenzte Fallback-Validierung laufen, ohne einen zweiten vollwertigen Suchstack zu etablieren.

### Datenmodelländerungen

Empfohlene technische Erweiterung fuer M3b:

- PostgreSQL-spezifische Suchspalte `search_vector` auf `document_chunks` oder generierter TSVECTOR-Ausdruck auf Basis von `content`.
- Optionaler Titelbezug aus `documents.title` im Suchquery selbst, nicht zwingend als persistierter Doppelspeicher.
- Keine Aenderung am kanonischen Inhaltsmodell: `document_versions.normalized_markdown` bleibt Textquelle, `document_chunks` bleibt Retrieval-Einheit.

### Indizes

Empfohlene Indexstrategie:

- `GIN`-Index auf `document_chunks.search_vector`
  - wenn `search_vector` materialisiert wird
- alternativ funktionaler `GIN`-Index auf `to_tsvector('simple', content)`
  - wenn keine persistierte Suchspalte eingefuehrt wird
- bestehende B-Tree-Indizes bleiben fuer Join-, Filter- und Ordnungszwecke relevant:
  - `documents(workspace_id, created_at DESC)`
  - `document_versions(document_id, created_at DESC)`
  - `document_chunks(document_id, document_version_id, chunk_index)`

Index-Rollen:

- GIN fuer Textsuche und Kandidatenselektion
- bestehende B-Tree-Indizes fuer Workspace-Filter, aktuelle Version, Reihenfolge und stabile Tie-Breaker

### Migration

Empfohlene Migrationsreihenfolge:

1. Alembic-Migration fuer `search_vector` oder funktionalen FTS-Index anlegen.
2. Backfill fuer bestehende Chunks aus `document_chunks.content` ausfuehren, falls materialisierte Suchspalte verwendet wird.
3. Trigger oder Update-Strategie definieren, damit neue oder geaenderte Chunks den Suchvektor konsistent halten.
4. PostgreSQL-Integrations- und EXPLAIN-Tests hinzufuegen.
5. Query API erst nach gruener DB-Validierung freigeben.

Praeferenz fuer M3b:

- Wenn der Wartungsaufwand niedrig bleiben soll, zuerst **funktionaler GIN-Index ohne neue persistierte Spalte**.
- Wenn spaeter haeufigere Ranking-Erweiterungen oder gewichtete Felder geplant sind, **materialisierte `search_vector`-Spalte** als kontrollierter naechster Schritt.

### Risiken

- PostgreSQL FTS loest keine semantische Suche; Synonyme und paraphrasierte Treffer bleiben begrenzt.
- SQLite FTS5 als zweiter Suchstack wuerde Verhalten zwischen lokalem und Zielsystem auseinanderziehen.
- Eine persistierte `search_vector`-Spalte erhoeht Pflegeaufwand bei Inserts und spaeteren Rechunking-Vorgaengen.
- Ein frueher Wechsel auf Vektorindex wuerde Chunking-, Reindexing- und Betriebsfragen zu frueh in M3b hineinziehen.
- Titel-Treffer als Ranking-Signal muessen sauber in der Query gewichtet werden, ohne redundante Datenspeicherung zu erzwingen.

## 4b. Failure Mode Matrix

Die folgende Matrix beschreibt die wichtigsten Ausfall- und Grenzfaelle fuer die M3b-Suche sowie das erwartete Verhalten in API und GUI.

| Fall | Ursache | Risiko | Erwartetes API-Verhalten | Erwartetes GUI-Verhalten | Mitigation |
|---|---|---|---|---|---|
| Query zu kurz | `q` enthaelt nur 1-2 Zeichen oder unterschreitet eine definierte Mindestlaenge fuer sinnvolle Volltextsuche. | Unnötige Last, sehr rauschige Treffer, inkonsistente Nutzererwartung. | `422 INVALID_QUERY` mit klarer Meldung, dass die Suchanfrage zu kurz ist. Keine Suchausfuehrung gegen den Index. | Inline oder als Fehlerzustand sichtbar: `Ungueltige Suche`. Vorhandene Dokumentliste bleibt sichtbar, es werden keine veralteten Treffer weiterverwendet. | Mindestlaenge serverseitig validieren, gleiche Regel optional clientseitig vorvalidieren, Testfall fuer kuerze Queries. |
| Query enthaelt nur Stopwords | `plainto_tsquery` oder verwendete Konfiguration reduziert die Query auf leere oder praktisch bedeutungslose Tokens. | Nutzer bekommt scheinbar kaputte Suche oder leere Antwort ohne Erklaerung. | Bevorzugt `422 INVALID_QUERY`, wenn die normalisierte Query keine suchbaren Tokens mehr enthaelt. Alternativ nur `200 []`, wenn die DB das nicht sauber vorvalidierbar liefert; dann muss das Verhalten dokumentiert bleiben. | GUI zeigt `Ungueltige Suche` oder einen erklaerenden Leerzustand wie `Die Suchanfrage enthaelt keine auswertbaren Begriffe`. Keine generische Fehlermeldung ohne Kontext. | Query-Normalisierung vor DB-Call pruefen, Stopword-only-Testfaelle anlegen, dokumentieren welche Textsuche-Konfiguration gilt. |
| keine Treffer | Query ist gueltig, aber kein lesbarer Chunk im Workspace matcht. | Nutzer verwechselt leere Ergebnismenge mit technischem Fehler. | `200` mit leerem Array. Kein Fehlerstatus. Pagination bleibt deterministisch. | Expliziter Leerzustand `Keine Treffer gefunden` mit Bezug auf den Suchbegriff. Dokumentliste und Suchfeld bleiben sichtbar. | Leerzustand bewusst gestalten, Suchbegriff sichtbar halten, keine technische Fehlermeldung fuer fachlich leeres Ergebnis. |
| sehr viele Treffer | Breite oder haeufige Query liefert grosse Treffermenge ueber viele Dokumente und Chunks. | Langsame Antwort, instabile Seitenwechsel, UI wirkt ueberladen oder springt zwischen Requests. | `200` mit deterministischer Pagination ueber `limit/offset`; Reihenfolge stabil ueber `rank DESC`, `documents.created_at DESC`, `chunk_index ASC`, `chunk_id ASC`. Keine unbounded Responses. | GUI zeigt nur erste Seite, spaeter paginierbar. Trefferzahl pro View begrenzen, kein unendliches ungeordnetes Rendering. | Harte `limit`-Grenzen beibehalten, stabile Tie-Breaker erzwingen, spaeter Cursor/Pagination erweitern, Performance-Tests mit breiten Queries. |
| kaputter Search Index | `search_vector`-Spalte, GIN-Index oder PostgreSQL-FTS-Funktion ist defekt, fehlt oder liefert DB-Fehler. | Suche faellt komplett aus oder liefert unzuverlaessige Ergebnisse. | `503 SERVICE_UNAVAILABLE` oder technischer Fehler mit internem Logging; kein stilles Fallback auf langsame Volltabelle ohne explizite Entscheidung. | GUI zeigt technischen Fehlerzustand `Service nicht verfuegbar` mit Retry-Moeglichkeit; keine leere Trefferliste vortaeuschen. | Health-/Migration-Checks fuer Search-Infrastruktur, Integrations- und EXPLAIN-Tests, Monitoring fuer Query-Fehler und Index-Drift. |
| geloeschtes Dokument mit altem Indexeintrag | Asynchroner oder inkonsistenter Indexstand referenziert Chunks/Dokumente, die fachlich geloescht wurden. | Nutzer sieht Phantomtreffer oder bekommt Broken Links. | Query muss nur ueber aktuelle Joins auf existierende `documents`, `document_versions` und `document_chunks` laufen; fachlich geloeschte Eintraege duerfen dadurch nicht ausgeliefert werden. Ergebnis idealerweise `200` ohne Phantomtreffer. | GUI darf keine Treffer auf nicht mehr existierende Dokumente zeigen. Falls Detail-Link spaeter `404` liefert, muss die Detailseite sauber `Dokument nicht gefunden` zeigen. | Keine denormalisierte Suchauslieferung ohne Join-Validierung, referentielle Integritaet und regelmaessige Reindex-/Integrity-Checks. |
| inkonsistente Scores | `ts_rank`-Werte schwanken bei Daten- oder Queryvarianten, Gleichstaende fuehren ohne Tie-Breaker zu wechselnder Reihenfolge. | Nicht reproduzierbare Trefferlisten, Pagination-Dubletten oder verschobene Ergebnisse. | `200` mit stabiler Ordnung durch feste sekundäre und tertiäre Sortierung; gleiche Query gegen gleichen Datenstand muss gleiche Reihenfolge liefern. | GUI darf auf Reload und Seitenwechsel keine springende Reihenfolge zeigen. Rank-Anzeige bleibt nur informativ, nicht als semantisches Versprechen. | Tie-Breaker im Query erzwingen, Ranking-Baseline dokumentieren, Regressionstests fuer Gleichstaende und Paging-Stabilitaet. |
| langsame Query | Breite Suchbegriffe, schlechte Selektivitaet, fehlende Indexnutzung oder grosse Offset-Werte fuehren zu hoher Latenz. | Timeouts, hohe DB-Last, schlechter GUI-Eindruck, potenzielle Retry-Stuerme. | Wenn noch innerhalb SLA: `200` mit Ergebnis. Bei Zeitueberschreitung oder technischer Degradation: kontrolliert `503 SERVICE_UNAVAILABLE`, nicht haengende Requests. | GUI zeigt Ladezustand waehrend der Suche; bei Ueberschreitung oder Fehler klarer technischer Zustand statt endloser Spinner. Keine blockierende Gesamtseite ohne Feedback. | EXPLAIN-/Performance-Tests, Query-Timeouts, Monitoring, spaeter Search-Telemetrie und ggf. andere Pagination-Strategie statt grosser Offsets. |

Leitlinien aus der Matrix:

- Fachlich leere Suche ist kein technischer Fehler: `200 []` plus klarer Leerzustand.
- Technische Degradation der Suchinfrastruktur ist kein leeres Ergebnis: `503 SERVICE_UNAVAILABLE` plus sichtbarer GUI-Fehlerzustand.
- Ranking und Pagination muessen deterministisch bleiben, auch wenn Scores selbst nicht semantisch interpretierbar sind.
- GUI darf das Suchfeld nicht ausblenden, nur weil Dokumentliste oder Trefferliste leer sind.

## 5. Tests

### Unit Tests

- Query-Validierung fuer `workspace_id`, `q`, `limit`, `offset`
- Ranking-Baseline fuer reproduzierbare Sortierung
- Filterlogik fuer Ausschluss nicht lesbarer Dokumente
- Mapping von Suchtreffern in API-Schema

### API-Tests

- erfolgreicher Suchlauf mit dokumentiertem Trefferformat
- Filterung nach `workspace_id`
- Pagination fuer Trefferlisten
- `WORKSPACE_REQUIRED`
- `INVALID_QUERY`
- `INVALID_PAGINATION`
- `SERVICE_UNAVAILABLE`

### Integrations- und DB-Tests

- PostgreSQL-Fulltextsuche liefert Treffer ueber Chunk-Inhalte
- Suchindex oder TSVECTOR-Pfad wird korrekt genutzt
- lesbare Dokumente mit gueltiger aktueller Version werden gefunden
- `failed`, `pending` oder OCR-pflichtige Dokumente werden nicht gefunden

### GUI-Integrationstests

- Ergebnisliste mit Dokumentbezug rendert korrekt
- Treffer zeigen Quellenanker sichtbar an
- Filterung per `workspace_id` ist in GUI und API konsistent
- Ein minimales Gold-Dataset fuer Retrieval-Evaluation ist in `docs/m3b-retrieval-evaluation-dataset.md` definiert.

## 6. Akzeptanzkriterien

- Es existiert eine read-only Query API fuer Chunk-basierte Volltextsuche.
- Die Suche arbeitet auf Chunk-Ebene und liefert immer Dokumentbezug.
- Treffer enthalten `document_id`, Dokumenttitel, Version, Chunk, `text_preview` und `source_anchor`.
- Ergebnisse sind mindestens nach einer technischen Ranking-Baseline sortiert.
- Die Suche ist nach `workspace_id` filterbar.
- Nicht lesbare Dokumente werden nicht indexiert oder nicht ausgeliefert.
- Der Endpunkt bleibt frei von Chat-, LLM-, Re-Ranking- und Embedding-Logik.
- PostgreSQL-basierte Retrieval-Tests sind vorhanden.
- Dokumentation und API-Vertrag sind mit der Implementierung synchronisiert.

## In Scope

- Volltextsuche ueber Chunks
- Ergebnisliste mit Dokumentbezug
- Ranking-Baseline
- Query API
- Filter nach `workspace_id`
- Quellenanker in Ergebnissen

## Out of Scope

- Chat
- LLM-Antwortgenerierung
- komplexes Re-Ranking
- semantische Suche, solange Embeddings nicht stabil sind
- automatische Zusammenfassungen