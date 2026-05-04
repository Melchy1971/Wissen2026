# Technical Debt Register: Paket 5

Stand: 2026-05-04

Dieses Register priorisiert technische Schulden nach Paket 5. Score = Wahrscheinlichkeit in Prozent * Auswirkung von 1 bis 10. Hoehere Scores werden zuerst behandelt.

## Top 5 kritische Schulden

| Rang | Debt | Severity | Impact | Wahrscheinlichkeit | Auswirkung | Score | Strategie |
|---:|---|---|---|---:|---:|---:|---|
| 1 | PostgreSQL-Integrationstests sind optional und im Standard-Gate geskippt | high | falsche Ergebnisse, Wartbarkeit | 75% | 9 | 675 | fix |
| 2 | Chunk-Performance `< 200ms` ist nicht gemessen | high | Performance | 70% | 8 | 560 | fix |
| 3 | OCR fehlt fuer gescannte PDFs | high | falsche Ergebnisse | 60% | 9 | 540 | defer |
| 4 | Parser liefern Quellenpositionen uneinheitlich | high | falsche Ergebnisse | 70% | 7 | 490 | fix |
| 5 | Import-Persistenz nutzt direkten `psycopg`-Zugriff neben SQLAlchemy-Read-Layer | medium | Wartbarkeit | 75% | 6 | 450 | fix |

## Priorisierte Liste

| Rang | ID | Technical Debt | Kategorie | Severity | Impact | Wahrscheinlichkeit | Auswirkung | Score | Strategie |
|---:|---|---|---|---|---|---:|---:|---:|---|
| 1 | TD-P5-001 | PostgreSQL-Integrationstests laufen nur mit `TEST_DATABASE_URL` und werden im lokalen Standardlauf geskippt. | fehlende Validierung | high | falsche Ergebnisse, Wartbarkeit | 75% | 9 | 675 | fix |
| 2 | TD-P5-002 | Chunk-Abfrage hat keine belastbare `< 200ms`-Messung mit Referenzdaten und echtem PostgreSQL-Query-Plan. | Performance | high | Performance | 70% | 8 | 560 | fix |
| 3 | TD-P5-003 | OCR ist nicht implementiert; gescannte PDFs werden nur als `OCR_REQUIRED` sichtbar. | unvollstaendiges Feature | high | falsche Ergebnisse | 60% | 9 | 540 | defer |
| 4 | TD-P5-004 | `source_anchor` ist API-seitig normalisiert, aber Parser liefern `page`, `paragraph`, `char_start`, `char_end` nicht konsistent. | inkonsistentes Datenmodell | high | falsche Ergebnisse | 70% | 7 | 490 | fix |
| 5 | TD-P5-005 | Import-Persistenz nutzt direkten `psycopg`-Zugriff, waehrend Read-Pfade SQLAlchemy Repository/Service verwenden. | Workaround | medium | Wartbarkeit | 75% | 6 | 450 | fix |
| 6 | TD-P5-006 | `/api/v1/documents` ist Zielpfad im API-Vertrag, aber aktuell nur `/documents` implementiert. | unvollstaendiges Feature | medium | Wartbarkeit | 65% | 6 | 390 | fix |
| 7 | TD-P5-007 | Ziel-DB-Status `alembic current == 20260504_0007` ist nicht verifiziert. | fehlende Validierung | high | Datenverlust, falsche Ergebnisse | 45% | 8 | 360 | fix |
| 8 | TD-P5-008 | Bestandsdaten werden vor Unique-Migration nicht automatisch auf doppelte `(workspace_id, content_hash)` geprueft. | fehlende Validierung | high | Datenverlust | 40% | 8 | 320 | fix |
| 9 | TD-P5-009 | DOC-Import haengt von lokal installiertem LibreOffice ab. | Workaround | medium | falsche Ergebnisse, Wartbarkeit | 55% | 5 | 275 | akzeptieren |
| 10 | TD-P5-010 | Unbekannte interne Fehler koennen trotz Error-Envelope noch als generische Serverfehler statt fachlicher Codes erscheinen. | fehlende Validierung | medium | Wartbarkeit | 45% | 6 | 270 | fix |
| 11 | TD-P5-011 | `updated_at` wird nicht einheitlich per DB-Trigger oder ORM-Event gepflegt. | inkonsistentes Datenmodell | medium | falsche Ergebnisse | 50% | 5 | 250 | defer |
| 12 | TD-P5-012 | Parser-Confidence und Qualitaetsmetriken fehlen. | unvollstaendiges Feature | medium | falsche Ergebnisse | 45% | 5 | 225 | defer |
| 13 | TD-P5-013 | Importstatuswerte `pending`, `parsing` und `failed` sind modelliert, aber die Importpipeline nutzt den vollen Statusautomaten noch nicht durchgehend. | unvollstaendiges Feature | medium | Wartbarkeit | 40% | 5 | 200 | defer |
| 14 | TD-P5-014 | Mehrbenutzerfelder existieren, aber keine Auth- oder Workspace-Rechtepruefung. | unvollstaendiges Feature | medium | Datenverlust, falsche Ergebnisse | 35% | 6 | 210 | defer |
| 15 | TD-P5-015 | ADR-Nummerierung ist historisch doppelt belegt. | Wartbarkeit | low | Wartbarkeit | 30% | 3 | 90 | akzeptieren |

## Detailbewertung

### TD-P5-001: PostgreSQL-Integrationstests optional

- Severity: high
- Impact: falsche Ergebnisse, Wartbarkeit
- Wahrscheinlichkeit: 75%
- Auswirkung: 9
- Score: 675
- Strategie: fix

Risiko: SQLite-Tests koennen PostgreSQL-spezifische Fehler bei JSONB, Constraints, Migrationen oder Query-Planung nicht vollstaendig abdecken.

Behandlung:

- Dedizierte PostgreSQL-Testdatenbank bereitstellen.
- `TEST_DATABASE_URL` im Standard-Gate oder CI setzen.
- Paket-5-Gate nur noch ohne PostgreSQL-Skips freigeben.

### TD-P5-002: Chunk-Performance nicht gemessen

- Severity: high
- Impact: Performance
- Wahrscheinlichkeit: 70%
- Auswirkung: 8
- Score: 560
- Strategie: fix

Risiko: Die Query ist als Projektion gebaut, aber ohne Referenzdaten und Query-Plan ist das `< 200ms`-Kriterium nicht bewiesen.

Behandlung:

- Referenzdatensatz definieren.
- Benchmark-Test fuer `GET /documents/{document_id}/chunks` ergaenzen.
- PostgreSQL-Indexbedarf fuer `(document_id, document_version_id, chunk_index)` pruefen.

### TD-P5-003: OCR fehlt

- Severity: high
- Impact: falsche Ergebnisse
- Wahrscheinlichkeit: 60%
- Auswirkung: 9
- Score: 540
- Strategie: defer

Risiko: Gescannte PDFs bleiben fuer M3 Suche/Retrieval inhaltlich unbrauchbar, obwohl sie als Dateien importiert werden koennen.

Behandlung:

- OCR als eigenes Paket planen.
- Bis dahin `OCR_REQUIRED` als harten Ausschluss fuer Suche/Retrieval nutzen.
- Keine OCR-pflichtigen Dokumente indexieren.

### TD-P5-004: Quellenpositionen uneinheitlich

- Severity: high
- Impact: falsche Ergebnisse
- Wahrscheinlichkeit: 70%
- Auswirkung: 7
- Score: 490
- Strategie: fix

Risiko: M3 kann zwar Chunks stabil referenzieren, aber Zitate koennen grob oder unvollstaendig sein.

Behandlung:

- Parser-spezifische Mapping-Tests fuer TXT, PDF und DOCX ergaenzen.
- `char_start`/`char_end` fuer Textpfade stabilisieren.
- PDF-Seiten und DOCX-Paragraphen granularer mappen.

### TD-P5-005: Uneinheitliche DB-Schicht im Import

- Severity: medium
- Impact: Wartbarkeit
- Wahrscheinlichkeit: 75%
- Auswirkung: 6
- Score: 450
- Strategie: fix

Risiko: Read-Pfade sind sauber geschichtet, Import-Persistenz nutzt aber direkten `psycopg`-Zugriff. Das erhoeht Wartungsaufwand und Risiko divergierender Transaktionslogik.

Behandlung:

- Import-Repository einfuehren.
- Gemeinsame SQLAlchemy-Session-Strategie fuer Import und Read nutzen.
- Duplicate-Konfliktbehandlung als Repository-Funktion kapseln.

## Strategieuebersicht

### Fix

Kurzfristig beheben, bevor M3 produktiv auf Paket 5 aufsetzt:

- TD-P5-001 PostgreSQL-Integrationstests verpflichtend machen.
- TD-P5-002 Chunk-Performance messen und indexieren.
- TD-P5-004 Quellenpositionen verbessern.
- TD-P5-005 Import-Persistenz vereinheitlichen.
- TD-P5-006 `/api/v1/documents` Alias implementieren.
- TD-P5-007 Ziel-DB-Migrationsstand verifizieren.
- TD-P5-008 Duplicate-Preflight fuer Bestandsdaten.
- TD-P5-010 Fehlerklassifikation fuer unbekannte interne Fehler schaerfen.

### Defer

Bewusst nach Paket 5 planen, aber nicht vergessen:

- TD-P5-003 OCR-Engine.
- TD-P5-011 Einheitliche `updated_at`-Pflege.
- TD-P5-012 Parser-Confidence.
- TD-P5-013 Vollstaendiger Importstatus-Automat.
- TD-P5-014 Auth und Workspace-Rechte.

### Akzeptieren

Als bekannte Einschraenkung akzeptieren, solange sie dokumentiert bleibt:

- TD-P5-009 LibreOffice-Abhaengigkeit fuer DOC-Import.
- TD-P5-015 Historische ADR-Nummerierung.
