# Day 8 / Task 9 — Pagination validation

## Objective

Pagination input must be bounded before it reaches the database. An API should not accept arbitrary values for `limit` or `offset`.

The current constraints are:

```text
limit >= 1
limit <= 100
offset >= 0
```

The deliberate maximum page size is **100**.

## Why the maximum is 100

A maximum of 100 is large enough for normal list screens, exports in small batches, and API consumers that need more than a single display row. It also prevents accidental requests for thousands or millions of documents.

The exact value is a product and capacity decision. The important engineering property is that the value is explicit, documented, and enforced.

## FastAPI validation

The route declares:

```python
limit: int | None = Query(default=None, ge=1, le=100)
offset: int = Query(default=0, ge=0)
```

FastAPI validates the query before the service or repository is called.

Examples:

| Request | Result |
|---|---|
| `?limit=20&offset=0` | Valid |
| `?limit=1&offset=0` | Valid |
| `?limit=100&offset=40` | Valid |
| `?limit=0` | HTTP 422 |
| `?limit=-1` | HTTP 422 |
| `?limit=101` | HTTP 422 |
| `?offset=-1` | HTTP 422 |
| `?limit=abc` | HTTP 422 |

The database is never asked to process an invalid page request.

## Why validation belongs at the API boundary

The API boundary is the earliest place where external input becomes application data. Rejecting invalid values there provides:

- a clear client-facing error
- consistent behavior for every persistence backend
- protection against oversized responses
- less unnecessary database work
- simpler repository assumptions

The repository still receives ordinary integers and does not need to interpret arbitrary strings.

## Validation is not authorization

Pagination bounds control resource usage, but they do not decide whether a caller may access documents. Authentication and authorization remain separate concerns.

Similarly:

- validation checks shape and range
- parameterization protects SQL structure
- authorization checks access rights
- business logic checks domain rules

## Implementation status

The existing `GET /documents` route enforces `1 <= limit <= 100` and `offset >= 0`. The repository then binds the values to PostgreSQL `LIMIT` and `OFFSET` placeholders.

No code change was necessary because the requested validation is already implemented.
