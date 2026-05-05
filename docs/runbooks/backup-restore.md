# Backup und Restore Runbook

Stand: 2026-05-05

## Zweck

Dieses Runbook beschreibt den operativen Zielprozess fuer M4e Backup und Restore im lokalen Produktbetrieb.

Das fachliche Konzept und die Architekturregeln stehen in [docs/m4e-backup-restore.md](H:/WissenMai2026/docs/m4e-backup-restore.md).

## Betriebsziel

- Das System soll nach DB- oder Dateisystemfehlern vollstaendig wiederherstellbar sein.
- Ein Backup gilt nur dann als erfolgreich, wenn Datenbank, technische Originaldatei-Kopien, Konfiguration und Manifest konsistent vorliegen.
- Search-Index-Dateien sind nicht pflichtig, weil der Index rekonstruierbar ist.

## Minimaler manueller Ablauf

1. Applikation in einen ruhigen Betriebszustand bringen.
2. Backup-CLI mit Zielpfad ausfuehren.
3. Manifest und Checksummen pruefen.
4. Backup-Artefakt an einen getrennten Speicherort kopieren.

## Minimaler Restore-Ablauf

1. Zielumgebung vorbereiten.
2. Manifest und Checksummen validieren.
3. Datenbank-Dump einspielen.
4. Dateikopien und Konfiguration wiederherstellen.
5. `alembic upgrade head` ausfuehren.
6. Integritaetspruefung starten.
7. Search-Index neu aufbauen.

## Operative Pflichtpruefungen

- Sind alle im Manifest deklarierten Dateien vorhanden?
- Stimmen die Hashwerte?
- Ist die Datenbank nach Restore erreichbar?
- Ist die Migration auf `head`?
- Ist der Search-Index neu baubar?

## Status in M4e

- Konzept definiert
- CLI/API-Vorschlag definiert
- operative Automatisierung noch nicht implementiert
