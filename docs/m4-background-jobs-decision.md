# M4 Entscheidung: Background Jobs fuer Import und Indexierung

Stand: 2026-05-05

## Entscheidung

Fuer M4 und den folgenden Zielzustand sollen **keine externen Worker wie Celery oder RQ** eingefuehrt werden. Ebenso soll der Import **nicht synchron bleiben**. Die finale Entscheidung ist daher:

- **Option 3: einfache interne Queue einfuehren**
- mit persistierten Job-Datensaetzen in der bestehenden PostgreSQL-Datenbank
- mit einem kleinen internen Worker pro Backend-Instanz fuer lokalen Betrieb
- `FastAPI BackgroundTasks` nur als technische Bruecke fuer das initiale Triggern, aber **nicht** als eigentliches Zuverlaessigkeitsmodell

Kurzform:

- Import fuer GUI-Uploads: asynchroner Jobpfad auf Basis persistierter Queue
- Search-Index-Rebuild: als expliziten Job modellieren statt als langen Admin-Request
- Celery/RQ: spaeter moeglich, aber bewusst nicht im Scope
- synchroner Upload: verworfen

### Klarer Zielzustand

Der Zielzustand ist nicht "BackgroundTasks", sondern:

- persistierte Queue ueber `background_jobs`
- `202 Accepted` mit Job-ID als stabiler API-Vertrag
- Polling ueber `GET /api/v1/jobs/{job_id}` fuer GUI und Admin-Oberflaechen
- interner Worker mit exklusivem Claiming und spaeterer Restart-Wiederaufnahme

Der aktuelle Stand darf `BackgroundTasks` zum Anschubsen eines In-Process-Workers verwenden. Diese Kopplung ist aber Uebergangstechnik und nicht die Architekturentscheidung.

## Begruendung

### Bewertete Optionen

| Option | Bewertung |
|---|---|
| 1. synchron lassen | fuer GUI-Uploads zu riskant |
| 2. FastAPI BackgroundTasks | zu wenig restart-sicher und zu wenig transparent |
| 3. einfache interne Queue | bester M4-Kompromiss |
| 4. Celery/RQ spaeter | sinnvoller Spaeterausbau, aber fuer M4 zu schwer |

### 1. synchron lassen

Vorteile:

- geringste Implementierungskomplexitaet
- unmittelbare Fehlerantwort im gleichen Request
- lokal sehr einfach zu betreiben

Nachteile:

- lange Requests bei DOC, DOCX und PDF bleiben direkt im GUI-Request haengen
- Risiko fuer Timeouts, Reverse-Proxy-Abbrueche und schlechte UX steigt mit GUI-Nutzung
- kein echter Fortschritt fuer Nutzer, nur blockierender Ladezustand
- Index-Rebuild als langer Admin-Request ist betrieblich unguenstig

Fazit:

- fuer Paket 5 vertretbar
- fuer M4-Produktisierung nicht mehr robust genug

### 2. FastAPI BackgroundTasks

Vorteile:

- geringe technische Einstiegshuerde
- kein zusaetzlicher externer Dienst
- Requests koennen frueh mit `202 Accepted` beantwortet werden

Nachteile:

- kein persistenter Jobzustand von Natur aus
- bei Prozess-Neustart gehen laufende Tasks verloren
- Fehlertransparenz nur gut, wenn man zusaetzlich eigene Jobpersistenz baut
- Fortschritt fuer die GUI ebenfalls nur mit zusaetzlicher Jobtabelle erreichbar

Fazit:

- allein nicht ausreichend
- nur als Ausloeser brauchbar, nicht als Zielarchitektur

### 3. einfache interne Queue

Vorteile:

- gute Balance aus Komplexitaet und Betriebssicherheit
- Jobs koennen in PostgreSQL persistiert werden
- GUI kann Status, Fehler und Fortschritt pollen
- Neustart-Sicherheit ist erreichbar, wenn Jobs beim Start sauber wieder aufgenommen werden
- lokaler Betrieb bleibt einfach, da keine zusaetzliche Infrastruktur noetig ist

Nachteile:

- etwas mehr Applikationslogik als bei synchronem Request
- Worker-Lebenszyklus und Locking muessen sauber geregelt werden
- nicht horizontal beliebig skalierbar ohne weitere Koordination

Fazit:

- fuer M4 die beste Zieloption

### 4. Celery/RQ spaeter

Vorteile:

- robustes etabliertes Worker-Modell
- gute Skalierbarkeit und Trennung von API und Worker
- besser fuer spaetere Batch- oder OCR-Szenarien

Nachteile:

- zusaetzliche Infrastruktur wie Redis oder Broker
- mehr Deployment- und Betriebsaufwand
- fuer lokalen Betrieb schwerer und fehleranfaelliger
- fuer die aktuelle Produktreife noch ueberdimensioniert

Fazit:

- als Spaeterausbau sinnvoll
- fuer M4 bewusst zu gross

## Kriterienbewertung

| Kriterium | synchron | BackgroundTasks | interne Queue | Celery/RQ spaeter |
|---|---|---|---|---|
| Komplexitaet | niedrig | niedrig bis mittel | mittel | hoch |
| Fehlertransparenz | mittel | niedrig ohne Zusatzarbeit | hoch | hoch |
| Persistenz | hoch im Request, sonst keine Jobs | niedrig | hoch | hoch |
| Restart-Sicherheit | niedrig fuer lange Requests | niedrig | mittel bis hoch | hoch |
| GUI-Fortschritt | schlecht | schlecht ohne Jobmodell | gut | gut |
| lokaler Betrieb | sehr gut | sehr gut | gut | mittel |

## Architekturentscheidung fuer M4

### Warum Import asynchron werden soll

GUI-Upload macht lange Request-Laufzeiten sichtbar. Das trifft besonders:

- PDF-Parsing
- DOC-Konvertierung ueber LibreOffice
- grosse Markdown- oder Textdateien mit vielen Chunks
- spaetere OCR- oder KI-nahe Verarbeitung

Deshalb soll der Upload-Request in M4 nur noch:

1. Datei annehmen
2. Job anlegen
3. schnell mit Job-ID und Status antworten

Die eigentliche Verarbeitung soll im Hintergrund laufen.

### Warum Indexierung ebenfalls als Job laufen soll

Der Search-Index-Rebuild ist bereits heute eine betriebliche Admin-Aktion. Als langer synchroner Request ist er unguenstig, weil:

- Laufzeit von Datenmenge abhaengt
- Admin-UI keine saubere Fortschrittsanzeige bekommt
- Abbruch und Restart schlecht nachvollziehbar sind

Fuer M4 soll auch der Rebuild daher als Job mit Statusmodell laufen.

## Implementierungsplan

### Phase 1: Jobmodell einfuehren

Neue Tabelle, z. B. `system_jobs` oder `background_jobs`:

- `id`
- `job_type`
- `status` (`queued`, `running`, `completed`, `failed`, `cancelled`)
- `workspace_id`
- `requested_by_user_id`
- `payload`
- `progress_current`
- `progress_total`
- `progress_message`
- `error_code`
- `error_message`
- `attempt_count`
- `locked_at`
- `locked_by`
- `created_at`
- `started_at`
- `finished_at`

Jobtypen fuer M4:

- `document_import`
- `search_index_rebuild`

### Phase 2: interne Queue und Worker

Im Backend einen kleinen Worker einfuehren, der:

- periodisch `queued` Jobs abholt
- per DB-Locking oder atomarem Statuswechsel exklusiv uebernimmt
- Fortschritt waehrend der Ausfuehrung schreibt
- Fehler strukturiert als `failed` persistiert

Wichtig fuer Restart-Sicherheit:

- `running` Jobs mit altem `locked_at` beim Start als requeuebar behandeln
- idempotente Jobhandler bauen

### Phase 3: Importpfad umstellen

Neuer Upload-Ablauf:

1. `POST /documents/import` nimmt Datei an
2. Datei wird temporaer abgelegt oder anderweitig fuer den Worker verfuegbar gemacht
3. `document_import`-Job wird angelegt
4. API antwortet mit `202 Accepted` und Job-ID

Ergaenzende Endpunkte:

- `GET /api/v1/jobs/{job_id}`
- optional `GET /api/v1/jobs?workspace_id=...&status=...`

GUI-Verhalten:

- Polling auf Jobstatus
- Statusanzeige `queued`, `running`, `completed`, `failed`
- nach Erfolg Navigation zum Dokumentdetail

Implementierter Stand in M4:

- `POST /documents/import` antwortet mit `202 Accepted` und einem `document_import`-Job
- `POST /api/v1/admin/search-index/rebuild` antwortet mit `202 Accepted` und einem `search_index_rebuild`-Job
- gemeinsames Polling ueber `GET /api/v1/jobs/{job_id}`
- Frontend zeigt normalisierte Jobzustandslabels statt roher Backend-Strings:
	- `queued` -> `In Warteschlange`
	- `running` -> `Wird verarbeitet`
	- `completed` -> `Abgeschlossen`
	- `failed` -> `Fehlgeschlagen`

### Phase 4: Index-Rebuild umstellen

Admin-Aktion nicht mehr direkt ausfuehren, sondern:

1. Rebuild-Job anlegen
2. `202 Accepted` mit Job-ID zurueckgeben
3. Admin-Diagnostik zeigt Fortschritt und Endstatus

Implementierter Stand in M4:

- Admin-Diagnostik pollt denselben generischen Jobstatus wie der Upload
- Upload und Rebuild verwenden damit bewusst keinen getrennten Polling-Mechanismus mehr

### Phase 5: Observability und Runbook

Erweitern um:

- Job-Events `job_queued`, `job_started`, `job_completed`, `job_failed`
- Metriken nach `job_type` und `status`
- Runbook fuer haengende oder wiederaufgenommene Jobs

## Nicht-Scope fuer M4

Nicht Teil dieser Entscheidung bzw. bewusst spaeter:

- synchroner Request mit vollstaendigem Importergebnis
- `FastAPI BackgroundTasks` als einziges Ausfuehrungs- und Zuverlaessigkeitsmodell
- Celery
- RQ
- Redis als Broker
- verteilte Worker-Farm
- priorisierte Multi-Queue-Strategien
- WebSockets oder Server-Sent Events fuer Live-Fortschritt
- Byte-genauer Upload-Fortschritt
- OCR-Pipeline-Ausbau als eigener Worker-Stack
- globale Batch-Orchestrierung fuer Massenimporte

Explizit ebenfalls nicht umgesetzt:

- Persistenz der Originaldatei als dauerhafte fachliche Quelle
- Resume mitten im Parserlauf
- eigenstaendige Jobhistorien- oder Ops-UI jenseits des aktuellen Polling-Modells

## Migrationsplan vom Ist-Zustand zum Zielzustand

### Phase A: Ist-Zustand absichern

Bereits vorhanden:

- persistierte Jobdatensaetze in `background_jobs`
- `document_import` und `search_index_rebuild` als Jobtypen
- API-Vertrag `202 Accepted + job_id`
- Polling ueber `GET /api/v1/jobs/{job_id}`

### Phase B: Worker-Semantik explizit machen

- Begriffe in Code und Dokumentation auf "persistierte interne Queue" vereinheitlichen
- `BackgroundTasks` nur noch als Startimpuls behandeln
- Job-Observability an Claim, Start, Ende und Fehler koppeln

### Phase C: Restart-Sicherheit vollenden

- Stale `running` Jobs erkennen
- Requeue- oder Recovery-Regeln fuer alte Locks definieren
- Worker-Claiming ohne Request-Lebenszyklus stabilisieren

### Phase D: Trigger entkoppeln

- optionalen App-internen Queue-Loop oder separaten Worker-Entrypoint nutzen
- `BackgroundTasks` spaeter entfernen oder rein optional machen

## Praktische Entscheidung in einem Satz

Fuer M4 sollen Import und Search-Indexierung von langen synchronen Requests auf eine **persistierte einfache interne Queue mit In-Process-Worker** umgestellt werden; `FastAPI BackgroundTasks` allein reichen dafuer nicht, und Celery/RQ bleiben ein bewusster Spaeterausbau.