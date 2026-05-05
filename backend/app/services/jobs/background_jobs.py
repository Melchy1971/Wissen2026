from __future__ import annotations

from datetime import UTC, datetime
import os
from pathlib import Path
import tempfile
from uuid import uuid4

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ApiError
from app.models.documents import BackgroundJob
from app.schemas.jobs import ImportJobResult, JobResponse, SearchIndexRebuildJobResult
from app.services.documents.import_executor import ImportExecutor
from app.services.search_index_service import SearchIndexRebuildService


class BackgroundJobNotFoundError(LookupError):
    pass


class BackgroundJobService:
    def __init__(self, session: Session) -> None:
        self._session = session

    @classmethod
    def from_session(cls, session: Session) -> "BackgroundJobService":
        return cls(session)

    def enqueue_import_job(
        self,
        *,
        workspace_id: str,
        requested_by_user_id: str,
        filename: str,
        mime_type: str,
        temp_file_path: str,
    ) -> BackgroundJob:
        now = datetime.now(UTC)
        job = BackgroundJob(
            id=str(uuid4()),
            job_type="document_import",
            status="queued",
            workspace_id=workspace_id,
            requested_by_user_id=requested_by_user_id,
            payload_={
                "filename": filename,
                "mime_type": mime_type,
                "temp_file_path": temp_file_path,
            },
            result_=None,
            progress_current=0,
            progress_total=1,
            progress_message="Import ist in Warteschlange",
            error_code=None,
            error_message=None,
            attempt_count=0,
            locked_at=None,
            locked_by=None,
            created_at=now,
            started_at=None,
            finished_at=None,
        )
        self._session.add(job)
        self._session.commit()
        self._session.refresh(job)
        return job

    def get_job(self, job_id: str) -> BackgroundJob:
        job = self._session.get(BackgroundJob, job_id)
        if job is None:
            raise BackgroundJobNotFoundError(job_id)
        return job

    def enqueue_search_index_rebuild_job(
        self,
        *,
        workspace_id: str,
        requested_by_user_id: str | None,
        target_workspace_id: str | None,
    ) -> BackgroundJob:
        now = datetime.now(UTC)
        job = BackgroundJob(
            id=str(uuid4()),
            job_type="search_index_rebuild",
            status="queued",
            workspace_id=workspace_id,
            requested_by_user_id=requested_by_user_id,
            payload_={"target_workspace_id": target_workspace_id},
            result_=None,
            progress_current=0,
            progress_total=1,
            progress_message="Rebuild ist in Warteschlange",
            error_code=None,
            error_message=None,
            attempt_count=0,
            locked_at=None,
            locked_by=None,
            created_at=now,
            started_at=None,
            finished_at=None,
        )
        self._session.add(job)
        self._session.commit()
        self._session.refresh(job)
        return job

    def to_response(self, job: BackgroundJob) -> JobResponse:
        result = job.result_ if isinstance(job.result_, dict) else None
        parsed_result = None
        if result is not None:
            if job.job_type == "document_import":
                parsed_result = ImportJobResult(**result)
            elif job.job_type == "search_index_rebuild":
                parsed_result = SearchIndexRebuildJobResult(**result)
        return JobResponse(
            id=job.id,
            job_type=job.job_type,
            status=job.status,
            workspace_id=job.workspace_id,
            requested_by_user_id=job.requested_by_user_id,
            filename=str(job.payload_.get("filename")) if isinstance(job.payload_, dict) else None,
            created_at=job.created_at,
            started_at=job.started_at,
            finished_at=job.finished_at,
            progress_current=job.progress_current,
            progress_total=job.progress_total,
            progress_message=job.progress_message,
            error_code=job.error_code,
            error_message=job.error_message,
            result=parsed_result,
        )

    @staticmethod
    def create_temp_upload_file(*, filename: str, source_bytes: bytes) -> str:
        temp_root = Path(settings.import_jobs_temp_dir or (Path(tempfile.gettempdir()) / "wissensbasis-import-jobs"))
        temp_root.mkdir(parents=True, exist_ok=True)
        suffix = Path(filename).suffix or ".bin"
        with tempfile.NamedTemporaryFile(delete=False, dir=temp_root, prefix="import-job-", suffix=suffix) as handle:
            handle.write(source_bytes)
            return handle.name


def process_import_job(job_id: str, bind: Engine | None = None) -> None:
    from sqlalchemy.orm import Session as SqlAlchemySession
    from app.db.session import get_engine

    with SqlAlchemySession(bind or get_engine()) as session:
        service = BackgroundJobService.from_session(session)
        try:
            job = service.get_job(job_id)
        except BackgroundJobNotFoundError:
            return

        if job.job_type != "document_import" or job.status not in {"queued", "failed"}:
            return

        now = datetime.now(UTC)
        job.status = "running"
        job.started_at = now
        job.finished_at = None
        job.locked_at = now
        job.locked_by = "in-process-worker"
        job.progress_current = 0
        job.progress_total = 1
        job.progress_message = "Import wird verarbeitet"
        job.error_code = None
        job.error_message = None
        job.attempt_count += 1
        session.add(job)
        session.commit()

        payload = job.payload_ if isinstance(job.payload_, dict) else {}
        temp_file_path = str(payload.get("temp_file_path") or "")
        filename = str(payload.get("filename") or "untitled")
        mime_type = str(payload.get("mime_type") or "application/octet-stream")

        try:
            source_bytes = Path(temp_file_path).read_bytes()
            result = ImportExecutor().execute(
                workspace_id=job.workspace_id,
                user_id=job.requested_by_user_id or settings.default_user_id,
                filename=filename,
                mime_type=mime_type,
                source_bytes=source_bytes,
            )
            job.status = "completed"
            job.progress_current = 1
            job.progress_total = 1
            job.progress_message = "Import abgeschlossen"
            job.result_ = result
            job.error_code = None
            job.error_message = None
        except ApiError as exc:
            job.status = "failed"
            job.progress_current = 1
            job.progress_total = 1
            job.progress_message = "Import fehlgeschlagen"
            job.error_code = exc.code
            job.error_message = exc.message
            job.result_ = None
        except Exception:
            job.status = "failed"
            job.progress_current = 1
            job.progress_total = 1
            job.progress_message = "Import fehlgeschlagen"
            job.error_code = "IMPORT_FAILED"
            job.error_message = "Document import failed"
            job.result_ = None
        finally:
            job.finished_at = datetime.now(UTC)
            job.locked_at = None
            job.locked_by = None
            session.add(job)
            session.commit()
            if temp_file_path:
                try:
                    os.remove(temp_file_path)
                except FileNotFoundError:
                    pass


def process_search_index_rebuild_job(job_id: str, bind: Engine | None = None) -> None:
    from sqlalchemy.orm import Session as SqlAlchemySession
    from app.db.session import get_engine

    with SqlAlchemySession(bind or get_engine()) as session:
        service = BackgroundJobService.from_session(session)
        try:
            job = service.get_job(job_id)
        except BackgroundJobNotFoundError:
            return

        if job.job_type != "search_index_rebuild" or job.status not in {"queued", "failed"}:
            return

        now = datetime.now(UTC)
        job.status = "running"
        job.started_at = now
        job.finished_at = None
        job.locked_at = now
        job.locked_by = "in-process-worker"
        job.progress_current = 0
        job.progress_total = 1
        job.progress_message = "Search-Index-Rebuild wird verarbeitet"
        job.error_code = None
        job.error_message = None
        job.attempt_count += 1
        session.add(job)
        session.commit()

        payload = job.payload_ if isinstance(job.payload_, dict) else {}
        target_workspace_id = payload.get("target_workspace_id")

        try:
            result = SearchIndexRebuildService.from_session(session).rebuild_search_index(workspace_id=target_workspace_id)
            job.status = "completed"
            job.progress_current = 1
            job.progress_total = 1
            job.progress_message = "Search-Index-Rebuild abgeschlossen"
            job.result_ = result
            job.error_code = None
            job.error_message = None
        except ApiError as exc:
            job.status = "failed"
            job.progress_current = 1
            job.progress_total = 1
            job.progress_message = "Search-Index-Rebuild fehlgeschlagen"
            job.error_code = exc.code
            job.error_message = exc.message
            job.result_ = None
        except Exception:
            job.status = "failed"
            job.progress_current = 1
            job.progress_total = 1
            job.progress_message = "Search-Index-Rebuild fehlgeschlagen"
            job.error_code = "SERVICE_UNAVAILABLE"
            job.error_message = "Search index rebuild failed"
            job.result_ = None
        finally:
            job.finished_at = datetime.now(UTC)
            job.locked_at = None
            job.locked_by = None
            session.add(job)
            session.commit()