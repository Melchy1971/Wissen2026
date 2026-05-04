# Importpipeline V1

Dieses Dokument beschreibt den aktuellen Stand der Importpipeline. Der implementierte vertikale Pfad
unterstuetzt TXT, Markdown und DOCX. PDF, OCR und KI-Normalisierung sind ueber Schnittstellen
vorbereitet, aber nicht umgesetzt.

## Importablauf

`POST /documents/import` akzeptiert einen Multipart-Upload mit `.txt`, `.md`, `.docx`, `.doc` oder `.pdf`.

Der Ablauf:

1. Upload-Bytes werden temporaer gelesen.
2. MIME-Type wird aus der Dateiendung fuer `.txt` oder `.md` kanonisiert.
3. SHA-256 `content_hash` wird aus den Upload-Bytes erzeugt.
4. Parser extrahiert Text oder Markdown und Parser-Metadaten.
5. Deterministischer Markdown-Normalizer erzeugt `normalized_markdown` und `markdown_hash`.
6. Duplikatpruefung sucht im Default-Workspace nach gleichem `content_hash`.
7. Bei neuem Inhalt wird ein `documents`-Datensatz angelegt.
8. Version 1 wird in `document_versions` gespeichert.
9. `documents.current_version_id` wird gesetzt.
10. `document_chunks` werden aus `normalized_markdown` erzeugt und gespeichert.
11. Original-Bytes werden verworfen.

Die Antwort enthaelt `document_id`, `version_id`, `title`, `chunk_count` und `duplicate_status`.

## Parser-Grenzen

Implementiert:

- `.txt` ueber `TextParser`
- `.md` ueber `MarkdownParser`
- `.docx` ueber `DocxParser`
- `.doc` ueber `DocParser` (Systemabhaengigkeit: LibreOffice, siehe unten)
- `.pdf` ueber `PdfParser` (Text-Extraktion; Scan-PDFs setzen `ocr_required = True`)

Encoding:

- UTF-8 mit BOM-Unterstuetzung wird bevorzugt.
- Danach folgt ein kontrollierter Fallback auf `cp1252`, dann `latin-1`.

### PDF-Dokumente (`.pdf`)

`.pdf`-Dateien werden ueber `PdfParser` (Bibliothek: `pypdf`, keine Systemabhaengigkeit) unterstuetzt.
Der Parser extrahiert Text pro Seite und erzeugt Markdown mit Seitenmarkern:

```markdown
<!-- page:1 -->

Inhalt der ersten Seite...

<!-- page:2 -->

Inhalt der zweiten Seite...
```

**OCR-Erkennung:** Wenn die extrahierte Textmenge unter dem Schwellenwert liegt
(`total_chars < page_count * 50`), setzt der Parser `ocr_required = True`. Damit signalisiert er,
dass es sich um ein Scan-PDF handelt, dessen Inhalt per OCR erschlossen werden muss.
Ohne konfigurierten OCR-Engine gibt der Import einen kontrollierten Fehler zurueck.

Verhalten:
- Text-PDFs werden vollstaendig extrahiert.
- Seitenbezug bleibt ueber `<!-- page:N -->`-Kommentare im Markdown erhalten.
- Seiten, deren Extraktion fehlschlaegt, werden als leer behandelt (kein Abbruch).
- Beschaedigte oder nicht lesbare PDFs liefern `ParserError`.
- Originaldatei wird nicht gespeichert.
- `metadata.page_count`, `metadata.extraction_method`, `metadata.total_chars_extracted`
  und `metadata.ocr_required` werden immer gesetzt.

Nicht implementiert:

- OCR (naechster Task)
- automatische KI-Interpretation

### DOC-Altdokumente (`.doc`)

`.doc`-Dateien werden ueber `DocParser` unterstuetzt. Da Python kein natives `.doc`-Parsing bietet,
konvertiert `DocParser` die Datei lokal per LibreOffice Headless in ein temporaeres `.docx` und
uebergibt dieses anschliessend an `DocxParser`.

**Systemabhaengigkeit:** LibreOffice muss installiert sein und `soffice` muss im PATH verfuegbar
sein. Fehlt LibreOffice, gibt der Import einen `ConverterNotAvailableError` mit Installationshinweis
zurueck – kein stiller Fallback.

Verhalten:
- Temporaere Dateien werden in einem `TemporaryDirectory` angelegt und nach der Verarbeitung
  automatisch geloescht – auch bei Fehlern.
- Die Original-Bytes werden nicht gespeichert.
- `metadata.converter_used` enthaelt den Namen des verwendeten LibreOffice-Befehls.
- Bei fehlendem LibreOffice: HTTP 422 mit Hinweis auf Installation.
- Bei korrupter `.doc`-Datei: HTTP 422 mit LibreOffice-Fehlermeldung.

Parser speichern keine Originaldateien. Dateiname, MIME-Type, Bytegroesse, Parsername,
Parser-Version und erkannte Kodierung duerfen als Metadaten gespeichert werden.

## Normalisierungsregeln

Der deterministische Normalizer veraendert keine fachliche Bedeutung. Er normalisiert nur Form:

- Windows- und klassische Mac-Zeilenenden werden zu LF.
- Fuehrende und trailing Leerzeichen ausserhalb von Codebloecken werden entfernt.
- Mehrere Leerzeilen werden reduziert.
- Eine Abschluss-Newline wird ergaenzt.

Erhalten bleiben:

- Markdown-Tabellen
- Codebloecke
- Ueberschriften
- Listen

Der Normalizer validiert kein Markdown und repariert keine defekten Tabellen.

## Chunking-Regeln

Chunks entstehen aus `document_versions.normalized_markdown`.

Regeln:

- Primaer wird nach Ueberschriften segmentiert.
- Sekundaer wird an Absatzgrenzen geteilt.
- Tabellenbloecke werden zusammengehalten.
- Codebloecke werden zusammengehalten.
- Jeder Chunk erhaelt `chunk_index`, `heading_path`, `anchor`, `content`, `content_hash`,
  `token_estimate` und `metadata`.

Anchor-Format:

```text
dv:<document_version_id>:c0000
```

Der Anchor ist maschinenlesbar und innerhalb einer Dokumentversion eindeutig. Er bleibt stabil, wenn
Dokumentversion, Normalisierung und Chunking-Reihenfolge gleich bleiben.

## Duplicate-Handling

Duplikate werden ueber `documents.content_hash` im Default-Workspace erkannt.

- Neuer Inhalt: `duplicate_status = "created"`
- Bereits vorhandener Inhalt: `duplicate_status = "duplicate_existing"`

Bei Duplikaten wird kein neues Dokument und keine neue Version angelegt. Die bestehende
`document_id`, `version_id` und Chunk-Anzahl werden zurueckgegeben.

Die Duplikaterkennung ist aktuell app-seitig umgesetzt. Eine DB-Unique-Constraint fuer
`workspace_id` und `content_hash` existiert noch nicht.

## Speicherentscheidung

Originaldateien werden nicht gespeichert.

Persistiert werden:

- Dokument-Metadaten in `documents`
- kanonischer Markdown in `document_versions.normalized_markdown`
- Markdown-Hash und Parser-/Normalisierungsmetadaten
- Chunks mit Quellenankern in `document_chunks`

Upload-Bytes leben nur waehrend der Request-Verarbeitung im Speicher.

## Tests

Lokale Tests laufen ohne PostgreSQL:

```bash
cd backend
pytest
```

Der echte Import-Integrationstest benoetigt eine dedizierte Testdatenbank:

```powershell
cd backend
$env:TEST_DATABASE_URL="postgresql+psycopg://user:password@host:5432/test_database"
pytest tests/integration/test_documents_import.py
```
