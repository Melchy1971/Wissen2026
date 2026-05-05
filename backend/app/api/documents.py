from dataclasses import dataclass
from time import perf_counter
from typing import Annotated, Iterator

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile, status

from app.core.config import settings
from app.core.database import DatabaseConfigurationError
from app.core.errors import (
    ApiError,
    BackgroundJobNotFoundApiError,
    DocumentNotFoundApiError,
    DocumentStateConflictApiError,
    FileTooLargeApiError,
    InvalidLifecycleStatusApiError,
)
from app.db.session import get_session
from app.observability.logging import bind_observability_context, log_event
from app.schemas.documents import (
    DocumentChunkPreview,
    DocumentDetail,
    DocumentLifecycleResponse,
    DocumentListItem,
    DocumentVersionSummary,
)
from app.schemas.jobs import JobResponse
from app.services.documents.import_executor import canonical_mime_type
from app.services.documents.lifecycle_service import (
    DocumentLifecycleConflictError,
    DocumentLifecycleNotFoundError,
    DocumentLifecycleService,
)
from app.services.documents.read_service import DocumentNotFoundError, DocumentReadService, DocumentStateConflictError
from app.services.jobs.background_jobs import BackgroundJobNotFoundError, BackgroundJobService, process_import_job


router = APIRouter(prefix="/documents", tags=["documents"])


@dataclass(frozen=True)
class UploadRequestContext:
    workspace_id: str
    user_id: str


def get_document_read_service() -> Iterator[DocumentReadService]:
    try:
        for session in get_session():
            yield DocumentReadService.from_session(session)
    except DatabaseConfigurationError as exc:
        raise ApiError(message=str(exc)) from exc


def get_upload_request_context() -> UploadRequestContext:
    return UploadRequestContext(
        workspace_id=settings.default_workspace_id,
        user_id=settings.default_user_id,
    )


def get_document_lifecycle_service() -> Iterator[DocumentLifecycleService]:
    try:
        for session in get_session():
            yield DocumentLifecycleService.from_session(session)
    except DatabaseConfigurationError as exc:
        raise ApiError(message=str(exc)) from exc


def get_background_job_service() -> Iterator[BackgroundJobService]:
    try:
        for session in get_session():
            yield BackgroundJobService.from_session(session)
    except DatabaseConfigurationError as exc:
        raise ApiError(message=str(exc)) from exc


@router.get("", response_model=list[DocumentListItem])
def list_documents(
    workspace_id: Annotated[str, Query(min_length=1)],
    service: Annotated[DocumentReadService, Depends(get_document_read_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    lifecycle_status: Annotated[str | None, Query()] = None,
    include_archived: bool = False,
) -> list[DocumentListItem]:
    try:
        if lifecycle_status not in {None, "active", "archived", "deleted"}:
            raise InvalidLifecycleStatusApiError(details={"lifecycle_status": lifecycle_status})
        return service.get_documents(
            workspace_id=workspace_id,
            limit=limit,
            offset=offset,
            lifecycle_status=lifecycle_status,
            include_archived=include_archived,
        )
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


@router.patch("/{document_id}/archive", response_model=DocumentLifecycleResponse)
def archive_document(
    document_id: str,
    service: Annotated[DocumentLifecycleService, Depends(get_document_lifecycle_service)],
) -> DocumentLifecycleResponse:
    try:
        document = service.archive(document_id)
    except DocumentLifecycleNotFoundError as exc:
        raise DocumentNotFoundApiError(details={"document_id": document_id}) from exc
    except DocumentLifecycleConflictError as exc:
        raise DocumentStateConflictApiError(message=str(exc), details={"document_id": document_id}) from exc
    return DocumentLifecycleResponse(
        document_id=document.id,
        lifecycle_status=document.lifecycle_status,
        archived_at=document.archived_at,
        deleted_at=document.deleted_at,
    )


@router.patch("/{document_id}/restore", response_model=DocumentLifecycleResponse)
def restore_document(
    document_id: str,
    service: Annotated[DocumentLifecycleService, Depends(get_document_lifecycle_service)],
) -> DocumentLifecycleResponse:
    try:
        document = service.restore(document_id)
    except DocumentLifecycleNotFoundError as exc:
        raise DocumentNotFoundApiError(details={"document_id": document_id}) from exc
    except DocumentLifecycleConflictError as exc:
        raise DocumentStateConflictApiError(message=str(exc), details={"document_id": document_id}) from exc
    return DocumentLifecycleResponse(
        document_id=document.id,
        lifecycle_status=document.lifecycle_status,
        archived_at=document.archived_at,
        deleted_at=document.deleted_at,
    )


@router.delete("/{document_id}", response_model=DocumentLifecycleResponse)
def delete_document(
    document_id: str,
    service: Annotated[DocumentLifecycleService, Depends(get_document_lifecycle_service)],
) -> DocumentLifecycleResponse:
    try:
        document = service.delete(document_id)
    except DocumentLifecycleNotFoundError as exc:
        raise DocumentNotFoundApiError(details={"document_id": document_id}) from exc
    return DocumentLifecycleResponse(
        document_id=document.id,
        lifecycle_status=document.lifecycle_status,
        archived_at=document.archived_at,
        deleted_at=document.deleted_at,
    )


@router.post("/import", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def import_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    request_context: Annotated[UploadRequestContext, Depends(get_upload_request_context)] = None,
    job_service: Annotated[BackgroundJobService, Depends(get_background_job_service)] = None,
) -> JobResponse:
    start_time = perf_counter()
    bind_observability_context(workspace_id=request_context.workspace_id, user_id=request_context.user_id)
    filename = file.filename or "untitled"
    mime_type = canonical_mime_type(filename, file.content_type)
    source_bytes = await file.read()
    if len(source_bytes) > settings.max_upload_file_size_bytes:
        duration_ms = int((perf_counter() - start_time) * 1000)
        log_event(
            "document_upload_failed",
            workspace_id=request_context.workspace_id,
            user_id=request_context.user_id,
            duration_ms=duration_ms,
            status="failed",
            error_code="FILE_TOO_LARGE",
        )
        raise FileTooLargeApiError(
            details={
                "filename": filename,
                "max_file_size_bytes": settings.max_upload_file_size_bytes,
                "received_file_size_bytes": len(source_bytes),
            }
        )
    temp_file_path = BackgroundJobService.create_temp_upload_file(filename=filename, source_bytes=source_bytes)
    job = job_service.enqueue_import_job(
        workspace_id=request_context.workspace_id,
        requested_by_user_id=request_context.user_id,
        filename=filename,
        mime_type=mime_type,
        temp_file_path=temp_file_path,
    )
    background_tasks.add_task(process_import_job, job.id, job_service._session.get_bind())
    return job_service.to_response(job)


@router.get("/import-jobs/{job_id}", response_model=JobResponse)
def get_import_job(
    job_id: str,
    job_service: Annotated[BackgroundJobService, Depends(get_background_job_service)],
) -> JobResponse:
    try:
        return job_service.to_response(job_service.get_job(job_id))
    except BackgroundJobNotFoundError as exc:
        raise BackgroundJobNotFoundApiError(details={"job_id": job_id}) from exc
