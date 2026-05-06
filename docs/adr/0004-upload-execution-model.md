# ADR 0004: Upload-Ausfuehrung ueber persistente interne Queue

## Status

Angenommen.

## 1. Kontext

Der Uploadpfad ist fachlich kein kurzer CRUD-Request mehr. Bereits heute koennen folgende Schritte die Laufzeit deutlich verlaengern:

- Parser-Ausfuehrung fuer PDF, DOCX und DOC
- DOC-Konvertierung ueber LibreOffice
- Chunking grosser Markdown-Inhalte
- spaetere Reindex- oder Recovery-Schritte

Gleichzeitig braucht die GUI einen nachvollziehbaren Status fuer den Upload. Ein blockierender synchroner Request liefert zwar direkte Fehler, aber kein robustes Nutzerfeedback bei langen Laufzeiten. Reine `FastAPI BackgroundTasks` entkoppeln zwar den HTTP-Request, loesen aber weder Restart-Sicherheit noch transparente Fehlerpersistenz.

Im aktuellen Repository existiert bereits ein asynchroner Jobvertrag mit `202 Accepted`, persistierter Tabelle `background_jobs` und Polling ueber `GET /api/v1/jobs/{job_id}`. Die Ausfuehrung wird jedoch noch durch einen In-Process-Trigger mit `BackgroundTasks` gestartet. Diese Kombination ist fuer lokale Nutzung praktikabel, aber nur dann ein belastbares Zielmodell, wenn die persistierte Queue selbst als Architektur gilt und `BackgroundTasks` nur als Startimpuls behandelt werden.

## 2. Bewertete Optionen

### Option 1: synchron

Staerken:

- geringste technische Komplexitaet
- unmittelbare HTTP-Fehlerantwort
- lokal leicht zu verstehen

Schwaechen:

- unguenstig fuer grosse Dateien und langsame Parser
- kein sauberes GUI-Feedback ausser blockierendem Ladezustand
- Restart waehrend des Requests fuehrt zu unklaren Zwischenzustaenden
- schlechter Fit fuer Search-Index-Rebuild und spaetere Recovery-Pfade

### Option 2: FastAPI BackgroundTasks

Staerken:

- geringe Einstiegshuerde
- fruehe `202 Accepted`-Antwort moeglich
- lokal ohne zusaetzliche Infrastruktur lauffaehig

Schwaechen:

- Tasks sind ohne zusaetzliche Persistenz nicht restart-sicher
- Fehlertransparenz entsteht erst durch separate Jobdaten
- kein eigener Scheduling-, Requeue- oder Claim-Mechanismus
- horizontal nur schwer kontrollierbar

### Option 3: interne persistente Queue

Staerken:

- robuster fuer grosse Dateien, weil die Verarbeitung entkoppelt wird
- GUI kann ueber persistierte Jobzustaende klar rueckmelden
- Fehler bleiben ueber `error_code`, `error_message`, Resultat und Observability nachvollziehbar
- lokale Nutzung bleibt ohne externe Broker praktikabel
- sauberer Pfad fuer spaetere Restart-Logik und Requeueing

Schwaechen:

- hoeherer Implementierungsaufwand als synchron oder reines `BackgroundTasks`
- Worker-Claiming, Stale-Lock-Recovery und Idempotenz muessen bewusst gebaut werden
- begrenzte Skalierung gegenueber dedizierten Worker-Systemen

## 3. Entscheidung

Der Zielzustand fuer Upload-Ausfuehrung ist:

- **Option 3: interne persistente Queue**
- Persistenz ueber die bestehende Datenbanktabelle `background_jobs`
- Ausfuehrung ueber einen kleinen internen Worker mit exklusivem Job-Claiming
- HTTP-Vertrag bleibt `POST /documents/import -> 202 Accepted + job_id`
- GUI-Fortschritt bleibt Polling-basiert ueber `GET /api/v1/jobs/{job_id}`

`FastAPI BackgroundTasks` sind **nicht** die Zielarchitektur. Sie duerfen nur als temporaere Bruecke dienen, um lokal nach dem Request einen In-Process-Worker anzustossen, solange noch kein eigenstaendiger Queue-Loop beim App-Start Jobs claimt.

Synchroner Upload wird nicht weiter verfolgt.

## 4. Entscheidung nach Bewertungskriterien

| Kriterium | synchron | FastAPI BackgroundTasks | interne persistente Queue |
|---|---|---|---|
| grosse Dateien | schwach | mittel | gut |
| GUI-Feedback | schwach | mittel mit Zusatzarbeit | gut |
| Restart-Sicherheit | schwach | schwach | mittel, spaeter gut |
| Fehlertransparenz | mittel | mittel mit Zusatzarbeit | gut |
| lokale Nutzung | sehr gut | sehr gut | gut |
| Komplexitaet | niedrig | niedrig bis mittel | mittel |

Begruendung der Endentscheidung:

- Fuer grosse Dateien ist synchroner Upload der schlechteste Fit.
- Fuer GUI-Feedback braucht es persistierte Status- und Fehlerdaten; reine `BackgroundTasks` liefern das nicht.
- Restart-Sicherheit ist nur mit einer echten Queue-Semantik erreichbar.
- Lokale Nutzung soll ohne Redis, RabbitMQ oder Celery moeglich bleiben.
- Die interne persistente Queue ist deshalb der kleinste robuste Zielzustand.

## 5. Was bewusst NICHT umgesetzt wird

Diese Entscheidung fuehrt ausdruecklich **nicht** ein:

- keinen synchronen Fachresponse mit fertigem Importergebnis
- keine Abhaengigkeit von `FastAPI BackgroundTasks` als Zuverlaessigkeitsmodell
- keinen externen Broker wie Redis oder RabbitMQ
- kein Celery- oder RQ-Setup
- keine verteilte Worker-Farm
- keine WebSockets oder Server-Sent Events fuer Live-Fortschritt
- keinen Byte-genauen Upload-Fortschritt
- keine Multi-Queue-Priorisierung
- keine Batch- oder Massenupload-Orchestrierung

Fuer den aktuellen Scope gilt ebenfalls:

- keine Persistenz der Originaldatei als fachlich fuehrende Quelle
- kein automatisches Resume mitten im Parserlauf
- kein genaues Progress-Modell unterhalb von `queued` / `running` / `completed` / `failed`

## 6. Konsequenzen

Positive Konsequenzen:

- Upload und Admin-Rebuild folgen demselben Jobmodell.
- GUI und Backend sprechen einen stabilen asynchronen Vertrag.
- Fehler koennen als Jobfehler und als strukturierte Events nachvollzogen werden.
- Lokale Nutzung bleibt einfach, weil kein externer Queue-Stack erforderlich ist.

Negative Konsequenzen:

- Die App traegt selbst Verantwortung fuer Queue-Claiming, Requeueing und Stale-Lock-Handling.
- Ohne weiteren Ausbau bleibt Restart-Sicherheit nur teilweise erreicht.
- Der Uebergangszustand mit `BackgroundTasks` kann semantisch mit der Zielarchitektur verwechselt werden, wenn er nicht klar dokumentiert bleibt.

## 7. Migrationsplan

### Phase 0: Ist-Zustand festhalten

Ist bereits implementiert:

- `background_jobs` als persistierter Jobdatensatz
- `document_import` als Jobtyp
- `POST /documents/import -> 202 Accepted`
- Polling ueber `GET /api/v1/jobs/{job_id}`
- In-Process-Trigger via `FastAPI BackgroundTasks`

### Phase 1: `BackgroundTasks` auf Brueckenrolle begrenzen

Ziel:

- Dokumentieren und im Code klar trennen, dass `BackgroundTasks` nur den Startimpuls geben
- keine fachliche Abhaengigkeit mehr auf den Request-Lebenszyklus

Technische Schritte:

- Queue- und Worker-Begriffe in Code und Doku vereinheitlichen
- Jobhandler idempotent halten
- Observability an Job-Claim, Job-Start, Job-Ende anschliessen

### Phase 2: echten internen Worker-Loop einfuehren

Ziel:

- Jobs werden nicht mehr nur durch den gerade antwortenden Request angestossen

Technische Schritte:

- App-Start-Hook oder separater interner Worker-Loop zieht `queued` Jobs periodisch
- exklusives Claiming ueber atomaren Statuswechsel oder DB-Locking
- Wiederaufnahme oder Requeue alter `running` Jobs anhand von `locked_at`

### Phase 3: Restart-Sicherheit fertigstellen

Ziel:

- Neustarts duerfen Jobs nicht still verlieren

Technische Schritte:

- Stale-Lock-Timeout definieren
- Recovery-Regeln fuer `queued` und alte `running` Jobs dokumentieren
- Runbook fuer haengende Jobs ergaenzen

### Phase 4: `BackgroundTasks` optional entfernen

Ziel:

- Wenn der interne Worker-Loop stabil ist, kann der direkte `BackgroundTasks`-Kick entfallen

Nicht zwingend sofort noetig:

- Der API-Vertrag bleibt identisch
- Das Frontend braucht keine Migration

## 8. Akzeptanzkriterien fuer den Zielzustand

Die Entscheidung gilt erst dann als voll umgesetzt, wenn:

1. Upload-Jobs auch ohne aktiven Request-Thread abgearbeitet werden koennen.
2. Alte `running` Jobs nach Neustart erkannt und behandelt werden.
3. Fehlerursachen ueber Jobstatus und Observability nachvollziehbar bleiben.
4. Die GUI unveraendert ueber `202 + job_id + polling` arbeiten kann.
5. `FastAPI BackgroundTasks` hoechstens noch optionaler Trigger, aber nicht mehr notwendiger Scheduler sind.