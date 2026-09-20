# Day 9 / Task 5 — Identify query responsibilities in the current code

## Objective

Inspect the current implementation before deciding whether a query abstraction is needed.

The goal is to trace the live request path and identify exactly where each responsibility lives.

## Current request flow

The current `GET /documents` flow is already clean and layered:

```text
HTTP
  ↓
Router
  ↓
Service
  ↓
Repository
  ↓
SQL
  ↓
PostgreSQL
```

The code evidence is in the following files:

- `src/api/document_routes.py`
- `src/services/document_service.py`
- `src/repositories/document_repository.py`
- `src/db/connection.py`
- `tests/test_api.py`
- `tests/test_postgres_integration.py`

## Locate validation in the current code

### HTTP and query parameter validation

The route owns HTTP-aware validation in `src/api/document_routes.py`.

Relevant parameters currently include:

```python
document_type: str | None = Query(default=None)
status_filter: str | None = Query(default=None, alias="status")
name_contains: str | None = Query(default=None, min_length=1)
limit: int | None = Query(default=None, ge=1, le=100)
offset: int = Query(default=0, ge=0)
sort_by: Literal["id", "name", "document_type", "version", "status", "created_at"] = "created_at"
sort_order: Literal["asc", "desc"] = "asc"
```

This is the router-level boundary for HTTP concerns:

- it parses the request
- it validates range and type constraints
- it rejects invalid inputs before repository code runs
- it keeps the API contract explicit

### Service-level validation and orchestration

The service in `src/services/document_service.py` forwards the query intent to the repository:

```python
def list_documents(
    self,
    document_type=None,
    status=None,
    name_contains=None,
    limit=None,
    offset=0,
    sort_by="created_at",
    sort_order="asc",
):
    return self.document_repository.list_documents(
        document_type=document_type,
        status=status,
        name_contains=name_contains,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
    )
```

This service method is responsible for:

- business-level orchestration
- preserving the query contract
- delegating to the repository

It does not construct SQL.

### Repository query construction and SQL execution

The repository in `src/repositories/document_repository.py` is where the query is assembled and executed.

The method signature is already a single query entry point:

```python
def list_documents(
    self,
    document_type=None,
    status=None,
    name_contains=None,
    limit=None,
    offset=0,
    sort_by="created_at",
    sort_order="asc",
):
```

Inside it, the repository does all of the following:

- validates sort field and direction against a fixed allow-list
- builds filter conditions for `document_type`, `status`, and `name_contains`
- builds the `WHERE` clause
- uses `ORDER BY` with a deterministic tie-breaker
- adds `LIMIT` and `OFFSET`
- binds values with `cursor.execute(query, tuple(values))`
- maps rows back to `Document` instances

This is the exact repository responsibility boundary described in the Day 8 architecture.

## Where `limit` is validated

`limit` is validated in the route:

```python
limit: int | None = Query(default=None, ge=1, le=100)
```

This means invalid values such as `limit=0` and `limit=101` are rejected before they reach the database.

## Where `offset` is validated

`offset` is validated in the route:

```python
offset: int = Query(default=0, ge=0)
```

This ensures negative offsets are rejected immediately.

## Where filters are validated

The route validates the filter-bearing query parameters and the service passes them through. There is no arbitrary raw SQL generation at either layer.

The repository performs the final SQL translation from validated values. This is the correct separation.

## Where sort field is validated

The repository validates `sort_by` against an allow-list:

```python
sort_columns = {
    "id": "id",
    "name": "name",
    "document_type": "document_type",
    "version": "version",
    "status": "status",
    "created_at": "created_at",
}
```

Then it raises if the field is not known:

```python
if sort_by not in sort_columns:
    raise ValueError(f"Unsupported sort field: {sort_by}")
```

This is exactly the Day 8 security requirement for `ORDER BY` safety.

## Where SQL is constructed

SQL is constructed in the repository:

```python
where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""
query = (
    "SELECT id, name, document_type, version, status "
    f"FROM documents{where_clause} "
    f"ORDER BY {sort_columns[sort_by]} {direction}, id ASC"
)
```

This is the correct place for SQL assembly because the repository owns persistence logic.

## Where parameters are bound

Parameters are bound in the repository at execution time:

```python
with database_connection() as connection:
    with connection.cursor() as cursor:
        cursor.execute(query, tuple(values))
```

The query uses placeholders such as `%s` and the values are passed separately. This is the correct parameterized pattern.

## Conclusion

The codebase already reflects a clean separation of responsibilities.

The implementation already matches the intended architecture:

- router: HTTP query parameters and validation
- service: business orchestration
- repository: SQL construction, parameter binding, and database execution
- PostgreSQL: actual filtering/order/pagination

Because this is already clean, no broad refactor or new abstraction is required. The best improvement is to formalize the existing query input into a request object only if the codebase later grows enough to justify it.

## Key takeaway

The current Day 8 implementation already does the right thing. The repository boundary is not bloated, and it does not need a blind refactor. The responsibility map is already correct.
