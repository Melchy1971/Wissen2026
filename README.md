# Wissensbasis V1

Wissensbasis V1 ist die Startarchitektur fuer eine lokale GUI mit remote angebundener Datenbank, versionierten Dokumentinhalten und klar abgegrenztem V1-Scope.

## Projektziel

Das Projekt schafft die technische und dokumentarische Grundlage fuer eine Single-User-Wissensbasis mit folgenden Leitplanken:

- Backend auf FastAPI.
- Frontend auf React/Vite.
- PostgreSQL als remote betriebene Datenbank.
- Alembic-Migrationen im Backend-Kontext.
- Markdown als kanonische Textquelle.
- Keine Authentifizierung in V1.
- Keine Pflicht zu Vektorsuche in V1.
- Keine Speicherung von Originaldateien als fachlich fuehrende Quelle.

Der aktuelle Stand bildet bewusst die V1-Startstruktur und Architekturentscheidungen ab. Fachlogik ist nur teilweise vorbereitet und wird nicht durch diese Dokumentation vorweggenommen.

## Hauptstruktur

- `backend/`: FastAPI-Anwendung, Services, Modelle, Schemas, Jobs, Tests und Alembic-Migrationen.
- `frontend/`: React/Vite-Oberflaeche, Feature-Struktur und Frontend-Tests.
- `docs/`: Architekturuebersicht, ADRs, API-Notizen, Prompt-Vorlagen, Runbooks und Projektstatus.
- `scripts/`: Leichtgewichtige Hilfsskripte fuer lokale Entwicklung.

## Startpunkt fuer Entwickler

1. Projektziel und V1-Grenzen in dieser Datei lesen.
2. Architekturentscheidungen unter `docs/adr/` lesen.
3. Bereichsspezifische README-Dateien in `backend/`, `frontend/`, `docs/` und `scripts/` verwenden.
4. Danach lokale Entwicklungsumgebung fuer Backend und Frontend einrichten.

Beispiel fuer den Einstieg:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt

cd ..\frontend
npm install
```

## ADRs

- [Technische Grundentscheidung fuer V1](h:\WissenMai2026\docs\adr\0001-tech-stack-v1.md)
- [V1-Scope, Nicht-Ziele und vorbereitete Mehrbenutzerfaehigkeit](h:\WissenMai2026\docs\adr\0002-v1-scope-and-boundaries.md)

Die aelteren Kurzfassungen unter `docs/adr/0001-tech-stack.md` und `docs/adr/0002-v1-scope.md` existieren weiterhin, die aktuellen Paket-1-Referenzen zeigen jedoch auf die ausfuehrlichen V1-ADRs.
