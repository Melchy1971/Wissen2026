from fastapi.testclient import TestClient

from app.main import app


def test_import_rejects_unsupported_file_type() -> None:
    client = TestClient(app)

    response = client.post(
        "/documents/import",
        files={"file": ("scan.pdf", b"%PDF-1.7", "application/pdf")},
    )

    assert response.status_code == 415
    assert response.json() == {"detail": "Only .txt and .md uploads are supported"}
