from typing import Annotated

from app.api.dependencies.auth import RequestAuthContext, require_workspace_member
from fastapi import APIRouter, Depends

from app.api.documents import get_background_job_service
from app.core.errors import BackgroundJobNotFoundApiError
from app.schemas.jobs import JobResponse
from app.services.jobs.background_jobs import BackgroundJobNotFoundError, BackgroundJobService


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    auth_context: Annotated[RequestAuthContext, Depends(require_workspace_member)],
    job_service: Annotated[BackgroundJobService, Depends(get_background_job_service)],
) -> JobResponse:
    try:
        job = job_service.get_job(job_id)
        if job.workspace_id != auth_context.workspace_id:
            raise BackgroundJobNotFoundError(job_id)
        return job_service.to_response(job)
    except BackgroundJobNotFoundError as exc:
        raise BackgroundJobNotFoundApiError(details={"job_id": job_id}) from exc