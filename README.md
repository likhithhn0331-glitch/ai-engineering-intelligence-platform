# AI Engineering Intelligence Platform

AI Engineering Change and Test Intelligence Platform.

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/) [![License](https://img.shields.io/badge/license-MIT-brightgreen)]()

Last updated: 2026-09-16

## Quickstart

Installation
1. Create and activate a virtual environment:
   .\.venv\Scripts\activate
2. Install dependencies:
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
3. Copy and edit environment file:
   copy .env.example .env
   (set DATABASE_URL in .env)
4. Run migrations:
   .\.venv\Scripts\python.exe src\database.py

Run locally

.\.venv\Scripts\python.exe -m uvicorn src.main:app --reload

Usage example

curl -X POST http://localhost:8000/documents -H "Content-Type: application/json" -d "{\"name\":\"engine-requirement\",\"document_type\":\"requirement\",\"version\":\"1.0\"}"

## Architecture

The application follows a layered architecture for document management:

HTTP Client
↓
FastAPI Router
↓
DocumentService
↓
DocumentRepository
↓
Database connection boundary
↓
PostgreSQL

This flow is implemented for the document endpoints:

POST /documents
↓
API Layer
↓
Service Layer
↓
Repository Layer
↓
Database connection
↓
PostgreSQL storage

## Project Structure

- `src/main.py` – FastAPI app entry point, global exception handlers, and root/health routes
- `src/api/document_routes.py` – HTTP endpoints for document operations; routes do not translate exceptions themselves
- `src/services/document_service.py` – Business logic, validation, document creation, and orchestration
- `src/repositories/document_repository.py` – PostgreSQL-backed repository with in-memory fallback for local non-DB runs
- `src/db/connection.py` – database configuration and connection lifecycle boundary
- `src/database.py` – migration runner and database initialization entry point
- `src/db/schema.sql` – schema reference file
- `migrations/001_create_documents_table.sql` – reproducible schema migration for the documents table
- `src/models/pydantic_model.py` – Request/response schemas
- `src/data_classes/document_class.py` – Document domain model
- `src/exceptions/document_exceptions.py` – Custom exceptions
- `tests/test_api.py` – API contract tests
- `tests/test_postgres_integration.py` – PostgreSQL end-to-end repository and API integration tests

## Database model

The PostgreSQL schema currently used by the application is:

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

This matches the fields already represented by the current API and intentionally does not add extra columns beyond the real project need.

## Database and configuration

The application uses environment-based configuration rather than hard-coded database credentials.

Configuration files:

- `.env` (local-only, not committed)
- `.env.example` (example template committed to Git)

Example:

```env
DATABASE_URL=postgresql://postgres:MyStrongPass123@localhost:5432/ai_engineering_platform
```

The app reads `DATABASE_URL` through the config connection boundary and the migration runner executes on startup when a valid database URL is present.

## Migration strategy

The schema is reproducible and not created manually once-off. The project includes a migration mechanism:

- `migrations/001_create_documents_table.sql`
- `src/database.py` runs migrations in ordered file sequence
- `schema_migrations` stores applied migration names so they are not repeated

This allows another developer to reproduce the table by running the migration task against a fresh PostgreSQL database.

## Connection lifecycle and failure handling

The application now includes a dedicated database connection boundary:

- `src/db/connection.py`
- `database_connection()` opens a connection, yields it to the repository, rolls back on failure, and closes it in a `finally` block
- `get_database_url()` reads environment-based configuration
- placeholder values such as `<user>`, `<password>`, `<host>`, and `<database>` are ignored to avoid invalid runtime DB attempts

This keeps DB access centralized and ensures connection cleanup is handled without leaking resources.

## Exception handling

Centralized FastAPI exception handling remains in `src/main.py` and is not reintroduced in the route layer.

- `DocumentNotFoundError` → HTTP 404 with JSON {"detail": "..."}
- `InvalidDocumentError` → HTTP 400 with JSON {"detail": "..."}
- `fastapi.exceptions.RequestValidationError` → HTTP 422 with validation details
- Generic `Exception` → HTTP 500 with JSON {"detail": "Internal server error"}

This is preserved across the PostgreSQL implementation so the API contract remains stable.

## Document API

### Create document

Request:

```json
{
  "name": "engine-requirement",
  "document_type": "requirement",
  "version": "1.0"
}
```

Response:

```json
{
  "id": "doc-001",
  "name": "engine-requirement",
  "document_type": "requirement",
  "version": "1.0",
  "status": "created"
}
```

### Supported document types

- `requirement`
- `design`
- `test`

### Endpoints

- `GET /` – app status
- `GET /health` – health check
- `POST /documents` – create a document
- `GET /documents` – list all documents
- `GET /documents/{document_id}` – fetch a document
- `PUT /documents/{document_id}` – update a document
- `DELETE /documents/{document_id}` – delete a document

## PostgreSQL persistence behavior

The repository no longer relies on a Python dictionary as the primary persistence mechanism. The repository pattern remains the same, but the underlying implementation now uses PostgreSQL SQL instead.

The effective SQL behavior is:

- create: `INSERT INTO documents ...`
- read all: `SELECT ... FROM documents`
- read by id: `SELECT ... FROM documents WHERE id = ...`
- update: `UPDATE documents SET ... WHERE id = ...`
- delete: `DELETE FROM documents WHERE id = ...`

The API behavior remains unchanged from the client perspective. Clients still interact with the same logical document model and receive the same shapes.

## Testing

A pytest suite under `tests/` verifies the API contract and PostgreSQL-backed behavior.

### Core API tests

`tests/test_api.py` covers:

- GET / → 200
- GET /health → 200 and `{"status": "healthy"}`
- POST /documents → 201 and created document returned
- Invalid POST /documents (missing fields) → 422 validation error
- GET /documents → 200 and list of documents returned
- GET /documents/{id} for an existing document → 200 and resource returned
- GET /documents/{id} for a missing document → 404 with descriptive message
- PUT /documents/{id} update → 200 and updated state returned
- DELETE /documents/{id} for an existing document → 204 and removal succeeds
- DELETE /documents/{id} for a missing document → 404 with descriptive message

### PostgreSQL integration tests

`tests/test_postgres_integration.py` verifies the PostgreSQL-backed implementation end to end:

- repository uses PostgreSQL when a valid `DATABASE_URL` is configured
- create then fetch returns the same document
- multiple creates then list returns all expected documents
- create then update then fetch shows updated values
- create then delete then fetch returns 404
- missing document fetch returns 404

The tests use a fixture to `TRUNCATE TABLE documents` between tests so one test does not leak data into another.

## Execution

Run the full suite:

```bash
./.venv/Scripts/python.exe -m pytest -q
```

Run the PostgreSQL integration subset:

```bash
./.venv/Scripts/python.exe -m pytest -q tests/test_postgres_integration.py
```

## Report files

- `docs/pytest_reports/report_1.md` – earlier API contract report
- `docs/pytest_reports/report_2.md` – PostgreSQL integration report
- `docs/pytest_reports/report_deliberate_failures.md` – deliberate database failure validation report

## Additional project documentation

The project includes focused engineering notes and verification artifacts covering the PostgreSQL implementation and interview-level understanding:

- `docs/notes/postgresql-deep-revision.md` – core PostgreSQL concepts and schema rationale
- `docs/notes/deliberate-database-failures.md` – duplicate key, missing field, invalid data, and not-found failure analysis
- `docs/notes/database-transactions-acid.md` – transaction flow and ACID guarantees
- `docs/notes/connection-lifecycle.md` – open, yield, rollback, close resource lifecycle
- `docs/notes/migration-understanding.md` – migration discipline and schema versioning
- `docs/notes/persistence-verification.md` – request tracing and persistence proof workflow
- `docs/actvity_tracker/day5.md` – Day 5 PostgreSQL implementation summary
- `docs/actvity_tracker/day6.md` – persistence verification and interview-critical validation steps

## Current architecture status

The project is now structured as:

FastAPI
↓
Service layer
↓
Repository layer
↓
Database connection boundary
↓
PostgreSQL

The persistence layer is no longer dictionary-based for the main path. The repository still preserves the same conceptual API contract while using SQL operations for create, list, get by id, update, and delete.

## Validation summary

The PostgreSQL-backed path is validated through:

- environment-based database configuration
- migration-driven schema setup
- dedicated connection lifecycle management
- repository CRUD SQL behavior
- API contract tests
- PostgreSQL integration tests
- deliberate failure tests for database-level validation and 404 behavior

This project currently reflects the actual engineering work that was completed and documented rather than a hypothetical future state.

## Notes

- The design remains intentionally conservative and avoids over-engineering beyond the current project need.
- Database-level constraints such as `CHECK` and separate test database provisioning are not expanded beyond the current scope, but the project has the migration, connection, and repository structure needed for PostgreSQL-backed persistence.
- Warnings observed during testing are related to third-party deprecations in the FastAPI/Starlette stack and do not block the application behavior.
- The `.env` file remains local-only and is intentionally not committed to source control.
