# Frontend M3a, M3b Retrieval-UI und M3c Chat-UI

Stand: 2026-05-04

## Status

Die GUI ist als read-only Basis umgesetzt, wurde fuer M3b um Retrieval-Suche erweitert und fuer M3c um eine dokumentgestuetzte Chat-Oberflaeche ergaenzt. M3c ist im Frontend funktional sichtbar, aber end-to-end noch nicht hart abgeschlossen, solange die stabile Chat-API im Backend fehlt.

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
- Frontend-Build: gruen.

## Aktuelle Luecken vor finaler Freigabe

- Keine separaten Routen fuer Versionen- und Chunk-Ansicht; beides ist aktuell in die Detailseite integriert.
- Keine echten Unit-Tests fuer ViewModel-Mapping und Fehlerabbildung.
- Keine separaten API-Mock-Tests fuer `404`, `409` und Netzwerkfehler auf API-Client-Ebene.
- Kein E2E-Smoke-Test fuer den Kernflow.
- Keine GUI-Pagination fuer umfangreiche Suchtreffermengen.
- Keine echte End-to-End-Verifikation gegen eine stabile Backend-Chat-API.

## Fazit

Der Frontend-Schnitt deckt jetzt auch den M3c-Chatvertrag ab und ist auf Vertragsebene belastbar. Der haerteste Restblocker fuer einen echten M3c-Abschluss liegt derzeit nicht im Frontend, sondern in der fehlenden stabilen Backend-Chat-API und im fehlenden end-to-end RAG-Nachweis.