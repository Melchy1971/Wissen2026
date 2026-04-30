# Datenmodell V1

Dieses Dokument beschreibt das M1-Datenbankschema ohne Codelektuere. V1 ist Single-User ohne
Authentifizierung. Mehrbenutzerfaehigkeit ist nur strukturell vorbereitet. Originaldateien werden
nicht gespeichert; kanonische Textquelle ist `document_versions.normalized_markdown`.

## Tabellenuebersicht

- `workspaces`: Arbeitsbereich-Stammdaten mit Default-Workspace fuer V1.
- `users`: vorbereitete User-Stammdaten mit Default-User, ohne Login-, Passwort- oder Sessiondaten.
- `documents`: Dokument-Metadaten, Workspace-/Owner-Zuordnung und aktueller Versionszeiger.
- `document_versions`: versionierter kanonischer Markdown-Inhalt und Parser-/OCR-/KI-Metadaten.
- `document_chunks`: aus einer Dokumentversion abgeleitete Textabschnitte mit Quellenanker.
- `categories`: workspace-faehige Kategorien.
- `tags`: workspace-faehige Tags mit normalisiertem Namen.
- `document_tags`: additive Tag-Zuordnung pro Dokument, Tag und Quelle.
- `chat_sessions`: vorbereitete Chat-Sitzungen mit Workspace-/Owner-Zuordnung.
- `chat_messages`: vorbereitete Chat-Nachrichten mit Basis-Kennzeichnung und Quellenmetadaten.
- `analysis_groups`: vorbereitete Analysegruppen.
- `analysis_group_documents`: Dokumentauswahl fuer Analysegruppen.
- `analysis_results`: vorbereitete Ergebnisse fuer Merge, Compare und Refine.
- `analysis_result_sources`: optionale Quellenbezuege fuer Analyseergebnisse.

## Wichtigste Beziehungen

- `documents.workspace_id` verweist auf `workspaces.id`.
- `documents.owner_user_id` verweist auf `users.id`.
- `document_versions.document_id` verweist auf `documents.id`.
- `documents.current_version_id` kann auf eine Version in `document_versions.id` zeigen.
- `document_chunks.document_id` und `document_chunks.document_version_id` binden Chunks an Dokument und Version.
- `categories.workspace_id` und `tags.workspace_id` machen Kategorien und Tags workspace-faehig.
- `document_tags` verbindet Dokumente und Tags additiv ueber `source`.
- Chat- und Analyse-Tabellen verweisen auf Workspaces, vorbereitete User und bei Quellen auf Dokumente, Versionen oder Chunks.

## Versionierungsprinzip

`documents` enthaelt stabile Dokument-Metadaten. Der eigentliche kanonische Text liegt in
`document_versions.normalized_markdown`. Jede Version gehoert genau zu einem Dokument und hat eine
eindeutige `version_number` pro Dokument. `documents.current_version_id` ist nullable, damit Dokument
und erste Version kontrolliert nacheinander angelegt werden koennen.

Originaldateien sind nicht Teil des Schemas. Persistiert werden abgeleitete Inhalte, Hashes,
Metadaten und versionierter Markdown.

## Chunk- und Quellenankerprinzip

Chunks entstehen spaeter aus `document_versions.normalized_markdown`. Jeder Chunk gehoert zu genau
einer Dokumentversion und besitzt einen `chunk_index` sowie einen `anchor`. Der Anchor ist pro
Dokumentversion eindeutig und kann spaeter fuer Chat- oder Analysezitate verwendet werden.

`heading_path` und `metadata` sind JSONB-Felder fuer Strukturinformationen, etwa Ueberschriften,
Tabellenhinweise oder Positionsdaten. Ein Fulltext-Index auf `content` ist vorbereitet, ersetzt aber
keine Suchlogik und ist keine Vektorsuche.

## Tag-Prinzip

Kategorien und Tags sind getrennt modelliert. Tags sind pro Workspace ueber `normalized_name`
eindeutig. `document_tags.source` ist kontrolliert auf `manual`, `ki` und `import`.

Die Zuordnung ist additiv: Der Primaerschluessel `(document_id, tag_id, source)` erlaubt, dass ein
manuelles Tag und ein KI-Tag fuer dasselbe Dokument parallel existieren. Manuelle Tags ueberschreiben
KI-Tags nicht automatisch.

## Chat- und Analyse-Vorbereitung

`chat_sessions` und `chat_messages` erlauben spaeter die Persistenz von Chatverlaeufen. `basis_type`
unterscheidet `knowledge_base`, `general`, `mixed` und `unknown`, ohne Chatlogik zu implementieren.
Quellen koennen zunaechst in `source_metadata` abgelegt werden.

Analysefunktionen werden ueber `analysis_groups`, `analysis_group_documents`, `analysis_results` und
`analysis_result_sources` vorbereitet. Ergebnisarten sind `merge`, `compare` und `refine`.
Analyseergebnisse koennen vor einem spaeteren Commit gespeichert werden; `commit_ref` ist optional.

## V1-Grenzen

- Keine Authentifizierung.
- Keine Rollen- oder Rechtepruefung.
- Keine Importpipeline.
- Keine Chat- oder Analyse-Service-Logik.
- Keine verpflichtende Vektorsuche.
- Keine Speicherung von Originaldateien.
