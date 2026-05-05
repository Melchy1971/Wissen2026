# Import

Stand: 2026-05-05

## M4b Upload-Flow

Der aktuelle Uploadpfad ist asynchron. Die GUI importiert keine Datei mehr synchron ueber einen direkten Fachresponse, sondern ueber einen persistierten Hintergrundjob.

Flow:

1. Benutzer waehlt in der Dokumentansicht genau eine Datei aus.
2. Das Frontend sendet `POST /documents/import` mit `multipart/form-data` und Feld `file`.
3. Der Backend-Endpoint legt einen `document_import`-Job an und antwortet mit `202 Accepted`.
4. Das Frontend pollt `GET /api/v1/jobs/{job_id}`.
5. Der Job endet in `completed` oder `failed`.
6. Bei `completed` enthaelt `result` das fachliche Importergebnis.
7. Bei `failed` bleiben fachliche Fehler in `error_code` und `error_message`.

## Importstatus

Jobstatus:

- `queued`
- `running`
- `completed`
- `failed`

Fachlicher Importstatus im Resultat:

- `chunked`: Dokument neu importiert und gechunkt
- `duplicate`: vorhandenes Dokument wiederverwendet

Weitere Datenpunkte im Resultat:

- `document_id`
- `version_id`
- `duplicate_of_document_id`
- `chunk_count`
- `parser_type`
- `warnings`

## Fehlercodes

Direkt am Upload-Endpoint:

- `FILE_TOO_LARGE`
- `UNSUPPORTED_FILE_TYPE`

Im Jobstatus:

- `PARSER_FAILED`
- `OCR_REQUIRED`
- `IMPORT_FAILED`

Bei Statusabfrage:

- `JOB_NOT_FOUND`

Im Frontend-Mapping:

- `NETWORK_ERROR`

## Duplicate-Verhalten

- Duplicate Detection ist serverseitig implementiert.
- Ein Duplicate fuehrt nicht zu einem fehlgeschlagenen Job, sondern zu einem erfolgreichen Abschluss mit `result.import_status = duplicate`.
- `result.duplicate_of_document_id` verweist auf das bestehende Dokument.
- Das aktuelle Frontend zeigt diesen Fall jedoch nur als generischen Erfolgszustand an.

## OCR-required-Verhalten

- PDF-Dateien mit zu wenig extrahierbarem Text werden als OCR-beduerftig erkannt.
- Da OCR nicht im Scope ist, endet der Job mit `status = failed` und `error_code = OCR_REQUIRED`.
- Das Frontend zeigt diesen Fall im allgemeinen Fehlerzustand an.

## Bekannte Einschraenkungen

- keine Mehrfachupload-UI
- kein Drag-and-drop
- kein Byte-Fortschritt, nur Jobstatus
- kein Direkt-Sprung in die Dokumentdetailansicht nach Erfolg
- kein dedizierter Duplicate-Ergebniszustand
- kein dedizierter OCR-Ergebniszustand
- Upload laeuft weiterhin im serverseitigen Default-Workspace-/Default-User-Kontext
- Dokumentansicht faellt weiterhin auf einen Default-Workspace im Frontend zurueck

## Abschlussentscheidung fuer M4b

- Dokumentation aktualisiert: ja
- Upload-Flow im Code nachweisbar: ja
- Vollstaendige M4b-Produktreife gemaess Zielbild: nein
- Entscheidung: M4b ist im aktuellen Repository nicht abgeschlossen