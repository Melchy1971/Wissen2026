# M4b - Upload-GUI

Stand: 2026-05-05

Kontext:

- Paket 5 liefert bereits den funktionalen Import-Endpunkt `POST /documents/import`.
- M3a liefert die GUI-Grundstruktur fuer Dokumentliste und Dokumentdetail.
- M4a fuehrt Authentifizierung und Workspace-Isolation ein; M4b muss den Upload daran anschliessen und darf keine alte Default-Workspace-Logik im Frontend verstecken.
- Der aktuelle Importpfad ist auf persistierte Hintergrundjobs umgestellt. `POST /documents/import` liefert `202 Accepted` mit einem `document_import`-Job, der ueber den generischen Jobstatus-Endpunkt gepollt wird.

## 1. Zielbild

Dokumente koennen ueber die Web-GUI gezielt importiert werden. Nutzer sehen waehrend und nach dem Upload, ob der Import laeuft, erfolgreich war, ein Duplicate gefunden wurde, OCR fehlt oder der Parser fehlgeschlagen ist. Nach erfolgreichem Import kann direkt in die Dokumentdetailansicht gewechselt werden.

M4b fuehrt dabei keine Batch- oder Mehrfachupload-Logik ein. Es macht den bereits vorhandenen Importpfad produktiv sichtbar und nachvollziehbar und nutzt dafuer den gemeinsamen Hintergrundjob-Mechanismus.

## 2. Scope

In Scope:

- Datei auswaehlen
- Upload starten
- Importstatus anzeigen
- Parserfehler anzeigen
- Duplicate anzeigen
- `OCR_REQUIRED` anzeigen
- Dokumentdetail nach erfolgreichem Import oeffnen

Out of Scope:

- Drag-and-drop Mehrfachupload
- Ordnerimport
- vollwertige Joblisten-, Historien- oder Massensteuerungs-UI; die Architekturentscheidung fuer den gemeinsamen Hintergrundjob-Mechanismus ist separat dokumentiert in [docs/m4-background-jobs-decision.md](H:/WissenMai2026/docs/m4-background-jobs-decision.md)
- OCR-Ausfuehrung
- externe Speicher

## 3. Screen-Spezifikation

### 3.1 Upload-Seite

Zweck:

- Einstiegspunkt fuer den Import eines einzelnen Dokuments.

Inhalt:

- Seitentitel wie `Dokument importieren`
- Dateiauswahl fuer genau eine Datei
- sichtbarer Hinweis auf unterstuetzte Formate:
  - `.txt`
  - `.md`
  - `.docx`
  - `.doc`
  - `.pdf`
- Primaeraktion `Upload starten`
- Sekundaeraktion `Abbrechen` oder Rueckkehr zur Dokumentliste

Verhalten:

- Ohne Datei bleibt der Start-Button deaktiviert.
- Nach Dateiauswahl werden mindestens Dateiname und optional erkannter Typ angezeigt.
- Es wird kein clientseitiger Mehrfachupload zugelassen.
- Workspace-Kontext kommt aus M4a-Auth-/Workspace-Zustand, nicht aus freier Benutzereingabe.

### 3.2 Upload-Fortschritt

Zweck:

- Sichtbar machen, dass der asynchrone Importjob angelegt wurde und verarbeitet wird.

Inhalt:

- Ladezustand mit laufender Aktion wie `Dokument wird importiert`
- Dateiname
- Status- und Fortschrittshinweis aus dem Hintergrundjob

Verhalten:

- Im implementierten Stand zeigt M4b keinen Byte-Fortschritt, sondern den Jobzustand des asynchronen Imports.
- Die GUI nutzt normalisierte Labels fuer den Jobzustand:
  - `queued` -> `In Warteschlange`
  - `running` -> `Wird verarbeitet`
  - `completed` -> `Abgeschlossen`
  - `failed` -> `Fehlgeschlagen`
- Der Nutzer kann waehrenddessen keine zweite Upload-Aktion starten.

### 3.3 Import-Ergebnis

Zweck:

- Erfolgreichen Import oder Duplicate transparent rueckmelden.

Erfolgsfall `created`:

- Erfolgstitel wie `Dokument importiert`
- Anzeige von:
  - `title`
  - `document_id`
  - `chunk_count`
  - `import_status`
- Aktion `Dokument oeffnen`
- Aktion `Weiteres Dokument importieren`

Duplicate-Fall `duplicate_existing`:

- neutraler Hinweis wie `Dokument bereits vorhanden`
- Anzeige von:
  - `title`
  - `document_id`
  - `import_status = duplicate`
- Aktion `Vorhandenes Dokument oeffnen`
- Aktion `Zur Dokumentliste`

Verhalten:

- Nach erfolgreichem Upload soll die GUI das Dokumentdetail oeffnen koennen.
- Bei Duplicate wird nicht so getan, als sei ein neues Dokument entstanden.

### 3.4 Fehlerzustand

Zweck:

- Technische und fachliche Importfehler klar von Erfolg und Duplicate trennen.

Pflichtfaelle:

- `PARSER_FAILED`
- `OCR_REQUIRED`
- `UNSUPPORTED_FILE_TYPE`
- `SERVICE_UNAVAILABLE`
- Netzwerkfehler

Darstellung:

- klarer Fehler-Titel
- API-Fehlercode sichtbar
- menschenlesbare Fehlernachricht
- optional strukturierte Details aus `error.details`, soweit fuer Nutzer sinnvoll
- Aktion `Erneut versuchen`
- Aktion `Zurueck`

Sonderfall `OCR_REQUIRED`:

- expliziter Hinweis, dass die Datei erkannt wurde, aber ohne OCR im aktuellen Scope nicht importiert werden kann

Sonderfall `PARSER_FAILED`:

- Parserfehler nicht als `Service down` maskieren
- Dateiname und MIME-Type aus den Details, wenn vorhanden, sichtbar machen

## 4. API-Abhaengigkeiten

### Primärer Endpunkt

- `POST /documents/import`

Current Backend Contract:

- multipart Upload mit einem Feld `file`
- unterstuetzte Dateitypen werden serverseitig ueber Dateiendung und MIME-Typ kanonisiert
- asynchroner Response mit Jobobjekt

Response `202`:

```json
{
  "id": "job-1",
  "job_type": "document_import",
  "status": "queued",
  "workspace_id": "workspace-1",
  "progress_current": 0,
  "progress_total": 1,
  "progress_message": "Import ist in Warteschlange",
  "result": null
}
```

Polling-Endpunkt:

```json
{
  "id": "job-1",
  "job_type": "document_import",
  "status": "completed",
  "workspace_id": "workspace-1",
  "progress_current": 1,
  "progress_total": 1,
  "progress_message": "Import abgeschlossen",
  "result": {
    "document_id": "doc-1",
    "version_id": "ver-1",
    "import_status": "chunked",
    "duplicate_of_document_id": null,
    "chunk_count": 12,
    "parser_type": "txt-parser",
    "warnings": []
  }
}
```

Relevanter Polling-Pfad:

- `GET /api/v1/jobs/{job_id}`

Relevante Fehlercodes:

| Status | Code | Bedeutung fuer M4b |
|---:|---|---|
| `415` | `UNSUPPORTED_FILE_TYPE` | Dateiformat nicht unterstuetzt |
| `422` | `PARSER_FAILED` | Parser oder Normalisierung im Job fehlgeschlagen |
| `422` | `OCR_REQUIRED` | Datei braucht OCR, OCR ist aber nicht im Scope |
| `503` | `SERVICE_UNAVAILABLE` | Backend oder DB derzeit nicht verfuegbar |
| n/a | `NETWORK_ERROR` | Frontend kann API nicht erreichen |

### Folgeendpunkte nach Erfolg

- `GET /documents/{document_id}`
- `GET /documents/{document_id}/versions`
- `GET /documents/{document_id}/chunks`

Diese werden benoetigt, um nach erfolgreichem Import direkt in die Dokumentdetailansicht zu navigieren.

### Abhaengigkeit zu M4a

- M4b darf den Upload nicht mehr in einen impliziten Default-Workspace schreiben.
- Nach M4a muss der Upload dem authentifizierten Benutzer und dem aktiven Workspace-Kontext zugeordnet werden.
- Wenn der Backend-Endpunkt dafuer angepasst wird, darf das Frontend keinen freien `workspace_id`-Parameter als Vertrauensbasis einfuehren.

## 5. ViewModels

### `UploadFileSelectionVM`

Zweck:

- UI-Zustand vor dem Start des Uploads.

Felder:

- `fileName`
- `mimeTypeLabel`
- `sizeLabel`
- `isSupportedCandidate`

### `UploadProgressVM`

Zweck:

- UI-Zustand waehrend des Hintergrundjobs.

Felder:

- `fileName`
- `statusLabel`
- `statusMessage`
- `isSubmitting`

### `ImportResultVM`

Zweck:

- Erfolgs- oder Duplicate-Zustand nach API-Response.

Felder:

- `documentId`
- `versionId`
- `title`
- `chunkCount`
- `duplicateStatus`
- `duplicateStatusLabel`
- `importStatus`
- `importStatusLabel`
- `canOpenDocument`
- `primaryActionLabel`

### `ImportErrorVM`

Zweck:

- Einheitliche Fehlerdarstellung fuer Upload-Fehler.

Felder:

- `code`
- `title`
- `message`
- `details`
- `retryAllowed`
- `showOcrHint`
- `showParserHint`

### Mapper-Regeln

- API-Erfolg und Duplicate werden nicht in einen gemeinsamen generischen `success=true`-Zustand kollabiert.
- `duplicate_status` steuert explizit die Ergebnisdarstellung.
- `OCR_REQUIRED` und `PARSER_FAILED` muessen in eigene nutzerverstaendliche Fehlerzustande ueberfuehrt werden.
- Nach erfolgreichem Import muss das Ergebnis-ViewModel die Navigation ins Dokumentdetail eindeutig erlauben.

## 6. Akzeptanzkriterien

- Nutzer koennen in der GUI genau eine Datei fuer den Import auswaehlen.
- Der Upload kann gezielt gestartet werden.
- Waehrend des Imports ist ein klarer Arbeitszustand sichtbar.
- Erfolgreiche Importe zeigen Titel, Importstatus und Folgeaktion zum Oeffnen des Dokuments.
- Duplicate-Faelle werden sichtbar als bereits vorhandenes Dokument dargestellt.
- `OCR_REQUIRED` wird als eigener fachlicher Fehlerzustand angezeigt.
- `PARSER_FAILED` wird als eigener fachlicher Fehlerzustand angezeigt.
- Nach erfolgreichem Import kann direkt in die Dokumentdetailansicht gewechselt werden.
- M4b fuehrt keine Mehrfachupload-, Queue-, OCR- oder externen Speicherpfade ein.

## 7. Risiken

- Die GUI suggeriert echten Upload-Fortschritt, obwohl der Backend-Pfad aktuell nur einen synchronen Request kennt.
- Duplicate-Faelle werden als Erfolg ohne Unterschied angezeigt und verschleiern, dass kein neues Dokument angelegt wurde.
- Parser- und OCR-Fehler werden zu technisch oder zu generisch dargestellt.
- M4b koppelt an die aktuelle Default-Workspace-Logik statt an den kuenftigen M4a-Kontext.
- Zu frueh Mehrfachupload oder Queue-Logik mitzudenken verwischt den Scope und verkompliziert die erste produktive Upload-Oberflaeche.