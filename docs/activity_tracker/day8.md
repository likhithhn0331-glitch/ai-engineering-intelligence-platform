# Day 8 — PostgreSQL querying, filtering, ordering, and pagination

## Overview

Day 5 established PostgreSQL-backed CRUD while preserving the application contract:

```text
FastAPI
  ↓
DocumentService
  ↓
DocumentRepository
  ↓
database_connection()
  ↓
PostgreSQL
```

Day 8 extends the read path from simple collection retrieval to controlled PostgreSQL querying:

```text
GET /documents
  ↓
Query parameters
  ↓
FastAPI validation
  ↓
DocumentService
  ↓
DocumentRepository query construction
  ↓
PostgreSQL
  ↓
filtered, ordered, paginated documents
```

The API response remains a list of the existing `DocumentResponse` objects. Querying changes which records are returned and their order; it does not break the established API shape.

## Day 8 objectives completed

- Study SQL `WHERE` filtering.
- Add controlled document querying.
- Add pagination with `LIMIT` and `OFFSET`.
- Bound pagination input before database access.
- Add meaningful filtering using `document_type`.
- Add controlled ordering using an allow-list.
- Keep SQL and database interaction inside the repository.
- Add tests for pagination, validation, filtering, and ordering.
- Use deliberate test data that makes query behavior observable.
- Understand the transaction boundary for future multi-write operations.

## Query parameters

`GET /documents` supports the following query parameters:

| Parameter | Purpose | Constraints or behavior |
|---|---|---|
| `document_type` | Exact type filter | Example: `requirement` |
| `status` | Exact status filter | Example: `created` |
| `name_contains` | Case-insensitive name search | Must not be empty |
| `limit` | Maximum number of returned rows | Optional, minimum 1, maximum 100 |
| `offset` | Number of matching rows to skip | Optional, minimum 0 |
| `sort_by` | Result sort column | Allow-listed document fields |
| `sort_order` | Sort direction | `asc` or `desc` |

Examples:

```text
GET /documents
GET /documents?document_type=requirement
GET /documents?status=created
GET /documents?limit=20&offset=0
GET /documents?limit=20&offset=20
GET /documents?sort_by=created_at&sort_order=desc
GET /documents?document_type=requirement&status=created&limit=20
```

The public API uses `sort_by` and `sort_order` to make the meaning explicit. The conceptual form `sort=created_at&order=desc` represents the same feature, but is not the implemented parameter spelling.

## SQL filtering with `WHERE`

`WHERE` filters candidate rows before PostgreSQL returns the result:

```sql
SELECT *
FROM documents
WHERE document_type = 'requirement';
```

Filtering by status:

```sql
SELECT *
FROM documents
WHERE status = 'created';
```

Multiple conditions use `AND`:

```sql
SELECT *
FROM documents
WHERE document_type = 'requirement'
  AND status = 'created';
```

Every condition must be true for a row to remain in the result. The repository builds the equivalent parameterized conditions:

```sql
WHERE document_type = %s
  AND status = %s
```

The values are passed separately to psycopg. The application does not concatenate request values into SQL.

Filtering in PostgreSQL is preferable to loading every row and filtering in Python. It reduces database-to-application transfer, application memory use, and Python processing. It also leaves PostgreSQL free to use suitable indexes.

## Ordering with `ORDER BY`

`ORDER BY` defines the result sequence:

```sql
ORDER BY created_at DESC;
```

`ASC` means ascending:

- oldest to newest timestamps
- A to Z text
- smallest to largest numbers

`DESC` means descending:

- newest to oldest timestamps
- Z to A text
- largest to smallest numbers

The repository appends a stable tie-breaker:

```sql
ORDER BY created_at DESC, id ASC
```

This is important because multiple documents can share the same timestamp, name, or status. Deterministic ordering supports reliable pagination, synchronization jobs, exports, caching, and tests.

Without `ORDER BY`, PostgreSQL does not promise a stable order. Clients must not infer insertion order from an unordered `SELECT`.

## Controlled ordering and allow-listing

Column names are SQL identifiers, not ordinary values. They should not be copied blindly from a request into `ORDER BY`.

The repository maps supported API names to known SQL columns:

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

The route also restricts `sort_by` with a `Literal`, and restricts `sort_order` to `asc` or `desc`.

The safety flow is:

```text
user input
  ↓
FastAPI validation
  ↓
repository allow-list
  ↓
known SQL column and direction
```

Filter values remain parameterized. Dynamic identifiers are controlled through the allow-list because ordinary `%s` parameters represent values, not column names.

## Pagination with `LIMIT` and `OFFSET`

Returning one million documents in one response is not reasonable. Pagination returns a bounded window:

```text
GET /documents?limit=20&offset=0
GET /documents?limit=20&offset=20
```

The PostgreSQL query shape is:

```sql
SELECT id, name, document_type, version, status
FROM documents
WHERE document_type = %s
ORDER BY created_at DESC, id ASC
LIMIT %s
OFFSET %s;
```

The logical order is:

1. identify candidate rows
2. apply `WHERE` filters
3. apply deterministic ordering
4. skip `OFFSET` rows
5. return up to `LIMIT` rows

With a page size of 20:

| Request | Rows represented |
|---|---|
| `limit=20&offset=0` | 1–20 |
| `limit=20&offset=20` | 21–40 |
| `limit=20&offset=40` | 41–60 |

An offset beyond the matching rows returns an empty list with HTTP 200. A final partial page returns the remaining rows.

The response remains a plain list to preserve the existing API contract. Metadata such as total count, `has_next`, or a cursor can be added later as an explicit contract change.

## Pagination validation

The API bounds external input before it reaches the repository:

```python
limit: int | None = Query(default=None, ge=1, le=100)
offset: int = Query(default=0, ge=0)
```

The deliberate maximum page size is 100. This is large enough for ordinary list and batch consumers while preventing accidental requests for an unbounded number of documents.

Examples:

| Request | Result |
|---|---|
| `?limit=20&offset=0` | Valid |
| `?limit=1` | Valid |
| `?limit=100` | Valid |
| `?limit=0` | HTTP 422 |
| `?limit=101` | HTTP 422 |
| `?offset=-1` | HTTP 422 |
| `?limit=abc` | HTTP 422 |

Validation, SQL parameterization, and authorization are separate controls:

- validation enforces type and range
- parameterization protects SQL structure
- authorization controls data access
- business rules control domain behavior

## `LIMIT`/`OFFSET` trade-off

Offset pagination is straightforward for small and moderate datasets:

```sql
LIMIT 20
OFFSET 40
```

At large offsets, such as `OFFSET 900000`, PostgreSQL may need to walk past many ordered rows before returning the requested page. The client may receive only 20 rows, but the database work can be much larger.

Offset pagination can also shift when records are inserted or deleted between requests. Stable ordering reduces ambiguity but does not create a consistent snapshot across independent requests.

Keyset or cursor pagination is the later production concept. Instead of skipping a large offset, it continues from the last ordering key:

```sql
SELECT id, name, document_type, version, status, created_at
FROM documents
WHERE (created_at, id) < (%s, %s)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

Cursor pagination is not implemented in Day 8. The current bounded `LIMIT`/`OFFSET` design is appropriate for the project’s current scope and establishes deterministic ordering for a future cursor design.

## Parameterized SQL

Unsafe SQL construction:

```python
query = f"SELECT * FROM documents WHERE name = '{name}'"
```

This allows input to alter SQL syntax and creates SQL injection risk.

Safe psycopg usage:

```python
cursor.execute(
    "SELECT * FROM documents WHERE name = %s",
    (name,),
)
```

The repository uses this pattern for:

- `document_type`
- `status`
- `name_contains`
- `limit`
- `offset`

For a name search, the wildcard is part of the bound value:

```python
values.append(f"%{name_contains}%")
```

with:

```sql
name ILIKE %s
```

Data must be supplied as parameters, not concatenated into SQL strings.

## Layer responsibilities

### Router

The router handles:

- HTTP method and path
- request query parameters
- FastAPI validation
- dependency injection
- response mapping

It must not open a database connection or execute SQL.

### Service

The service handles:

- business rules
- validation and orchestration
- delegation to the repository

It forwards query intent but does not construct PostgreSQL statements.

### Repository

The repository handles:

- SQL
- database interaction
- query construction
- parameter binding
- mapping database rows into domain `Document` objects

The architecture remains:

```text
Router
  ↓
Service
  ↓
Repository
  ↓
PostgreSQL
```

This preserves the separation established during CRUD implementation.

## Do not put SQL in the router

This is an anti-pattern:

```python
@app.get("/documents")
def get_documents():
    cursor.execute("SELECT * FROM documents")
    return cursor.fetchall()
```

It mixes HTTP, SQL, connection lifecycle, raw database rows, and response behavior. It would couple the API directly to PostgreSQL and bypass the service/repository boundary.

The correct flow is:

```text
router query parameters
  ↓
service.list_documents(...)
  ↓
repository.list_documents(...)
  ↓
parameterized PostgreSQL SELECT
```

## Tests added

### API-level tests

The API tests cover:

1. default pagination behavior through `GET /documents`
2. explicit `limit=2`
3. `limit=2&offset=2` returning the expected page
4. invalid `limit=0` returning HTTP 422
5. invalid `offset=-1` returning HTTP 422
6. `document_type=requirement` filtering
7. preservation of the existing document response shape

### PostgreSQL integration tests

The live database tests cover:

- PostgreSQL repository selection
- create/get CRUD round trips
- list and update behavior
- combined filtering, ordering, and pagination
- observable `created_at DESC` ordering
- delete behavior and missing-document handling

The ordering test deliberately assigns distinct timestamps:

```text
Older Requirement   → 2026-01-01
Middle Requirement  → 2026-01-02
Newest Requirement  → 2026-01-03
```

It then verifies that descending order returns newest, middle, and older records. The test does not rely on identical or coincidental insertion timestamps.

## Transaction concept

Day 8 does not add a complex transaction system. It establishes where transactions belong and why they matter.

If one service operation requires three logically related writes:

```text
BEGIN
write A
write B
write C
COMMIT
```

then a failure in any write should cause:

```text
ROLLBACK
```

The writes should use one connection and one transaction. Committing each write through independent connections would allow partial state:

```text
connection A: write A, COMMIT
connection B: write B, COMMIT
connection C: write C, FAIL
```

The existing `database_connection()` context manager already centralizes connection opening, successful commit, rollback on failure, and closure. Future multi-write service operations should introduce a shared transaction context rather than independently committing each write.

## Validation summary

The completed test suite reports:

```text
29 passed
```

This validates that:

- existing CRUD behavior remains intact
- query parameters are accepted and bounded
- invalid pagination values fail at the API boundary
- filtering works through the repository
- ordering is deterministic and observable
- pagination returns the expected pages
- PostgreSQL integration remains connected and functional

## Final takeaway

Day 8 moves the project from PostgreSQL CRUD to PostgreSQL querying without breaking the architecture.

The router receives and validates query intent. The service orchestrates. The repository owns SQL and database mapping. PostgreSQL performs filtering, ordering, and pagination. Parameterized values and allow-listed identifiers protect the query boundary, while deterministic test data proves the behavior rather than relying on accidental row order.
