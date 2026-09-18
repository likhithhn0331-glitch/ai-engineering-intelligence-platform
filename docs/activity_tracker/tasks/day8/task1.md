# Day 8 / Task 1 — Move from PostgreSQL CRUD to PostgreSQL querying

## Task

Day 5 established PostgreSQL-backed CRUD while preserving the API contract:

```text
FastAPI -> Service -> Repository -> database_connection() -> PostgreSQL
```

Day 8 extends the read path. The goal is not to add random SQL to the route layer. The goal is to express query intent at the API boundary, pass it through the service, and let the repository translate it into safe PostgreSQL queries.

The existing `GET /documents` response remains a JSON list of the same `DocumentResponse` objects. Querying changes which rows are returned and in what order; it does not change the response shape.

## What changed

`GET /documents` now supports:

| Parameter | Meaning | Example |
|---|---|---|
| `document_type` | Exact document-type filter | `?document_type=requirement` |
| `status` | Exact status filter | `?status=created` |
| `name_contains` | Case-insensitive substring search | `?name_contains=api` |
| `limit` | Maximum number of rows, from 1 to 100 | `?limit=20` |
| `offset` | Number of matching rows to skip | `?offset=20` |
| `sort_by` | Allow-listed sort column | `?sort_by=name` |
| `sort_order` | `asc` or `desc` | `?sort_order=desc` |

Examples:

```text
GET /documents?document_type=requirement
GET /documents?name_contains=api&sort_by=name&sort_order=asc
GET /documents?status=created&limit=20&offset=40
```

The default behavior is intentionally compatible with the original endpoint:

- no filters
- insertion order (`created_at ASC, id ASC`) in PostgreSQL
- no limit
- offset zero

## Query lifecycle

### 1. FastAPI parses and validates query parameters

The route in `src/api/document_routes.py` declares the query contract. FastAPI rejects invalid values before the service is called:

- `limit` must be between 1 and 100
- `offset` must be zero or greater
- `sort_by` must be one of the known document fields
- `sort_order` must be `asc` or `desc`
- `name_contains` cannot be an empty string

This validation prevents malformed requests from reaching the database and provides a predictable HTTP 422 response.

### 2. The service forwards query intent

`DocumentService.list_documents()` remains a business-layer method. It does not construct SQL. It forwards the validated query values to the repository, preserving the same dependency direction used by CRUD.

This keeps the route independent of PostgreSQL and keeps SQL knowledge out of the service.

### 3. The repository builds a parameterized query

`DocumentRepository.list_documents()` handles the PostgreSQL read:

```sql
SELECT id, name, document_type, version, status
FROM documents
WHERE document_type = %s
  AND name ILIKE %s
ORDER BY name DESC, id ASC
LIMIT %s OFFSET %s
```

The actual `WHERE` clauses are assembled only for supplied filters. Values are always passed separately to `cursor.execute(query, values)`. This means user input is not interpolated into SQL values and remains protected by psycopg parameter binding.

### 4. Dynamic sorting is allow-listed

SQL parameters cannot safely represent identifiers such as column names. Therefore, `sort_by` is never inserted directly from the request. The repository maps approved API names to approved SQL identifiers:

```python
{
    "id": "id",
    "name": "name",
    "document_type": "document_type",
    "version": "version",
    "status": "status",
    "created_at": "created_at",
}
```

The sort direction is also restricted to `ASC` or `DESC`. The secondary `id ASC` ordering makes results deterministic when two rows have the same primary sort value.

### 5. PostgreSQL performs filtering and pagination

Filtering, sorting, and pagination occur in PostgreSQL rather than after loading every row into Python. This matters as the table grows:

- `WHERE` reduces the result set
- `ORDER BY` gives a defined result order
- `LIMIT` caps the response size
- `OFFSET` supports simple page traversal

The repository still maps returned rows into domain `Document` objects, so the service and response layers do not depend on raw database tuples.

## Query design decisions

### Why filtering belongs in SQL

Filtering in Python would require reading all rows first. SQL filtering reduces network transfer and application memory use, and lets PostgreSQL use indexes when suitable indexes are added later.

### Why pagination is bounded

An unbounded collection endpoint can return an unnecessarily large response. The API permits a maximum page size of 100. The limit is optional to preserve the original behavior, but clients that page through data should provide it.

### Why sorting needs a stable tie-breaker

Sorting only by `name` or `created_at` can produce unstable page boundaries when values are equal. Adding `id ASC` as a secondary order gives repeatable results for the same dataset.

### Why `ILIKE` is used for name search

`name_contains` is intended as a simple case-insensitive search. PostgreSQL `ILIKE` expresses that behavior directly:

```sql
name ILIKE '%api%'
```

The search value is still passed as a bound parameter. The repository, not the client, constructs the `%` pattern.

## Repository boundary and fallback behavior

The repository retains the existing local in-memory fallback when PostgreSQL is not configured. The fallback applies the same filters, sort options, offset, and limit in Python. This keeps local API behavior aligned with the PostgreSQL path, while the configured application path executes the real SQL query.

The fallback is not a replacement for PostgreSQL verification. The PostgreSQL integration tests are the evidence that the production persistence path works.

## Tests added

The query behavior is covered at two levels:

### API-level query test

`tests/test_api.py` verifies that query parameters are accepted through `GET /documents`, filters are applied, sorting is honored, and `limit` bounds the response.

### PostgreSQL integration query test

`tests/test_postgres_integration.py` inserts multiple rows and verifies the live database path combines:

- exact `document_type` filtering
- case-insensitive `name_contains` filtering
- descending name ordering
- `limit`
- `offset`

The integration fixture truncates `documents` before and after each test, so query assertions do not depend on data left by another test.

## What Day 8 proves

Day 5 proved that the repository could persist documents through PostgreSQL. Day 8 proves that the repository can express useful read behavior without breaking the layered architecture:

```text
HTTP query parameters
        ↓
FastAPI validation
        ↓
DocumentService
        ↓
DocumentRepository
        ↓
Parameterized PostgreSQL SELECT
        ↓
Document domain objects
        ↓
Existing DocumentResponse list
```

The important transition is from “the database can store and retrieve a row” to “the database can answer a constrained business query efficiently and safely.”

## Validation command

Run the complete suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Run only PostgreSQL-backed tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_postgres_integration.py
```

The PostgreSQL-specific command requires a valid `DATABASE_URL`. A passing integration test confirms that the query is executed against PostgreSQL rather than only against the in-memory fallback.
