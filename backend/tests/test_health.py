import importlib

from app.core.config import settings


def test_app_is_importable() -> None:
    module = importlib.import_module("app.main")

    assert module.app is not None


def test_health_returns_ok(client) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_database_health_reports_missing_configuration(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "database_url", None)

    response = client.get("/health/db")

    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "SERVICE_UNAVAILABLE",
            "message": "DATABASE_URL is not configured",
            "details": {},
        }
    }
