from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.v1.admin import get_background_job_service
from app.core.config import settings
from app.main import app


class FakeBackgroundJobService:
    def __init__(self) -> None:
        self.calls: list[str | None] = []
        self.created_at = datetime(2026, 5, 5, 0, 0, tzinfo=UTC)

    def enqueue_search_index_rebuild_job(self, *, workspace_id: str, requested_by_user_id: str | None, target_workspace_id: str | None):
        from types import SimpleNamespace

        self.calls.append(target_workspace_id)
        return SimpleNamespace(
            id="job-1",
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
            created_at=self.created_at,
            started_at=None,
            finished_at=None,
        )

    def to_response(self, job):
        return {
            "id": job.id,
            "job_type": job.job_type,
            "status": job.status,
            "workspace_id": job.workspace_id,
            "requested_by_user_id": job.requested_by_user_id,
            "filename": None,
            "created_at": self.created_at,
            "started_at": None,
            "finished_at": None,
            "progress_current": 0,
            "progress_total": 1,
            "progress_message": "Rebuild ist in Warteschlange",
            "error_code": None,
            "error_message": None,
            "result": None,
        }


def test_admin_search_index_rebuild_requires_authentication() -> None:
    response = TestClient(app).post("/api/v1/admin/search-index/rebuild")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


def test_admin_search_index_rebuild_requires_valid_admin_token(monkeypatch) -> None:
    monkeypatch.setattr(settings, "admin_api_token", "expected-token")

    response = TestClient(app).post(
        "/api/v1/admin/search-index/rebuild",
        headers={"x-admin-token": "wrong-token"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ADMIN_REQUIRED"


def test_admin_search_index_rebuild_returns_stable_shape(monkeypatch) -> None:
    monkeypatch.setattr(settings, "admin_api_token", "expected-token")
    service = FakeBackgroundJobService()
    app.dependency_overrides[get_background_job_service] = lambda: service
    try:
        response = TestClient(app).post(
            "/api/v1/admin/search-index/rebuild?workspace_id=workspace-1",
            headers={"x-admin-token": "expected-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    assert service.calls == ["workspace-1"]
    assert response.json() == {
        "id": "job-1",
        "job_type": "search_index_rebuild",
        "status": "queued",
        "workspace_id": "workspace-1",
        "requested_by_user_id": None,
        "filename": None,
        "created_at": "2026-05-05T00:00:00Z",
        "started_at": None,
        "finished_at": None,
        "progress_current": 0,
        "progress_total": 1,
        "progress_message": "Rebuild ist in Warteschlange",
        "error_code": None,
        "error_message": None,
        "result": None,
    }