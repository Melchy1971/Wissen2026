from fastapi.testclient import TestClient


def test_documents_require_authenticated_workspace_context() -> None:
    from app.main import app

    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/documents")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


def test_documents_list_uses_authenticated_workspace(client: TestClient, document_fixture: dict[str, str]) -> None:
    response = client.get("/documents")

    assert response.status_code == 200
    payload = response.json()
    assert [document["id"] for document in payload] == [
        document_fixture["document_id"],
        "00000000-0000-0000-0000-000000000102",
    ]


def test_document_detail_is_scoped_to_authenticated_workspace(client: TestClient, document_fixture: dict[str, str]) -> None:
    response = client.get(f"/documents/{document_fixture['document_id']}")

    assert response.status_code == 200
    assert response.json()["id"] == document_fixture["document_id"]