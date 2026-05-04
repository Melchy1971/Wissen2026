# Datenmodell-Invarianten: Document, DocumentVersion, Chunk

Stand: 2026-05-04

Diese Invarianten beschreiben Regeln, die fuer das Dokumentmodell immer gelten muessen. Code und Datenbank sind die Ground Truth. Wenn eine Invariante aktuell nicht hart abgesichert ist, wird sie als Risiko benannt.

## Invariantenliste

| ID | Invariante | Aktuelle Absicherung | Empfohlene Absicherung |
|---|---|---|---|
| INV-001 | Ein lesbares Dokument hat mindestens eine Version. | Service teilweise | DB/Service |
| INV-002 | `Document.current_version_id` zeigt auf eine Version desselben Dokuments. | teilweise DB | DB |
| INV-003 | Eine Version gehoert genau zu einem Dokument. | DB | beibehalten |
| INV-004 | `version_number` ist pro Dokument eindeutig. | DB | beibehalten |
| INV-005 | Versionnummern sind positiv und monoton steigend pro Dokument. | teilweise DB/Code | DB/Service |
| INV-006 | `content_hash` ist pro Workspace eindeutig. | DB | beibehalten |
| INV-007 | Ein Chunk gehoert genau zu einer Version. | DB | beibehalten |
| INV-008 | Ein Chunk gehoert zum gleichen Dokument wie seine Version. | DB | beibehalten |
| INV-009 | `Chunk.position` ist eindeutig innerhalb einer Version. | DB | beibehalten |
| INV-010 | Chunk-Positionen sind nicht negativ und stabil sortierbar. | DB | beibehalten |
| INV-011 | Chunk-Anker ist eindeutig innerhalb einer Version. | DB | beibehalten |
| INV-012 | Chunks der aktuellen Version sind bei `import_status = chunked` vorhanden. | Service | DB/Service |
| INV-013 | Chunk-Inhalt ist nicht leer. | DB | beibehalten |
| INV-014 | `source_anchor` folgt dem normalisierten Schema. | Migration/Service teilweise | DB/Service |
| INV-015 | Importstatus ist einer der erlaubten Werte. | DB | beibehalten |
| INV-016 | `parsed`/`chunked` Dokumente haben eine aktuelle Version. | Service | DB/Service |
| INV-017 | `failed` oder `pending` Dokumente muessen nicht versioniert sein. | Service-Konvention | Service |
| INV-018 | `Document.updated_at >= Document.created_at`. | keine harte Absicherung | DB |
| INV-019 | `DocumentVersion.created_at >= Document.created_at`. | keine harte Absicherung | Service/DB |
| INV-020 | `DocumentVersion.markdown_hash` ist nicht leer. | DB | beibehalten |

## Detailregeln

### INV-001: Ein lesbares Dokument hat mindestens eine Version

Definition:

- Ein Dokument mit `import_status in ('parsed', 'chunked', 'duplicate')` muss eine aktuelle Version besitzen.
- Ein Dokument mit `pending`, `parsing` oder `failed` darf temporaer ohne Version existieren.

Verletzungsfall:

- `documents.import_status = 'chunked'`, aber `documents.current_version_id IS NULL`.
- `GET /documents/{id}` koennte Metadaten liefern, aber keine nachvollziehbare kanonische Textquelle.

Aktuelle Absicherung:

- Service: `DocumentReadService` behandelt `parsed`/`chunked` ohne Version als `DOCUMENT_STATE_CONFLICT`.
- DB: keine harte Check-Constraint, weil `current_version_id` nullable ist.

Empfohlene Absicherung:

- DB Check Constraint:
  - `import_status in ('pending', 'parsing', 'failed') OR current_version_id IS NOT NULL`
- Zusaetzlich Service-Test fuer alle Statuskombinationen.

### INV-002: `Document.current_version_id` zeigt auf eine Version desselben Dokuments

Definition:

- Wenn `documents.current_version_id` gesetzt ist, muss die referenzierte Version existieren und `document_versions.document_id = documents.id` haben.

Verletzungsfall:

- Dokument A zeigt auf eine Version von Dokument B.
- M3 wuerde Chunks oder Versionen eines falschen Dokuments indexieren.

Aktuelle Absicherung:

- DB: Foreign Key `documents.current_version_id -> document_versions.id` prueft nur Existenz der Version.
- DB: keine zusammengesetzte Constraint fuer `(documents.id, current_version_id)`.

Empfohlene Absicherung:

- Composite Foreign Key von `(documents.id, current_version_id)` auf `document_versions(document_id, id)`.
- Vorhandene Unique Constraint `uq_document_versions_document_id_id` kann dafuer genutzt werden.

### INV-003: Eine Version gehoert genau zu einem Dokument

Definition:

- Jede Zeile in `document_versions` hat genau ein nicht-null `document_id`.

Verletzungsfall:

- Version ohne Dokument oder mit geloeschtem Dokument.

Aktuelle Absicherung:

- DB: `document_versions.document_id` ist `NOT NULL`.
- DB: Foreign Key auf `documents.id` mit `ON DELETE CASCADE`.

Empfohlene Absicherung:

- Beibehalten.
- Keine API schreiben, die Versionen ohne Dokument erzeugt.

### INV-004: `version_number` ist pro Dokument eindeutig

Definition:

- Innerhalb eines Dokuments darf es jede `version_number` nur einmal geben.

Verletzungsfall:

- Zwei Versionen eines Dokuments haben `version_number = 1`.
- Chronologie und aktuelle Version werden uneindeutig.

Aktuelle Absicherung:

- DB: Unique Constraint `uq_document_versions_document_version_number` auf `(document_id, version_number)`.

Empfohlene Absicherung:

- Beibehalten.
- Service soll neue Versionen nur ueber `max(version_number) + 1` oder sequenzielle Locking-Strategie erzeugen.

### INV-005: Versionnummern sind positiv und monoton steigend pro Dokument

Definition:

- `version_number > 0`.
- Eine neuere Version eines Dokuments darf keine kleinere oder gleiche Nummer als eine bestehende neue Version bekommen.

Verletzungsfall:

- Versionen `1, 3, 2` werden nachtraeglich erzeugt.
- `created_at DESC` und `version_number DESC` widersprechen sich fachlich.

Aktuelle Absicherung:

- DB: Check Constraint `version_number > 0`.
- DB: Eindeutigkeit pro Dokument.
- Keine harte DB-Absicherung fuer Lueckenlosigkeit oder Monotonie bezogen auf Erstellreihenfolge.

Empfohlene Absicherung:

- Service-Methode fuer Versionserzeugung als einzige Schreibstelle.
- Bei paralleler Versionserzeugung Transaktion mit Row Lock auf `documents`.
- Optional DB-Trigger, der neue `version_number` gegen `max(version_number)` validiert.

### INV-006: `content_hash` ist pro Workspace eindeutig

Definition:

- Innerhalb eines Workspaces darf es denselben Dokument-Content-Hash nur einmal geben.

Verletzungsfall:

- Zwei Dokumente mit gleichem Inhalt im selben Workspace.
- Suche/Retrieval liefert doppelte Treffer.

Aktuelle Absicherung:

- DB: Unique Constraint `uq_documents_workspace_content_hash` auf `(workspace_id, content_hash)`.
- Service: Duplicate Handling gibt bestehendes Dokument zurueck.

Empfohlene Absicherung:

- Beibehalten.
- Vor Produktivmigration Datencheck auf bestehende Duplikate ausfuehren.

### INV-007: Ein Chunk gehoert genau zu einer Version

Definition:

- Jeder Chunk hat genau eine `document_version_id`.

Verletzungsfall:

- Chunk ohne Version.
- Chunk kann nicht stabil zitiert oder reindexiert werden.

Aktuelle Absicherung:

- DB: `document_chunks.document_version_id` ist `NOT NULL`.
- DB: Foreign Key auf `document_versions.id` mit `ON DELETE CASCADE`.

Empfohlene Absicherung:

- Beibehalten.

### INV-008: Ein Chunk gehoert zum gleichen Dokument wie seine Version

Definition:

- `document_chunks.document_id` muss dem `document_versions.document_id` der referenzierten Version entsprechen.

Verletzungsfall:

- Chunk ist in Dokument A eingetragen, referenziert aber Version von Dokument B.
- Dokumentdetail und Chunk-Endpunkt koennen falsche Chunks liefern.

Aktuelle Absicherung:

- DB: Composite Foreign Key `fk_document_chunks_document_version_pair` auf `(document_id, document_version_id) -> document_versions(document_id, id)`.

Empfohlene Absicherung:

- Beibehalten.

### INV-009: `Chunk.position` ist eindeutig innerhalb einer Version

Definition:

- Pro `document_version_id` darf jeder `chunk_index` nur einmal vorkommen.
- API-Feld `position` entspricht `chunk_index`.

Verletzungsfall:

- Zwei Chunks derselben Version haben `position = 4`.
- Sortierung und Zitate sind nicht deterministisch.

Aktuelle Absicherung:

- DB: Unique Constraint `uq_document_chunks_version_chunk_index`.

Empfohlene Absicherung:

- Beibehalten.

### INV-010: Chunk-Positionen sind nicht negativ und stabil sortierbar

Definition:

- `chunk_index >= 0`.
- Chunks werden fuer die API nach `chunk_index ASC` sortiert.

Verletzungsfall:

- Negative Positionen oder uneindeutige Reihenfolge.

Aktuelle Absicherung:

- DB: Check Constraint `ck_document_chunks_chunk_index_non_negative`.
- Repository: `ORDER BY Chunk.chunk_index.asc()`.

Empfohlene Absicherung:

- Beibehalten.
- Optional Integrationstest mit mehreren Chunks auf echter PostgreSQL-DB.

### INV-011: Chunk-Anker ist eindeutig innerhalb einer Version

Definition:

- `anchor` darf innerhalb einer `document_version_id` nur einmal vorkommen.

Verletzungsfall:

- Zwei Chunks koennen mit demselben Quellenanker zitiert werden.

Aktuelle Absicherung:

- DB: Unique Constraint `uq_document_chunks_version_anchor`.
- DB: Check Constraint `anchor` nicht blank.

Empfohlene Absicherung:

- Beibehalten.

### INV-012: Chunks der aktuellen Version sind bei `import_status = chunked` vorhanden

Definition:

- Wenn `documents.import_status = 'chunked'`, muss mindestens ein Chunk fuer `documents.current_version_id` existieren.

Verletzungsfall:

- Dokument ist als chunked markiert, aber Retrieval findet keinen Chunk.

Aktuelle Absicherung:

- Service: `DocumentReadService` wirft `DOCUMENT_STATE_CONFLICT`, wenn `chunked` und `chunk_count == 0`.
- DB: keine harte Absicherung, weil Cross-Table-Existenz nicht per einfachem Check Constraint abbildbar ist.

Empfohlene Absicherung:

- Service-Invariante beibehalten.
- Import in einer Transaktion aus Dokument, Version, Chunks und Statusupdate.
- Optional Deferred Trigger in PostgreSQL zur Pruefung nach Transaktionsende.

### INV-013: Chunk-Inhalt ist nicht leer

Definition:

- `document_chunks.content` muss nicht-leeren Text enthalten.

Verletzungsfall:

- Leere Chunks belasten Index und liefern wertlose Treffer.

Aktuelle Absicherung:

- DB: Check Constraint `length(trim(content)) > 0`.

Empfohlene Absicherung:

- Beibehalten.
- Chunking-Service soll leere Chunks vor Insert verwerfen.

### INV-014: `source_anchor` folgt dem normalisierten Schema

Definition:

- API-Source-Anchor hat immer:
  - `type`
  - `page`
  - `paragraph`
  - `char_start`
  - `char_end`
- `type` ist `text`, `pdf_page`, `docx_paragraph` oder `legacy_unknown`.

Verletzungsfall:

- Freie Metadaten-Blobs oder alte Felder wie `offset` erscheinen in API-Responses.

Aktuelle Absicherung:

- Migration normalisiert Legacy-Daten.
- Service baut aus Metadaten ein Pydantic `DocumentChunkSourceAnchor`.
- DB: keine JSON-Schema-Check-Constraint.

Empfohlene Absicherung:

- Service- und API-Tests beibehalten.
- Optional PostgreSQL Check Constraints fuer JSONB-Schluessel und erlaubte `type`-Werte.
- Parser-Ausgaben zentral ueber Source-Anchor-Builder erzwingen.

### INV-015: Importstatus ist einer der erlaubten Werte

Definition:

- `documents.import_status` darf nur `pending`, `parsing`, `parsed`, `chunked`, `failed` oder `duplicate` sein.

Verletzungsfall:

- Unbekannter Status bricht Read-API, M3-Filter oder Monitoring.

Aktuelle Absicherung:

- DB: Check Constraint `ck_documents_import_status_allowed`.
- Schema: Pydantic `ImportStatus` Literal.

Empfohlene Absicherung:

- Beibehalten.

### INV-016: `parsed`/`chunked` Dokumente haben eine aktuelle Version

Definition:

- `parsed` und `chunked` bedeuten, dass normalisierter Markdown in einer aktuellen Version existiert.

Verletzungsfall:

- Dokument erscheint als importiert, aber `latest_version` ist `null`.

Aktuelle Absicherung:

- Service: `DOCUMENT_STATE_CONFLICT`.
- DB: keine harte Absicherung.

Empfohlene Absicherung:

- DB Check Constraint analog INV-001.
- Importstatus nur im selben Transaktionsblock mit `current_version_id` setzen.

### INV-017: `failed` oder `pending` Dokumente muessen nicht versioniert sein

Definition:

- Dokumente in nicht abgeschlossenen oder fehlgeschlagenen Importzustaenden duerfen ohne Version existieren.

Verletzungsfall:

- Eine zu harte Constraint wuerde legitime `pending`/`failed`-Dokumente verhindern.

Aktuelle Absicherung:

- Service-Konvention: Read-Detail erlaubt `pending` ohne Version.

Empfohlene Absicherung:

- Statusuebergangstabelle oder Service-Policy dokumentieren.
- Tests fuer erlaubte und verbotene Status-/Versionskombinationen.

### INV-018: `Document.updated_at >= Document.created_at`

Definition:

- Ein Dokument darf nicht vor seiner Erstellung aktualisiert worden sein.

Verletzungsfall:

- Negative Lebensdauer in UI, Sortierung oder Auditing.

Aktuelle Absicherung:

- Keine harte Absicherung.

Empfohlene Absicherung:

- DB Check Constraint `updated_at >= created_at`.
- Einheitliche Pflege von `updated_at` per DB-Trigger oder ORM-Event.

### INV-019: `DocumentVersion.created_at >= Document.created_at`

Definition:

- Eine Version darf fachlich nicht vor ihrem Dokument erstellt worden sein.

Verletzungsfall:

- Historie ist unplausibel.

Aktuelle Absicherung:

- Keine harte Absicherung.

Empfohlene Absicherung:

- Service-Invariante bei Versionserzeugung.
- Optional DB-Trigger, weil Cross-Table-Check nicht einfach per Check Constraint moeglich ist.

### INV-020: `DocumentVersion.markdown_hash` ist nicht leer

Definition:

- Jede Version muss einen nicht-leeren Hash des normalisierten Markdown enthalten.

Verletzungsfall:

- Versionen koennen nicht dedupliziert, validiert oder reproduzierbar referenziert werden.

Aktuelle Absicherung:

- DB: Check Constraint `ck_document_versions_markdown_hash_not_blank`.

Empfohlene Absicherung:

- Beibehalten.
- Optional Unique Constraint `(document_id, markdown_hash)`, falls identische Versionen pro Dokument verboten werden sollen.

## Absicherungskonzept

### DB-seitig hart absichern

Diese Regeln gehoeren in Constraints, weil sie unabhaengig von API, Service oder Importpfad gelten muessen:

- `content_hash` eindeutig pro Workspace.
- `version_number > 0`.
- `(document_id, version_number)` eindeutig.
- `(document_version_id, chunk_index)` eindeutig.
- `(document_version_id, anchor)` eindeutig.
- Chunk gehoert zum gleichen Dokument wie seine Version.
- Importstatus nur aus erlaubter Wertemenge.
- `updated_at >= created_at`.
- `parsed`/`chunked`/`duplicate` nur mit `current_version_id`.
- `current_version_id` zeigt auf Version desselben Dokuments.

### Service-seitig absichern

Diese Regeln brauchen fachliche Statuslogik oder Transaktionssteuerung:

- Versionnummern monoton erzeugen.
- Dokument, Version, Chunks und Statusupdate atomar persistieren.
- `chunked` erst nach erfolgreichem Chunk-Insert setzen.
- `failed` mit sichtbarer Fehlerursache setzen.
- `pending`/`parsing` ohne Version erlauben, aber nicht als lesbar fuer Retrieval behandeln.

### Repository-/Query-seitig absichern

Diese Regeln muessen in Query-Form stabil bleiben:

- Dokumentliste sortiert `created_at DESC`.
- Versionen sortiert `created_at DESC`, bei Gleichstand `version_number DESC`.
- Chunks sortiert `chunk_index ASC`.
- Chunk-Endpunkt liest nur Chunks der aktuellen Version.
- Detail-Endpunkt laedt keine Volltext-Chunks.

### Testseitig absichern

Pflichttests fuer Invarianten:

- Duplicate `(workspace_id, content_hash)` verletzt Unique Constraint.
- Versionnummer doppelt innerhalb eines Dokuments verletzt Unique Constraint.
- Chunkposition doppelt innerhalb einer Version verletzt Unique Constraint.
- Chunk mit falschem `(document_id, document_version_id)` wird abgelehnt.
- `chunked` ohne Chunks liefert `DOCUMENT_STATE_CONFLICT`.
- `parsed`/`chunked` ohne Version liefert `DOCUMENT_STATE_CONFLICT`.
- `pending` ohne Version bleibt lesbar als Pending-Status.
- API gibt immer normalisiertes `source_anchor` aus.

### Migrations-/Datencheck vor Produktivbetrieb

Vor Anwendung neuer harter Constraints auf Bestandsdaten:

```sql
select workspace_id, content_hash, count(*)
from documents
group by workspace_id, content_hash
having count(*) > 1;
```

```sql
select document_id, version_number, count(*)
from document_versions
group by document_id, version_number
having count(*) > 1;
```

```sql
select document_version_id, chunk_index, count(*)
from document_chunks
group by document_version_id, chunk_index
having count(*) > 1;
```

```sql
select d.id, d.current_version_id
from documents d
left join document_versions v on v.id = d.current_version_id
where d.current_version_id is not null
  and (v.id is null or v.document_id <> d.id);
```
