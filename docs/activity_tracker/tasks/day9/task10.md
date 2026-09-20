# Day 9 / Task 10 — Database unavailable during `GET /documents`

## Objective

Understand what happens when PostgreSQL is unavailable while a read request is executing.

The flow is:

```text
HTTP request
  ↓
Router
  ↓
Service
  ↓
Repository
  ↓
connection failure
  ↓
exception
  ↓
API error handling
  ↓
HTTP response
```

The application must not respond with a fake success payload such as:

```json
{
  "status": "success"
}
```

when the database is actually unavailable.

## Failure path

In the current architecture, the repository sits behind a database connection boundary in `src/db/connection.py`.

When PostgreSQL cannot be reached, the connection layer raises a `DatabaseUnavailableError`.

This is then handled centrally in `src/main.py` by the `DatabaseUnavailableError` exception handler:

```python
@app.exception_handler(DatabaseUnavailableError)
async def database_unavailable_handler(request: Request, exc: DatabaseUnavailableError):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": exc.message},
    )
```

So a database failure does not produce a fabricated success response. It produces a real HTTP 503.

## Why this matters

A client must be able to distinguish between:

- data was successfully retrieved
- the system is unavailable
- the request cannot be processed

Returning success when the persistence layer fails is a correctness bug because the caller may believe the query result is valid even though it did not come from the database.

## Route-level effect

A read request like:

```text
GET /documents
```

should either:

- return the data successfully, or
- fail with an HTTP 503 if the database is unavailable

It should never pretend that the query succeeded when the database failed.

## Why the exception boundary matters

The repository is where database access happens. The route should not continue as if the database call succeeded. The exception must bubble to the app-level global handler so the system sends the correct HTTP status and a truthful response.

This is exactly the reason centralized exception handling is important: it prevents partial or misleading success responses.

## Key takeaway

When PostgreSQL is unavailable, the API must fail explicitly and honestly. Returning a fake success response would hide the failure and mislead clients.
