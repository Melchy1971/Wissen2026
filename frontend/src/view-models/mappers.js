export function mapImportStatus(status) {
  const lookup = {
    pending: { kind: 'pending', label: 'Ausstehend', tone: 'warning' },
    parsing: { kind: 'parsing', label: 'Wird verarbeitet', tone: 'info' },
    parsed: { kind: 'parsed', label: 'Geparst', tone: 'info' },
    chunked: { kind: 'chunked', label: 'Lesbar', tone: 'success' },
    failed: { kind: 'failed', label: 'Fehlgeschlagen', tone: 'danger' },
    duplicate: { kind: 'duplicate', label: 'Bereits vorhanden', tone: 'neutral' },
  };

  return lookup[status] || { kind: 'unknown', label: 'Unbekannt', tone: 'neutral' };
}

export function mapError(error) {
  return {
    code: error?.code || 'UNKNOWN_ERROR',
    title: mapErrorTitle(error?.code),
    message: error?.message || 'Ein unbekannter Fehler ist aufgetreten.',
    details: error?.details || {},
    status: error?.status ?? null,
  };
}

function mapErrorTitle(code) {
  const titles = {
    NETWORK_ERROR: 'API nicht erreichbar',
    SERVICE_UNAVAILABLE: 'Service nicht verfuegbar',
    DOCUMENT_NOT_FOUND: 'Dokument nicht gefunden',
    DOCUMENT_STATE_CONFLICT: 'Dokumentzustand inkonsistent',
    WORKSPACE_REQUIRED: 'Workspace fehlt',
    INVALID_PAGINATION: 'Ungueltige Pagination',
    OCR_REQUIRED: 'OCR erforderlich',
    PARSER_FAILED: 'Parser fehlgeschlagen',
  };

  return titles[code] || 'Fehler';
}

function formatDate(value) {
  if (!value) {
    return 'Unbekannt';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return 'Unbekannt';
  }

  return new Intl.DateTimeFormat('de-DE', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function formatSourceAnchor(anchor) {
  if (!anchor) {
    return 'Keine Quellenposition verfuegbar';
  }

  const parts = [anchor.type || 'unknown'];
  if (anchor.page != null) parts.push(`Seite ${anchor.page}`);
  if (anchor.paragraph != null) parts.push(`Absatz ${anchor.paragraph}`);
  if (anchor.char_start != null || anchor.char_end != null) {
    parts.push(`Zeichen ${anchor.char_start ?? '?'}-${anchor.char_end ?? '?'}`);
  }
  return parts.join(' | ');
}

export function mapDocumentListItem(item) {
  const importStatus = mapImportStatus(item.import_status);
  return {
    id: item.id,
    title: item.title || 'Unbenanntes Dokument',
    mimeType: item.mime_type || 'unbekannt',
    createdAtLabel: formatDate(item.created_at),
    updatedAtLabel: formatDate(item.updated_at),
    latestVersionId: item.latest_version_id || null,
    importStatus,
    versionCount: item.version_count ?? 0,
    chunkCount: item.chunk_count ?? 0,
  };
}

export function mapVersionItem(item, latestVersionId = null) {
  return {
    id: item.id,
    versionNumber: item.version_number ?? 0,
    createdAtLabel: formatDate(item.created_at),
    contentHash: item.content_hash || null,
    isLatest: latestVersionId != null && item.id === latestVersionId,
  };
}

export function mapChunkItem(item) {
  return {
    id: item.chunk_id,
    position: item.position ?? 0,
    positionLabel: `Chunk ${((item.position ?? 0) + 1).toString()}`,
    textPreview: item.text_preview || '',
    sourceAnchorLabel: formatSourceAnchor(item.source_anchor),
  };
}

export function mapDocumentDetail(detail, versions, chunks) {
  const importStatus = mapImportStatus(detail.import_status);
  return {
    id: detail.id,
    title: detail.title || 'Unbenanntes Dokument',
    workspaceId: detail.workspace_id || 'unbekannt',
    ownerUserId: detail.owner_user_id || null,
    sourceType: detail.source_type || 'unbekannt',
    mimeType: detail.mime_type || 'unbekannt',
    contentHash: detail.content_hash || null,
    createdAtLabel: formatDate(detail.created_at),
    updatedAtLabel: formatDate(detail.updated_at),
    parserVersion: detail.parser_metadata?.parser_version || 'Unbekannt',
    ocrUsed: detail.parser_metadata?.ocr_used ?? null,
    importStatus,
    chunkCount: detail.chunk_summary?.chunk_count ?? 0,
    totalChars: detail.chunk_summary?.total_chars ?? 0,
    latestVersionId: detail.latest_version_id || null,
    versions: Array.isArray(versions) ? versions.map((item) => mapVersionItem(item, detail.latest_version_id)) : [],
    chunks: Array.isArray(chunks) ? chunks.map(mapChunkItem) : [],
  };
}