from pathlib import Path
from typing import Annotated, Iterator, Literal

from fastapi import APIRouter, Depends, File, Query, UploadFile
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import DatabaseConfigurationError
from app.core.errors import (
    ApiError,
    DocumentNotFoundApiError,
    DocumentStateConflictApiError,
    OcrRequiredApiError,
    ParserFailedApiError,
    UnsupportedFileTypeApiError,
)
from app.db.session import get_session
from app.models.import_models import ImportRequest
from app.schemas.documents import (
    DocumentChunkPreview,
    DocumentDetail,
    DocumentListItem,
    DocumentVersionSummary,
    ImportStatus,
)
from app.services.chunking_service import ChunkingError
from app.services.documents.import_persistence_service import DocumentImportPersistenceService
from app.services.documents.read_service import DocumentNotFoundError, DocumentReadService, DocumentStateConflictError
from app.services.import_service import ImportService
from app.services.markdown_normalizer import DeterministicMarkdownNormalizer
from app.services.parser_service import DocParser, DocxParser, MarkdownParser, PdfParser, StaticParserSelector, TextParser


router = APIRouter(prefix="/documents", tags=["documents"])

DuplicateStatus = Literal["created", "duplicate_existing"]


class ImportDocumentResponse(BaseModel):
    document_id: str
    version_id: str | None
    title: str
    chunk_count: int
    duplicate_status: DuplicateStatus
    import_status: ImportStatus


def build_import_service() -> ImportService:
    return ImportService(
        parser_selector=StaticParserSelector([TextParser(), MarkdownParser(), DocxParser(), DocParser(), PdfParser()]),
        normalizer=DeterministicMarkdownNormalizer(),
    )


def get_document_read_service() -> Iterator[DocumentReadService]:
    try:
        for session in get_session():
            yield DocumentReadService.from_session(session)
    except DatabaseConfigurationError as exc:
        raise ApiError(message=str(exc)) from exc


@router.get("", response_model=list[DocumentListItem])
def list_documents(
    workspace_id: Annotated[str, Query(min_length=1)],
    service: Annotated[DocumentReadService, Depends(get_document_read_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[DocumentListItem]:
    try:
        return service.get_documents(workspace_id=workspace_id, limit=limit, offset=offset)
    except DatabaseConfigurationError as exc:
        raise ApiError(message=str(exc)) from exc


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: str,
    service: Annotated[DocumentReadService, Depends(get_document_read_service)],
) -> DocumentDetail:
    try:
        return service.get_document_detail(document_id)
    except DocumentNotFoundError as exc:
        raise DocumentNotFoundApiError(details={"document_id": document_id}) from exc
    except DocumentStateConflictError as exc:
        raise DocumentStateConflictApiError(message=str(exc), details={"document_id": document_id}) from exc
    except DatabaseConfigurationError as exc:
        raise ApiError(message=str(exc)) from exc


@router.get("/{document_id}/versions", response_model=list[DocumentVersionSummary])
def list_document_versions(
    document_id: str,
    service: Annotated[DocumentReadService, Depends(get_document_read_service)],
) -> list[DocumentVersionSummary]:
    try:
        return service.get_versions(document_id)
    except DocumentNotFoundError as exc:
        raise DocumentNotFoundApiError(details={"document_id": document_id}) from exc
    except DatabaseConfigurationError as exc:
        raise ApiError(message=str(exc)) from exc


@router.get("/{document_id}/chunks", response_model=list[DocumentChunkPreview])
def list_document_chunks(
    document_id: str,
    service: Annotated[DocumentReadService, Depends(get_document_read_service)],
    limit: Annotated[int | None, Query(ge=1, le=500)] = None,
) -> list[DocumentChunkPreview]:
    try:
        return service.get_chunks(document_id, limit=limit)
    except DocumentNotFoundError as exc:
        raise DocumentNotFoundApiError(details={"document_id": document_id}) from exc
    except DatabaseConfigurationError as exc:
        raise ApiError(message=str(exc)) from exc


@router.post("/import", response_model=ImportDocumentResponse)
async def import_document(file: UploadFile = File(...)) -> ImportDocumentResponse:
    filename = file.filename or "untitled"
    mime_type = canonical_mime_type(filename, file.content_type)
    source_bytes = await file.read()

    request = ImportRequest(filename=filename, mime_type=mime_type, source_bytes=source_bytes)
    import_result = build_import_service().import_document(request)
    if not import_result.success or import_result.document is None:
        detail = import_result.errors[0].message if import_result.errors else "Import failed"
        error_code = import_result.errors[0].code if import_result.errors else "parser_failed"
        details = {
            "filename": filename,
            "mime_type": mime_type,
            "import_errors": [error.model_dump() for error in import_result.errors],
        }
        if error_code == "ocr_failed":
            raise OcrRequiredApiError(message=detail, details=details)
        raise ParserFailedApiError(message=detail, details=details)
    if import_result.source_content_hash is None:
        raise ParserFailedApiError(message="Import did not produce a content hash", details={"filename": filename})

    title = title_from_filename(filename)
    try:
        persisted = DocumentImportPersistenceService().persist_import(
            workspace_id=settings.default_workspace_id,
            owner_user_id=settings.default_user_id,
            title=title,
            mime_type=mime_type,
            content_hash=import_result.source_content_hash,
            document=import_result.document,
        )
    except DatabaseConfigurationError as exc:
        raise ApiError(message=str(exc)) from exc
    except ChunkingError as exc:
        raise ParserFailedApiError(message=str(exc), details={"filename": filename}) from exc

    return ImportDocumentResponse(
        document_id=persisted.document_id,
        version_id=persisted.version_id,
        title=persisted.title,
        chunk_count=persisted.chunk_count,
        duplicate_status="duplicate_existing" if persisted.duplicate_existing else "created",
        import_status=persisted.import_status,
    )


def canonical_mime_type(filename: str, content_type: str | None) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".txt":
        return "text/plain"
    if suffix == ".md":
        return "text/markdown"
    if suffix == ".docx":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if suffix == ".doc":
        return "application/msword"
    if suffix == ".pdf":
        return "application/pdf"

    raise UnsupportedFileTypeApiError(
        message="Only .txt, .md, .docx, .doc and .pdf uploads are supported",
        details={"filename": filename, "content_type": content_type},
    )


def title_from_filename(filename: str) -> str:
    title = Path(filename).stem.strip()
    return title or "Untitled"
