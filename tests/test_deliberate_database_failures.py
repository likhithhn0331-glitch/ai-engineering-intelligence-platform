import pytest
from fastapi.testclient import TestClient

from src.database import initialize_database
from src.db.connection import get_database_url
from src.main import app

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


pytestmark = pytest.mark.skipif(
    not get_database_url() or psycopg is None,
    reason="requires a configured PostgreSQL DATABASE_URL",
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_documents():
    database_url = get_database_url()
    if database_url and psycopg is not None:
        initialize_database()
        with psycopg.connect(database_url, autocommit=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute("TRUNCATE TABLE documents;")
    yield
    if database_url and psycopg is not None:
        initialize_database()
        with psycopg.connect(database_url, autocommit=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute("TRUNCATE TABLE documents;")


def test_duplicate_primary_key_is_rejected_by_database():
    database_url = get_database_url()
    assert database_url is not None

    with psycopg.connect(database_url, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO documents (id, name, document_type, version, status) VALUES (%s, %s, %s, %s, %s)",
                ("doc-dup", "alpha", "requirement", "1.0", "created"),
            )

            with pytest.raises(psycopg.errors.UniqueViolation):
                cursor.execute(
                    "INSERT INTO documents (id, name, document_type, version, status) VALUES (%s, %s, %s, %s, %s)",
                    ("doc-dup", "beta", "requirement", "2.0", "created"),
                )


def test_missing_required_field_is_rejected_by_database():
    database_url = get_database_url()
    assert database_url is not None

    with psycopg.connect(database_url, autocommit=True) as connection:
        with connection.cursor() as cursor:
            with pytest.raises(psycopg.errors.NotNullViolation):
                cursor.execute(
                    "INSERT INTO documents (id, document_type, version, status) VALUES (%s, %s, %s, %s)",
                    ("doc-missing", "requirement", "1.0", "created"),
                )


def test_invalid_document_type_is_rejected_by_service_validation(client):
    payload = {"name": "Invalid Type", "document_type": "unsupported", "version": "1.0"}
    resp = client.post("/documents", json=payload)
    assert resp.status_code == 400
    assert "Invalid document type" in resp.json()["detail"]


def test_update_nonexistent_document_returns_not_found(client):
    resp = client.put(
        "/documents/does-not-exist",
        json={"name": "Updated Name", "document_type": "design", "version": "2.0"},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Document with ID 'does-not-exist' not found."


def test_delete_nonexistent_document_returns_not_found(client):
    resp = client.delete("/documents/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Document with ID 'does-not-exist' not found."
