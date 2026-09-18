# Day 8 / Task 7 — Controlled document querying without breaking the architecture

## Objective

Add controlled document querying while preserving the existing layered architecture.

Before Day 8, the collection request followed this path:

```text
GET /documents
    ↓
DocumentService
    ↓
DocumentRepository
    ↓
PostgreSQL
```

The Day 8 query path extends the request with validated query intent:

```text
GET /documents
    ↓
Query parameters
    ↓
Service validation and forwarding
    ↓
Repository query construction
    ↓
PostgreSQL
```

The important design decision is that querying is added inside the existing boundaries. The route does not become a database layer, the service does not construct SQL, and PostgreSQL remains behind the repository.

## What “controlled querying” means

The API accepts a defined set of query parameters:

| Parameter | Purpose | Control |
|---|---|---|
| `document_type` | Exact type filter | Value is bound as a SQL parameter |
| `status` | Exact status filter | Value is bound as a SQL parameter |
| `name_contains` | Case-insensitive name search | Search pattern is bound as a SQL parameter |
| `sort_by` | Select result ordering | Restricted to known columns |
| `sort_order` | Select ordering direction | Restricted to `asc` or `desc` |
| `limit` | Bound page size | Integer from 1 through 100 |
| `offset` | Number of rows to skip | Integer greater than or equal to 0 |

The client can express query intent, but it cannot submit arbitrary SQL.

Examples:

```text
GET /documents?document_type=requirement
GET /documents?status=created
GET /documents?document_type=requirement&status=created
GET /documents?sort_by=created_at&sort_order=desc
GET /documents?limit=20&offset=40
```

## Request lifecycle

### 1. HTTP request enters FastAPI

The request is received by the `GET /documents` route in `src/api/document_routes.py`.

The route declares the supported query parameters using FastAPI's `Query` declarations and a `Literal` allow-list for ordering:

- invalid numeric ranges are rejected
- unsupported sort fields are rejected
- unsupported sort directions are rejected
- empty search values are rejected

FastAPI returns a validation response before database access when the query contract is violated.

### 2. Query parameters are passed to the service

The route remains thin. It does not assemble SQL or open a database connection.

It forwards the validated values to:

```python
service.list_documents(
    document_type=document_type,
    status=status_filter,
    name_contains=name_contains,
    limit=limit,
    offset=offset,
    sort_by=sort_by,
    sort_order=sort_order,
)
```

This keeps HTTP concerns in the API layer and query orchestration in the service layer.

### 3. The service preserves the dependency direction

`DocumentService.list_documents()` accepts query intent and forwards it to the repository.

The service does not know whether the repository uses PostgreSQL, an in-memory test implementation, or another persistence mechanism. It also does not build SQL fragments.

This preserves the original dependency direction:

```text
API → Service → Repository
```

Query support extends the existing method contract instead of creating a second persistence path.

### 4. The repository translates intent into SQL

`DocumentRepository.list_documents()` is the database-facing query boundary.

For supplied filters, it builds conditions such as:

```sql
WHERE document_type = %s
  AND status = %s
  AND name ILIKE %s
```

The values are supplied separately:

```python
cursor.execute(query, tuple(values))
```

The repository is therefore responsible for:

- assembling only the requested conditions
- keeping placeholder order aligned with value order
- binding user values safely
- applying ordering
- applying pagination
- converting database rows into `Document` objects

### 5. PostgreSQL executes the controlled query

PostgreSQL evaluates the query and returns only the matching, ordered, paginated rows.

The logical query sequence is:

```text
FROM documents
    ↓
WHERE filters matching rows
    ↓
ORDER BY gives a deterministic sequence
    ↓
OFFSET skips rows in that sequence
    ↓
LIMIT bounds the returned page
```

The application does not load the entire table and filter it in Python on the PostgreSQL path.

### 6. Results return through the existing layers

The repository maps each PostgreSQL row to a domain `Document`.

The service returns the document collection to the route. The route maps each object to the existing `DocumentResponse` shape:

```json
[
  {
    "id": "doc-001",
    "name": "Engine Requirements",
    "document_type": "requirement",
    "version": "1.0",
    "status": "created"
  }
]
```

Querying changes which documents appear in the list, not the representation of an individual document.

## Why the architecture remains stable

The architecture is preserved because each layer has one clear responsibility:

| Layer | Responsibility |
|---|---|
| FastAPI route | Parse and validate HTTP query parameters |
| Service | Forward query intent through the business boundary |
| Repository | Translate intent into safe persistence queries |
| Connection boundary | Open, commit/rollback, and close database resources |
| PostgreSQL | Filter, order, and paginate stored rows |
| Response model | Preserve the API response contract |

No route imports `psycopg`. No service executes SQL. No client controls a raw SQL string.

## Security controls

Controlled querying requires two different protections.

### Parameterized values

Filter values, search patterns, limits, and offsets use psycopg parameters:

```sql
WHERE status = %s
LIMIT %s
OFFSET %s
```

Request data is treated as data, not concatenated into SQL syntax.

### Allow-listed identifiers

Column names cannot be safely supplied as ordinary value parameters. The repository maps known API names to known SQL identifiers:

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

The sort direction is independently restricted to `ASC` or `DESC`.

Together, parameterization and allow-listing prevent the query API from becoming an arbitrary SQL execution interface.

## Deterministic results

Pagination requires a stable ordering. The repository appends `id ASC` as a tie-breaker:

```sql
ORDER BY created_at DESC, id ASC
```

Without an explicit order, PostgreSQL is free to return rows in any plan-dependent order. Without a tie-breaker, equal timestamps or names can move between pages.

Deterministic ordering makes repeated requests more predictable for:

- user interfaces
- batch jobs
- exports
- tests
- page-based clients

## PostgreSQL versus fallback behavior

When a valid database URL is configured, the repository executes the controlled query in PostgreSQL.

When PostgreSQL is not configured, the existing repository fallback applies equivalent filters, sorting, offset, and limit in memory. This preserves local behavior and keeps the API usable in a non-database environment.

The fallback does not replace PostgreSQL validation. The PostgreSQL integration tests verify the real database path.

## Testing the architecture

The implementation is covered at two levels:

### API contract coverage

The API tests verify that:

- query parameters are accepted
- filters affect returned documents
- sorting and page size are applied
- the response remains a list of `DocumentResponse` objects

### PostgreSQL integration coverage

The integration tests verify that:

- the repository uses the configured PostgreSQL database
- combined filters work through the live API
- sorting and pagination are applied by the database-backed path
- CRUD behavior remains intact

This matters because a passing unit-style test against an in-memory dictionary would not prove that PostgreSQL query construction works.

## Final flow

The complete Day 8 collection flow is:

```text
GET /documents?document_type=requirement&status=created&limit=20
        ↓
FastAPI parses and validates query parameters
        ↓
DocumentService.list_documents(...)
        ↓
DocumentRepository.list_documents(...)
        ↓
Parameterized SELECT with WHERE, ORDER BY, LIMIT, and OFFSET
        ↓
database_connection()
        ↓
PostgreSQL
        ↓
filtered rows
        ↓
Document domain objects
        ↓
DocumentResponse list
        ↓
HTTP 200 response
```

## Key takeaway

Day 8 does not replace the CRUD architecture. It adds a controlled read capability to it.

The API exposes query intent, FastAPI validates the public contract, the service preserves the business boundary, the repository owns SQL translation, and PostgreSQL performs the filtering, ordering, and pagination. This is the correct progression from PostgreSQL CRUD to PostgreSQL querying without leaking persistence concerns into the rest of the application.
