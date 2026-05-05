from typing import Annotated, Iterator

from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.api.dependencies.auth import RequestAuthContext, require_workspace_admin
from app.core.config import settings
from app.core.database import DatabaseConfigurationError
from app.core.errors import ApiError
from app.db.session import get_session
from app.schemas.jobs import JobResponse
from app.services.jobs.background_jobs import BackgroundJobService, process_search_index_rebuild_job


router = APIRouter(prefix="/admin", tags=["admin"])


def get_background_job_service() -> Iterator[BackgroundJobService]:
    try:
        for session in get_session():
            yield BackgroundJobService.from_session(session)
    except DatabaseConfigurationError as exc:
        raise ApiError(message=str(exc)) from exc


@router.post("/search-index/rebuild", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
def rebuild_search_index(
    background_tasks: BackgroundTasks,
    auth_context: Annotated[RequestAuthContext, Depends(require_workspace_admin)],
    service: BackgroundJobService = Depends(get_background_job_service),
) -> JobResponse:
    job = service.enqueue_search_index_rebuild_job(
        workspace_id=auth_context.workspace_id,
        requested_by_user_id=auth_context.user_id,
        target_workspace_id=auth_context.workspace_id,
    )
    session = getattr(service, "_session", None)
    if session is not None:
        background_tasks.add_task(process_search_index_rebuild_job, job.id, session.get_bind())
    return service.to_response(job)