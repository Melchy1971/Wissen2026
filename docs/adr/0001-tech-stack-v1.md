# ADR 0001: Technische Grundentscheidung fuer die V1-Wissensbasis

## Status

Angenommen.

## Kontext

Die Wissensbasis V1 benoetigt eine technisch klare, lokal betreibbare Startarchitektur mit folgenden Randbedingungen:

- Backend als HTTP-API fuer Import, Verarbeitung, Suche, Chat, Analyse und Persistenzkoordination.
- Frontend als lokal gestartete GUI fuer den Single-User-Betrieb.
- PostgreSQL wird remote betrieben; die GUI laeuft in V1 lokal.
- Datenbankschemaaenderungen muessen versioniert und reproduzierbar sein.
- KI-Zugriffe muessen ueber ein austauschbares Provider-Interface laufen; V1 verwendet lokal Ollama.
- OCR soll lokal ausfuehrbar bleiben.
- Authentifizierung ist explizit nicht Bestandteil von V1.
- Spaetere Remote-Faehigkeit soll architektonisch vorbereitet, aber nicht vorgezogen werden.

Zusatzannahmen fuer V1:

- Originaldateien werden nicht gespeichert.
- Markdown ist die kanonische Textquelle nach Import und Verarbeitung.
- Datenmodelle duerfen vorbereitende Felder fuer spaetere Workspace- und User-Zuordnung enthalten, ohne daraus bereits ein Mehrbenutzerkonzept abzuleiten.

## Entscheidung

Die V1-Wissensbasis verwendet folgenden technischen Grundschnitt:

- Backend: FastAPI.
- Frontend: React mit Vite.
- Datenbank: remote betriebenes PostgreSQL.
- Migrationen: Alembic im Backend-Kontext.
- KI-Anbindung: lokaler Ollama-Provider hinter einem austauschbaren Provider-Interface.
- OCR: lokal ausgefuehrte OCR-Komponenten.
- Betrieb V1: GUI lokal, Datenbank remote.

Die Entscheidung gilt als umgesetzt, wenn die folgenden Architekturregeln eingehalten werden:

1. Backend-HTTP-Logik, Datenzugriff, Migrationsverwaltung und Service-Orchestrierung liegen ausschliesslich im Backend.
2. Frontend-Code enthaelt keine direkte Datenbanklogik und keine Backend-internen Fachimplementierungen.
3. Alembic-Konfiguration und Revisionsverwaltung liegen unter dem Backend-Verzeichnis.
4. KI-Provider werden nur ueber das Provider-Interface eingebunden; V1 nutzt dafuer lokal Ollama.
5. OCR wird lokal ausgefuehrt und fuehrt keine verpflichtende Cloud-Abhaengigkeit ein.
6. Die Persistenz speichert abgeleitete Inhalte und Metadaten, aber keine Originaldateien als kanonische Quelle.
7. Authentifizierung bleibt in V1 unimplementiert.

## Alternativen

### Monolithisches Python-Rendering ohne getrenntes Frontend

Verworfen, weil die klare Trennung zwischen GUI und API fuer spaetere Remote-Faehigkeit schwach waere und Frontend-Entwicklung unnötig an Backend-Rendering koppeln wuerde.

### Vollstaendig lokaler Betrieb mit lokaler Datenbank

Verworfen, weil der vorgesehene V1-Betrieb eine remote erreichbare PostgreSQL-Datenbank voraussetzt und Schemaentwicklung gegen eine realistischere Betriebsform validiert werden soll.

### SQLite statt PostgreSQL

Verworfen, weil spaetere Remote-Faehigkeit, Mehrbenutzer-Vorbereitung und robuste Migrationspfade mit PostgreSQL konsistenter vorbereitet werden als mit einer lokalen Dateidatenbank.

### Migrationen ausserhalb des Backends

Verworfen, weil Alembic direkt an Python-Modelle und Backend-Konfiguration gekoppelt ist und ausserhalb des Backend-Kontexts unnoetige Pflege- und Abstimmungsfehler erzeugen wuerde.

### Direkte Bindung an einen einzelnen KI-Provider ohne Abstraktion

Verworfen, weil ein austauschbares Provider-Interface noetig ist, um lokale V1-Nutzung zu ermoeglichen und spaetere Providerwechsel oder Tests ohne strukturelle Umbauten vorzubereiten.

### Cloud-basierte OCR als V1-Standard

Verworfen, weil V1 lokale Verarbeitung bevorzugt und keine zusaetzliche verpflichtende externe Laufzeit- oder Datenschutzabhaengigkeit einfuehren soll.

## Konsequenzen

### Positive Konsequenzen

- Die Architektur ist fuer V1 einfach lokal entwickelbar und bleibt dabei klar getrennt.
- PostgreSQL und Alembic schaffen eine belastbare Grundlage fuer versionierte Schemaentwicklung.
- Das Provider-Interface reduziert die Kopplung an lokale oder spaetere andere KI-Backends.
- Lokale OCR und lokaler Ollama-Betrieb halten V1 unabhaengig von verpflichtenden Cloud-Diensten.
- Die Trennung von Frontend und Backend bereitet spaetere Remote-Bereitstellung vor, ohne sie bereits umzusetzen.

### Negative Konsequenzen und Trade-offs

- Der Betrieb verteilt sich bereits in V1 ueber lokale GUI und remote Datenbank; das erhoeht Konfigurations- und Netzwerkabhaengigkeiten gegenueber einem rein lokalen Setup.
- React/Vite plus FastAPI fuehren bewusst zwei getrennte Entwicklungsumgebungen statt eines einfacheren Ein-Prozess-Stacks ein.
- PostgreSQL ist betriebsseitig schwerer als SQLite, liefert aber die gewuenschte Zukunftsfaehigkeit.
- Das Provider-Interface erzeugt zusaetzliche Abstraktion, obwohl V1 nur einen realen Provider vorsieht.

## Risiken

- Netzwerkausfaelle oder Konfigurationsfehler zwischen lokaler GUI, lokalem Backend und remote Datenbank koennen V1-Betrieb stoeren.
- Lokale OCR und lokaler Ollama-Betrieb haengen von der Leistungsfaehigkeit des Nutzerrechners ab.
- Die Vorbereitung von Workspace-/User-Feldern kann spaeter falsch als teilweise Mehrbenutzerunterstuetzung interpretiert werden, wenn die V1-Grenzen nicht konsequent dokumentiert bleiben.
- Ein Provider-Interface ohne disziplinierte Nutzung kann spaeter durch provider-spezifische Sonderfaelle unterlaufen werden.

## Nicht-Ziele

- Keine Implementierung von Authentifizierung, Rollen oder Mandantenlogik in V1.
- Keine Festlegung auf Vektorsuche als Pflichtbestandteil von V1.
- Keine Einfuehrung einer Docker-Compose-Pflicht fuer Entwicklung oder Betrieb.
- Keine Vorentscheidung fuer spaetere Cloud- oder Hosting-Topologien ausserhalb des beschriebenen V1-Betriebs.
- Keine Speicherung von Originaldateien als fachlich fuehrende Quelle.