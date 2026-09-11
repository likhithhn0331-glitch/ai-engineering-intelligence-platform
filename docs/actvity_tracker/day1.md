# Day 1 — Detailed Implementation, Theory, and Architecture

Date: 2026-09-11T23:00:00+05:30

## 1. Purpose of this document
This report documents the current software (SW) state, architectural decisions, theoretical background (especially around API error handling), and file-level explanations of the code implemented so far. It also documents testing approach and how to run the system and tests.

## 2. Current software (SW) environment
- Application: AI Engineering Intelligence Platform
- Python: 3.14.4
- FastAPI: 0.141.1
- Uvicorn: 0.52.4
- Pytest: 9.1.1
- Location: repository root (C:\likhi\Interview\ai-engineering-intelligence-platform)

## 3. High-level architecture and design
The application uses a simple layered architecture for clarity and separation of concerns:
- HTTP Client (caller)
- FastAPI Router (API layer)
- Service Layer (business logic & validation)
- Repository Layer (persistence abstraction)
- In-memory Store (current backing store for prototyping)

Rationale:
- Separation of responsibilities keeps HTTP concerns (status codes & shapes) separate from domain logic (validation, rules) and persistence (CRUD). This makes testing and future replacement of the storage or API layer straightforward.

Flow (example POST /documents):
1. Client sends JSON to POST /documents
2. Pydantic schema (DocumentCreate) validates request shape
3. Router hands validated data to DocumentService
4. DocumentService performs domain validation and constructs Document domain object
5. Repository persists the Document in-memory and returns it
6. Router builds DocumentResponse and returns HTTP 201

## 4. Theory: Exceptions → API error handling mapping
Key idea: Python exceptions are internal signals; they must be translated to precise HTTP responses at the API boundary.
- DocumentNotFoundError → HTTP 404 Not Found. Meaning: requested resource does not exist.
- InvalidDocumentError → HTTP 400 Bad Request. Meaning: client supplied invalid data according to business rules.
- RequestValidationError (Pydantic/FastAPI) → HTTP 422 Unprocessable Entity. Meaning: request JSON shape or types are invalid.
- Unexpected Exception → HTTP 500 Internal Server Error (log details, do not leak internals to clients).

Benefits of centralized handlers:
- Single place to control error payload shape and status codes
- Avoids repeating try/except blocks in every route
- Ensures consistent logging and non-leaking of internal errors

## 5. File-by-file implementation explanations

### src/main.py
- Creates FastAPI app instance and registers routers.
- Adds centralized exception handlers using @app.exception_handler for:
  - DocumentNotFoundError (returns JSON 404 with {"detail": message})
  - InvalidDocumentError (returns JSON 400 with {"detail": message})
  - RequestValidationError (returns JSON 422 with validation details)
  - Generic Exception (returns JSON 500 with {"detail": "Internal server error"} and logs stack trace)

Why: mapping domain exceptions to HTTP codes here keeps controllers thin and consistent.

### src/exceptions/document_exceptions.py
- DocumentNotFoundError(Exception): stores document_id and a message property
- InvalidDocumentError(Exception): stores message property

These are domain exceptions used by the service layer to signal specific error conditions.

### src/models/pydantic_model.py
- DocumentCreate(BaseModel): request schema for creating documents (name, document_type, version)
- DocumentResponse(BaseModel): response schema (id, name, document_type, version, status)

Pydantic ensures type validation and helpful error messages prior to entering business logic.

### src/data_classes/document_class.py
- Document domain data class (simple typed attributes: id, name, document_type, version, status)

Used by the service and repository as the domain representation.

### src/repositories/document_repository.py
- In-memory repository implemented as a dict mapping id → Document
- CRUD operations: create_document, get_document, delete_document, list_documents, update_document

Notes:
- Simple and synchronous for now; easy to replace with a DB-backed implementation.

### src/services/document_service.py
- Business rules live here:
  - Valid document types: ["requirement","design","test"]
  - `create_document` checks required fields, uniqueness by name, assigns id if missing, constructs Document, and persists via repository. Raises InvalidDocumentError for validation failures.
  - `get_document` fetches and raises DocumentNotFoundError if absent.
  - `update_document` and `delete_document` call `get_document` to ensure existence and raise DocumentNotFoundError when needed.

Why in service layer: Business rules can be tested independently of HTTP; raising domain exceptions keeps domain semantics explicit.

### src/api/document_routes.py
- Defines FastAPI APIRouter and route functions for POST, GET, PUT, DELETE, and listing.
- Returns Pydantic DocumentResponse objects.
- Per-route try/except blocks were intentionally removed so domain exceptions bubble to global handlers in main.py (clear boundary between API and business logic).

### tests/test_api.py
- Uses fastapi.testclient.TestClient to exercise the running app in-process.
- Fixtures:
  - reset_repository (autouse) re-initializes document_routes.repository and service to ensure test isolation.
  - client returns TestClient(app).
- Tests:
  - test_root_returns_200: GET / -> 200
  - test_health_returns_healthy: GET /health -> 200 and status=="healthy"
  - test_post_documents_success: POST /documents -> 201 and checks returned fields
  - test_invalid_request_validation_error: POST missing required field -> 422
  - test_missing_document_returns_404: GET non-existent -> 404 with expected message

Why: These tests demonstrate the API contract and exercise the exception handling in an end-to-end manner without the need for external servers or databases.

### docs/pytest_reports/report_1.md
- Captures pytest run output, environment versions, and notes about warnings observed.

### README.md updates
- Documents the new centralized exception handling approach and tests location and instructions.

## 6. How to run locally
- Create and activate virtualenv, install requirements (fastapi, uvicorn, pytest)
  - python -m venv .venv
  - .\.venv\Scripts\activate
  - pip install -r requirements.txt
- Run tests:
  - python -m pytest -q
- Run server for manual testing:
  - uvicorn src.main:app --reload --port 8000
- Example curl:
  - curl -X POST "http://localhost:8000/documents" -H "Content-Type: application/json" -d '{"name":"d1","document_type":"requirement","version":"1.0"}'

## 7. Testing philosophy and guarantees
- Unit vs integration: current tests are lightweight integration tests that exercise the FastAPI app with an in-memory repository. That approach validates the API contract, schema validation, exception mapping, and basic persistence logic.
- Isolation: tests reset repository state via an autouse fixture to avoid inter-test dependencies.
- Next steps: add tests for update/delete, concurrency tests, and repository persistence replacement tests.

## 8. Potential improvements (next iterations)
- Replace in-memory repository with a pluggable persistent backend (Postgres, SQLite) and add migration scripts.
- Add CI pipeline (GitHub Actions) to run pytest and upload docs/pytest_reports as artifacts.
- Improve logging configuration and structured error payloads (include error codes and trace IDs).
- Harden validation and add contract tests (OpenAPI-based) and property-based tests for the service layer.

## 9. Contact
For clarifications about design choices or to propose changes, open an issue or pull request in this repository.

'
