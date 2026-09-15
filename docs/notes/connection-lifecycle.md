# Connection Lifecycle and Repository Boundary

## Overview

The project now uses a dedicated database connection boundary so the repository does not manage database lifecycle details in every method.

This is the flow:

Request
↓
Repository
↓
Open connection
↓
Execute SQL
↓
Commit or rollback
↓
Close connection

## What the connection boundary does

The `database_connection()` context manager is responsible for:
- opening a database connection
- yielding it to repository code
- executing SQL statements
- committing the transaction on success
- rolling back automatically on failure
- closing the connection in a `finally` block

This keeps resource management consistent and prevents leaks.

## Why centralize it

If every repository method independently handles connection creation and cleanup, the project becomes harder to maintain.

Centralizing connection handling improves:
- consistency across database operations
- cleanup reliability
- predictable error handling
- maintainability
- testability

## Why this matters in interviews

A strong explanation is:

> Database connection lifecycle management should be centralized because the same rules apply across all repository methods: open connection, run SQL, commit or rollback, and close the resource. If each method does this itself, it becomes easy to forget cleanup, duplicate error handling, and create inconsistent behavior under failure.

## Conceptual flow

```python
@contextmanager
def database_connection():
    connection = psycopg.connect(DATABASE_URL)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
```

This ensures the repository methods remain focused on business logic and SQL mapping, while the connection lifecycle remains stable and reusable.

## Why not open a connection everywhere

Opening and closing connections repeatedly can be inefficient and error-prone.

By using a dedicated boundary:
- the repository logic stays clean
- resource lifecycle is predictable
- connection failure handling is consistent
- tests can isolate and validate repository behavior more easily

## Practical takeaway for this project

The architecture remains:

FastAPI -> Service -> Repository -> Database connection -> PostgreSQL

The connection layer is not an over-engineered abstraction; it is the correct boundary for a small but real database-backed application.

This is the correct engineering choice for the project's current scope because it preserves separation of concerns without adding unnecessary complexity.
