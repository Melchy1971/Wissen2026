# Frontend M3a, M3b Retrieval-UI, M3c Chat/RAG-Foundation-UI und M4-Produktisierungsstand

Stand: 2026-05-05

## Status

Die GUI ist als read-only Basis umgesetzt, wurde fuer M3b um Retrieval-Suche erweitert, fuer M3c um eine dokumentgestuetzte Chat-Oberflaeche ergaenzt und in M4 um Upload- sowie Admin-Diagnostik-Slices erweitert. Ein voll integriertes Auth-/Workspace-Modell im Sinne von M4a ist im vorliegenden Frontend aber noch nicht konsistent abgeschlossen.

## Umgesetzter Scope

- Route `/documents` fuer die Dokumentliste.
- Route `/documents/:id` fuer Dokumentdetail.
- Anzeige von Metadaten, Importstatus, Versionen und Chunk-Vorschau im Detailscreen.
- Getrennter API-Client fuer die Dokument-Read-Pfade.
- Einfache Suchmaske auf der Dokumentuebersicht.
- Ergebnisliste fuer Chunk-Treffer mit Vorschau, Rank und Quellenanker.
- Link vom Suchtreffer zum Dokumentdetail.
- Route `/chat` und `/chat/:id` fuer Chat-Sessions.
- Upload-Block auf `/documents` mit Hintergrundjob-Polling.
- Admin-Diagnostik fuer Search-Index-Rebuild mit Hintergrundjob-Polling.
- Sessionliste fuer Chat.
- Formular fuer neue Session.
- Frageformular fuer Chat-Nachrichten.
- Nachrichtenverlauf mit Assistant-Antworten.
- Sichtbarer Quellenblock mit Citations.
- Sichtbarer Insufficient-Context-Zustand.
- Fehlerzustaende fuer `CHAT_SESSION_NOT_FOUND`, `CHAT_MESSAGE_INVALID`, `INSUFFICIENT_CONTEXT`, `RETRIEVAL_FAILED` und `LLM_UNAVAILABLE`.
- POST-Message-Request gegen den echten Vertrag mit `workspace_id`, `question` und `retrieval_limit`.
- POST-Message-Response wird als Assistant-Message mit Citations und Confidence gemappt.
- Lade-, Leer- und Fehlerzustaende.
- Sichtbare Fehlercodes im UI.
- Normalisierte Jobstatuslabels fuer Upload und Admin-Rebuild.

## M4b Upload-GUI im aktuellen Stand

Nachweisbar implementiert:

- Dateiauswahl fuer `.txt`, `.md`, `.docx`, `.doc` und `.pdf`
- Upload-Start direkt in der Dokumentansicht
- Blockierung eines zweiten Uploads waehrend `loading` oder `polling`
- Polling des generischen Jobstatus-Endpunkts
- generische Erfolgsanzeige mit Dateiname, Dokument-ID und Chunk-Anzahl
- generische Fehleranzeige ueber gemappte Fehlercodes wie `OCR_REQUIRED` und `PARSER_FAILED`
- Neuladen der Dokumentliste nach erfolgreichem Abschluss

Upload-Flow in der GUI:

- Benutzer waehlt Datei aus
- Frontend sendet `POST /documents/import`
- GUI zeigt `queued`/`running` ueber normalisierte Joblabels
- GUI pollt `GET /api/v1/jobs/{job_id}` alle 250 ms
- bei `completed` wird das Ergebnisfeld angezeigt
- bei `failed` wird `ErrorState` mit gemapptem Fehlercode angezeigt

Importstatus im UI:

- Jobstatuslabels: `In Warteschlange`, `Wird verarbeitet`, `Abgeschlossen`, `Fehlgeschlagen`
- fachliche Importstatuswerte wie `chunked` oder `duplicate` werden aktuell nicht als eigene UI-Zustaende visualisiert

Duplicate-Verhalten:

- Der Backend-Fall ist nachweisbar, die GUI behandelt ihn aktuell aber wie einen generischen Erfolgsfall.
- Es gibt keinen dedizierten Text wie `Dokument bereits vorhanden` und keine spezifische Aktion `Vorhandenes Dokument oeffnen`.

OCR-required-Verhalten:

- `OCR_REQUIRED` wird im allgemeinen Fehlerzustand angezeigt.
- Es gibt keinen spezialisierten OCR-Hinweis mit erklaerter Nicht-Scope-Folgeaktion.

## Bewusst nicht umgesetzt

- Mutation.
- Rollen und Rechte fuer regulare Fachendpunkte.
- OCR-UI.
- Embeddings.
- Query-Vorschlaege, Facetten und gespeicherte Suchen.
- Streaming.
- Agentenaktionen.
- Bearbeiten von Antworten.
- Dokument-Upload aus dem Chat.

## Aktuelle Struktur

- `frontend/src/api/`: API-Client, Dokument-Requests und Chat-Requests.
- `frontend/src/app/`: App-Rahmen und Routing.
- `frontend/src/components/`: Dokument-, Chat- und Statuskomponenten.
- `frontend/src/pages/`: Dokumentliste, Dokumentdetail und Chat-Seite.
- `frontend/src/view-models/`: Mapping und UI-nahe Ableitungen.
- `frontend/src/tests/pages/`: bisherige Screen-Tests.

## Aktueller Nachweis

- Screen-Tests fuer Dokumentliste und Dokumentdetail: vorhanden.
- Screen-Tests fuer Suchtreffer, Such-Leerzustand und Such-Fehlerzustand: vorhanden.
- Screen-Tests fuer Chat-Sessionliste, Chat-Nachrichten, Quellenanzeige und Insufficient-Context-Zustand: vorhanden.
- Screen-Tests fuer neue Session, Frage senden, Assistant-Antwort mit Quellen und Chat-Fehlercodes: vorhanden.
- Frontend-Build: gruen.

Aktuell verifiziert:

- `npm test`: `14 passed`
- `npm run build -- --clearScreen=false`: erfolgreich

## Aktuelle Luecken vor finaler Freigabe

- Keine separaten Routen fuer Versionen- und Chunk-Ansicht; beides ist aktuell in die Detailseite integriert.
- Keine echten Unit-Tests fuer ViewModel-Mapping und Fehlerabbildung.
- Keine separaten API-Mock-Tests fuer `404`, `409` und Netzwerkfehler auf API-Client-Ebene.
- Kein E2E-Smoke-Test fuer den Kernflow.
- Keine GUI-Pagination fuer umfangreiche Suchtreffermengen.
- Kein Browser-E2E-Test gegen einen laufenden Backend-Prozess; die aktuelle Absicherung erfolgt ueber Vitest/Fetch-Mocks gegen den echten API-Vertrag.
- Kein Direktlink in die Dokumentdetailansicht nach erfolgreichem Upload.
- Kein dedizierter Duplicate-Zustand im Upload-Ergebnis.
- Kein dedizierter OCR-Zustand im Upload-Ergebnis.
- Polling nutzt festen 250-ms-Takt ohne Backoff.
- Dokumente und Chat ziehen den Workspace weiterhin aus `workspace_id` im Query-String.
- Dokumente und Chat fallen teilweise auf einen hart codierten Default-Workspace zurueck.
- Kein Login-Screen, kein Logout und kein serverseitig aufgeloester Benutzerkontext in der GUI.
- Admin-Rechte werden separat ueber manuelles `x-admin-token` im UI modelliert.

## M4a Konsistenzstand im Frontend

Nachweisbar implementiert:

- Fehlerabbildung fuer `AUTH_REQUIRED`, `ADMIN_REQUIRED`, `WORKSPACE_REQUIRED`
- Admin-Diagnostik mit explizitem Admin-Token-Feld
- Workspace-Sichtbarkeit in Dokument- und Chat-Routen

Nicht nachweisbar implementiert:

- Login-Screen
- Logout-Flow
- Sessionwiederherstellung
- geschuetzter Route-Guard aus einem echten Auth-Kontext
- Vermeidung freier `workspace_id`-Navigation fuer Dokumente und Chat

## Fazit

Der Frontend-Schnitt deckt Dokumente, Suche, Chat sowie erste M4-Produktisierungs-Slices fuer Upload und Admin-Rebuild ab. Der Upload-Flow selbst ist sichtbar und testbar, M4b ist aber nicht konsistent abgeschlossen, weil zentrale Ergebniszustaende wie Duplicate, OCR-required und Direktnavigation ins Dokumentdetail in der GUI noch nicht spezifiziert umgesetzt sind.
