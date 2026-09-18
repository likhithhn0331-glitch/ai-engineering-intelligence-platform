import pytest
from fastapi.testclient import TestClient

from src.database import initialize_database
from src.db.connection import get_database_url
from src.main import app
from src.repositories.document_repository import DocumentRepository
from src.data_classes.document_class import Document

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
def clear_documents():
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


def test_postgres_repository_uses_database_backend():
    repo = DocumentRepository()
    assert repo.use_postgres is True

    created = repo.create_document(
        Document(
            id_="doc-pg-001",
            name="Repository Round Trip",
            document_type="requirement",
            version="1.0",
            status="created",
        )
    )

    fetched = repo.get_document("doc-pg-001")
    assert created.id == "doc-pg-001"
    assert fetched is not None
    assert fetched.name == "Repository Round Trip"


def test_postgres_create_and_get_document_end_to_end(client):
    payload = {"name": "PG Roundtrip", "document_type": "test", "version": "7.1"}

    create_resp = client.post("/documents", json=payload)
    assert create_resp.status_code == 201

    created = create_resp.json()
    document_id = created["id"]
    assert created["name"] == payload["name"]
    assert created["status"] == "created"

    get_resp = client.get(f"/documents/{document_id}")
    assert get_resp.status_code == 200
    fetched = get_resp.json()
    assert fetched["id"] == document_id
    assert fetched["name"] == payload["name"]
    assert fetched["document_type"] == payload["document_type"]
    assert fetched["version"] == payload["version"]


def test_postgres_list_and_update_document_end_to_end(client):
    first = {"name": "PG One", "document_type": "requirement", "version": "1.0"}
    second = {"name": "PG Two", "document_type": "design", "version": "2.0"}

    first_resp = client.post("/documents", json=first)
    second_resp = client.post("/documents", json=second)
    assert first_resp.status_code == 201
    assert second_resp.status_code == 201

    list_resp = client.get("/documents")
    assert list_resp.status_code == 200
    documents = list_resp.json()
    names = {doc["name"] for doc in documents}
    assert names == {"PG One", "PG Two"}

    document_id = first_resp.json()["id"]
    update_resp = client.put(
        f"/documents/{document_id}",
        json={"name": "PG One Updated", "document_type": "test", "version": "3.0"},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["name"] == "PG One Updated"
    assert updated["document_type"] == "test"
    assert updated["version"] == "3.0"

    get_resp = client.get(f"/documents/{document_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "PG One Updated"


def test_postgres_query_filters_sorts_and_paginates_documents(client):
    documents = [
        {"name": "Architecture Spec", "document_type": "design", "version": "2.0"},
        {"name": "API Requirement", "document_type": "requirement", "version": "1.0"},
        {"name": "Database Requirement", "document_type": "requirement", "version": "1.1"},
    ]
    for payload in documents:
        response = client.post("/documents", json=payload)
        assert response.status_code == 201

    response = client.get(
        "/documents",
        params={
            "document_type": "requirement",
            "name_contains": "requirement",
            "sort_by": "name",
            "sort_order": "desc",
            "limit": 1,
            "offset": 1,
        },
    )

    assert response.status_code == 200
    assert [document["name"] for document in response.json()] == ["API Requirement"]


def test_postgres_created_at_desc_order_is_observable(client):
    created_ids = {}
    for name in ["Older Requirement", "Newest Requirement", "Middle Requirement"]:
        response = client.post(
            "/documents",
            json={"name": name, "document_type": "requirement", "version": "1.0"},
        )
        assert response.status_code == 201
        created_ids[name] = response.json()["id"]

    database_url = get_database_url()
    with psycopg.connect(database_url, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE documents
                SET created_at = CASE id
                    WHEN %s THEN TIMESTAMPTZ '2026-01-01 00:00:00+00'
                    WHEN %s THEN TIMESTAMPTZ '2026-01-03 00:00:00+00'
                    WHEN %s THEN TIMESTAMPTZ '2026-01-02 00:00:00+00'
                END
                WHERE id IN (%s, %s, %s)
                """,
                (
                    created_ids["Older Requirement"],
                    created_ids["Newest Requirement"],
                    created_ids["Middle Requirement"],
                    created_ids["Older Requirement"],
                    created_ids["Newest Requirement"],
                    created_ids["Middle Requirement"],
                ),
            )

    response = client.get(
        "/documents",
        params={"sort_by": "created_at", "sort_order": "desc"},
    )

    assert response.status_code == 200
    assert [document["name"] for document in response.json()] == [
        "Newest Requirement",
        "Middle Requirement",
        "Older Requirement",
    ]


def test_postgres_delete_document_end_to_end(client):
    payload = {"name": "PG Delete Me", "document_type": "requirement", "version": "1.0"}
    create_resp = client.post("/documents", json=payload)
    assert create_resp.status_code == 201
    document_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/documents/{document_id}")
    assert delete_resp.status_code == 204
    assert delete_resp.content == b""

    get_resp = client.get(f"/documents/{document_id}")
    assert get_resp.status_code == 404
    assert get_resp.json()["detail"] == f"Document with ID '{document_id}' not found."
