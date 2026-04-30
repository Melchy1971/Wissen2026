# Architekturuebersicht

## Servicegrenzen

- Import-Service
- OCR-Service
- Parser-Service
- Markdown-Normalizer
- KI-Provider-Interface
- Document-Service
- Version-Service
- Search-Service
- Chat-Service
- Analysis-Service
- Backup-/Health-Service

## Persistenzregeln

- Originaldateien werden nicht gespeichert.
- Markdown ist kanonische Inhaltsquelle.
- Jede Dokumentaenderung erzeugt eine neue Version.
- Chunks enthalten Quellenanker fuer Suche und Chat-Zitate.
- Workspace- und User-Felder existieren ab M1, Auth bleibt V1-explizit ausgeschlossen.
