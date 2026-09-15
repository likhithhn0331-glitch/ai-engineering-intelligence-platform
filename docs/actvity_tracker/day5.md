# Day 5 — PostgreSQL Integration for Document Persistence

## Goal

The goal of Day 5 was to replace the in-memory persistence layer with PostgreSQL while preserving the existing architecture and API contract. The service and route layers were kept intact, and the repository was changed so that it reads and writes through PostgreSQL instead of a Python dictionary.

## Architectural requirement

The architecture had to remain layered:

FastAPI
↓
Service
↓
Repository
↓
Database connection
↓
PostgreSQL

The client-facing behavior was kept stable. The API still exposed the same logical document resource and the same status codes, even though the storage backing store changed.

## Core decisions

### 1. Preserve the existing API contract

The API still exposes the same document model:

- `id`
- `name`
- `document_type`
- `version`
- `status`

This means the application continues returning the same JSON shape to clients regardless of whether the real persistence mechanism is a dict or PostgreSQL.

### 2. Preserve centralized error handling

The project keeps the centralized FastAPI exception architecture in `src/main.py`.

- `DocumentNotFoundError` → HTTP 404
- `InvalidDocumentError` → HTTP 400
- `RequestValidationError` → HTTP 422
- generic exception → HTTP 500

Routes were not refactored back to per-route exception translation. This separation keeps business logic and API mapping distinct.

### 3. Keep the repository contract

The conceptual `DocumentRepository` interface remained the same, but its implementation changed from dictionary-backed storage to PostgreSQL-backed SQL operations.

## Implementation details

### Database schema

The project created a minimal, project-appropriate schema based on the current API:

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

This matches the current API’s fields without adding speculative columns.

### Reproducible schema creation

For reproducibility, the system uses migration files under `migrations/`.

The migration runner in `src/database.py`:

- reads `DATABASE_URL`
- creates a `schema_migrations` tracking table
- applies SQL files in order
- records each applied migration name

This avoids a one-off manual table creation process.

### Database configuration

The project uses environment-based configuration instead of hard-coded credentials.

- `.env` contains local secrets and is gitignored
- `.env.example` contains placeholders
- `DATABASE_URL` is loaded from the environment

Example:

```env
DATABASE_URL=postgresql://postgres:MyStrongPass123@localhost:5432/ai_engineering_platform
```

### Connection boundary

A dedicated connection boundary was added in `src/db/connection.py`.

This layer provides:

- configuration lookup
- database URL validation
- connection creation
- rollback on repository failure
- connection closure in a `finally` block

This is the boundary between application logic and PostgreSQL.

### Repository implementation

The repository was changed to execute PostgreSQL SQL operations for the core CRUD flow:

- create: `INSERT INTO documents ...`
- list: `SELECT ... FROM documents`
- get by id: `SELECT ... FROM documents WHERE id = ...`
- update: `UPDATE documents SET ... WHERE id = ...`
- delete: `DELETE FROM documents WHERE id = ...`

The repository still returns domain objects shaped as the original `Document` class, so the rest of the application does not need to know whether storage is in-memory or PostgreSQL.

## Service and API behavior

The `DocumentService` behavior remains the same from the client perspective:

- validate request fields
- validate document type
- reject duplicate names in the current business rule
- generate document IDs in the same style
- call repository methods

The API still exposes the same routes:

- `POST /documents`
- `GET /documents`
- `GET /documents/{document_id}`
- `PUT /documents/{document_id}`
- `DELETE /documents/{document_id}`

The only change is how persistence is implemented underneath.

## Testing and validation

The project added PostgreSQL integration tests in `tests/test_postgres_integration.py`.

These tests cover:

1. repository uses PostgreSQL when configured
2. create then fetch returns the same document
3. create multiple then fetch all documents
4. create then update then fetch shows updated state
5. create then delete then fetch returns 404
6. missing document fetch returns 404

A fixture resets the table between tests using `TRUNCATE TABLE documents` so test isolation is maintained.

## What was validated

The application was validated with pytest:

```bash
./.venv/Scripts/python.exe -m pytest -q
```

Result:

- 15 passed

This means:

- the original API tests still pass
- the PostgreSQL integration tests also pass
- the implementation preserved the architecture and the original external behavior

## Key takeaway

Day 5 was not just “connect PostgreSQL.” The real engineering work was to keep the software layers clean while replacing only the storage implementation, preserve the centralized error architecture, maintain the API contract, and validate behavior through integration tests against a real database.
