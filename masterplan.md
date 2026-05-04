# Wissensbasis V1 - Masterplan

**Stand:** 2026-05-04  
**Ground Truth:** Code und Migrationen sind verbindlich. Dokumentation beschreibt den Stand, entscheidet ihn aber nicht.  
**Ziel:** Eine robuste Wissensbasis, in der Dokumente importiert, normalisiert, versioniert, als Chunks lesbar gemacht, spaeter durchsucht und im Chat/Analysekontext verwendet werden koennen.

V1 bleibt Single-User ohne Authentifizierung. Workspace- und User-Felder sind datenmodellseitig vorbereitet, aber noch keine Produktfunktion. Paket 5 hat die stabile Dokument-Read-API und Datenkonsistenz vor M3 Suche/Retrieval hergestellt.

---

## 1. Leitentscheidungen

| Bereich | Entscheidung | Aktueller Stand |
|---|---|---|
| Backend | FastAPI | ✅ implementiert |
| Frontend | React/Vite | GUI-Start erst nach Paket-5-Gate mit Score >= 90 |
| Datenbank | PostgreSQL als Ziel-DB | Schema und Alembic-Migrationen vorhanden |
| Test-DB | SQLite fuer lokale API-/Unit-Tests, optional PostgreSQL via `TEST_DATABASE_URL` | ✅ implementiert |
| Migrationen | Alembic | ✅ implementiert |
| Auth V1 | Nicht implementieren | gilt weiterhin |
| Mehrbenutzer | Datenmodell vorbereiten, Logik spaeter | vorbereitet |
| Originaldateien | Nicht speichern | gilt weiterhin |
| Kanonischer Inhalt | `document_versions.normalized_markdown` | ✅ implementiert |
| Versionierung | Dokument zeigt ueber `current_version_id` auf aktuelle Version | ✅ implementiert |
| Chunking | Chunks aus normalisiertem Markdown | ✅ implementiert |
| Quellenanker | normalisiertes `source_anchor` fuer API | ✅ implementiert |
| Duplicate Protection | DB-seitig per `(workspace_id, content_hash)` | ✅ implementiert |
| Fehlerstandard | einheitliches API-Error-Envelope | ✅ implementiert fuer Paket-5-Pfade |
| OCR | explizit nicht Teil von Paket 5 | fehlt |
| GUI-Start | M3a erst nach erfolgreichem Paket-5-Gate mit Score >= 90 | noch nicht gestartet |
| Suche/Retrieval | M3, nur auf stabile Read-API und GUI-Foundation aufsetzen | noch nicht implementiert |
| Chat | nach M3 | noch nicht implementiert |
| Analyse | nach Chat/Retrieval-Grundlage | vorbereitet im Datenmodell, Fachlogik fehlt |
| Vektorsuche | optional, nicht V1-kritisch | fehlt |
| Backup/Restore | spaeterer Betriebsmeilenstein | fehlt |

---

## 2. Aktueller Scope-Stand

### Implemented

- FastAPI-App mit Healthchecks.
- ✅ Alembic-Migrationen fuer Dokumente, Versionen, Chunks, Tags, Chat-/Analyse-Grundtabellen.
- ✅ Parser fuer TXT, MD, DOCX, DOC und PDF ohne OCR.
- ✅ Importpipeline mit Parser-Auswahl, Markdown-Normalisierung, Persistenz und Chunking.
- ✅ Harte Duplicate Protection ueber Unique Constraint `(workspace_id, content_hash)`.
- ✅ Expliziter `import_status` fuer Dokumente.
- Dokument-Read-API:
  - ✅ `GET /documents`
  - ✅ `GET /documents/{document_id}`
  - ✅ `GET /documents/{document_id}/versions`
  - ✅ `GET /documents/{document_id}/chunks`
  - ✅ `POST /documents/import`
- API-Fehlerstandard:
  - ✅ `DOCUMENT_NOT_FOUND`
  - ✅ `WORKSPACE_REQUIRED`
  - ✅ `INVALID_PAGINATION`
  - ✅ `DOCUMENT_STATE_CONFLICT`
  - ✅ `DUPLICATE_DOCUMENT`
  - ✅ `UNSUPPORTED_FILE_TYPE`
  - ✅ `OCR_REQUIRED`
  - ✅ `PARSER_FAILED`
  - ✅ `SERVICE_UNAVAILABLE`
- Paket-5-Dokumentation:
  - ✅ Statusdokument
  - ✅ API-Vertrag
  - ✅ Datenmodell-Dokumentation
  - ✅ ADR
  - ✅ Definition of Done

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

- ✅ Dokumentimport fuer TXT, MD, DOCX, DOC und PDF.
- ✅ Sichtbarer OCR-Bedarf fuer PDFs ohne extrahierbaren Text.
- ✅ Speicherung als normalisierter Markdown in PostgreSQL.
- ✅ Dokumentversionierung.
- ✅ Chunking mit stabiler Reihenfolge.
- ✅ Normalisierte Quellenanker fuer Chunks.
- ✅ Harte DB-Deduplizierung.
- ✅ Stabile Read-API fuer Dokumente, Versionen und Chunks.
- ✅ Einheitlicher Fehlerstandard.
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

Vor M3 gelten diese Grenzen als harte Systemgrenzen. Details und Durchsetzungsregeln stehen in `docs/m3-system-boundaries.md`.

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

React/Vite bleibt das Ziel fuer die V1-GUI. Die GUI wird bewusst nicht vor Abschluss von Paket 5 entwickelt. GUI-Start ist erst in M3a zulaessig, wenn das Paket-5-Abschluss-Gate erfolgreich mit Score >= 90 erreicht wurde und der Dokument-API-Vertrag als stabile Integrationsbasis vorliegt.

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

**Status:** ✅ implemented.

**Ziel:** Neubeginn sauber fixieren, Toolgrenzen definieren, Repo-Struktur festlegen.

### Ergebnis

- ✅ ADRs fuer Tech-Stack und V1-Scope vorhanden.
- ✅ Backend-/Frontend-/Docs-Struktur vorhanden.
- ✅ FastAPI/Alembic-Grundlage vorhanden.

---

## M1 - Datenbank, Migrationen und Dokumentmodell

**Status:** ✅ implemented mit offenen Betriebsdetails.

**Ziel:** Schema fuer Dokumente, Versionen, Tags, Chunks und spaetere Mehrbenutzerfaehigkeit.

### Ergebnis

- ✅ Workspaces und Users vorbereitet.
- ✅ Documents und DocumentVersions implementiert.
- ✅ Chunks implementiert.
- ✅ Categories, Tags und DocumentTags implementiert.
- ✅ Chat- und Analyse-Grundtabellen vorbereitet.
- ✅ DB-Healthcheck vorhanden.
- ✅ Alembic ist gesetztes Migrationstool.

### Offen

- Pflichtlauf der PostgreSQL-Integrationstests in CI.
- Betriebsrunbook fuer echte Ziel-DB.

---

## M2 - Import, Parser und Markdown-Normalisierung

**Status:** partial.

**Ziel:** Importpipeline fuer Dokumente mit Parsern, Normalisierung und Persistenz.

### Implementiert

- ✅ Parser-Interface.
- ✅ TXT- und MD-Parser.
- ✅ DOCX-Parser.
- ✅ DOC-Parser via LibreOffice-Konvertierung.
- ✅ PDF-Parser ohne OCR.
- ✅ Markdown-Normalizer.
- ✅ Chunking.
- ✅ Import erzeugt Dokument, Version und Chunks.
- ✅ Duplicate Detection und DB-seitige Duplicate Protection.

### Nicht implementiert

- OCR-Ausfuehrung.
- KI-/Ollama-Normalisierung als aktiver Importschritt.
- Parser-Confidence.
- Vollstaendige Quellenpositionsdaten fuer alle Parser.

---

## Paket 5 - Dokument-Read-API und Datenkonsistenz vor Retrieval

**Status:** ✅ implemented.

**Ziel:** Dokumente stabil lesbar machen und API-Stabilitaet herstellen, bevor M3 Suche/Retrieval startet.

### Implementiert

- ✅ `GET /documents`.
- ✅ `GET /documents/{document_id}`.
- ✅ `GET /documents/{document_id}/versions`.
- ✅ `GET /documents/{document_id}/chunks`.
- ✅ `POST /documents/import` stabilisiert.
- ✅ Pydantic Response Models.
- ✅ Service-/Repository-Trennung fuer Read-Pfade.
- ✅ Keine direkte DB-Nutzung im Dokument-Router fuer Read-Endpunkte.
- ✅ Importstatus.
- ✅ Normalisierte Chunk-Source-Anchors.
- ✅ DB Unique Constraint fuer Duplicate Protection.
- ✅ Deterministisches Duplicate Handling.
- ✅ Einheitlicher API-Fehlerstandard.
- ✅ Unit-, API- und optionale Integrationstests.
- ✅ API-Vertrag und ADR.

### Akzeptanzstatus

- ✅ Paket 5 ist fachlich abgeschlossen.
- ✅ Paket 5 ist technisch als Abschluss-Gate verifiziert.
- Restpunkte sind als technische Schulden dokumentiert:
  - `/api/v1/documents` Alias fehlt.
  - Import-Persistenz nutzt teilweise direkten `psycopg`-Zugriff.
  - Parser liefern Quellenpositionen noch uneinheitlich.

### Abschlussnachweis

- ✅ Standardlauf verifiziert: `42 passed, 1 skipped`.
- ✅ PostgreSQL-Integrationslauf verifiziert: `6 passed`.
- ✅ Ruecklauf fuer beruehrte Read-/Import-Pfade verifiziert: `19 passed`.
- ✅ PostgreSQL-Benchmark auf Referenzdaten verifiziert:
  - `GET /documents = 3.1ms`
  - `GET /documents/{id} = 3.4ms`
  - `GET /documents/{id}/chunks = 2.1ms`
- ✅ Finale Paketbewertung: `96/100`.
- ✅ Finale Entscheidung: `abgeschlossen`.

---

## M3a - GUI Foundation

**Status:** partial.

**Ziel:** Read-only Web-GUI zur Sichtbarmachung des Backend-Zustands auf stabiler Backend- und API-Basis, ohne Such-, Chat- oder Analysefachlogik vorzuziehen.

### Harte Startbedingungen

- Paket 5 ist im Abschluss-Gate erfolgreich freigegeben.
- Paket-5-Gesamtscore ist `>= 90`.
- Der Dokument-API-Vertrag fuer Read- und Import-Pfade ist mit dem Code synchronisiert.
- Read-API, Fehlerstandard und Datenkonsistenz sind auf PostgreSQL praktisch verifiziert.
- Offene Restpunkte aus Paket 5 sind dokumentierte Nicht-Blocker und nicht contract-critical fuer die GUI-Basis.

### Scope

- Technische GUI-Grundstruktur mit React/Vite stabilisieren.
- API-Client-Schicht strikt gegen den dokumentierten Dokument-API-Vertrag aufbauen.
- Basisnavigation und App-Shell fuer Dokumentliste und Dokumentdetail bereitstellen.
- Lade-, Leer- und Fehlerzustaende passend zum API-Error-Envelope definieren.
- Frontend-Typen, DTO-Mapping und Vertragsgrenzen zwischen Backend und GUI festziehen.
- Read-only Sicht auf Dokumentliste, Dokumentdetail, Versionen, Chunks und Importstatus ueber vorhandene Endpunkte anbinden.
- Fehlerzustaende und Zustandskonflikte sichtbar machen, ohne fachliche Korrektur- oder Schreibpfade einzufuehren.

### Nicht-Scope

- Keine Suche, kein Ranking und kein Retrieval.
- Kein Chat und keine Chat-UI.
- Kein Upload.
- Kein Bearbeiten von Dokumenten, Versionen oder Chunks.
- Keine Rollen- und Rechteverwaltung.
- Keine Analyse-, Merge-, Refine- oder Commit-Oberflaechen.
- Keine OCR-UI oder parsernahen Sonderlogiken ausser sichtbarer Status- und Fehlerdarstellung.
- Keine Embeddings oder embeddingnahe Oberflaechen.
- Keine direkte Kopplung an DB-Strukturen, Parser-Interna oder undokumentierte Response-Felder.

### Zielbild

- Die GUI ist ein lesender Beobachter des Backend-Zustands.
- Nutzer sehen, welche Dokumente im System vorhanden sind, in welchem Importzustand sie sich befinden und welche Versionen und Chunks aktuell lesbar sind.
- Die GUI bildet nur bereits vorhandene Backend-Faehigkeiten ab und fuehrt keine neue Fachlogik ein.
- Jeder sichtbare Zustand in der GUI muss direkt aus einem dokumentierten API-Response ableitbar sein.

### Screens

- Dokumentliste
  - Tabelle oder Kartenansicht mit `title`, `mime_type`, `created_at`, `updated_at`, `import_status`, `version_count`, `chunk_count`.
  - Leerstates und Fehlerstate fuer fehlende `workspace_id`, ungueltige Pagination oder Backend-Fehler.
- Dokumentdetail
  - Stammdaten des Dokuments, `import_status`, `latest_version`, Parser-Metadaten und Chunk-Summary.
  - Sichtbarer Hinweis bei inkonsistentem Dokumentzustand oder nicht lesbarem Dokument.
- Versionen-Ansicht
  - Read-only Liste der vorhandenen Versionen in API-Reihenfolge.
  - Anzeige von `version_number`, `created_at`, `content_hash` und relevanten Metadaten aus dem Vertrag.
- Chunks-Ansicht
  - Read-only Liste der Chunks der aktuellen Version in `position ASC`.
  - Anzeige von `position`, `text_preview` und normalisiertem `source_anchor`.
- Fehler- und Statusdarstellung
  - Gemeinsame UI-Komponente fuer API-Fehler, Leerstates und Konfliktzustaende.
  - Sichtbare Darstellung von `OCR_REQUIRED`, `DOCUMENT_STATE_CONFLICT`, `DOCUMENT_NOT_FOUND`, `WORKSPACE_REQUIRED` und `INVALID_PAGINATION`, soweit sie ueber die M3a-Screens auftreten.

### User Flows

- Nutzer oeffnet die Dokumentliste fuer einen Workspace und sieht alle lesbaren Dokumente mit Importstatus.
- Nutzer waehlt ein Dokument aus der Liste und gelangt in die Dokumentdetailansicht.
- Nutzer oeffnet von dort die Versionen-Ansicht und sieht die Versionshistorie read-only.
- Nutzer oeffnet die Chunks-Ansicht und sieht die Chunks der aktuellen Version mit Quellenanker und Vorschautext.
- Nutzer trifft auf einen Fehler- oder Konfliktzustand und bekommt den Backend-Status sichtbar, ohne dass die GUI versucht, ihn still zu reparieren.

### API-Abhaengigkeiten

- Dokumentliste haengt an `GET /documents`.
- Dokumentdetail haengt an `GET /documents/{document_id}`.
- Versionen-Ansicht haengt an `GET /documents/{document_id}/versions`.
- Chunks-Ansicht haengt an `GET /documents/{document_id}/chunks`.
- Importstatus wird ausschliesslich aus dokumentierten Response-Feldern wie `import_status` gelesen.
- Fehlerdarstellung haengt am standardisierten Error-Envelope `{"error": {"code": "...", "message": "...", "details": {...}}}`.
- M3a fuehrt keine neue API ein; sie konsumiert ausschliesslich vorhandene Paket-5-Endpunkte.

### Begruendung fuer den spaeten GUI-Start

- Vor Paket 5 waere die GUI gegen instabile Read-Pfade, uneinheitliche Fehlerfaelle und wechselnde Datenzustandsregeln entwickelt worden.
- Fruehe GUI-Entwicklung haette Backend-Unschaerfen kaschiert statt den API-Vertrag zu haerten.
- Paket 5 definiert die stabile Integrationsgrenze fuer Dokumentliste, Dokumentdetail, Versionen, Chunks, Import und Fehlerbehandlung.
- Erst nach erfolgreichem Paket-5-Gate lohnt sich GUI-Arbeit, weil dann Backend, Datenmodell und Vertragsgrenzen belastbar genug sind und teure UI-Nacharbeit durch API-Brueche vermieden wird.

### Abhaengigkeiten zwischen Backend, API-Vertrag und GUI

- Backend liefert die fachliche Wahrheit fuer Dokumentzustand, Versionen, Chunks und Fehlercodes.
- Der API-Vertrag ist die einzige erlaubte Kopplung zwischen GUI und Backend.
- GUI konsumiert nur dokumentierte Endpunkte und contract-critical Felder.
- Backend-Aenderungen mit GUI-Auswirkung muessen zuerst im API-Vertrag beschrieben werden, bevor die GUI sie konsumiert.
- M3 baut fuer Suchfunktionen auf derselben GUI-Foundation auf, erweitert sie aber erst nach stabiler Such-API.

### Gate-Regel

- Start von M3a nur, wenn Paket 5 im Abschluss-Gate den Score `>= 90` erreicht und als `freigegeben` bzw. `abgeschlossen` dokumentiert ist.

### Akzeptanzkriterien

- Die GUI zeigt eine Dokumentliste fuer einen Workspace auf Basis von `GET /documents` an.
- Die GUI zeigt fuer ein Dokument eine Detailansicht auf Basis von `GET /documents/{document_id}` an.
- Die GUI zeigt Versionen read-only auf Basis von `GET /documents/{document_id}/versions` an.
- Die GUI zeigt Chunks read-only auf Basis von `GET /documents/{document_id}/chunks` an.
- `import_status` ist in Liste und Detail sichtbar.
- Relevante Fehlerzustaende aus dem API-Vertrag werden sichtbar angezeigt und nicht verdeckt.
- M3a fuehrt keine Schreiboperationen, keinen Upload, keine Suche, keinen Chat, keine OCR-Logik und keine Embedding-Logik ein.
- Die GUI koppelt nur an dokumentierte Endpunkte und contract-critical Felder.

### Aktueller Abschlussstand

- ✅ Minimaler read-only GUI-Prototyp ist implementiert.
- ✅ Dokumentliste ist unter `/documents` sichtbar.
- ✅ Dokumentdetail ist unter `/documents/:id` sichtbar.
- ✅ Versionen und Chunk-Vorschau werden im Detailscreen angezeigt.
- ✅ Importstatus und Fehlercodes sind sichtbar.
- ✅ Suche, Chat, Upload und Mutation sind nicht implementiert.
- ✅ Frontend-Testlauf verifiziert: `5 passed`.
- ✅ Frontend-Build verifiziert: `vite build` erfolgreich.
- Offen fuer harten Abschluss:
  - Unit-Tests fuer ViewModel-Mapping und Fehlerabbildung.
  - dedizierte API-Mock-Tests fuer `404`, `409` und API down.
  - E2E-Smoke-Test fuer Liste -> Detail -> Chunks.

### Vorlaeufige Entscheidung

- M3a ist als Prototyp umgesetzt, aber nicht als final abgeschlossen freigegeben.
- M3b Retrieval startet erst nach Schliessung der offenen Testluecken.

---

## M3 - Suche und Quellenanker

**Status:** next.

**Ziel:** Robuste Volltext- und Tag-Suche mit zitierfaehigen Quellen auf Basis der stabilen Paket-5-Read-API.

### Vorbedingungen

- M3a GUI Foundation ist abgeschlossen, falls die GUI parallel zur Suche weiterentwickelt wird.
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
4. M3a GUI Foundation nach Paket-5-Gate starten.
5. M3 Such-Contract definieren.
6. PostgreSQL-Fulltext-Suche auf Chunks implementieren.
7. Such-API mit Quellenanker-Responses bauen.
8. Ranking- und Filtertests ergaenzen.
9. Danach M4 Chat auf Retrieval-Ergebnisse aufsetzen.

---

## 8. Risiken und Gegenmassnahmen

| Risiko | Auswirkung | Gegenmassnahme |
|---|---|---|
| OCR fehlt | gescannte PDFs sind fuer Suche/Chat nicht nutzbar | `OCR_REQUIRED` sichtbar halten, OCR als eigenes Paket planen |
| Parser-Qualitaet uneinheitlich | schlechte Chunks oder Quellenanker | Parser-Metriken und Format-spezifische Tests ergaenzen |
| Quellenpositionen unvollstaendig | Zitate koennen grob bleiben | `source_anchor` weiter anreichern, Legacy sauber kennzeichnen |
| GUI startet vor stabilem API-Gate | UI koppelt gegen instabile Backend-Vertraege | GUI-Start strikt erst nach Paket-5-Gate mit Score >= 90 |
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
- [M3a GUI Implementierungsplan](docs/m3a-implementation-plan.md)
- [M3a GUI ViewModels](docs/m3a-viewmodels.md)
- [Definition of Done: Paket 5](docs/paket-5-definition-of-done.md)
- [ADR: Dokument-Read-API und Datenkonsistenz vor Retrieval](docs/adr/0003-document-read-api-before-retrieval.md)
