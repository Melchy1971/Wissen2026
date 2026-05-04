from typing import Any


class ApiError(Exception):
    status_code = 500
    code = "INTERNAL_ERROR"
    message = "Internal server error"

    def __init__(self, message: str | None = None, details: dict[str, Any] | None = None) -> None:
        self.message = message or self.message
        self.details = details or {}
        super().__init__(self.message)


class DocumentNotFoundApiError(ApiError):
    status_code = 404
    code = "DOCUMENT_NOT_FOUND"
    message = "Document not found"


class WorkspaceRequiredApiError(ApiError):
    status_code = 422
    code = "WORKSPACE_REQUIRED"
    message = "workspace_id is required"


class InvalidPaginationApiError(ApiError):
    status_code = 422
    code = "INVALID_PAGINATION"
    message = "Invalid pagination parameters"


class DocumentStateConflictApiError(ApiError):
    status_code = 409
    code = "DOCUMENT_STATE_CONFLICT"
    message = "Document state is inconsistent"


class DuplicateDocumentApiError(ApiError):
    status_code = 409
    code = "DUPLICATE_DOCUMENT"
    message = "Document already exists"


class UnsupportedFileTypeApiError(ApiError):
    status_code = 415
    code = "UNSUPPORTED_FILE_TYPE"
    message = "Unsupported file type"


class OcrRequiredApiError(ApiError):
    status_code = 422
    code = "OCR_REQUIRED"
    message = "OCR is required but no OCR engine is configured"


class ParserFailedApiError(ApiError):
    status_code = 422
    code = "PARSER_FAILED"
    message = "Document parser failed"


class ServiceUnavailableApiError(ApiError):
    status_code = 503
    code = "SERVICE_UNAVAILABLE"
    message = "Service unavailable"
