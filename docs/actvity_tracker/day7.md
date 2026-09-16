# Day 7 — Final Implementation Summary and Software Architecture

Date: 2026-09-16

## 1. Overview

This project implements a layered document-management service built with FastAPI and PostgreSQL. The main goal was to keep the API contract stable while moving the persistence layer from a simple in-memory Python dictionary to a real database-backed repository.

The final implementation includes:

- FastAPI application with document routes
- Service-layer business validation and orchestration
- Repository pattern with PostgreSQL-backed persistence
- Database connection boundary and migration runner
- Centralized exception handling and HTTP mapping
- End-to-end tests for API and database-backed behavior
- Reliability-focused review of transaction, SQL safety, and failure handling

## 2. Changes implemented across the project

### 2.1 API foundational layer

The application was built as a clean HTTP entry point around the FastAPI framework:

- `src/main.py` creates the FastAPI app
- root and health endpoints are exposed at `/` and `/health`
- the document router is included into the app
- centralized exception handlers map internal errors to proper HTTP responses

The API contract remains stable for clients:

- `GET /`
- `GET /health`
- `POST /documents`
- `GET /documents`
- `GET /documents/{document_id}`
- `PUT /documents/{document_id}`
- `DELETE /documents/{document_id}`

### 2.2 Domain model and request/response contracts

The app uses a small but explicit domain model:

- `src/data_classes/document_class.py` defines the `Document` data class
- `src/models/pydantic_model.py` defines request and response schemas
- supported document types are validated in the service layer: `requirement`, `design`, `test`

The request/response flow is intentionally simple and predictable:

- create request includes `name`, `document_type`, and `version`
- response includes `id`, `name`, `document_type`, `version`, and `status`

### 2.3 Service-layer business logic

The service layer handles validation and orchestration rather than HTTP concerns:

- `src/services/document_service.py`
- validates required fields
- validates allowed document types
- checks duplicate names according to business rules
- generates or preserves document IDs
- invokes repository CRUD operations
- raises domain exceptions instead of returning raw HTTP codes

This keeps business logic separate from FastAPI and makes it testable without web-layer coupling.

### 2.4 Repository abstraction and persistence implementation

The repository layer was designed to keep the same logical interface while swapping the storage backend:

- `src/repositories/document_repository.py`
- repository methods implement create, list, get, update, and delete
- the repository reads and writes domain objects in a consistent format
- a Postgres-backed implementation was added and protected by a database configuration check
- when a valid `DATABASE_URL` is present, the repository uses PostgreSQL
- when configuration is absent or initialization fails, it falls back to an in-memory dictionary for local development safety

This allows the service and routes to remain consistent while the storage mechanism can evolve.

### 2.5 Database connection and configuration boundary

The project introduced a dedicated persistence boundary to isolate database concerns:

- `src/db/connection.py`
- loads environment variables from `.env`
- resolves `DATABASE_URL` or `TEST_DATABASE_URL`
- validates placeholder values like `<user>`, `<password>`, `<host>`, and `<database>`
- creates a PostgreSQL connection using `psycopg`
- ensures rollback on failures
- closes the connection in `finally`
- wraps low-level DB failures into `DatabaseUnavailableError`

This ensures the repository does not directly own connection lifecycle decisions.

### 2.6 Database initialization and schema migration

The project supports reproducible database setup:

- `src/database.py` is the initialization and migration runner
- `migrations/001_create_documents_table.sql` creates the `documents` table
- a `schema_migrations` mechanism tracks which SQL migrations have already run
- database setup can be repeated safely across environments

Schema created:

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

### 2.7 Exception handling and API reliability

The project keeps centralized HTTP error translation in `src/main.py`:

- `DocumentNotFoundError` -> HTTP 404
- `InvalidDocumentError` -> HTTP 400
- `DatabaseUnavailableError` -> HTTP 503
- `RequestValidationError` -> HTTP 422
- generic exceptions -> HTTP 500

This separation is intentional:

- routes do not translate business exceptions themselves
- service layer raises domain exceptions
- API layer maps them consistently at the boundary

### 2.8 PostgreSQL persistence and validation

The project was validated against a real PostgreSQL-backed path:

- the repository executes SQL such as `INSERT`, `SELECT`, `UPDATE`, and `DELETE`
- queries use parameterized statements to prevent SQL injection
- database operations are exercised through integration tests
- tests confirm documents remain available after restart, which is a real persistence proof rather than just an in-memory success path

### 2.9 Test coverage and validation

Tests under `tests/` cover API contract and persistence behavior:

- `tests/test_api.py` verifies API routes, validation, and exception mapping
- `tests/test_postgres_integration.py` verifies PostgreSQL repository behavior and persistence

Examples covered:

- root and health endpoints
- create document returns `201`
- missing or invalid payloads return `422`/`400`
- missing document returns `404`
- update and delete flows work correctly
- persisted document remains readable from PostgreSQL

## 3. Software architecture

The overall architecture follows a layered design:

```text
HTTP Client
    ↓
FastAPI Router
    ↓
DocumentService
    ↓
DocumentRepository
    ↓
Database Connection Boundary
    ↓
PostgreSQL
```

### 3.1 Layer responsibilities

1. Presentation/API layer
   - `src/api/document_routes.py`
   - handles request parsing and HTTP flow
   - delegates business decisions to the service layer

2. Service layer
   - `src/services/document_service.py`
   - enforces business rules and validation
   - owns document lifecycle logic
   - raises domain exceptions

3. Repository layer
   - `src/repositories/document_repository.py`
   - abstracts persistence behind a repository API
   - supports both PostgreSQL and in-memory fallback based on environment/configuration

4. Database boundary
   - `src/db/connection.py`
   - manages environment-based DB config
   - opens database connections
   - handles rollback/commit lifecycle
   - converts low-level DB errors into application-level exceptions

5. Database
   - PostgreSQL stores the real document data
   - schema is managed via migration files under `migrations/`

### 3.2 Runtime flow for create document

```text
Client -> POST /documents
    -> FastAPI request validation
    -> document_routes.create_document
    -> DocumentService.create_document
    -> validation checks + document creation
    -> DocumentRepository.create_document
    -> database_connection()
    -> PostgreSQL INSERT
    -> commit/close connection
    -> response returned as DocumentResponse
```

### 3.3 Error flow

```text
Service or repository raises domain exception
    -> FastAPI exception handler in src/main.py
    -> JSONResponse with appropriate status code and detail
```

Examples:

- invalid business input -> `400 Bad Request`
- missing resource -> `404 Not Found`
- DB connectivity issue -> `503 Service Unavailable`
- malformed request schema -> `422 Unprocessable Entity`

## 4. Key files and responsibilities

- `src/main.py` — app setup, global exception handlers, root and health endpoints
- `src/api/document_routes.py` — HTTP endpoints for CRUD operations
- `src/services/document_service.py` — validation and business rules
- `src/repositories/document_repository.py` — persistence abstraction and repository logic
- `src/db/connection.py` — DB config and connection lifecycle
- `src/database.py` — migration runner and initialization
- `src/exceptions/document_exceptions.py` — domain exceptions
- `src/models/pydantic_model.py` — Pydantic schemas
- `src/data_classes/document_class.py` — Document domain model
- `migrations/001_create_documents_table.sql` — database schema migration
- `tests/test_api.py` — API verification
- `tests/test_postgres_integration.py` — persistence verification

## 5. Reliability review findings

The final codebase includes a Day 7 reliability review that identifies the strengths and weaknesses of the current architecture.

Major strengths:

- parameterized SQL for safety
- centralized connection lifecycle management
- explicit exception separation between service and API layers
- database-backed persistence beyond ephemeral in-memory state

Areas addressed or highlighted for improvement:

- repository fallback logic should be narrowly scoped and explicit
- transaction ownership should be centralized consistently
- runtime database failures should be handled deliberately and documented
- fallback-to-memory behavior should not silently mask serious persistence issues in production

## 6. Final status

The implemented system is a functional, layered application that successfully demonstrates:

- API-first document management
- domain-driven service logic
- PostgreSQL-backed repository persistence
- stable contract between routers and client
- centralized error handling
- reproducible database setup through migrations
- end-to-end validation through tests

This is the final software architecture and implementation state captured for Day 7.
