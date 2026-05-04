# M3a GUI ViewModels

Stand: 2026-05-04

Diese Spezifikation definiert die ViewModels fuer `M3a - GUI Foundation`.

Ziel ist, dass die GUI nicht direkt an rohe Backend-Responses gekoppelt wird. API-Responses werden zuerst in stabile, UI-orientierte ViewModels gemappt. Damit bleiben Anzeigeformat, Fallbacks und Feldsemantik im Frontend kontrollierbar, auch wenn sich technische Backend-Details spaeter aendern.

## Regeln

- ViewModels sind read-only.
- ViewModels verwenden nur dokumentierte API-Felder.
- ViewModels enthalten Anzeigeformate und Fallbacks, die nicht eins zu eins aus dem Backend stammen muessen.
- Die GUI konsumiert ViewModels, nicht rohe API-Responses.
- Fehlende oder optionale API-Felder muessen in ein darstellbares UI-Modell ueberfuehrt werden.

## DocumentListItemVM

Zweck:

- Ein einzelnes Dokument in der Dokumentuebersicht darstellen.

| Feld | Datentyp | Quelle aus API Response | Fallback bei fehlenden Daten | Anzeigeformat |
|---|---|---|---|---|
| `id` | `string` | `GET /documents[].id` | keiner, Eintrag ungueltig ohne ID | nicht prominent, intern fuer Navigation |
| `title` | `string` | `GET /documents[].title` | `Unbenanntes Dokument` | Klartext |
| `mimeType` | `string` | `GET /documents[].mime_type` | `unbekannt` | Badge oder Sekundaertext |
| `createdAtIso` | `string` | `GET /documents[].created_at` | leerer String | technisch, nicht direkt anzeigen |
| `createdAtLabel` | `string` | abgeleitet aus `created_at` | `Unbekannt` | lokalisierter Datums-/Zeittext |
| `updatedAtIso` | `string` | `GET /documents[].updated_at` | leerer String | technisch, nicht direkt anzeigen |
| `updatedAtLabel` | `string` | abgeleitet aus `updated_at` | `Unbekannt` | lokalisierter Datums-/Zeittext |
| `latestVersionId` | `string \| null` | `GET /documents[].latest_version_id` | `null` | nicht direkt, optional in Statuslogik |
| `importStatus` | `ImportStatusVM` | abgeleitet aus `GET /documents[].import_status` | `unknown`-VM | Badge mit Label und Tonalitaet |
| `versionCount` | `number` | `GET /documents[].version_count` | `0` | Ganzzahl |
| `chunkCount` | `number` | `GET /documents[].chunk_count` | `0` | Ganzzahl |
| `isReadable` | `boolean` | abgeleitet aus `importStatus.kind` | `false` | nicht direkt, fuer UI-Entscheidungen |
| `detailRoute` | `string` | abgeleitet aus `id` | leerer String | Linkziel |

## DocumentDetailVM

Zweck:

- Detailansicht eines Dokuments inklusive aktuellem Zustand, letzter Version und Summary.

| Feld | Datentyp | Quelle aus API Response | Fallback bei fehlenden Daten | Anzeigeformat |
|---|---|---|---|---|
| `id` | `string` | `GET /documents/{id}.id` | keiner | intern und Copy-Value |
| `workspaceId` | `string` | `GET /documents/{id}.workspace_id` | `unbekannt` | Sekundaertext |
| `ownerUserId` | `string \| null` | `GET /documents/{id}.owner_user_id` | `null` | optionaler Sekundaertext |
| `title` | `string` | `GET /documents/{id}.title` | `Unbenanntes Dokument` | Headline |
| `sourceType` | `string` | `GET /documents/{id}.source_type` | `unbekannt` | Badge oder Sekundaertext |
| `mimeType` | `string` | `GET /documents/{id}.mime_type` | `unbekannt` | Badge oder Sekundaertext |
| `contentHash` | `string \| null` | `GET /documents/{id}.content_hash` | `null` | optional gekuerzt |
| `createdAtIso` | `string` | `GET /documents/{id}.created_at` | leerer String | technisch |
| `createdAtLabel` | `string` | abgeleitet aus `created_at` | `Unbekannt` | lokalisierter Datums-/Zeittext |
| `updatedAtIso` | `string` | `GET /documents/{id}.updated_at` | leerer String | technisch |
| `updatedAtLabel` | `string` | abgeleitet aus `updated_at` | `Unbekannt` | lokalisierter Datums-/Zeittext |
| `latestVersionId` | `string \| null` | `GET /documents/{id}.latest_version_id` | `null` | optionaler Referenzwert |
| `latestVersion` | `VersionListItemVM \| null` | abgeleitet aus `GET /documents/{id}.latest_version` | `null` | Summary-Karte |
| `parserVersion` | `string` | `GET /documents/{id}.parser_metadata.parser_version` | `Unbekannt` | Klartext |
| `ocrUsed` | `boolean \| null` | `GET /documents/{id}.parser_metadata.ocr_used` | `null` | Ja/Nein/Unbekannt |
| `kiProvider` | `string \| null` | `GET /documents/{id}.parser_metadata.ki_provider` | `null` | optionaler Sekundaertext |
| `kiModel` | `string \| null` | `GET /documents/{id}.parser_metadata.ki_model` | `null` | optionaler Sekundaertext |
| `parserMetadata` | `Record<string, unknown>` | `GET /documents/{id}.parser_metadata.metadata` | leeres Objekt | Key-Value-Liste, falls angezeigt |
| `importStatus` | `ImportStatusVM` | abgeleitet aus `GET /documents/{id}.import_status` | `unknown`-VM | Statuskarte/Badge |
| `chunkCount` | `number` | `GET /documents/{id}.chunk_summary.chunk_count` | `0` | Ganzzahl |
| `totalChars` | `number` | `GET /documents/{id}.chunk_summary.total_chars` | `0` | Ganzzahl mit Trennern |
| `firstChunkId` | `string \| null` | `GET /documents/{id}.chunk_summary.first_chunk_id` | `null` | optional |
| `lastChunkId` | `string \| null` | `GET /documents/{id}.chunk_summary.last_chunk_id` | `null` | optional |
| `hasReadableVersion` | `boolean` | abgeleitet aus `latestVersion !== null` | `false` | nicht direkt |
| `hasChunks` | `boolean` | abgeleitet aus `chunkCount > 0` | `false` | nicht direkt |

## VersionListItemVM

Zweck:

- Ein einzelner Versionseintrag in der Versionsansicht oder als Summary in der Detailansicht.

| Feld | Datentyp | Quelle aus API Response | Fallback bei fehlenden Daten | Anzeigeformat |
|---|---|---|---|---|
| `id` | `string` | `GET /documents/{id}/versions[].id` oder `GET /documents/{id}.latest_version.id` | keiner | intern |
| `versionNumber` | `number` | `GET /documents/{id}/versions[].version_number` oder `GET /documents/{id}.latest_version.version_number` | `0` | `v{n}` |
| `createdAtIso` | `string` | `GET /documents/{id}/versions[].created_at` oder `GET /documents/{id}.latest_version.created_at` | leerer String | technisch |
| `createdAtLabel` | `string` | abgeleitet aus `created_at` | `Unbekannt` | lokalisierter Datums-/Zeittext |
| `contentHash` | `string \| null` | `GET /documents/{id}/versions[].content_hash` oder `GET /documents/{id}.latest_version.content_hash` | `null` | optional gekuerzt |
| `isLatest` | `boolean` | aus Kontext beim Mapping | `false` | Badge `Aktuell` |

## ChunkListItemVM

Zweck:

- Ein einzelner Chunk in der Chunk-Ansicht.

| Feld | Datentyp | Quelle aus API Response | Fallback bei fehlenden Daten | Anzeigeformat |
|---|---|---|---|---|
| `chunkId` | `string` | `GET /documents/{id}/chunks[].chunk_id` | keiner | intern |
| `position` | `number` | `GET /documents/{id}/chunks[].position` | `0` | Ganzzahl |
| `positionLabel` | `string` | abgeleitet aus `position` | `Chunk 0` | `Chunk {position + 1}` oder `Pos. {position}` |
| `textPreview` | `string` | `GET /documents/{id}/chunks[].text_preview` | leerer String | Vorschautext |
| `textPreviewLabel` | `string` | abgeleitet aus `text_preview` | `Keine Vorschau verfuegbar` | mehrzeiliger Text |
| `sourceAnchorType` | `string` | `GET /documents/{id}/chunks[].source_anchor.type` | `unknown` | Badge oder Label |
| `sourceAnchorPage` | `number \| null` | `GET /documents/{id}/chunks[].source_anchor.page` | `null` | Ganzzahl, optional |
| `sourceAnchorParagraph` | `number \| null` | `GET /documents/{id}/chunks[].source_anchor.paragraph` | `null` | Ganzzahl, optional |
| `sourceAnchorCharStart` | `number \| null` | `GET /documents/{id}/chunks[].source_anchor.char_start` | `null` | Ganzzahl, optional |
| `sourceAnchorCharEnd` | `number \| null` | `GET /documents/{id}/chunks[].source_anchor.char_end` | `null` | Ganzzahl, optional |
| `sourceAnchorLabel` | `string` | abgeleitet aus `source_anchor` | `Keine Quellenposition verfuegbar` | menschenlesbarer Kurztext |

## ImportStatusVM

Zweck:

- Backend-Importstatus in ein darstellbares UI-Modell mit Label und Tonalitaet uebersetzen.

| Feld | Datentyp | Quelle aus API Response | Fallback bei fehlenden Daten | Anzeigeformat |
|---|---|---|---|---|
| `kind` | `'pending' \| 'parsing' \| 'parsed' \| 'chunked' \| 'failed' \| 'duplicate' \| 'unknown'` | `import_status` aus Liste oder Detail | `unknown` | intern |
| `label` | `string` | Mapping aus `kind` | `Unbekannt` | Badge-/Statuslabel |
| `tone` | `'neutral' \| 'info' \| 'success' \| 'warning' \| 'danger'` | Mapping aus `kind` | `neutral` | visuelle Tonalitaet |
| `isTerminal` | `boolean` | Mapping aus `kind` | `false` | intern |
| `isReadable` | `boolean` | Mapping aus `kind` | `false` | intern |
| `description` | `string` | Mapping aus `kind` | `Kein Status verfuegbar` | Hilfetext |

Empfohlenes Mapping:

| API `import_status` | `kind` | `label` | `tone` | `isTerminal` | `isReadable` |
|---|---|---|---|---:|---:|
| `pending` | `pending` | `Ausstehend` | `warning` | nein | nein |
| `parsing` | `parsing` | `Wird verarbeitet` | `info` | nein | nein |
| `parsed` | `parsed` | `Geparst` | `info` | nein | eingeschraenkt |
| `chunked` | `chunked` | `Lesbar` | `success` | ja | ja |
| `failed` | `failed` | `Fehlgeschlagen` | `danger` | ja | nein |
| `duplicate` | `duplicate` | `Bereits vorhanden` | `neutral` | ja | ja |
| unbekannt oder leer | `unknown` | `Unbekannt` | `neutral` | nein | nein |

Hinweis:

- `parsed` sollte UI-seitig nicht als voll lesbar interpretiert werden, solange die GUI fuer M3a Versionen und Chunks als Kernzustand sichtbar machen soll.

## ErrorVM

Zweck:

- Standardisiertes UI-Modell fuer API-Fehler und Konfliktzustaende.

| Feld | Datentyp | Quelle aus API Response | Fallback bei fehlenden Daten | Anzeigeformat |
|---|---|---|---|---|
| `code` | `string` | `error.code` | `UNKNOWN_ERROR` | intern und optional Badge |
| `title` | `string` | Mapping aus `error.code`, sonst `error.message` | `Fehler` | Headline |
| `message` | `string` | `error.message` | `Ein unbekannter Fehler ist aufgetreten.` | Klartext |
| `details` | `Record<string, unknown>` | `error.details` | leeres Objekt | optional ausklappbar |
| `httpStatus` | `number \| null` | HTTP-Response-Status | `null` | optional |
| `severity` | `'info' \| 'warning' \| 'danger'` | Mapping aus `error.code` oder HTTP-Status | `danger` | visuelle Tonalitaet |
| `isRetryable` | `boolean` | Mapping aus `error.code` | `false` | intern fuer UI-Aktion |
| `userActionLabel` | `string \| null` | Mapping aus `error.code` | `null` | Button-/Hinweistext |

Empfohlenes Mapping:

| API `error.code` | `title` | `severity` | `isRetryable` | `userActionLabel` |
|---|---|---|---:|---|
| `WORKSPACE_REQUIRED` | `Workspace fehlt` | `warning` | nein | `Workspace auswaehlen` |
| `INVALID_PAGINATION` | `Ungueltige Seitennavigation` | `warning` | nein | `Pagination pruefen` |
| `DOCUMENT_NOT_FOUND` | `Dokument nicht gefunden` | `warning` | nein | `Zur Dokumentliste` |
| `DOCUMENT_STATE_CONFLICT` | `Dokumentzustand inkonsistent` | `danger` | nein | `Backend-Zustand pruefen` |
| `SERVICE_UNAVAILABLE` | `Service nicht verfuegbar` | `danger` | ja | `Erneut versuchen` |
| `OCR_REQUIRED` | `OCR erforderlich` | `warning` | nein | `Dokumentstatus ansehen` |
| unbekannt | `Unbekannter Fehler` | `danger` | nein | `Erneut laden` |

## Mapping API -> ViewModel

### `GET /documents` -> `DocumentListItemVM[]`

```text
response[].id -> vm.id
response[].title -> vm.title
response[].mime_type -> vm.mimeType
response[].created_at -> vm.createdAtIso -> vm.createdAtLabel
response[].updated_at -> vm.updatedAtIso -> vm.updatedAtLabel
response[].latest_version_id -> vm.latestVersionId
response[].import_status -> mapImportStatus() -> vm.importStatus
response[].version_count -> vm.versionCount
response[].chunk_count -> vm.chunkCount
vm.importStatus.isReadable -> vm.isReadable
vm.id -> vm.detailRoute
```

### `GET /documents/{id}` -> `DocumentDetailVM`

```text
response.id -> vm.id
response.workspace_id -> vm.workspaceId
response.owner_user_id -> vm.ownerUserId
response.title -> vm.title
response.source_type -> vm.sourceType
response.mime_type -> vm.mimeType
response.content_hash -> vm.contentHash
response.created_at -> vm.createdAtIso -> vm.createdAtLabel
response.updated_at -> vm.updatedAtIso -> vm.updatedAtLabel
response.latest_version_id -> vm.latestVersionId
response.latest_version -> mapVersionItem(isLatest=true) -> vm.latestVersion
response.parser_metadata.parser_version -> vm.parserVersion
response.parser_metadata.ocr_used -> vm.ocrUsed
response.parser_metadata.ki_provider -> vm.kiProvider
response.parser_metadata.ki_model -> vm.kiModel
response.parser_metadata.metadata -> vm.parserMetadata
response.import_status -> mapImportStatus() -> vm.importStatus
response.chunk_summary.chunk_count -> vm.chunkCount
response.chunk_summary.total_chars -> vm.totalChars
response.chunk_summary.first_chunk_id -> vm.firstChunkId
response.chunk_summary.last_chunk_id -> vm.lastChunkId
derived latestVersion !== null -> vm.hasReadableVersion
derived chunkCount > 0 -> vm.hasChunks
```

### `GET /documents/{id}/versions` -> `VersionListItemVM[]`

```text
response[].id -> vm.id
response[].version_number -> vm.versionNumber
response[].created_at -> vm.createdAtIso -> vm.createdAtLabel
response[].content_hash -> vm.contentHash
context first item or matching latestVersionId -> vm.isLatest
```

### `GET /documents/{id}/chunks` -> `ChunkListItemVM[]`

```text
response[].chunk_id -> vm.chunkId
response[].position -> vm.position -> vm.positionLabel
response[].text_preview -> vm.textPreview -> vm.textPreviewLabel
response[].source_anchor.type -> vm.sourceAnchorType
response[].source_anchor.page -> vm.sourceAnchorPage
response[].source_anchor.paragraph -> vm.sourceAnchorParagraph
response[].source_anchor.char_start -> vm.sourceAnchorCharStart
response[].source_anchor.char_end -> vm.sourceAnchorCharEnd
source anchor fields -> vm.sourceAnchorLabel
```

### Error-Envelope -> `ErrorVM`

```text
response.error.code -> vm.code
mapErrorTitle(response.error.code, response.error.message) -> vm.title
response.error.message -> vm.message
response.error.details -> vm.details
http status -> vm.httpStatus
mapErrorSeverity(response.error.code, http status) -> vm.severity
mapRetryability(response.error.code) -> vm.isRetryable
mapActionLabel(response.error.code) -> vm.userActionLabel
```

## Mapping-Regeln

- Datumswerte werden immer doppelt gehalten: roh als ISO-String und formatiert als UI-Label.
- Nullable API-Felder werden nicht ungeprueft gerendert; die ViewModel-Schicht setzt explizite Fallbacks.
- `ImportStatusVM` und `ErrorVM` sind zentrale Shared-Modelle fuer alle M3a-Screens.
- Die GUI darf keine Felder direkt aus `parser_metadata.metadata` voraussetzen, die nicht im Vertrag garantiert sind.
- Die GUI darf `text_preview` nicht als Volltext interpretieren.
- `source_anchor` wird tolerant gemappt; fehlende Teilwerte bleiben `null` und werden UI-seitig nicht als Fehler behandelt.

## Fehlerzustandsmatrix

Grundregeln:

- Keine Reparaturaktionen in der GUI.
- Keine versteckten Fehler.
- Der Fehlercode bleibt fuer Debugging sichtbar.
- Erlaubte Nutzeraktionen duerfen nur lesen, navigieren, Parameter korrigieren oder erneut laden.

| Fall | Erkennung | Anzeige | Technische Ursache | Erlaubte Nutzeraktion |
|---|---|---|---|---|
| API nicht erreichbar | HTTP-Fehler ohne gueltigen JSON-Envelope, Netzwerkfehler oder `503 SERVICE_UNAVAILABLE` | Vollflaechiger Fehlerzustand mit Titel `Service nicht verfuegbar`, sichtbarem Fehlercode `SERVICE_UNAVAILABLE` oder `NETWORK_ERROR`, Klartextmeldung und Debug-Details, falls vorhanden | Backend nicht gestartet, DB nicht verfuegbar, CORS-/Netzwerkproblem oder Konfigurationsfehler | `Erneut laden`, `Zurueck zur Uebersicht`, technische Details lesen |
| Dokument nicht gefunden | `404` mit `error.code = DOCUMENT_NOT_FOUND` auf Detail-, Versions- oder Chunk-Screen | Fehlerkarte mit Titel `Dokument nicht gefunden`, sichtbarem Code `DOCUMENT_NOT_FOUND`, Hinweis, dass das Dokument unter der aktuellen ID nicht verfuegbar ist | Dokument-ID existiert nicht mehr, falsche Route, veralteter Link | `Zur Dokumentuebersicht`, `Vorherige Seite`, Debug-Details anzeigen |
| Dokument ohne Version | Detail-Response liefert `409` mit `error.code = DOCUMENT_STATE_CONFLICT` und Meldung wie `Document exists without a latest version` oder Detail-Response zeigt `import_status = pending` und `latest_version = null` | Bei `pending`: leerer fachlicher Zwischenzustand mit sichtbarem Statusbadge `Ausstehend`; bei `409`: Konfliktkarte mit sichtbarem Code `DOCUMENT_STATE_CONFLICT` und unveraenderter Backend-Meldung | Dokument ist noch nicht fertig persistiert oder Datenzustand ist inkonsistent; Read-Service erkennt fehlende `latest_version` fuer lesbaren Status als Konflikt | `Zur Dokumentuebersicht`, `Erneut laden`, Debug-Details lesen |
| Version ohne Chunks | Detail-Response liefert `409` mit `error.code = DOCUMENT_STATE_CONFLICT` und Meldung `Document import is chunked but latest version has no chunks`; Chunk-Screen kann alternativ leer sein, wenn keine `latest_version` existiert | Konfliktkarte mit Titel `Dokumentzustand inkonsistent`, sichtbarem Code `DOCUMENT_STATE_CONFLICT` und technischer Meldung; kein normaler Leerzustand vortaeuschen | Dokumentstatus ist `chunked`, aber zugehoerige Chunks fehlen; Read-Service bewertet das als Inkonsistenz | `Zur Dokumentdetailansicht`, `Zur Dokumentuebersicht`, `Erneut laden`, Debug-Details lesen |
| Import failed | `import_status = failed` in Listen- oder Detail-Response oder importnaher Fehlercode aus frueherem Kontext | Statuskarte oder Tabellenbadge `Fehlgeschlagen` mit sichtbarem Status und, wenn vorhanden, sichtbarem Fehlercode; kein stilles Ausblenden des Dokuments | Parser- oder Persistenzfehler im Importpfad; Dokument blieb im Fehlerzustand stehen | `Zur Dokumentuebersicht`, `Dokumentdetail ansehen`, Debug-Details lesen |
| OCR required | sichtbarer Fehlercode `OCR_REQUIRED` oder dokumentierter Statuskontext, z. B. Dokument nicht lesbar wegen OCR-Bedarf | Warnkarte mit Titel `OCR erforderlich`, sichtbarem Code `OCR_REQUIRED`, Hinweis, dass kein OCR in M3a ausgefuehrt wird | PDF ohne extrahierbaren Text; Backend signalisiert fehlende OCR-Faehigkeit | `Zur Dokumentuebersicht`, `Dokumentstatus ansehen`, Debug-Details lesen |
| Parser failed | sichtbarer Fehlercode `PARSER_FAILED` aus importnahem Kontext oder `import_status = failed`, wenn Fehler nur noch als Status sichtbar ist | Fehler- oder Statuskarte `Parser fehlgeschlagen` mit sichtbarem Code `PARSER_FAILED` oder Status `Fehlgeschlagen`; Rohfehler nicht verschleiern | Parser konnte Quelldatei nicht in kanonischen Markdown ueberfuehren | `Zur Dokumentuebersicht`, `Dokumentstatus ansehen`, Debug-Details lesen |
| Leere Dokumentliste | `GET /documents` liefert `200` mit leerem Array | Leerstatescreen `Keine Dokumente vorhanden` mit sichtbarem Workspace-Bezug; kein Fehlercode, da kein Fehler vorliegt | Workspace enthaelt aktuell keine Dokumente oder Pagination zeigt keine Treffer | `Zur ersten Seite`, `Workspace pruefen`, `Erneut laden` |

Hinweise zur Einordnung:

- `Import failed`, `OCR required` und `Parser failed` sind in M3a primaer Status- oder importnahe Fehlerbilder. Die aktuelle Read-API liefert dafuer nicht in jedem Screen einen separaten Fehler-Endpoint, daher muss die GUI zwischen `ErrorVM` und `ImportStatusVM` unterscheiden.
- Ein leerer Zustand ist niemals als technischer Fehler zu tarnen. Umgekehrt darf ein technischer Konflikt nie als leerer Normalzustand erscheinen.
- Konfliktmeldungen aus dem Backend bleiben in `ErrorVM.message` unveraendert sichtbar, auch wenn die GUI einen benutzerfreundlichen Titel darueberlegt.