# Projektstatus

## Abgeschlossenes Paket

Paket 1 ist abgeschlossen.

Umfang von Paket 1:

- Repo-Struktur geprueft und dokumentarisch geschaerft.
- Tech-Stack-ADR fuer V1 erstellt.
- V1-Scope-ADR fuer Grenzen, Nicht-Ziele und vorbereitete Mehrbenutzerfaehigkeit erstellt.

## Geaenderte Dateien

- `README.md`
- `backend/README.md`
- `backend/tests/README.md`
- `backend/migrations/README.md`
- `backend/app/api/v1/endpoints/README.md`
- `backend/app/jobs/README.md`
- `backend/app/models/README.md`
- `backend/app/schemas/README.md`
- `backend/app/services/README.md`
- `frontend/README.md`
- `frontend/src/components/README.md`
- `docs/README.md`
- `docs/api/README.md`
- `docs/adr/0001-tech-stack-v1.md`
- `docs/adr/0002-v1-scope-and-boundaries.md`
- `scripts/README.md`

## Offene Risiken

- Die ADR-Nummerierung ist aktuell doppelt belegt, weil neben den neuen V1-ADRs noch aeltere Kurzfassungen mit denselben Nummern vorhanden sind.
- Die vorbereitenden Felder fuer spaetere Workspace- und User-Zuordnung sind bislang dokumentiert, aber noch nicht in Modellen oder Migrationen konkretisiert.
- Die Dokumentation beschreibt bewusst Zielstruktur und Architekturgrenzen, nicht den vollstaendigen Implementierungsstand einzelner Features.

## Naechstes Paket

Paket 2 ist bereit.

Empfohlener Fokus fuer Paket 2:

- Datenmodell und Alembic-Ausgangsschema fuer V1 konkretisieren.
- Klare Backend-Domains fuer Dokumente, Versionen und Import-Pipeline anlegen.
- API-Vertraege und leere Endpunkt-Skelette entlang der ADR-Grenzen vorbereiten.

## ADR-Startpunkte

- [Technische Grundentscheidung fuer V1](h:\WissenMai2026\docs\adr\0001-tech-stack-v1.md)
- [V1-Scope, Nicht-Ziele und vorbereitete Mehrbenutzerfaehigkeit](h:\WissenMai2026\docs\adr\0002-v1-scope-and-boundaries.md)