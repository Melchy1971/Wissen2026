# Wissensbasis V1 - Masterplan

**Stand:** 2026-05-04  
**Ground Truth:** Code und Migrationen sind verbindlich. Dokumentation beschreibt den Stand, entscheidet ihn aber nicht.  
**Ziel:** Eine robuste Wissensbasis, in der Dokumente importiert, normalisiert, versioniert, als Chunks lesbar gemacht, spaeter durchsucht und im Chat/Analysekontext verwendet werden koennen.

V1 bleibt Single-User ohne Authentifizierung. Workspace- und User-Felder sind datenmodellseitig vorbereitet, aber noch keine Produktfunktion. Paket 5 hat die stabile Dokument-Read-API und Datenkonsistenz vor M3 Suche/Retrieval hergestellt.

---

## 1. Leitentscheidungen

| Bereich | Entscheidung | Aktueller Stand |
|---|---|---|
| Backend | FastAPI | implementiert |
| Frontend | React/Vite | vorgesehen, nicht Fokus von Paket 5 |
| Datenbank | PostgreSQL als Ziel-DB | Schema und Alembic-Migrationen vorhanden |
| Test-DB | SQLite fuer lokale API-/Unit-Tests, optional PostgreSQL via `TEST_DATABASE_URL` | implementiert |
| Migrationen | Alembic | implementiert |
| Auth V1 | Nicht implementieren | gilt weiterhin |
| Mehrbenutzer | Datenmodell vorbereiten, Logik spaeter | vorbereitet |
| Originaldateien | Nicht speichern | gilt weiterhin |
| Kanonischer Inhalt | `document_versions.normalized_markdown` | implementiert |
| Versionierung | Dokument zeigt ueber `current_version_id` auf aktuelle Version | implementiert |
| Chunking | Chunks aus normalisiertem Markdown | implementiert |
| Quellenanker | normalisiertes `source_anchor` fuer API | implementiert |
| Duplicate Protection | DB-seitig per `(workspace_id, content_hash)` | implementiert |
| Fehlerstandard | einheitliches API-Error-Envelope | implementiert fuer Paket-5-Pfade |
| OCR | explizit nicht Teil von Paket 5 | fehlt |
| Suche/Retrieval | M3, nur auf stabile Read-API aufsetzen | noch nicht implementiert |
| Chat | nach M3 | noch nicht implementiert |
| Analyse | nach Chat/Retrieval-Grundlage | vorbereitet im Datenmodell, Fachlogik fehlt |
| Vektorsuche | optional, nicht V1-kritisch | fehlt |
| Backup/Restore | spaeterer Betriebsmeilenstein | fehlt |

---

## 2. Aktueller Scope-Stand

### Implemented

- FastAPI-App mit Healthchecks.
- Alembic-Migrationen fuer Dokumente, Versionen, Chunks, Tags, Chat-/Analyse-Grundtabellen.
- Parser fuer TXT, MD, DOCX, DOC und PDF ohne OCR.
- Importpipeline mit Parser-Auswahl, Markdown-Normalisierung, Persistenz und Chunking.
- Harte Duplicate Protection ueber Unique Constraint `(workspace_id, content_hash)`.
- Expliziter `import_status` fuer Dokumente.
- Dokument-Read-API:
  - `GET /documents`
  - `GET /documents/{document_id}`
  - `GET /documents/{document_id}/versions`
  - `GET /documents/{document_id}/chunks`
  - `POST /documents/import`
- API-Fehlerstandard:
  - `DOCUMENT_NOT_FOUND`
  - `WORKSPACE_REQUIRED`
  - `INVALID_PAGINATION`
  - `DOCUMENT_STATE_CONFLICT`
  - `DUPLICATE_DOCUMENT`
  - `UNSUPPORTED_FILE_TYPE`
  - `OCR_REQUIRED`
  - `PARSER_FAILED`
  - `SERVICE_UNAVAILABLE`
- Paket-5-Dokumentation:
  - Statusdokument
  - API-Vertrag
  - Datenmodell-Dokumentation
  - ADR
  - Definition of Done

### Partial

- PostgreSQL-Integrationstests existieren, laufen aber nur mit `TEST_DATABASE_URL`.
- PDF-Parser erkennt OCR-Bedarf, fuehrt aber kein OCR aus.
- DOC-Parser haengt von lokal verfuegbarem LibreOffice ab.
- Quellenanker sind API-seitig normalisiert, aber Parser liefern nicht fuer alle Formate vollstaendige Positionsdaten.
- `/api/v1/documents` ist als Zielpfad dokumentiert, aktuell ist `/documents` implementiert.
- Import-Persistenz nutzt teilweise noch direkten `psycopg`-Zugriff.

### Missing

- OCR-Engine.
- Authentifizierung und Autorisierung.
- echte Workspace-/User-Verwaltung.
- Suche, Ranking, Retrieval und Embeddings.
- Chat-Service und Chat-UI.
- Analyse-/Merge-/Refine-Fachlogik.
- Backup-/Restore-Automatisierung.
- verpflichtende PostgreSQL-CI-Integrationstests.

---

## 3. V1-Scope

### Muss in V1

- Dokumentimport fuer TXT, MD, DOCX, DOC und PDF.
- Sichtbarer OCR-Bedarf fuer PDFs ohne extrahierbaren Text.
- Speicherung als normalisierter Markdown in PostgreSQL.
- Dokumentversionierung.
- Chunking mit stabiler Reihenfolge.
- Normalisierte Quellenanker fuer Chunks.
- Harte DB-Deduplizierung.
- Stabile Read-API fuer Dokumente, Versionen und Chunks.
- Einheitlicher Fehlerstandard.
- Volltextsuche und Tagfilter in M3.
- Chat mit Quellenpflicht bei Dokumentbezug nach M3.
- Analysefunktionen nach stabiler Retrieval-Grundlage.
- Produktionsnahe Tests fuer Kernpfade.

### Explizit nicht in V1

- Authentifizierung.
- aktive Rollen-/Rechtepruefung.
- vollstaendige Mehrbenutzerlogik.
- Vektorsuche als Pflichtbestandteil.
- VPS-Deployment von GUI/API als Muss.
- vollstaendiges Alerting.
- Speicherung der Originaldateien.

### Explizit nicht in Paket 5

- Suche.
- Chat.
- UI.
- OCR.
- Embeddings.
- Ranking.
- Analysefachlogik.

---

## 4. Architekturzielbild

### Backend

FastAPI stellt klare Schichten bereit:

- Router: HTTP, Request/Response-Mapping, Dependency Injection.
- Services: fachliche Regeln und Zustandsentscheidungen.
- Repositories: Datenbankzugriff.
- Schemas: stabile Pydantic-Request-/Response-Modelle.
- Models: SQLAlchemy-Persistenzmodell.
- Migrations: Alembic.

Aktuell umgesetzt fuer Paket 5:

- Dokument-Router.
- Dokument-Read-Service.
- Dokument-Repository.
- Dokument-Schemas.
- Fehlerklassen und Exception Handler.
- Import-Persistenz mit DB-Duplicate-Sicherung.

Noch zu vereinheitlichen:

- Import-Persistenz vollstaendig in die gleiche Repository-/Session-Struktur ueberfuehren.
- `/api/v1/documents` als kompatiblen Alias implementieren, wenn M3 strikt versionierte Pfade nutzen soll.

### Frontend

React/Vite bleibt das Ziel fuer die V1-GUI. Paket 5 enthaelt keine UI-Arbeit.

### Datenbank

PostgreSQL bleibt zentrale Persistenz:

- Dokumente.
- Dokumentversionen.
- normalisierter Markdown.
- Chunks.
- Chunk-Metadaten und Quellenanker.
- Kategorien und Tags.
- Dokument-Tag-Verknuepfungen.
- vorbereitete Chat- und Analyse-Tabellen.

---

## 5. Datenmodell-Prinzipien

### Muss-Felder Dokument

- `id`
- `workspace_id`
- `owner_user_id`
- `title`
- `source_type`
- `mime_type`
- `content_hash`
- `current_version_id`
- `import_status`
- `created_at`
- `updated_at`

Constraints:

- Unique Constraint auf `(workspace_id, content_hash)`.
- Check Constraint fuer erlaubte `import_status`-Werte.

### Muss-Felder Dokumentversion

- `id`
- `document_id`
- `version_number`
- `normalized_markdown`
- `markdown_hash`
- `parser_version`
- `ocr_used`
- `ki_provider`
- `ki_model`
- `metadata`
- `created_at`

### Chunk-Prinzipien

- Chunks entstehen aus `normalized_markdown`.
- Chunks werden ueber `chunk_index ASC` gelesen.
- API nennt die Position `position`.
- Fulltext wird nicht in Dokument-Detail-Responses ausgeliefert.
- Chunk-Endpoint liefert `text_preview` statt Volltext.
- Jeder API-Chunk hat ein normalisiertes `source_anchor`.

Normalisiertes `source_anchor`:

```json
{
  "type": "text",
  "page": null,
  "paragraph": null,
  "char_start": 0,
  "char_end": 200
}
```

Erlaubte Typen:

- `text`
- `pdf_page`
- `docx_paragraph`
- `legacy_unknown`

### Tag-Prinzipien

- Kategorien und Tags getrennt modellieren.
- KI-Tags und manuelle Tags als unterschiedliche Herkunft speichern.
- Manuelle Tags ergaenzen KI-Tags, kein automatisches Ueberschreiben.

---

## 6. Meilensteinplan

## M0 - Projektgrundlage und Architekturvertrag

**Status:** implemented.

**Ziel:** Neubeginn sauber fixieren, Toolgrenzen definieren, Repo-Struktur festlegen.

### Ergebnis

- ADRs fuer Tech-Stack und V1-Scope vorhanden.
- Backend-/Frontend-/Docs-Struktur vorhanden.
- FastAPI/Alembic-Grundlage vorhanden.

---

## M1 - Datenbank, Migrationen und Dokumentmodell

**Status:** implemented mit offenen Betriebsdetails.

**Ziel:** Schema fuer Dokumente, Versionen, Tags, Chunks und spaetere Mehrbenutzerfaehigkeit.

### Ergebnis

- Workspaces und Users vorbereitet.
- Documents und DocumentVersions implementiert.
- Chunks implementiert.
- Categories, Tags und DocumentTags implementiert.
- Chat- und Analyse-Grundtabellen vorbereitet.
- DB-Healthcheck vorhanden.
- Alembic ist gesetztes Migrationstool.

### Offen

- Pflichtlauf der PostgreSQL-Integrationstests in CI.
- Betriebsrunbook fuer echte Ziel-DB.

---

## M2 - Import, Parser und Markdown-Normalisierung

**Status:** partial.

**Ziel:** Importpipeline fuer Dokumente mit Parsern, Normalisierung und Persistenz.

### Implementiert

- Parser-Interface.
- TXT- und MD-Parser.
- DOCX-Parser.
- DOC-Parser via LibreOffice-Konvertierung.
- PDF-Parser ohne OCR.
- Markdown-Normalizer.
- Chunking.
- Import erzeugt Dokument, Version und Chunks.
- Duplicate Detection und DB-seitige Duplicate Protection.

### Nicht implementiert

- OCR-Ausfuehrung.
- KI-/Ollama-Normalisierung als aktiver Importschritt.
- Parser-Confidence.
- Vollstaendige Quellenpositionsdaten fuer alle Parser.

---

## Paket 5 - Dokument-Read-API und Datenkonsistenz vor Retrieval

**Status:** implemented.

**Ziel:** Dokumente stabil lesbar machen und API-Stabilitaet herstellen, bevor M3 Suche/Retrieval startet.

### Implementiert

- `GET /documents`.
- `GET /documents/{document_id}`.
- `GET /documents/{document_id}/versions`.
- `GET /documents/{document_id}/chunks`.
- `POST /documents/import` stabilisiert.
- Pydantic Response Models.
- Service-/Repository-Trennung fuer Read-Pfade.
- Keine direkte DB-Nutzung im Dokument-Router fuer Read-Endpunkte.
- Importstatus.
- Normalisierte Chunk-Source-Anchors.
- DB Unique Constraint fuer Duplicate Protection.
- Deterministisches Duplicate Handling.
- Einheitlicher API-Fehlerstandard.
- Unit-, API- und optionale Integrationstests.
- API-Vertrag und ADR.

### Akzeptanzstatus

- Paket 5 ist fachlich abgeschlossen.
- Restpunkte sind als technische Schulden dokumentiert:
  - `/api/v1/documents` Alias fehlt.
  - PostgreSQL-Integrationstests sind optional.
  - Import-Persistenz nutzt teilweise direkten `psycopg`-Zugriff.
  - Parser liefern Quellenpositionen noch uneinheitlich.

---

## M3 - Suche und Quellenanker

**Status:** next.

**Ziel:** Robuste Volltext- und Tag-Suche mit zitierfaehigen Quellen auf Basis der stabilen Paket-5-Read-API.

### Vorbedingungen

- M3 nutzt dokumentierte Read-Endpunkte und contract-critical Felder.
- M3 greift nicht direkt auf Parser-Interna oder freie Chunk-Metadaten zu.
- Chunks werden ueber `chunk_id`, `position` und `source_anchor` referenziert.
- Duplicate-Dokumente sind DB-seitig verhindert.
- Parser-/OCR-Fehler sind sichtbar.

### Tasks

- Such-Contract fuer M3 definieren.
- PostgreSQL-Fulltext-Suche auf Chunks implementieren.
- Suche ueber Tags und Kategorien implementieren.
- Rankinglogik fuer Volltexttreffer implementieren.
- Quellenanker im Suchergebnis ausgeben.
- Such-API bauen.
- Tests fuer Ranking, Filter und Quellenanker.
- Optional: kompatiblen `/api/v1/documents`-Alias vor M3-Clientbindung einfuehren.

### Akzeptanzkriterien

- Suche findet Inhalte ueber Markdown/Chunks.
- Tagfilter funktionieren.
- Treffer enthalten Dokument, Version, Chunk und normalisierten Quellenanker.
- Tabelleninhalte sind durchsuchbar, soweit sie als Markdown/Chunks extrahiert wurden.
- Suche indexiert keine Dokumente mit `failed`, `pending` oder OCR-pflichtigem Fehlerzustand.

---

## M4 - Chat mit Wissensbasisbezug

**Status:** missing.

**Ziel:** Chat beantwortet Fragen zielgerichtet, nutzt Trefferkontext, zitiert bei Dokumentbezug und kennzeichnet allgemeine Antworten.

### Tasks

- Chat-Service mit Retrieval-Schritt.
- Prompt-Vertrag fuer dokumentbasierte Antworten.
- Quellenpflicht bei Dokumentbezug.
- Kennzeichnung fuer Antworten ausserhalb der Wissensbasis.
- Dokumentvergleich im Chat.
- Chat-Session- und Message-Persistenz.
- Frontend-Chatseite.
- Tests fuer Halluzinationsschutz und Quellenlogik.

### Akzeptanzkriterien

- Bei Dokumentbezug werden Quellen geliefert.
- Ohne passende Quelle wird der Status transparent gekennzeichnet.
- Vergleich mehrerer Dokumente ist moeglich.
- Allgemeine Antworten sind klar als nicht aus der Wissensbasis gekennzeichnet.

---

## M5 - Analyse, Merge, Refine und Commit

**Status:** missing.

**Ziel:** Dokumente vergleichen, konsolidieren, bearbeiten, freigeben und als neues Dokument committen.

### Tasks

- Analysegruppen fachlich nutzbar machen.
- Dokumentauswahl fuer Analyse.
- Merge erzeugt konsolidierte Zusammenfassung.
- Refine erlaubt Ton, Struktur, Detailgrad, Quellengewichtung, Inhalte und Tags.
- UI fuer Quellen-/Abschnittsabwahl.
- Freigabeschritt vor Commit.
- Commit erzeugt neues Dokument mit Version 1.
- Commit erzeugt Chunks, Tags und Quellenmetadaten.
- Tests fuer Merge, Refine, Commit und Rollback.

### Akzeptanzkriterien

- Kein Analyseergebnis wird ohne Freigabe als Wissensdokument gespeichert.
- Nutzer kann Quellen/Abschnitte vor Commit abwaehlen.
- Commit erzeugt immer ein neues Dokument.
- Quellenbezug bleibt nachvollziehbar.

---

## M6 - Backup, Restore-Doku und Betriebsgrundlage

**Status:** missing.

**Ziel:** Produktionsnaher Betrieb fuer PostgreSQL mit automatisiertem Backup und Healthcheck.

### Tasks

- Backup-Script fuer externen Speicher.
- Backup-Konfiguration dokumentieren.
- Manuellen Restore-Test dokumentieren.
- DB-Healthcheck.
- API-Healthcheck.
- Fehlerlogging standardisieren.
- Betriebsrunbook fuer 1h Wiederherstellungsziel.

### Akzeptanzkriterien

- Backup laeuft automatisiert.
- Restore ist manuell dokumentiert und einmal geprueft.
- Healthcheck erkennt DB-Ausfall.
- Betrieb ist ohne manuelle Ad-hoc-Schritte nachvollziehbar.

---

## 7. Naechste sequenzielle Schritte

1. Paket-5-Aenderungen committen.
2. Optionalen `/api/v1/documents`-Alias implementieren, falls M3 direkt versionierte Pfade verwenden soll.
3. PostgreSQL-Integrationstests fuer Paket-5-Read-API in CI oder lokalem Standardlauf absichern.
4. M3 Such-Contract definieren.
5. PostgreSQL-Fulltext-Suche auf Chunks implementieren.
6. Such-API mit Quellenanker-Responses bauen.
7. Ranking- und Filtertests ergaenzen.
8. Danach M4 Chat auf Retrieval-Ergebnisse aufsetzen.

---

## 8. Risiken und Gegenmassnahmen

| Risiko | Auswirkung | Gegenmassnahme |
|---|---|---|
| OCR fehlt | gescannte PDFs sind fuer Suche/Chat nicht nutzbar | `OCR_REQUIRED` sichtbar halten, OCR als eigenes Paket planen |
| Parser-Qualitaet uneinheitlich | schlechte Chunks oder Quellenanker | Parser-Metriken und Format-spezifische Tests ergaenzen |
| Quellenpositionen unvollstaendig | Zitate koennen grob bleiben | `source_anchor` weiter anreichern, Legacy sauber kennzeichnen |
| `/api/v1/documents` Alias fehlt | M3 koennte spaeter auf unversionierten Pfad koppeln | Alias vor M3-Clientbindung implementieren |
| Import-Persistenz nutzt direkten `psycopg` | uneinheitliche DB-Schicht | nach Paket 5 in Repository-/Session-Struktur ueberfuehren |
| PostgreSQL-Tests optional | DB-spezifische Fehler koennen unbemerkt bleiben | `TEST_DATABASE_URL` in CI setzen |
| Allgemeiner Chat halluziniert | falsche Antworten | M4 erst nach M3, Quellenpflicht und Antwortstatus erzwingen |
| Remote-DB-Latenz | langsame Suche/Importe | Indizes, Projektionen, Pagination und Batch-Strategien |

---

## 9. Referenzdokumente

- [Projektstatus](docs/status.md)
- [Datenmodell V1](docs/data-model.md)
- [V1 Dokument-API Contract](docs/api/v1-document-api-contract.md)
- [Definition of Done: Paket 5](docs/paket-5-definition-of-done.md)
- [ADR: Dokument-Read-API und Datenkonsistenz vor Retrieval](docs/adr/0003-document-read-api-before-retrieval.md)
