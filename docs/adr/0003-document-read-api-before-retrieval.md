# ADR 0003: Dokument-Read-API und Datenkonsistenz vor Retrieval

## Status

Angenommen.

## 1. Kontext

Paket 5 bereitet die Wissensdb auf M3 Suche/Retrieval vor. M3 darf nicht direkt auf unstabile Importdetails, freie Metadaten oder implizite Datenbankannahmen aufsetzen. Stattdessen braucht M3 eine stabile, nachvollziehbare Read-Schicht fuer Dokumente, Versionen und Chunks.

Der aktuelle Stand enthaelt bereits Import, Normalisierung, Versionierung und Chunking. Vor M3 muessen diese Daten aber ueber einen belastbaren API-Vertrag lesbar sein. Gleichzeitig muessen Datenkonsistenz und Deduplizierung so abgesichert werden, dass Retrieval nicht auf doppelte oder inkonsistente Dokumente indexiert.

OCR bleibt fuer Paket 5 ausdruecklich ausserhalb des Scopes. PDFs ohne extrahierbaren Text werden als OCR-pflichtig erkannt, aber nicht per OCR verarbeitet.

## 2. Problem

Ohne stabile Read-API wuerde M3 Suche/Retrieval direkt von internen Tabellen, Parser-Metadaten oder unfertigen Endpunkten abhaengen. Das haette mehrere Risiken:

- Retrieval koennte Chunks ohne stabile Dokument- oder Versionsreferenz indexieren.
- Duplicate Imports koennten zu mehrfachen Suchtreffern fuer denselben Inhalt fuehren.
- Parser- und OCR-Fehler koennten still als leere oder unvollstaendige Dokumente erscheinen.
- Freie oder uneinheitliche Chunk-Metadaten koennten Quellenangaben unzuverlaessig machen.
- Breaking Changes in der Dokument-API koennten M3 spaeter ohne klare Versionierung brechen.

## 3. Entscheidung

Vor M3 wird eine stabile Dokument-Read-API implementiert und als v1-Vertrag dokumentiert.

Die API umfasst:

- `GET /documents`
- `GET /documents/{document_id}`
- `GET /documents/{document_id}/versions`
- `GET /documents/{document_id}/chunks`
- `POST /documents/import` als bestehender Importpfad mit stabilisiertem Fehler- und Duplicate-Verhalten

Die Architektur trennt:

- Router fuer Request/Response- und HTTP-Mapping,
- Services fuer fachliche Regeln,
- Repositories fuer DB-Zugriff,
- Pydantic-Schemas fuer stabile Response-Modelle,
- SQLAlchemy-Modelle und Alembic-Migrationen fuer Persistenz.

Duplicate Protection wird DB-seitig ueber einen Unique Constraint auf `(workspace_id, content_hash)` abgesichert. Die Import-Persistenz behandelt Constraint-Konflikte deterministisch und gibt bei Duplicate-Imports das bestehende Dokument zurueck, statt hart fehlzuschlagen.

Dokumente erhalten einen expliziten `import_status` mit den Werten:

- `pending`
- `parsing`
- `parsed`
- `chunked`
- `failed`
- `duplicate`

Chunks erhalten normalisierte `source_anchor`-Daten, damit Retrieval spaeter Quellen stabil referenzieren kann. Legacy-Metadaten werden nicht geloescht, aber in API-Responses nicht frei ausgegeben.

OCR bleibt explizit ausserhalb von Paket 5. OCR-pflichtige Dokumente werden als Fehlerfall sichtbar gemacht, aber nicht verarbeitet.

## 4. Alternativen

### Alternative A: M3 direkt auf DB-Tabellen aufsetzen

Verworfen.

Direkter Tabellenzugriff wuerde M3 eng an interne Persistenzdetails koppeln. Schon kleine Schema- oder Repository-Aenderungen koennten Retrieval brechen.

### Alternative B: Read-API erst waehrend M3 bauen

Verworfen.

Dann wuerden Suche/Retrieval und API-Stabilisierung gleichzeitig entstehen. Das erhoeht das Risiko, dass Retrieval auf provisorische Felder oder inkonsistente Fehlerzustaende aufsetzt.

### Alternative C: OCR vor M3 implementieren

Verworfen fuer Paket 5.

OCR ist wichtig fuer gescannte PDFs, aber kein notwendiger Bestandteil einer stabilen Read-Schicht. OCR wuerde den Scope deutlich vergroessern und Parser-/Betriebsrisiken in Paket 5 ziehen.

### Alternative D: Duplicate Handling nur in Applikationslogik lassen

Verworfen.

Eine rein app-seitige Vorabpruefung kann parallele Imports nicht sicher verhindern. Der Unique Constraint ist notwendig, um Race Conditions zu vermeiden.

## 5. Konsequenzen

Positive Konsequenzen:

- M3 kann auf dokumentierte, stabile Endpunkte aufsetzen.
- Chunks sind eindeutig ueber `chunk_id`, Dokument, Version, Position und `source_anchor` referenzierbar.
- Duplicate Imports sind DB-seitig abgesichert.
- Parser-, OCR- und State-Konflikte sind als API-Fehler sichtbar.
- Read-API und Services sind testbar, auch ohne FastAPI oder echte PostgreSQL-Instanz.

Negative Konsequenzen:

- Paket 5 fuehrt zusaetzliche Struktur ein: Repository-Layer, Error-Standard, API-Contract und weitere Migrationen.
- OCR bleibt bewusst offen; gescannte PDFs sind fuer Retrieval weiterhin nicht nutzbar.
- Einige Parser liefern noch keine perfekt granularen Quellenpositionen.
- Es entsteht ein stabiler API-Vertrag, der spaetere Aenderungen disziplinierter und aufwaendiger macht.

Technische Schulden bleiben:

- Import-Persistenz nutzt teilweise noch direkten `psycopg`-Zugriff.
- PostgreSQL-Integrationstests sind optional und benoetigen `TEST_DATABASE_URL`.
- `/api/v1/documents` ist als Zielpfad dokumentiert, waehrend aktuell `/documents` implementiert ist.

## 6. Akzeptanzkriterien

Paket 5 gilt als akzeptiert, wenn folgende Kriterien erfuellt sind:

1. `GET /documents` liefert stabile Dokumentlisten mit Pagination, Workspace-Filter und Aggregaten.
2. `GET /documents/{document_id}` liefert Metadaten, aktuelle Version, Parser-Metadaten, Importstatus und Chunk-Summary.
3. `GET /documents/{document_id}/versions` liefert Versionen nachvollziehbar und sortiert.
4. `GET /documents/{document_id}/chunks` liefert nur Chunks der aktuellen Version, ohne Volltext im Detail-Endpunkt.
5. Jeder Chunk hat einen normalisierten `source_anchor`.
6. Duplicate Protection ist per DB-Constraint abgesichert.
7. Duplicate-Import-Konflikte werden deterministisch behandelt.
8. API-Fehler verwenden ein einheitliches Fehlerformat.
9. OCR-pflichtige Dokumente werden sichtbar als Fehlerfall behandelt, ohne OCR in Paket 5 zu implementieren.
10. Die Kernpfade sind durch Unit-, API- und optionale Integrationstests abgedeckt.
11. Der API-Vertrag fuer v1 ist dokumentiert, inklusive Breaking-Change-Regeln und contract-critical Feldern.
