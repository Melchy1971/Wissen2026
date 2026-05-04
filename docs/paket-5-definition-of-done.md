# Definition of Done: Paket 5

Diese Checkliste definiert die Muss-Kriterien fuer Paket 5. Ein Punkt gilt nur als erledigt, wenn er durch Code, Migration, Test, API-Response oder Dokumentation konkret pruefbar ist.

## API

- [ ] `GET /documents` erfordert `workspace_id`; ein fehlender Wert liefert den Fehlercode `WORKSPACE_REQUIRED`.
- [ ] `GET /documents` akzeptiert `limit` mit Default `20` und Maximalwert `100`.
- [ ] `GET /documents` akzeptiert `offset` mit Default `0`.
- [ ] `GET /documents` sortiert Dokumente stabil nach `created_at DESC`.
- [ ] `GET /documents` liefert pro Eintrag exakt die stabilen Felder `id`, `title`, `mime_type`, `created_at`, `updated_at`, `latest_version_id`, `import_status`, `version_count` und `chunk_count`.
- [ ] `GET /documents/{document_id}` liefert Dokument-Metadaten, `latest_version`, Parser-Metadaten, `import_status` und `chunk_summary`.
- [ ] `GET /documents/{document_id}` laedt keine vollstaendigen Chunks und keinen Volltext.
- [ ] `GET /documents/{document_id}` liefert `DOCUMENT_NOT_FOUND`, wenn die Dokument-ID unbekannt ist.
- [ ] `GET /documents/{document_id}` liefert `DOCUMENT_STATE_CONFLICT`, wenn ein Dokument in einem inkonsistenten Zustand ist.
- [ ] `GET /documents/{document_id}/versions` liefert alle Versionen eines Dokuments in `created_at DESC`.
- [ ] `GET /documents/{document_id}/versions` liefert pro Version `id`, `version_number`, `created_at` und `content_hash`.
- [ ] `GET /documents/{document_id}/chunks` liefert nur Chunks der `latest_version`.
- [ ] `GET /documents/{document_id}/chunks` liefert Chunks in stabiler Reihenfolge nach `position ASC`.
- [ ] `GET /documents/{document_id}/chunks` liefert pro Chunk `chunk_id`, `position`, `text_preview` und `source_anchor`.
- [ ] `text_preview` ist serverseitig auf maximal 200 Zeichen begrenzt.
- [ ] Der Dokument-Router enthaelt keinen direkten Datenbankzugriff.
- [ ] Router-Aufgaben sind auf Request-/Response-Mapping, Dependency Injection und HTTP-Fehlermapping beschraenkt.

## Datenbank

- [ ] Die Datenbank enthaelt einen Unique Constraint auf `(workspace_id, content_hash)` fuer Dokumente.
- [ ] Parallele Inserts desselben Inhalts im selben Workspace koennen nicht zu zwei Dokumentdatensaetzen fuehren.
- [ ] Duplicate-Konflikte werden deterministisch behandelt und geben das bestehende Dokument zurueck.
- [ ] Dokumente besitzen einen expliziten `import_status`.
- [ ] Erlaubte Importstatuswerte sind ausschliesslich `pending`, `parsing`, `parsed`, `chunked`, `failed` und `duplicate`.
- [ ] Bestehende Dokumente werden beim Migrationslauf anhand vorhandener Chunks auf `parsed` oder `chunked` gesetzt.
- [ ] Chunks enthalten einen normalisierten `source_anchor`.
- [ ] Das normalisierte `source_anchor`-Schema enthaelt `type`, `page`, `paragraph`, `char_start` und `char_end`.
- [ ] Legacy-Chunk-Metadaten werden bei Migrationen nicht geloescht.
- [ ] Alembic-Migrationen fuer Duplicate Constraint, Importstatus und Source-Anchor-Normalisierung sind vorhanden.

## Tests

- [ ] Es gibt einen API-Test fuer `GET /documents` mit Workspace-Filter, Pagination und Response-Feldern.
- [ ] Es gibt einen Service-Test fuer `get_documents()` ohne FastAPI.
- [ ] Es gibt einen API-Test fuer `GET /documents/{document_id}` inklusive `latest_version`, `parser_metadata`, `import_status` und `chunk_summary`.
- [ ] Es gibt Tests fuer `DOCUMENT_NOT_FOUND`.
- [ ] Es gibt Tests fuer `DOCUMENT_STATE_CONFLICT`.
- [ ] Es gibt einen Test, der parallele oder konkurrierende Duplicate-Inserts simuliert.
- [ ] Der Duplicate-Test beweist, dass nur ein Dokumentdatensatz entsteht.
- [ ] Es gibt einen API-Test fuer `GET /documents/{document_id}/chunks`.
- [ ] Der Chunk-Test prueft `position ASC`.
- [ ] Der Chunk-Test prueft, dass `text_preview` maximal 200 Zeichen enthaelt.
- [ ] Der Chunk-Test prueft das normalisierte `source_anchor`-Schema.
- [ ] Es gibt Tests fuer Parser-Fehler, nicht unterstuetzte Dateitypen und OCR-pflichtige PDFs.
- [ ] Die lokale Testumgebung laeuft ohne manuelle Setup-Schritte.
- [ ] PostgreSQL-Integrationstests sind dokumentiert und koennen ueber `TEST_DATABASE_URL` aktiviert werden.

## Dokumentation

- [ ] `docs/status.md` trennt `implemented`, `partial` und `missing` nachvollziehbar.
- [ ] `docs/status.md` nennt OCR als bekannte Limitation.
- [ ] `docs/status.md` nennt Parser-Qualitaet als bekannte Limitation, solange Parser uneinheitliche Qualitaet liefern.
- [ ] Der API-Vertrag fuer v1 ist dokumentiert.
- [ ] Der API-Vertrag beschreibt Endpunkte, Request-Parameter, Response-Schemas, Fehlerformat und Versionierung.
- [ ] Contract-critical Felder sind im API-Vertrag explizit markiert.
- [ ] Breaking-Change-Regeln sind dokumentiert.
- [ ] Die ADR fuer Dokument-Read-API und Datenkonsistenz vor Retrieval ist vorhanden.
- [ ] Die Dokumentation enthaelt den Grundsatz: Ground Truth ist Code, nicht Dokumentation.

## Fehlerbehandlung

- [ ] API-Fehler folgen einheitlich dem Format `{"error": {"code": "...", "message": "...", "details": {...}}}`.
- [ ] `DOCUMENT_NOT_FOUND` ist fuer unbekannte Dokumente implementiert.
- [ ] `WORKSPACE_REQUIRED` ist fuer fehlende Workspace-Filter implementiert.
- [ ] `INVALID_PAGINATION` ist fuer ungueltige `limit`- oder `offset`-Werte implementiert.
- [ ] `DOCUMENT_STATE_CONFLICT` ist fuer inkonsistente Dokumentzustaende implementiert.
- [ ] `DUPLICATE_DOCUMENT` ist als definierter Fehlercode vorhanden, auch wenn Duplicate-Imports regulaer deterministisch aufgeloest werden.
- [ ] `UNSUPPORTED_FILE_TYPE` ist fuer nicht unterstuetzte Dateitypen implementiert.
- [ ] `OCR_REQUIRED` ist fuer PDFs ohne extrahierbaren Text implementiert.
- [ ] `PARSER_FAILED` ist fuer Parser-Fehler implementiert.
- [ ] Validierungsfehler von FastAPI werden in den definierten Fehlerstandard gemappt, sofern sie Paket-5-Parameter betreffen.

## Performance

- [ ] `GET /documents` nutzt keine impliziten Lazy Loads.
- [ ] `GET /documents` erzeugt keine N+1 Queries fuer Version- oder Chunk-Aggregate.
- [ ] `GET /documents` liest keinen Volltext aus Chunks.
- [ ] `GET /documents/{document_id}` berechnet `chunk_summary` per Aggregat oder Projektion, nicht durch Laden aller Chunk-Objekte.
- [ ] `GET /documents/{document_id}/chunks` nutzt eine Projektion statt voller ORM-Objekte.
- [ ] `GET /documents/{document_id}/chunks` begrenzt den uebertragenen Text auf `text_preview`.
- [ ] `GET /documents/{document_id}/chunks` fragt ausschliesslich Chunks der aktuellen Version ab.
- [ ] `GET /documents/{document_id}/chunks` unterstuetzt optionales `limit`.
- [ ] Datenbankabfragen fuer Read-Endpunkte sind in Tests oder Code-Review nachvollziehbar auf ihre Query-Anzahl pruefbar.

## M3-Bereitschaft

- [ ] M3 kann Dokumente ausschliesslich ueber dokumentierte Read-Endpunkte lesen.
- [ ] M3 muss keine internen Tabellen, ORM-Modelle oder Parser-Metadaten direkt verwenden.
- [ ] Jedes Dokument ist ueber `id`, `workspace_id`, `latest_version_id` und `import_status` stabil bewertbar.
- [ ] Jede Version ist ueber `id`, `version_number`, `created_at` und `content_hash` nachvollziehbar.
- [ ] Jeder Chunk ist ueber `chunk_id`, `position` und `source_anchor` eindeutig referenzierbar.
- [ ] Duplicate-Dokumente sind DB-seitig verhindert.
- [ ] Parser-Fehler und OCR-Bedarf sind ueber API-Fehler oder `import_status` sichtbar.
- [ ] Der v1-API-Vertrag benennt, welche Felder sich fuer M3 nicht ohne Breaking Change aendern duerfen.
- [ ] No-Go fuer M3 gilt, wenn einer der Bereiche API, Datenbank, Fehlerbehandlung oder Tests ein Muss-Kriterium nicht erfuellt.
