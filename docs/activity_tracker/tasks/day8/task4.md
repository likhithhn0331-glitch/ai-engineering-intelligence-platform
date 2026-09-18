# Day 8 / Task 4 — Pagination with `LIMIT` and `OFFSET`

## Task

Returning every document is not reasonable when a system contains a large collection. If the table contains one million rows, a request that returns all one million rows creates unnecessary database work, network transfer, application memory use, and response latency.

Pagination returns a bounded window:

```text
GET /documents?limit=20&offset=0
GET /documents?limit=20&offset=20
```

The corresponding SQL is:

```sql
SELECT id, name, document_type, version, status
FROM documents
ORDER BY created_at DESC, id ASC
LIMIT 20
OFFSET 40;
```

## `LIMIT`

`LIMIT` caps the number of rows returned:

```sql
SELECT *
FROM documents
ORDER BY created_at DESC
LIMIT 20;
```

At most 20 rows are returned. The database may find more matching rows, but the result sent to the application is bounded.

The API limits `limit` to a maximum of 100. This prevents a client from accidentally requesting an unbounded page while still allowing normal list views and batch consumers.

## `OFFSET`

`OFFSET` skips rows before returning the page:

```sql
SELECT *
FROM documents
ORDER BY created_at DESC
LIMIT 20
OFFSET 40;
```

This requests rows 41 through 60 of the ordered result, assuming at least 60 rows exist.

With a page size of 20:

| Request | Rows represented |
|---|---|
| `limit=20&offset=0` | 1–20 |
| `limit=20&offset=20` | 21–40 |
| `limit=20&offset=40` | 41–60 |

`OFFSET` is applied after the result has been ordered. Without a stable `ORDER BY`, page contents can move between requests.

## Pagination lifecycle

```text
HTTP limit/offset
        ↓
FastAPI validates non-negative offset and bounded limit
        ↓
DocumentService forwards page intent
        ↓
DocumentRepository builds SELECT
        ↓
PostgreSQL filters and orders rows
        ↓
PostgreSQL applies LIMIT/OFFSET
        ↓
bounded response list
```

The current endpoint preserves its original list response shape. Pagination changes the number of returned documents, not the JSON representation of each document.

## Combining filters and pagination

Pagination normally follows filtering and ordering:

```sql
SELECT id, name, document_type, version, status
FROM documents
WHERE document_type = %s
  AND status = %s
ORDER BY created_at DESC, id ASC
LIMIT %s
OFFSET %s;
```

The logical sequence is:

1. identify candidate rows from `documents`
2. apply `WHERE` filters
3. order matching rows
4. skip the requested offset
5. return up to the requested limit

For example:

```text
GET /documents?document_type=requirement&status=created&limit=20&offset=40
```

means “return page three of the ordered set of created requirements,” not “skip 40 rows from the whole table before filtering.”

## Empty and final pages

If `offset` is beyond the number of matching rows, PostgreSQL returns an empty list. That is a normal page result, not an error.

If fewer rows remain than the requested limit, PostgreSQL returns only the remaining rows. A client can stop when the response contains fewer rows than its requested page size, although a production API may eventually expose metadata such as `has_next` or a total count.

The current API intentionally returns only the existing document list to preserve its contract.

## Key takeaway

`LIMIT` controls page size. `OFFSET` controls how many already-ordered matching rows are skipped. Together they provide a simple page-based API, but deterministic `ORDER BY` is essential for stable results.
