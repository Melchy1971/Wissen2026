from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Any

from pydantic import BaseModel, Field

from app.core.errors import (
    ApiError,
    ImportFailedApiError,
    OcrRequiredApiError,
    ParserFailedApiError,
    ServiceUnavailableApiError,
    UnsupportedFileTypeApiError,
)
from app.models.import_models import ImportRequest
from app.observability.logging import bind_observability_context, log_event
from app.services.chunking_service import ChunkingError
from app.services.documents.import_persistence_service import DocumentImportPersistenceService
from app.services.import_service import ImportService
from app.services.markdown_normalizer import DeterministicMarkdownNormalizer
from app.services.parser_service import DocParser, DocxParser, MarkdownParser, PdfParser, StaticParserSelector, TextParser


class ImportWarningPayload(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


def build_import_service() -> ImportService:
    return ImportService(
        parser_selector=StaticParserSelector([TextParser(), MarkdownParser(), DocxParser(), DocParser(), PdfParser()]),
        normalizer=DeterministicMarkdownNormalizer(),
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


def parser_type_from_import_result(import_result: ImportRequest | Any) -> str:
    metadata = import_result.document.metadata if import_result.document is not None else import_result.metadata
    parser_name = metadata.get("parser_name") if isinstance(metadata, dict) else None
    if isinstance(parser_name, str) and parser_name.strip():
        return parser_name.strip()

    parser_version = import_result.document.parser_version if import_result.document is not None else None
    if isinstance(parser_version, str) and parser_version.strip():
        return parser_version.strip()

    return "unknown"


def title_from_filename(filename: str) -> str:
    title = Path(filename).stem.strip()
    return title or "Untitled"


def build_import_warnings(import_result: ImportRequest | Any) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    for error in import_result.errors:
        warnings.append(
            ImportWarningPayload(
                code=error.code.upper(),
                message=error.message,
                details={
                    "stage": error.stage,
                    "recoverable": error.recoverable,
                    **(error.metadata or {}),
                },
            ).model_dump()
        )
    return warnings


class ImportExecutor:
    def execute(
        self,
        *,
        workspace_id: str,
        user_id: str,
        filename: str,
        mime_type: str,
        source_bytes: bytes,
    ) -> dict[str, Any]:
        start_time = perf_counter()
        bind_observability_context(workspace_id=workspace_id, user_id=user_id)
        log_event(
            "document_upload_started",
            workspace_id=workspace_id,
            user_id=user_id,
            status="started",
        )

        request = ImportRequest(filename=filename, mime_type=mime_type, source_bytes=source_bytes)
        try:
            import_result = build_import_service().import_document(request)
        except ApiError:
            duration_ms = int((perf_counter() - start_time) * 1000)
            log_event(
                "document_upload_failed",
                workspace_id=workspace_id,
                user_id=user_id,
                duration_ms=duration_ms,
                status="failed",
            )
            raise
        except Exception as exc:
            duration_ms = int((perf_counter() - start_time) * 1000)
            log_event(
                "document_upload_failed",
                workspace_id=workspace_id,
                user_id=user_id,
                duration_ms=duration_ms,
                status="failed",
                error_code="IMPORT_FAILED",
            )
            raise ImportFailedApiError(
                message="Import pipeline crashed unexpectedly",
                details={"filename": filename, "mime_type": mime_type},
            ) from exc

        if not import_result.success or import_result.document is None:
            detail = import_result.errors[0].message if import_result.errors else "Import failed"
            error_code = import_result.errors[0].code if import_result.errors else "parser_failed"
            duration_ms = int((perf_counter() - start_time) * 1000)
            details = {
                "filename": filename,
                "mime_type": mime_type,
                "import_errors": [error.model_dump() for error in import_result.errors],
            }
            log_event(
                "document_upload_failed",
                workspace_id=workspace_id,
                user_id=user_id,
                duration_ms=duration_ms,
                status="failed",
                error_code=error_code.upper(),
            )
            if error_code == "parser_failed":
                log_event(
                    "parser_failed",
                    workspace_id=workspace_id,
                    user_id=user_id,
                    duration_ms=duration_ms,
                    status="failed",
                    error_code="PARSER_FAILED",
                )
            if error_code == "ocr_failed":
                raise OcrRequiredApiError(message=detail, details=details)
            if error_code == "unsupported_type":
                raise UnsupportedFileTypeApiError(message=detail, details=details)
            raise ParserFailedApiError(message=detail, details=details)

        if import_result.source_content_hash is None:
            raise ParserFailedApiError(message="Import did not produce a content hash", details={"filename": filename})

        try:
            persisted = DocumentImportPersistenceService().persist_import(
                workspace_id=workspace_id,
                owner_user_id=user_id,
                title=title_from_filename(filename),
                mime_type=mime_type,
                content_hash=import_result.source_content_hash,
                document=import_result.document,
            )
        except ChunkingError as exc:
            duration_ms = int((perf_counter() - start_time) * 1000)
            log_event(
                "document_upload_failed",
                workspace_id=workspace_id,
                user_id=user_id,
                duration_ms=duration_ms,
                status="failed",
                error_code="PARSER_FAILED",
            )
            log_event(
                "parser_failed",
                workspace_id=workspace_id,
                user_id=user_id,
                duration_ms=duration_ms,
                status="failed",
                error_code="PARSER_FAILED",
            )
            raise ParserFailedApiError(message=str(exc), details={"filename": filename}) from exc
        except ApiError:
            raise
        except Exception as exc:
            duration_ms = int((perf_counter() - start_time) * 1000)
            log_event(
                "document_upload_failed",
                workspace_id=workspace_id,
                user_id=user_id,
                duration_ms=duration_ms,
                status="failed",
                error_code="IMPORT_FAILED",
            )
            raise ServiceUnavailableApiError(message="Import persistence failed") from exc

        duration_ms = int((perf_counter() - start_time) * 1000)
        if persisted.duplicate_existing:
            log_event(
                "duplicate_detected",
                workspace_id=workspace_id,
                user_id=user_id,
                duration_ms=duration_ms,
                status="duplicate",
            )
        log_event(
            "document_upload_completed",
            workspace_id=workspace_id,
            user_id=user_id,
            duration_ms=duration_ms,
            status="completed",
        )

        return {
            "document_id": persisted.document_id,
            "version_id": persisted.version_id,
            "import_status": persisted.import_status,
            "duplicate_of_document_id": persisted.document_id if persisted.duplicate_existing else None,
            "chunk_count": persisted.chunk_count,
            "parser_type": parser_type_from_import_result(import_result),
            "warnings": build_import_warnings(import_result),
        }