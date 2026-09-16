import os
from contextlib import contextmanager
from typing import Iterator

from dotenv import load_dotenv

from src.exceptions.document_exceptions import DatabaseUnavailableError

load_dotenv()

try:
    import psycopg
except ImportError:  # pragma: no cover - dependency is optional until runtime config is set
    psycopg = None


class DatabaseConfigurationError(RuntimeError):
    """Raised when the application is missing database configuration."""


class DatabaseOperationError(RuntimeError):
    """Raised when a database operation fails unexpectedly."""


def get_database_url() -> str | None:
    database_url = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        return None

    placeholder_tokens = ("<user>", "<password>", "<host>", "<database>")
    if any(token in database_url for token in placeholder_tokens):
        return None

    return database_url


def get_database_config() -> str:
    database_url = get_database_url()
    if not database_url:
        raise DatabaseConfigurationError("DATABASE_URL is not configured.")
    return database_url


@contextmanager
def database_connection() -> Iterator[object]:
    if psycopg is None:
        raise DatabaseConfigurationError("psycopg is required for PostgreSQL access.")

    try:
        connection = psycopg.connect(get_database_config(), autocommit=False)
    except Exception as exc:
        raise DatabaseUnavailableError("Database is unavailable.") from exc

    try:
        yield connection
        # Commit when the caller block exits normally. This centralizes
        # transaction lifecycle and ensures callers don't forget to commit.
        try:
            connection.commit()
        except Exception as exc:
            # If commit fails, attempt rollback to leave the DB in a clean state
            try:
                connection.rollback()
            except Exception:
                pass
            if isinstance(exc, psycopg.Error):
                raise DatabaseUnavailableError("Database is unavailable.") from exc
            raise
    except Exception as exc:
        try:
            connection.rollback()
        except Exception:
            pass
        if isinstance(exc, psycopg.Error):
            raise DatabaseUnavailableError("Database is unavailable.") from exc
        raise
    finally:
        connection.close()
