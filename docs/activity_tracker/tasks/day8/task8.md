# Day 8 / Task 8 — Add pagination

## Objective

Extend `GET /documents` with bounded page navigation using `limit` and `offset`.

Examples:

```text
GET /documents?limit=20&offset=0
GET /documents?limit=20&offset=20
```

The first request asks for the first page of up to 20 documents. The second skips the first 20 matching documents and asks for the next page.

## SQL representation

The repository translates the page request into PostgreSQL:

```sql
SELECT id, name, document_type, version, status
FROM documents
ORDER BY created_at ASC, id ASC
LIMIT %s
OFFSET %s;
```

The values are bound as parameters rather than concatenated into SQL.

## Request flow

```text
HTTP query parameters
        ↓
FastAPI Query validation
        ↓
DocumentService.list_documents()
        ↓
DocumentRepository.list_documents()
        ↓
PostgreSQL LIMIT/OFFSET
        ↓
bounded DocumentResponse list
```

Pagination is added to the existing collection endpoint. It does not create a separate route and does not change the document response shape.

## Page calculation

With a page size of 20:

| Page | Request | Rows |
|---|---|---|
| 1 | `limit=20&offset=0` | 1–20 |
| 2 | `limit=20&offset=20` | 21–40 |
| 3 | `limit=20&offset=40` | 41–60 |

`OFFSET` is applied to the ordered result, not to the raw table. Therefore, a stable `ORDER BY` is required for predictable pages.

## Empty and partial pages

If no matching rows remain after the offset, the endpoint returns an empty list with HTTP 200. If fewer rows remain than the requested limit, the endpoint returns only those remaining rows.

The current response remains a plain list to preserve the existing contract. Metadata such as total count, `has_next`, or a next cursor can be introduced later as an explicit API change.

## Implementation status

The Day 8 repository already supports:

- optional `limit`
- optional `offset`
- PostgreSQL `LIMIT` and `OFFSET`
- equivalent fallback behavior when PostgreSQL is unavailable
- deterministic ordering before pagination

No additional code was needed for this documentation task.
