# Day 8 / Task 11 — Add controlled ordering

## Objective

Allow API consumers to choose a supported ordering without allowing arbitrary SQL identifiers.

The project’s public parameter names are:

```text
GET /documents?sort_by=created_at&sort_order=desc
GET /documents?sort_by=name&sort_order=asc
```

The conceptual form `sort=created_at&order=desc` expresses the same idea, but the implemented API uses `sort_by` and `sort_order` to make the meaning explicit.

## SQL representation

The repository produces an ordering such as:

```sql
ORDER BY created_at DESC, id ASC
```

or:

```sql
ORDER BY name ASC, id ASC
```

The secondary `id ASC` key makes equal primary values deterministic, which is important for pagination.

## Why arbitrary `ORDER BY` input is unsafe

Ordinary SQL parameters represent values:

```sql
WHERE name = %s
```

A column identifier is different. A client should not be allowed to submit arbitrary text that is copied into:

```sql
ORDER BY <client-input>
```

Blind insertion could allow malformed SQL or injection through the identifier position.

## Allow-list design

The repository maps approved public names to approved SQL identifiers:

```python
ALLOWED_SORT_FIELDS = {
    "id": "id",
    "name": "name",
    "document_type": "document_type",
    "version": "version",
    "status": "status",
    "created_at": "created_at",
}
```

The process is:

```text
user input
    ↓
route Literal validation
    ↓
repository allow-list lookup
    ↓
known SQL column
```

The direction is independently restricted to `asc` or `desc` and converted to the SQL keywords `ASC` or `DESC`.

Unsupported values are rejected before arbitrary text can become part of the query.

## Deterministic ordering for consumers

Ordering is an API behavior, not merely a presentation detail. Consumers may depend on it for:

- stable pagination
- repeatable synchronization
- predictable user interfaces
- exports
- caching
- reliable tests

Without `ORDER BY`, PostgreSQL does not promise a stable order. Without a tie-breaker, rows with equal names or timestamps can move between pages.

The repository therefore uses:

```sql
ORDER BY <approved_column> <approved_direction>, id ASC
```

## Implementation status

Controlled ordering is already implemented in the route and repository:

- supported fields are explicitly listed
- supported directions are `asc` and `desc`
- values use parameter binding
- identifiers come only from the allow-list
- `id ASC` provides a deterministic tie-breaker

No code changes were necessary for this task.
