# Frontend M3a, M3b Retrieval-UI, M3c Chat/RAG-Foundation-UI und M4-Produktisierungsstand

Stand: 2026-05-05

## Status

Die GUI ist als read-only Basis umgesetzt, wurde fuer M3b um Retrieval-Suche erweitert, fuer M3c um eine dokumentgestuetzte Chat-Oberflaeche ergaenzt und in M4 um Upload- sowie Admin-Diagnostik-Slices erweitert. Der Upload-Slice nutzt bereits den zentralen Auth-/Workspace-Kontext; ein voll integriertes Frontend-Modell fuer Chat, Admin und Navigation ist aber noch nicht konsistent abgeschlossen.

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
- Lifecycle-Filter, Archive, Restore und Soft-Delete in der Dokument-GUI.
- Sessionliste fuer Chat.
- Formular fuer neue Session.
- Frageformular fuer Chat-Nachrichten.
- Nachrichtenverlauf mit Assistant-Antworten.
- Sichtbarer Quellenblock mit Citations.
- Sichtbarer Insufficient-Context-Zustand.
- Fehlerzustaende fuer `CHAT_SESSION_NOT_FOUND`, `CHAT_MESSAGE_INVALID`, `INSUFFICIENT_CONTEXT`, `RETRIEVAL_FAILED` und `LLM_UNAVAILABLE`.
- POST-Message-Request im aktuellen Frontend weiterhin mit `workspace_id`, `question` und `retrieval_limit`.
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
- Erfolgsanzeige mit Dateiname, Dokument-ID, `import_status` und Chunk-Anzahl
- Duplicate-Hinweis `bereits vorhanden` inklusive Anzeige der vorhandenen Dokument-ID
- generische Fehleranzeige ueber gemappte Fehlercodes wie `OCR_REQUIRED` und `PARSER_FAILED`
- Fehleranzeige fuer `FILE_TOO_LARGE`
- Neuladen der Dokumentliste nach erfolgreichem Abschluss
- Upload-Anfragen nutzen den zentralen Request-Kontext mit `Authorization` und `X-Workspace-Id`

Upload-Flow in der GUI:

- Benutzer waehlt Datei aus
- Frontend sendet `POST /documents/import`
- GUI zeigt `queued`/`running` ueber normalisierte Joblabels
- GUI pollt `GET /api/v1/jobs/{job_id}` alle 250 ms
- bei `completed` wird das Ergebnisfeld angezeigt
- bei `failed` wird `ErrorState` mit gemapptem Fehlercode angezeigt

Importstatus im UI:

- Jobstatuslabels: `In Warteschlange`, `Wird verarbeitet`, `Abgeschlossen`, `Fehlgeschlagen`
- fachliche Importstatuswerte wie `chunked` oder `duplicate` werden im Ergebnistext sichtbar angezeigt

Duplicate-Verhalten:

- Der Backend-Fall ist nachweisbar und die GUI zeigt `Dokument bereits vorhanden` als Erfolgshinweis.
- Es gibt weiterhin keine spezifische Aktion `Vorhandenes Dokument oeffnen`.

OCR-required-Verhalten:

- `OCR_REQUIRED` wird im allgemeinen Fehlerzustand angezeigt.
- Es gibt keinen spezialisierten OCR-Hinweis mit erklaerter Nicht-Scope-Folgeaktion.

## M4c Lifecycle-GUI im aktuellen Stand

Nachweisbar implementiert:

- Dokumentliste filtert zwischen `active` und `archived`.
- `deleted` wird in der GUI nicht als eigener Filter angeboten.
- Dokumentdetail zeigt Lifecycle-Badge und Lifecycle-Hinweis.
- aktive Dokumente koennen archiviert werden.
- archivierte Dokumente koennen wiederhergestellt werden.
- Dokumente koennen per GUI soft-geloescht werden.
- nach Archive und Restore wird der Detailzustand neu geladen.
- nach Soft-Delete navigiert die GUI zur Dokumentliste zurueck.

Nachweisbar nicht umgesetzt:

- keine GUI fuer geloeschte Dokumente
- keine Admin-Restore- oder Purge-Funktion fuer `deleted`
- kein eigener Frontend-Flow fuer historische Citations ueber den bereits angezeigten Chatverlauf hinaus

Bekannte Einschraenkungen im Lifecycle-Slice:

- Die GUI dokumentiert, dass archivierte Dokumente nicht in Suche oder Chat erscheinen, stützt sich dafuer aber auf Backend-Verhalten statt auf eigenen Browser-E2E-Nachweis.
- Der Lifecycle-Slice ist ueber Screen-Tests verifiziert, nicht ueber Browser-E2E gegen ein laufendes Gesamtsystem.
- Der letzte fokussierte Frontend-Lauf fuer angrenzende Lifecycle-/Rebuild-Screens war nicht vollstaendig gruen, weil ein separater Admin-Diagnostics-Test in einen `NETWORK_ERROR` lief.

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
- Keine Darstellung von `warnings` im Upload-Ergebnis.
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

Der Frontend-Schnitt deckt Dokumente, Suche, Chat sowie erste M4-Produktisierungs-Slices fuer Upload, Lifecycle und Admin-Rebuild ab. Der Lifecycle-Flow fuer Dokumentliste und Dokumentdetail ist ueber Screen-Tests nachgewiesen. Fuer M4c darf daraus aber nur gefolgert werden, dass die Dokument-GUI lokal konsistent wirkt; ein vollstaendig gruener angrenzender Frontend-Gesamtnachweis lag im letzten fokussierten Lauf nicht vor.
