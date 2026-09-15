from fastapi.testclient import TestClient
import pytest

from src.main import app
import src.api.document_routes as document_routes
from src.repositories.document_repository import DocumentRepository
from src.services.document_service import DocumentService


@pytest.fixture
def client():
    return TestClient(app)


def test_root_returns_200(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_health_returns_healthy(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json().get("status") == "healthy"


def test_post_documents_success(client):
    payload = {"name": "Test Doc", "document_type": "requirement", "version": "1.0"}
    resp = client.post("/documents", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Doc"
    assert data["document_type"] == "requirement"
    assert data["version"] == "1.0"
    assert data["id"].startswith("doc-")
    assert data["status"] == "created"


def test_get_document_returns_created_document(client):
    payload = {"name": "Retrieve Doc", "document_type": "requirement", "version": "1.0"}
    create_resp = client.post("/documents", json=payload)
    assert create_resp.status_code == 201
    document_id = create_resp.json()["id"]

    resp = client.get(f"/documents/{document_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == document_id
    assert data["name"] == "Retrieve Doc"
    assert data["document_type"] == "requirement"
    assert data["version"] == "1.0"
    assert data["status"] == "created"


def test_list_documents_returns_all_documents(client):
    first = {"name": "First Doc", "document_type": "requirement", "version": "1.0"}
    second = {"name": "Second Doc", "document_type": "design", "version": "2.1"}

    post_one = client.post("/documents", json=first)
    post_two = client.post("/documents", json=second)

    assert post_one.status_code == 201
    assert post_two.status_code == 201

    resp = client.get("/documents")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert [doc["name"] for doc in data] == ["First Doc", "Second Doc"]
    assert all(doc["status"] == "created" for doc in data)


def test_update_document_updates_document(client):
    payload = {"name": "Original Doc", "document_type": "requirement", "version": "1.0"}
    create_resp = client.post("/documents", json=payload)
    assert create_resp.status_code == 201
    document_id = create_resp.json()["id"]

    updated_payload = {"name": "Updated Doc", "document_type": "design", "version": "2.0"}
    resp = client.put(f"/documents/{document_id}", json=updated_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == document_id
    assert data["name"] == "Updated Doc"
    assert data["document_type"] == "design"
    assert data["version"] == "2.0"

    follow_up = client.get(f"/documents/{document_id}")
    assert follow_up.status_code == 200
    assert follow_up.json()["name"] == "Updated Doc"


def test_create_then_get_returns_same_document(client):
    payload = {"name": "Roundtrip Doc", "document_type": "test", "version": "7.3"}
    create_resp = client.post("/documents", json=payload)
    assert create_resp.status_code == 201
    document_id = create_resp.json()["id"]

    get_resp = client.get(f"/documents/{document_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == document_id
    assert data["name"] == payload["name"]
    assert data["document_type"] == payload["document_type"]
    assert data["version"] == payload["version"]
    assert data["status"] == "created"


def test_invalid_request_validation_error(client):
    # Missing required 'name' field should produce a validation error (422)
    payload = {"document_type": "requirement", "version": "1.0"}
    resp = client.post("/documents", json=payload)
    assert resp.status_code == 422
    assert "detail" in resp.json()


def test_delete_document_removes_document(client):
    payload = {"name": "Delete Me", "document_type": "requirement", "version": "1.0"}
    create_resp = client.post("/documents", json=payload)
    assert create_resp.status_code == 201
    document_id = create_resp.json()["id"]

    resp = client.delete(f"/documents/{document_id}")
    assert resp.status_code == 204
    assert resp.content == b""

    follow_up = client.get(f"/documents/{document_id}")
    assert follow_up.status_code == 404
    assert follow_up.json().get("detail") == f"Document with ID '{document_id}' not found."


def test_missing_document_returns_404(client):
    resp = client.get("/documents/nonexistent-id")
    assert resp.status_code == 404
    assert resp.json().get("detail") == "Document with ID 'nonexistent-id' not found."


def test_delete_missing_document_returns_404(client):
    resp = client.delete("/documents/nonexistent-id")
    assert resp.status_code == 404
    assert resp.json().get("detail") == "Document with ID 'nonexistent-id' not found."