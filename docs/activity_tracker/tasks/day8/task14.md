# Day 8 / Task 14 — Project tests for querying

## Objective

Tests should prove the new behavior through the public API and, where appropriate, against the live PostgreSQL path.

## Test checklist

### 1. Default pagination

Request:

```text
GET /documents
```

Create known records first and verify the default behavior remains intact. With no limit or offset, the response contains the created collection in its documented deterministic order.

### 2. Explicit limit

Request:

```text
GET /documents?limit=2
```

Create at least three records and verify that no more than two are returned.

### 3. Offset

Create four records in a known order:

```text
Page Document 0
Page Document 1
Page Document 2
Page Document 3
```

Request:

```text
GET /documents?limit=2&offset=2
```

Verify that the response is exactly `Page Document 2` and `Page Document 3`.

### 4. Invalid limit

Request:

```text
GET /documents?limit=0
```

Expected result: HTTP 422 validation failure. The request must not reach the repository.

### 5. Invalid offset

Request:

```text
GET /documents?offset=-1
```

Expected result: HTTP 422 validation failure.

### 6. Filtering

Create both requirement and design documents, then request:

```text
GET /documents?document_type=requirement
```

Verify every returned document has `document_type == "requirement"` and that the design record is excluded.

### 7. Ordering

Verify:

```text
GET /documents?sort_by=created_at&sort_order=desc
```

actually orders by `created_at DESC`, rather than merely returning insertion order by accident.

## Test placement

`tests/test_api.py` covers HTTP validation and API behavior. `tests/test_postgres_integration.py` covers the configured PostgreSQL repository and verifies that SQL behavior works against the real database.

The tests intentionally use data with observable differences. Assertions should not depend on two records having identical timestamps or on unspecified database order.

## Evidence

The project now covers:

- default collection behavior
- explicit page size
- offset page selection
- invalid pagination input
- document-type filtering
- deterministic descending timestamp ordering

The public API contract remains a list of document response objects.
