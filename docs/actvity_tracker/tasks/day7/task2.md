# Day 7 / Task 2 — Inspect the architecture and explain the request lifecycle

## Task

Read and verify the implementation in the current repository before making any assumptions about the architecture.

Required files to inspect:
- src/main.py
- src/api/document_routes.py
- src/services/document_service.py
- src/repositories/document_repository.py
- src/db/connection.py
- src/database.py
- src/models/pydantic_model.py
- src/data_classes/document_class.py
- src/exceptions/document_exceptions.py
- tests/test_api.py
- tests/test_postgres_integration.py

The question to answer is:

"Can I explain the complete request lifecycle without looking at the code?"

Lifecycle to explain:

HTTP request
¯
FastAPI route
¯
Pydantic validation
¯
DocumentService
¯
DocumentRepository
¯
database_connection()
¯
PostgreSQL
¯
result
¯
domain/service response
¯
HTTP response

If any one arrow is unclear, the correct action is to inspect that specific layer before modifying behavior.

## Solution

Yes — after reading the actual implementation in the repository, the full lifecycle can be explained precisely from code and it matches the layered architecture described in the project.

### 1) HTTP request enters the FastAPI app

The application entry point is `src/main.py`.

- `app = FastAPI(title="AI Engineering Intelligence Platform")` creates the application object.
- `initialize_database()` runs immediately at import time.
- The app exposes root endpoints for `/` and `/health`.
- `app.include_router(document_router)` attaches the document API routes.

This means the request first reaches the ASGI app as a standard FastAPI request. The application then routes it based on path and HTTP method.

### 2) FastAPI route receives the request

The request handling layer lives in `src/api/document_routes.py`.

The router defines the document API endpoints:
- `POST /documents`
- `GET /documents`
- `GET /documents/{document_id}`
- `PUT /documents/{document_id}`
- `DELETE /documents/{document_id}`

A single shared service instance is created at module load time:

- `repository = DocumentRepository()`
- `service = DocumentService(repository)`

Then the dependency function:

- `get_document_service() -> DocumentService`

returns that service object for each request.

This is the important architectural point: the route layer is thin and delegates all domain logic to the service layer.

### 3) Pydantic validation occurs before the route body is processed

The request schemas are defined in `src/models/pydantic_model.py`:

- `DocumentCreate` requires:
  - `name: str`
  - `document_type: str`
  - `version: str`
- `DocumentResponse` contains:
  - `id`, `name`, `document_type`, `version`, `status`

For `POST /documents`, the route signature is:

```python
async def create_document(document: DocumentCreate, service: DocumentService = Depends(get_document_service))
```

FastAPI automatically validates incoming JSON against `DocumentCreate` before invoking the function. If the payload is missing required fields, the app raises a `RequestValidationError`, which is handled centrally in `src/main.py`.

The response model (`response_model=DocumentResponse`) also ensures the outgoing JSON shape is consistent and that values returned from the service are serialized correctly.

### 4) Route delegates to `DocumentService`

The service class is in `src/services/document_service.py`.

The methods are:
- `create_document(document_data)`
- `get_document(document_id)`
- `update_document(document_id, updated_data)`
- `delete_document(document_id)`
- `list_documents()`

The service is the business logic layer. It does not talk directly to the database; it talks to a repository interface object.

For example, in `create_document()`:

- it validates that `name` is present
- it validates `document_type` against allowed values: `requirement`, `design`, `test`
- it checks for duplicate names across existing documents
- it creates a deterministic ID if one is not supplied
- it builds a `Document` object from `src/data_classes/document_class.py`
- it calls `self.document_repository.create_document(document)`

If any validation fails, the service raises custom exceptions:
- `InvalidDocumentError` for invalid or duplicate data
- `DocumentNotFoundError` when an ID does not exist

These exception classes are defined in `src/exceptions/document_exceptions.py`:

- `DocumentNotFoundError(document_id)` sets `message = "Document with ID '{id}' not found."`
- `InvalidDocumentError(message)` stores the validation issue

### 5) `DocumentRepository` performs persistence

The repository is in `src/repositories/document_repository.py`.

It has a dual behavior:

- if a valid `DATABASE_URL` is configured, it uses PostgreSQL
- otherwise it falls back to an in-memory dictionary

The constructor does this:

```python
self.documents = {}
self.use_postgres = False
if get_database_url():
    try:
        initialize_database()
        self.use_postgres = True
    except Exception:
        self.use_postgres = False
```

That means the repository is intentionally environment-aware. In the real repository state, PostgreSQL is enabled when the database URL is configured and valid.

The repository implements:
- `create_document(document)`
- `get_document(document_id)`
- `delete_document(document_id)`
- `list_documents()`
- `update_document(document_id, updated_data)`

For PostgreSQL-backed operations, it uses SQL like:

- `INSERT INTO documents ...`
- `SELECT id, name, document_type, version, status FROM documents WHERE id = %s`
- `UPDATE documents SET ... WHERE id = %s RETURNING ...`
- `DELETE FROM documents WHERE id = %s RETURNING id`

The conversion helper:

```python
@staticmethod
def _row_to_document(row):
```

maps PostgreSQL rows back into a domain `Document` instance.

### 6) `database_connection()` manages the DB boundary

The connection lifecycle is defined in `src/db/connection.py`.

Key behavior:

```python
def get_database_url() -> str | None:
    database_url = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        return None
```

It ignores placeholder values such as:
- `<user>`
- `<password>`
- `<host>`
- `<database>`

The actual context manager is:

```python
@contextmanager
def database_connection() -> Iterator[object]:
    connection = psycopg.connect(get_database_config(), autocommit=False)
    try:
        yield connection
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
```

This is the transaction boundary. It ensures:
- a connection is opened for the repository operation
- exceptions trigger rollback
- the connection is closed in `finally`

This is the exact database connection boundary that the repository relies on for PostgreSQL writes and reads.

### 7) PostgreSQL schema and migration initialization

The database bootstrap lives in `src/database.py`.

The migration runner does this:

- uses `database_connection()`
- finds SQL files in `migrations/`
- creates a `schema_migrations` table if it does not already exist
- applies only new migration files
- records applied names to prevent re-execution

The migration is for the `documents` table.

This means the repository calls the database boundary, which relies on a valid `DATABASE_URL`, and the migration runner ensures the table exists with the expected columns.

### 8) Result comes back from PostgreSQL

Once the SQL statement succeeds, PostgreSQL returns rows or confirmation of the write. The repository converts these results to `Document` objects, or returns `True/False` for delete operations.

This is the key bridge between the database and the application domain:

- database row -> repository row conversion -> `Document` instance
- then the service can continue working with the object model

This is why the service and route layers do not operate on raw SQL objects — they work with domain model objects and Pydantic responses.

### 9) Domain/service response is returned

The service returns a `Document` object or an exception. The route then resolves it into a `DocumentResponse` object using the schema in `src/models/pydantic_model.py`.

Examples in `src/api/document_routes.py`:

```python
return DocumentResponse(
    id=document.id,
    name=document.name,
    document_type=document.document_type,
    version=document.version,
    status=document.status,
)
```

This is the transformation from internal domain model to HTTP-safe response schema.

### 10) HTTP response is sent to the client

The final response is handled by FastAPI automatically.

- If a route returns a Pydantic model, FastAPI serializes it to JSON.
- If a route returns `None` with `204 No Content`, it sends an empty response.
- If a domain exception is raised, the global exception handlers in `src/main.py` map it to:
  - `DocumentNotFoundError` -> 404
  - `InvalidDocumentError` -> 400
  - `RequestValidationError` -> 422
  - generic `Exception` -> 500

This is the real lifecycle chain that the repository implements.

## The final answer

Yes: the complete request lifecycle is:

HTTP request
¯
FastAPI route
¯
Pydantic validation
¯
DocumentService
¯
DocumentRepository
¯
database_connection()
¯
PostgreSQL
¯
result
¯
domain/service response
¯
HTTP response

And this is not just conceptual — it is visible in the actual repository structure and code.

## Evidence from tests

The test files confirm the architecture behaves as designed:

- `tests/test_api.py` validates endpoint-level behavior and exception mapping.
- `tests/test_postgres_integration.py` verifies the repository actually uses PostgreSQL-backed behavior when configured.

Examples include:
- successful create/get/list/update/delete flows
- 404 for missing records
- 422 for validation errors
- database-backed roundtrip operations using `DocumentRepository`

This confirms the route → service → repository → database_connection → PostgreSQL → response chain is not merely theoretical, but executed and validated in the project.
