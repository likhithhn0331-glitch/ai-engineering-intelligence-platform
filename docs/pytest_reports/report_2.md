# PostgreSQL Integration Test Report (report_2)

## Purpose

This report documents the PostgreSQL-backed end-to-end integration tests added for the document API. The goal is to verify that the application behaves correctly when persistence is backed by PostgreSQL rather than the in-memory dictionary.

The new test file is:

- `tests/test_postgres_integration.py`

## What was implemented

The project now has a structured PostgreSQL persistence flow:

1. `DATABASE_URL` is read from environment configuration.
2. A migration runner initializes the schema when the app starts.
3. A dedicated database connection boundary manages connection lifecycle and resource closure.
4. `DocumentRepository` uses PostgreSQL for `create`, `get`, `list`, `update`, and `delete` operations when a valid PostgreSQL connection is configured.
5. A lightweight fallback remains for local or non-database test runs, but the production path is PostgreSQL-backed.

The application continues to expose the same API contract to clients. The storage implementation changed beneath the repository, but the API behavior and error architecture remain aligned with the existing system.

## Schema under test

The PostgreSQL schema is created from:

- `migrations/001_create_documents_table.sql`

The table is:

```sql
CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    document_type VARCHAR(255) NOT NULL,
    version VARCHAR(255) NOT NULL,
    status VARCHAR(255) NOT NULL DEFAULT 'created',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

The migration runner also creates a `schema_migrations` table to record which migration files have already been applied.

## Test isolation strategy

The PostgreSQL integration tests are designed to avoid interference between test cases:

- each test uses a real PostgreSQL-backed repository
- an autouse fixture performs `TRUNCATE TABLE documents;` before and after each test
- the schema is initialized before the table is truncated to ensure the table exists

This gives each test a clean, reproducible starting state and prevents one test from leaking state into the next.

## Test cases implemented

### 1. `test_postgres_repository_uses_database_backend`

Purpose:
- verifies the repository is using PostgreSQL in a configured environment
- verifies the repository can create a document and read it back from PostgreSQL

Checks:
- `repo.use_postgres is True`
- a document can be inserted into the `documents` table through the repository
- a subsequent `get_document()` returns the same record

Pass condition:
- the repository reports Postgres mode enabled
- the inserted row is present and its stored values match the expected ones

### 2. `test_postgres_create_and_get_document_end_to_end`

Purpose:
- verifies the API create flow and single-document lookup work end to end with PostgreSQL

Checks:
- `POST /documents` returns `201`
- the returned JSON has the expected `name`, `document_type`, `version`, and `status`
- `GET /documents/{id}` returns the same record data

Pass condition:
- the HTTP status code is correct
- the created document is returned with the same logical identity and values
- the retrieved record matches the data inserted through the API

### 3. `test_postgres_list_and_update_document_end_to_end`

Purpose:
- verifies collection reading and update behavior in PostgreSQL-backed mode

Checks:
- two documents can be created via the API
- `GET /documents` contains both records
- `PUT /documents/{id}` updates the selected document
- a subsequent `GET /documents/{id}` shows the updated values

Pass condition:
- the API returns all expected documents in the list
- the update response contains the new values
- the persisted state reflects the updated data on readback

### 4. `test_postgres_delete_document_end_to_end`

Purpose:
- verifies deletion and 404-not-found semantics with PostgreSQL persistence

Checks:
- `POST /documents` creates a document
- `DELETE /documents/{id}` returns `204`
- a subsequent `GET /documents/{id}` returns `404`
- the 404 detail matches the expected message format

Pass condition:
- the delete succeeds with the expected status code
- the record disappears from the database
- a later lookup correctly triggers `DocumentNotFoundError` → global handler → HTTP 404

## How a test is deemed as passed

A PostgreSQL integration test is considered passed when all assertions for that test succeed under the configured database environment.

The criteria are:

- the HTTP response status matches the expected status code
- the returned JSON payload matches the expected logical document data
- the database state matches the expected persisted state after create, update, and delete operations
- the repository correctly reads the data stored in PostgreSQL
- centralized error handling continues to produce the correct HTTP responses for not-found conditions

### Example pass rule

For the delete test, the test passes only if all of the following are true:

1. a document is created successfully with `201`
2. the delete endpoint returns `204`
3. a subsequent fetch of the same ID returns `404`
4. the JSON body detail equals `Document with ID '{id}' not found.`

If any assertion fails, the test fails and the test runner reports the failure.

## Execution command

The PostgreSQL integration tests were executed with:

```bash
./.venv/Scripts/python.exe -m pytest -q tests/test_postgres_integration.py
```

## Result

The PostgreSQL integration suite passed successfully:

- `4 passed`

This confirms the PostgreSQL-backed repository implementation is working end to end for the critical document flows: creation, retrieval, listing, update, delete, and not-found handling.
