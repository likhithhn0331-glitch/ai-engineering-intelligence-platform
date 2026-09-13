# AI Engineering Intelligence Platform

AI Engineering Change and Test Intelligence Platform.

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
In-Memory Store

This flow is implemented for the document endpoints:

POST /documents
↓
API Layer
↓
Service Layer
↓
Repository Layer
↓
Storage

## Project Structure

- `src/main.py` – FastAPI app entry point, global exception handlers, and root/health routes
- `src/api/document_routes.py` – HTTP endpoints for document operations (exceptions now bubble to global handlers)
- `src/services/document_service.py` – Business logic, validation, and orchestration
- `src/repositories/document_repository.py` – In-memory persistence layer
- `src/models/pydantic_model.py` – Request/response schemas
- `src/data_classes/document_class.py` – Document domain model
- `src/exceptions/document_exceptions.py` – Custom exceptions

## Exception handling

To ensure Python exceptions map to meaningful HTTP responses, centralized FastAPI exception handlers were added in `src/main.py`:

- `DocumentNotFoundError` → HTTP 404 with JSON {"detail": "..."}
- `InvalidDocumentError` → HTTP 400 with JSON {"detail": "..."}
- `fastapi.exceptions.RequestValidationError` → HTTP 422 with validation details
- Generic `Exception` → HTTP 500 with JSON {"detail": "Internal server error"} (and server-side logging)

Per-route try/except blocks that converted application exceptions into HTTPExceptions were removed from `src/api/document_routes.py` so service-layer exceptions can bubble up to the global handlers. This preserves clear separation between application errors and API error mapping.

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

## Testing

A pytest suite under `tests/` verifies the API contract, layered behavior, and exception handling. The Day 2 suite covers:

- GET / → 200
- GET /health → 200 and `{"status": "healthy"}`
- POST /documents → 201 and created document returned
- Invalid POST /documents (missing fields) → 422 validation error
- GET /documents → 200 and list of documents returned
- GET /documents/{id} for an existing document → 200 and resource returned
- GET /documents/{id} for a missing document → 404 with descriptive message
- DELETE /documents/{id} for an existing document → 204 and removal succeeds
- DELETE /documents/{id} for a missing document → 404 with descriptive message

Run tests:

```bash
python -m pytest -q
```

A test run report is saved at `docs/pytest_reports/report_1.md` which contains environment details, pytest output, and notes.

## Architecture notes for Day 2

The Day 2 work confirms the architectural boundary:

- HTTP routes handle request/response and status codes
- Pydantic models define the API contract
- `DocumentService` owns document business behavior and validation
- `DocumentRepository` owns in-memory storage operations
- Global exception handlers translate domain failures to HTTP responses

This keeps the API layer thin and ensures retrieval, listing, and deletion all pass through the service layer instead of bypassing it.

## Notes

- The repository layer currently uses an in-memory dictionary for persistence and is reset during tests via a fixture.
- Warnings observed during testing are related to third-party deprecations (starlette/testclient and HTTP_422 naming). Consider upgrading dependencies in the future.

