from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.documents import get_background_job_service
from app.core.errors import BackgroundJobNotFoundApiError
from app.schemas.jobs import JobResponse
from app.services.jobs.background_jobs import BackgroundJobNotFoundError, BackgroundJobService


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    job_service: Annotated[BackgroundJobService, Depends(get_background_job_service)],
) -> JobResponse:
    try:
        return job_service.to_response(job_service.get_job(job_id))
    except BackgroundJobNotFoundError as exc:
        raise BackgroundJobNotFoundApiError(details={"job_id": job_id}) from exc