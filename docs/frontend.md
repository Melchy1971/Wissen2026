# Frontend M3a, M3b Retrieval-UI und M3c Chat/RAG-Foundation-UI

Stand: 2026-05-05

## Status

Die GUI ist als read-only Basis umgesetzt, wurde fuer M3b um Retrieval-Suche erweitert und fuer M3c um eine dokumentgestuetzte Chat-Oberflaeche ergaenzt. Die ChatPage ist jetzt gegen die echte Backend-Chat-API ausgerichtet. Ein voll integrierter Produkt-Chat im Sinne von M4 ist damit noch nicht erreicht; M3c Foundation ist aber abgeschlossen.

## Umgesetzter Scope

- Route `/documents` fuer die Dokumentliste.
- Route `/documents/:id` fuer Dokumentdetail.
- Anzeige von Metadaten, Importstatus, Versionen und Chunk-Vorschau im Detailscreen.
- Getrennter API-Client fuer die Dokument-Read-Pfade.
- Einfache Suchmaske auf der Dokumentuebersicht.
- Ergebnisliste fuer Chunk-Treffer mit Vorschau, Rank und Quellenanker.
- Link vom Suchtreffer zum Dokumentdetail.
- Route `/chat` und `/chat/:id` fuer Chat-Sessions.
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

## Bewusst nicht umgesetzt

- Upload.
- Mutation.
- Rollen und Rechte.
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

## Fazit

Der Frontend-Schnitt deckt den M3c-Chatvertrag ab und ist auf Vertragsebene belastbar. M3c ist frontendseitig abgeschlossen. M4 bleibt eine fachliche Erweiterung fuer produktiven LLM-Betrieb, Streaming, erweiterte Chat-Funktionen und Analyseintegration.
