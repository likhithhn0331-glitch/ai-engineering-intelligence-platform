# Task 1 — Detailed Architecture (Implementation Complete)

Status: Implemented and validated.

```text
HTTP Client
    |
    v
FastAPI Application (src/main.py)
    |  - registers routers
    |  - exposes / and /health
    |  - centralizes exception handling
    |  - maps domain errors to HTTP status codes
    v
API Layer (src/api/document_routes.py)
    |  - POST /documents
    |  - GET /documents
    |  - GET /documents/{document_id}
    |  - PUT /documents/{document_id}
    |  - DELETE /documents/{document_id}
    v
DocumentService (src/services/document_service.py)
    |  - validates business rules
    |  - checks document type, name uniqueness, existence
    |  - constructs the domain model
    v
DocumentRepository (src/repositories/document_repository.py)
    |  - CRUD operations
    |  - stores documents in a dict keyed by document id
    v
In-Memory Storage
    |
    +--------------------------------+
    | Dictionary-based persistence    |
    | Example: {id -> Document}       |
    +--------------------------------+
    ^
    |
    +---------------------------------------------+
    | Supporting layers:                          |
    | - src/models/pydantic_model.py              |
    | - src/data_classes/document_class.py       |
    | - src/exceptions/document_exceptions.py    |
    +---------------------------------------------+
```

Request flow:
1. Client sends an HTTP request to the FastAPI app.
2. FastAPI validates input using Pydantic models.
3. API router delegates work to DocumentService.
4. Service enforces domain rules and creates/updates a Document object.
5. Repository persists it in the in-memory dictionary.
6. Response is serialized back through the router and returned to the client.

Error flow:
- InvalidDocumentError -> 400 Bad Request
- DocumentNotFoundError -> 404 Not Found
- RequestValidationError -> 422 Unprocessable Entity
- Unexpected exception -> 500 Internal Server Error

Architecture summary:
- Presentation Layer: FastAPI + route handlers
- Application Layer: Service methods and validation rules
- Persistence Layer: Repository abstraction over in-memory storage
- Domain Layer: Document model, validation schemas, and custom exceptions

This reflects the implementation currently present in the project and is ready for future extension to a database-backed repository.
