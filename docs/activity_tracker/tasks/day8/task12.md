# Day 8 / Task 12 — Repository responsibility

## Objective

Keep the query architecture separated:

```text
Router
    ↓
Service
    ↓
Repository
    ↓
PostgreSQL
```

Adding query parameters must not blur the responsibilities of these layers.

## Repository responsibilities

The repository owns persistence details:

- SQL statements
- database interaction
- query construction
- parameter binding
- mapping database records to domain objects

In this project, `DocumentRepository.list_documents()` builds the `SELECT` statement, appends the requested `WHERE` conditions, applies the allow-listed `ORDER BY`, adds `LIMIT` and `OFFSET`, executes through `database_connection()`, and maps rows into `Document` instances.

The repository knows PostgreSQL syntax. The service and router do not need to know cursor APIs or SQL placeholders.

## Service responsibilities

The service owns application-level behavior:

- business rules
- domain validation
- orchestration
- calling the repository

`DocumentService.list_documents()` forwards validated query intent to the repository. It does not construct SQL. This keeps the service independent from the storage technology and makes the repository replaceable.

## Router responsibilities

The router owns HTTP concerns:

- request parameters
- FastAPI validation declarations
- dependency injection
- response mapping
- HTTP status behavior

The route accepts query parameters such as `limit`, `offset`, `document_type`, `sort_by`, and `sort_order`. It then calls the service and returns the existing `DocumentResponse` list.

## Why the boundary matters

If SQL is placed in the router:

- HTTP code becomes coupled to PostgreSQL
- database connections are opened in request handlers
- transaction handling becomes inconsistent
- SQL becomes difficult to test independently
- the service/repository architecture is bypassed
- a future storage change affects API code

The Day 8 change should make the query path richer without changing the dependency direction.

## Final responsibility table

| Layer | Owns | Does not own |
|---|---|---|
| Router | HTTP/query parsing and responses | SQL or database lifecycle |
| Service | business rules and orchestration | PostgreSQL syntax |
| Repository | SQL, DB calls, row mapping | HTTP response formatting |

## Key takeaway

Pagination, filtering, and ordering are API features, but their database implementation remains a repository concern. The architecture stays intact because the router calls the service and the service calls the repository.
