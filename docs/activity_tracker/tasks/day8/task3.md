# Day 8 / Task 3 — SQL ordering with `ORDER BY`

## Task

Study how PostgreSQL controls the order of rows returned by a query:

```sql
SELECT id, name, document_type, version, status, created_at
FROM documents
ORDER BY created_at DESC;
```

and:

```sql
SELECT id, name, document_type, version, status, created_at
FROM documents
ORDER BY name ASC;
```

The API exposes the same intent through query parameters:

```text
GET /documents?sort_by=created_at&sort_order=desc
GET /documents?sort_by=name&sort_order=asc
```

## `ASC` and `DESC`

`ASC` means ascending order:

- numbers: smallest to largest
- text: alphabetically from A to Z
- timestamps: oldest to newest

`DESC` means descending order:

- numbers: largest to smallest
- text: alphabetically from Z to A
- timestamps: newest to oldest

`ASC` is the default direction when no direction is specified:

```sql
ORDER BY name;
```

is equivalent to:

```sql
ORDER BY name ASC;
```

For documents, recent records are commonly more useful first:

```sql
ORDER BY created_at DESC;
```

## Ordering is not guaranteed without `ORDER BY`

SQL does not promise a stable row order merely because rows were inserted in a particular sequence. PostgreSQL may return rows differently after an index is added, statistics change, a query plan changes, or table maintenance occurs.

This query has no contractual ordering:

```sql
SELECT *
FROM documents;
```

If an API returns a collection, clients should not infer meaning from the order unless the API explicitly defines it. The repository therefore uses an explicit default:

```sql
ORDER BY created_at ASC, id ASC
```

## Deterministic ordering

An API consumer may need deterministic ordering for:

- pagination
- repeatable user interfaces
- synchronization jobs
- exports
- tests
- caching
- comparing two responses

Sorting by only one column may still leave ties. Several documents can have the same `created_at`, name, or status. A secondary key makes the order deterministic:

```sql
ORDER BY created_at DESC, id ASC;
```

This means newer documents appear first. If two documents have the same timestamp, their IDs decide their relative order consistently.

The current repository always appends `id ASC` as a tie-breaker:

```sql
ORDER BY <approved_column> <approved_direction>, id ASC
```

That is important when `LIMIT` and `OFFSET` divide rows into pages.

## API and repository boundary

The route accepts an allow-listed `sort_by` and `sort_order`. The repository maps the public names to known SQL identifiers:

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

The application does not insert arbitrary request text into the `ORDER BY` clause. The route validation and repository allow-list together ensure that only supported columns and directions are used.

## Query examples

Newest documents first:

```sql
SELECT id, name, document_type, version, status
FROM documents
ORDER BY created_at DESC, id ASC;
```

Alphabetical document names:

```sql
SELECT id, name, document_type, version, status
FROM documents
ORDER BY name ASC, id ASC;
```

Requirements first, then newest within each group:

```sql
SELECT id, name, document_type, version, status
FROM documents
ORDER BY document_type ASC, created_at DESC, id ASC;
```

## Key takeaway

`ORDER BY` is part of the API contract for collection results. `ASC` and `DESC` define direction, while a stable tie-breaker such as `id` prevents ambiguous page boundaries. Deterministic ordering is not cosmetic; it is required for reliable pagination and repeatable consumers.
