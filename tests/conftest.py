import os

import pytest

try:
    import psycopg
except ImportError:  # pragma: no cover - optional in memory-only runs
    psycopg = None

from src.api import document_routes
from src.db.connection import get_database_url
from src.repositories.document_repository import DocumentRepository
from src.services.document_service import DocumentService


@pytest.fixture(autouse=True)
def reset_repository():
    database_url = get_database_url()
    if database_url and psycopg is not None:
        try:
            with psycopg.connect(database_url, autocommit=True) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("TRUNCATE TABLE documents;")
        except Exception:
            pass

    document_routes.repository = DocumentRepository()
    document_routes.service = DocumentService(document_routes.repository)
    yield

    if database_url and psycopg is not None:
        try:
            with psycopg.connect(database_url, autocommit=True) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("TRUNCATE TABLE documents;")
        except Exception:
            pass
