from typing import Annotated, Iterator

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Query, status

from app.core.config import settings
from app.core.database import DatabaseConfigurationError
from app.core.errors import AdminRequiredApiError, ApiError, AuthRequiredApiError
from app.db.session import get_session
from app.schemas.jobs import JobResponse
from app.services.jobs.background_jobs import BackgroundJobService, process_search_index_rebuild_job


router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin_access(x_admin_token: Annotated[str | None, Header()] = None) -> None:
    if x_admin_token is None or not x_admin_token.strip():
        raise AuthRequiredApiError()
    if x_admin_token != settings.admin_api_token:
        raise AdminRequiredApiError()


def get_background_job_service() -> Iterator[BackgroundJobService]:
    try:
        for session in get_session():
            yield BackgroundJobService.from_session(session)
    except DatabaseConfigurationError as exc:
        raise ApiError(message=str(exc)) from exc


@router.post("/search-index/rebuild", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
def rebuild_search_index(
    background_tasks: BackgroundTasks,
    workspace_id: Annotated[str | None, Query(min_length=1)] = None,
    _admin: None = Depends(require_admin_access),
    service: BackgroundJobService = Depends(get_background_job_service),
) -> JobResponse:
    job = service.enqueue_search_index_rebuild_job(
        workspace_id=workspace_id or "ALL",
        requested_by_user_id=None,
        target_workspace_id=workspace_id,
    )
    session = getattr(service, "_session", None)
    if session is not None:
        background_tasks.add_task(process_search_index_rebuild_job, job.id, session.get_bind())
    return service.to_response(job)