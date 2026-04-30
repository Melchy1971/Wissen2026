# Services

Fachnahe Service- und Pipelinebausteine des Backends.

## Zweck

- Import, Parsing, OCR, Normalisierung, Dokumente, Suche, Chat, Analyse und Backup logisch trennen.
- Provider-Integrationen hinter klaren Schnittstellen halten.
- HTTP- und UI-Details aus diesem Bereich fernhalten.

## Import-Schnittstellen

- `import_service.py`: Orchestriert den spaeteren Ablauf Parser -> optional OCR -> Markdown-Normalisierung.
- `parser_service.py`: Parser-Protokoll und Parser-Auswahl fuer DOC, DOCX, TXT, MD, PDF und spaetere Erweiterungen.
- `ocr_service.py`: Protokoll fuer lokale OCR, ohne konkrete Engine-Implementierung.
- `markdown_normalizer.py`: Normalizer-Protokoll und KI-gestuetzter Fallback-Rahmen.
- `ki_provider.py`: Austauschbares Provider-Protokoll fuer KI-Normalisierung.
- `../models/import_models.py`: Transportmodelle fuer Importanfrage, extrahierten Inhalt, normalisierten Markdown, Ergebnis und Fehler.

Originaldatei-Bytes duerfen nur transient verarbeitet werden. Persistiert werden spaeter
normalisierter Markdown, Hashes und Metadaten wie Dateiname und MIME-Type.
