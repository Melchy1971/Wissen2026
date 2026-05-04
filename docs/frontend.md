# Frontend M3a

Stand: 2026-05-04

## Status

M3a ist als minimaler read-only GUI-Prototyp umgesetzt, aber noch nicht als vollstaendig abgeschlossen freigegeben.

## Umgesetzter Scope

- Route `/documents` fuer die Dokumentliste.
- Route `/documents/:id` fuer Dokumentdetail.
- Anzeige von Metadaten, Importstatus, Versionen und Chunk-Vorschau im Detailscreen.
- Getrennter API-Client fuer die Dokument-Read-Pfade.
- Lade-, Leer- und Fehlerzustaende.
- Sichtbare Fehlercodes im UI.

## Bewusst nicht umgesetzt

- Suche.
- Chat.
- Upload.
- Mutation.
- Rollen und Rechte.
- OCR-UI.
- Embeddings.

## Aktuelle Struktur

- `frontend/src/api/`: API-Client und Dokument-Requests.
- `frontend/src/app/`: App-Rahmen und Routing.
- `frontend/src/components/`: Dokument- und Statuskomponenten.
- `frontend/src/pages/`: Dokumentliste und Dokumentdetail.
- `frontend/src/view-models/`: Mapping und UI-nahe Ableitungen.
- `frontend/src/tests/pages/`: bisherige Screen-Tests.

## Aktuelle Luecken vor finaler Freigabe

- Keine separaten Routen fuer Versionen- und Chunk-Ansicht; beides ist aktuell in die Detailseite integriert.
- Keine echten Unit-Tests fuer ViewModel-Mapping und Fehlerabbildung.
- Keine separaten API-Mock-Tests fuer `404`, `409` und Netzwerkfehler auf API-Client-Ebene.
- Kein E2E-Smoke-Test fuer den Kernflow.

## Fazit

Der Frontend-Schnitt ist als M3a-Prototyp belastbar genug fuer weitere GUI-Haertung, aber noch nicht testseitig vollstaendig genug fuer einen harten Abschluss und ein Go fuer M3b Retrieval.