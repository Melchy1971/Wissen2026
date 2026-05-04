# Wissensbasis V1 - Optimierter Masterplan

**Stand:** 2026-04-30  
**Ziel:** Produktionsnaher Neubeginn einer lokalen/remote-faehigen Wissensbasis. Dokumente werden importiert, per lokaler KI/OCR normalisiert, als Markdown in PostgreSQL persistiert, versioniert, durchsucht, analysiert und per Chat zielgerichtet abgefragt. V1 ist Single-User, aber datenmodellseitig auf spaetere Rollen- und Mehrbenutzerfaehigkeit vorbereitet.

---

## 1. Leitentscheidungen

| Bereich | Entscheidung |
|---|---|
| Betriebsmodell V1 | GUI lokal, PostgreSQL remote auf VPS |
| Spaeteres Ziel | API und GUI ebenfalls auf VPS betreibbar |
| Backend | FastAPI |
| Frontend | React/Vite |
| Datenbank | PostgreSQL remote |
| Datenzugriff | SQL direkt |
| Migrationen | node-pg-migrate nur wenn Node-Tooling gesetzt bleibt; sonst Alembic pruefen |
| Auth V1 | Nicht implementieren |
| Mehrbenutzer | Datenmodell vorbereiten, Logik spaeter |
| KI Import | Lokal via Ollama, austauschbar per Provider-Interface |
| OCR | Lokal |
| Originaldateien | Nicht speichern, nur extrahierter Markdown plus Metadaten |
| Versionierung | Jede Dokumentaenderung erzeugt neue Version |
| Suche V1 | Volltextsuche + Tags |
| Chat V1 | Pflicht, allgemein erlaubt, Quellen bei Dokumentbezug Pflicht |
| Analyse | Dokumente durchsuchen, vergleichen, konsolidieren, freigeben, committen |
| Vektorsuche | Optional, nicht V1-kritisch |
| Backup | Automatisiert auf externen Speicher |
| Restore | Manuell dokumentierter Test |
| Monitoring | Healthcheck ausreichend |
| Akzeptierte Ausfallzeit | 1 Stunde |

---

## 2. Optimierter V1-Scope

### Muss in V1

- Import fuer DOC, TXT, MD und PDF.
- Scan-PDF und Text-PDF werden ueber denselben Importpfad verarbeitet.
- Lokale OCR fuer nicht direkt extrahierbaren Text.
- KI-gestuetzte Normalisierung via lokalem Ollama-Provider.
- Provider-Interface fuer spaetere Austauschbarkeit.
- Speicherung als Markdown in PostgreSQL.
- Robuste Suche vor originalgetreuer Formatabbildung.
- Tabellen muessen moeglichst verlustfrei erhalten bleiben.
- Dokumentversionierung bei jeder Aenderung.
- Kategorien + Tags.
- KI-Tags und manuelle Tags werden additiv gefuehrt.
- Volltextsuche und Tagfilter.
- Chat mit Dokumentbezug und Quellenpflicht bei dokumentbasierten Antworten.
- Chat darf allgemein antworten, muss dann klar kennzeichnen: nicht aus Wissensbasis.
- Dokumentvergleich im Chat und in Analysefunktion.
- Merge erzeugt konsolidierte Zusammenfassung als neues Wissensdokument.
- Refine darf Ton, Struktur, Detailgrad, Quellengewichtung, Inhalte und Tags bearbeiten.
- Vor Commit: Freigabe und Moeglichkeit, Quellen/Abschnitte abzuwählen.
- Commit erzeugt immer neues Dokument.
- Produktionsnahe Tests fuer Kernpfade.
- PR-basierter Entwicklungsfluss.

### Explizit nicht in V1

- Authentifizierung.
- Aktive Rollen-/Rechtepruefung.
- Vollstaendige Mehrbenutzerlogik.
- Vektorsuche als Pflichtbestandteil.
- VPS-Deployment von GUI/API.
- Vollstaendiges Alerting.
- Speicherung der Originaldateien.

---

## 3. Architekturzielbild

### Backend

FastAPI stellt klare Servicegrenzen bereit:

- Import-Service
- OCR-Service
- Parser-Service
- Markdown-Normalizer
- KI-Provider-Interface
- Document-Service
- Version-Service
- Search-Service
- Chat-Service
- Analysis-Service
- Backup-/Health-Service

### Frontend

React/Vite ist fuer V1 die bessere Wahl gegenueber Next.js, weil:

- GUI zuerst lokal laufen soll.
- Server-Side Rendering keinen erkennbaren V1-Nutzen hat.
- Build- und Deployment-Komplexitaet niedriger bleibt.
- Claude Studio UI-Komponenten schneller isoliert bauen kann.

### Datenbank

PostgreSQL bleibt zentrale Persistenz:

- Dokumente
- Dokumentversionen
- Markdown-Inhalte
- Chunks
- Kategorien
- Tags
- Dokument-Tag-Verknuepfungen
- Analysegruppen
- Analyseergebnisse
- Quellenverweise
- Chat-Sessions
- Chat-Nachrichten
- Health-/Job-Status

---

## 4. Datenmodell-Prinzipien

### Muss-Felder Dokument

- `id`
- `workspace_id` vorbereitet, V1 Default-Workspace
- `owner_user_id` vorbereitet, V1 Default-User
- `title`
- `source_type`
- `mime_type`
- `content_hash`
- `current_version_id`
- `created_at`
- `updated_at`

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
- Tabellen werden nicht zerlegt, wenn technisch vermeidbar.
- Jeder Chunk bekommt Quellenanker.
- Quellenanker muessen Chat-Zitate ermoeglichen.

### Tag-Prinzipien

- Kategorien und Tags getrennt modellieren.
- KI-Tags und manuelle Tags als unterschiedliche Herkunft speichern.
- Manuelle Tags ergaenzen KI-Tags, kein automatisches Ueberschreiben.

---

## 5. Meilensteinplan

## M0 - Projektgrundlage und Architekturvertrag

**Ziel:** Neubeginn sauber fixieren, Toolgrenzen definieren, Repo-Struktur festlegen.

### Tasks

- Architektur-ADR fuer Tech-Stack erstellen.
- ADR fuer V1-Scope und spaetere Mehrbenutzerfaehigkeit erstellen.
- Repo-Struktur fuer Backend, Frontend, DB, Docs und Scripts festlegen.
- PR-Regel und Branch-Konvention festlegen.
- Task-Kontrakt-Format definieren.
- Review-Prompt pro Meilenstein vorbereiten.

### Akzeptanzkriterien

- Entscheidungen sind dokumentiert.
- Kein Auth-Code in V1.
- Datenmodell ist mehrbenutzerfaehig vorbereitet.
- Jede Umsetzung laeuft ueber Task-Kontrakt und PR.

---

## M1 - Datenbank, Migrationen und Dokumentmodell

**Ziel:** PostgreSQL-Schema fuer Dokumente, Versionen, Tags, Chunks und spaetere Mehrbenutzerfaehigkeit.

### Tasks

- Migrationen fuer Workspaces und Users als vorbereitete Default-Struktur.
- Migrationen fuer Documents und DocumentVersions.
- Migrationen fuer Chunks mit Quellenankern.
- Migrationen fuer Categories, Tags und DocumentTags.
- Migrationen fuer Analysis- und Chat-Grundtabellen.
- DB-Verbindungsmodul fuer remote PostgreSQL.
- Healthcheck fuer DB-Verbindung.

### Akzeptanzkriterien

- Remote-PostgreSQL ist konfigurierbar.
- Jede Dokumentaenderung kann als Version gespeichert werden.
- Markdown ist kanonische Textquelle.
- Source-Anker sind pro Chunk vorhanden.
- Mehrbenutzerfelder existieren, erzwingen aber noch keine Auth.

---

## M2 - Import, Parser, OCR und Markdown-Normalisierung

**Ziel:** Stabile Importpipeline fuer DOC, TXT, MD und PDF inklusive lokaler OCR und Ollama-Normalisierung.

### Tasks

- Parser-Interface definieren.
- Parser fuer TXT und MD.
- Parser fuer DOC/DOCX.
- Parser fuer PDF mit Text- und Scan-Fallback.
- Lokalen OCR-Service integrieren.
- Ollama-Provider-Interface erstellen.
- Markdown-Normalizer bauen.
- Tabellen-Erhalt priorisieren.
- Import erzeugt Dokumentversion, Chunks, Kategorien und Tags.
- Duplikaterkennung ueber Hashes.
- KI-Duplikatanalyse mit manueller Auswahl vorbereiten.

### Akzeptanzkriterien

- Import speichert keine Originaldatei.
- Extrahierter Markdown wird persistiert.
- OCR laeuft lokal.
- Provider ist austauschbar.
- Fehlerhafter KI-Output blockiert nicht zwingend den Import, sondern erzeugt validierbare Fallbacks.

---

## M3 - Suche und Quellenanker

**Ziel:** Robuste Volltext- und Tag-Suche mit zitierfaehigen Quellen.

### Tasks

- PostgreSQL-Fulltext-Suche auf Chunks.
- Suche ueber Tags und Kategorien.
- Rankinglogik fuer Volltexttreffer.
- Quellenanker im Suchergebnis ausgeben.
- Such-API bauen.
- Frontend-Suchseite bauen.
- Tests fuer Ranking, Filter und Quellenanker.

### Akzeptanzkriterien

- Suche findet Inhalte ueber Markdown/Chunks.
- Tagfilter funktionieren.
- Treffer enthalten Dokument, Version, Chunk und Quellenanker.
- Tabelleninhalte sind durchsuchbar.

---

## M4 - Chat mit Wissensbasisbezug

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

- Falsche Antworten werden staerker vermieden als Antwortluecken.
- Bei Dokumentbezug werden Quellen geliefert.
- Ohne passende Quelle wird der Status transparent gekennzeichnet.
- Vergleich mehrerer Dokumente ist moeglich.

---

## M5 - Analyse, Merge, Refine und Commit

**Ziel:** Dokumente vergleichen, konsolidieren, bearbeiten, freigeben und als neues Dokument committen.

### Tasks

- Analysegruppen modellieren.
- Dokumentauswahl fuer Analyse.
- Merge erzeugt konsolidierte Zusammenfassung.
- Refine erlaubt Ton, Struktur, Detailgrad, Quellengewichtung, Inhalte und Tags.
- UI fuer Quellen-/Abschnittsabwahl.
- Freigabeschritt vor Commit.
- Commit erzeugt neues Dokument mit Version 1.
- Commit erzeugt Chunks, Tags und Quellenmetadata.
- Tests fuer Merge, Refine, Commit und Rollback.

### Akzeptanzkriterien

- Kein Analyseergebnis wird ohne Freigabe gespeichert.
- Nutzer kann Quellen/Abschnitte vor Commit abwählen.
- Commit erzeugt immer ein neues Dokument.
- Quellenbezug bleibt nachvollziehbar.

---

## M6 - Backup, Restore-Doku und Betriebsgrundlage

**Ziel:** Produktionsnaher Betrieb fuer remote PostgreSQL mit automatisiertem Backup und Healthcheck.

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
- Betrieb ist ohne Docker Compose startbar.

---

## 6. KI-Werkzeug-Arbeitsteilung

| Werkzeug | Rolle | Darf entscheiden | Darf nicht entscheiden |
|---|---|---|---|
| Claude Cowork | Architektur, ADRs, Refactoring, Implementierung | Architekturvorschlaege, technische Trade-offs | Scope ohne Freigabe erweitern |
| Claude Studio | GUI, Frontend-Logik, UI-Komponenten | UI-Struktur innerhalb Task-Kontrakt | Backend, DB, Architektur |
| Codex | Groessere Features nach Task-Kontrakt | Umsetzung innerhalb Akzeptanzkriterien | Architektur aendern |
| GitHub Copilot | Inline-Code, Boilerplate, Tests | lokale Codevorschlaege | Architekturentscheidungen |

---

## 7. Standard-Task-Prompt-Format

Jeder Task-Prompt muss enthalten:

1. Ziel
2. Kontextdateien
3. Nicht aendern
4. Akzeptanzkriterien
5. Outputformat
6. Tests
7. Analyse zuerst, Code danach
8. Tokenlimit/Dateigrenzen

---

## 8. Tokenstrategie

- Prompts pro Task, nicht pro gesamtem Meilenstein.
- Kontext nur dateibasiert liefern.
- Keine kompletten Projektbaumausgaben, nur relevante Dateien.
- Jeder KI-Schritt startet mit kurzer Analyse.
- Umsetzung erst nach Analyse.
- Output-Vertrag erzwingt kompakte Ergebnisse.
- Wiederverwendbare Prompt-Schablonen nutzen.
- Review nur pro Meilenstein, nicht pro Task.
- Codex bekommt konkrete Patch-Aufgaben mit Akzeptanzkriterien.
- Claude Studio bekommt UI-Aufgaben ohne Backend-Kontext.

---

## 9. Risiken und Gegenmassnahmen

| Risiko | Auswirkung | Gegenmassnahme |
|---|---|---|
| OCR-Qualitaet schlecht | Falsche Inhalte in Suche/Chat | OCR-Confidence speichern, Review-Marker setzen |
| KI-Normalisierung veraendert Inhalt | Vertrauensverlust | Normalizer darf strukturieren, nicht interpretieren; Validierung und Diff |
| Keine Originaldatei gespeichert | Reimport erschwert | Hash, Dateiname, Parsermetadata und Markdown-Version speichern |
| Allgemeiner Chat halluziniert | Falsche Antworten | Kennzeichnung: nicht aus Wissensbasis; Quellenpflicht bei Dokumentbezug |
| Remote-DB-Latenz | Langsame Suche/Importe | Pooling, Indizes, Batch-Import, asynchrone Jobs |
| 15 GB MVP | Lange Imports und Backups | Job-Queue, Statusmodell, inkrementelle Verarbeitung |
| Mehrbenutzer spaeter schwer nachruestbar | Datenmodellbruch | Workspace/User-Felder ab M1 vorbereiten |
| node-pg-migrate passt schlecht zu FastAPI | Toolbruch | Frueh entscheiden: node-pg-migrate behalten oder Alembic wechseln |

---

## 10. Offene Architekturentscheidung

### Migrationstool

Aktuelle Vorgabe: SQL direkt + FastAPI + node-pg-migrate.  
Problem: node-pg-migrate fuehrt Node-Tooling ein, obwohl Backend FastAPI ist.

**Empfohlene Entscheidung:** Alembic pruefen und wahrscheinlich verwenden, wenn kein bestehender Node-Grund vorhanden ist.

**Entscheidungsregel:**

- Wenn Repo bereits Node-Migrationsstruktur hat: node-pg-migrate behalten.
- Wenn echter Neubeginn: Alembic verwenden.

---

## 11. Naechste sequenzielle Schritte

1. M0 abschliessen: ADRs, Repo-Struktur, Task-Kontrakt.
2. Migrationstool final entscheiden.
3. M1 DB-Schema implementieren.
4. M2 Importpipeline minimal vertikal bauen: TXT/MD zuerst.
5. DOC/PDF/OCR ergaenzen.
6. M3 Suche bauen.
7. M4 Chat bauen.
8. M5 Analyse bauen.
9. M6 Backup/Healthcheck bauen.
10. Meilenstein-Review ausfuehren.
