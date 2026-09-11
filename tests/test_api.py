from fastapi.testclient import TestClient
import pytest

from src.main import app
import src.api.document_routes as document_routes
from src.repositories.document_repository import DocumentRepository
from src.services.document_service import DocumentService


@pytest.fixture(autouse=True)
def reset_repository():
    # Recreate repository and service so tests are isolated
    document_routes.repository = DocumentRepository()
    document_routes.service = DocumentService(document_routes.repository)


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


def test_invalid_request_validation_error(client):
    # Missing required 'name' field should produce a validation error (422)
    payload = {"document_type": "requirement", "version": "1.0"}
    resp = client.post("/documents", json=payload)
    assert resp.status_code == 422
    assert "detail" in resp.json()


def test_missing_document_returns_404(client):
    resp = client.get("/documents/nonexistent-id")
    assert resp.status_code == 404
    assert resp.json().get("detail") == "Document with ID 'nonexistent-id' not found."