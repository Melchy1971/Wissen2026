# Frontend

React/Vite-Oberflaeche fuer Wissensbasis V1.

## Zweck

- UI, Navigation, Zustandsverwaltung und Benutzungsfluss liegen ausschliesslich im Frontend.
- Fachliche Persistenz, Import-Pipelines und Datenbankzugriffe bleiben im Backend.
- Die Struktur ist auf Feature-Ordner vorbereitet, ohne V1 fachlich zu erweitern.

## Struktur

- `src/app/`: App-Rahmen und Einstiegskomposition.
- `src/features/`: Feature-orientierte Oberflaechen fuer Import, Dokumente, Suche, Chat und Analyse.
- `src/components/`: Wiederverwendbare UI-Bausteine.
- `src/lib/`: Frontend-nahe Hilfen und Integrationscode.
- `src/styles/`: Globale Styles.
- `tests/`: Frontend-spezifische Tests.