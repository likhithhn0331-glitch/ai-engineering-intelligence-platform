# Day 8 / Task 5 — `LIMIT`/`OFFSET` trade-offs

## Task

`LIMIT` and `OFFSET` are straightforward for small datasets:

```sql
SELECT id, name, document_type, version, status
FROM documents
ORDER BY created_at DESC, id ASC
LIMIT 20
OFFSET 0;
```

However, a large offset can become expensive:

```sql
OFFSET 900000
```

The later production concept is keyset or cursor pagination. It is not implemented in this task; the goal is to understand why it exists.

## Why large offsets cost more

A page with `OFFSET 0` can return the first 20 ordered rows quickly. A page with `OFFSET 900000` still asks PostgreSQL to identify and order the earlier rows so it can skip them before returning the next 20.

Even when an index helps locate rows in order, the database may need to walk past a large number of entries. The application receives only 20 rows, but the database work required to reach those rows can be much larger.

The cost is affected by:

- number of rows skipped
- filtering conditions
- ordering column and available indexes
- table statistics
- data distribution
- whether the sort can use an index

The exact plan should be measured with:

```sql
EXPLAIN
SELECT id, name, document_type, version, status
FROM documents
ORDER BY created_at DESC, id ASC
LIMIT 20
OFFSET 900000;
```

`EXPLAIN ANALYZE` provides runtime measurements but executes the query, so it should be used deliberately in production environments.

## When offset pagination is appropriate

`LIMIT`/`OFFSET` remains useful when:

- the dataset is small or moderate
- users need numbered pages
- jumping directly to a page matters
- the offset remains bounded
- simplicity is more valuable than maximum throughput
- the endpoint is an internal or administrative view

It is easy for clients to understand:

```text
page 1 -> limit=20, offset=0
page 2 -> limit=20, offset=20
page 3 -> limit=20, offset=40
```

The current implementation is intentionally sufficient for the project’s size and learning goal.

## The deeper problem: changing data

Offset pagination can also produce duplicates or omissions when rows are inserted or deleted between requests. If page one is read, then a new newest document is inserted before page two is requested, the rows at later offsets shift.

Stable ordering reduces ambiguity, but it cannot make an offset snapshot-consistent across independent requests. A production design must decide whether it needs a snapshot, a cursor, or eventual consistency.

## Keyset/cursor pagination

Keyset pagination uses the values from the last row of the current page to find the next page. It does not ask the database to count past a large offset.

For an ordering of newest `created_at` first and `id` as a tie-breaker, the next-page condition could be:

```sql
SELECT id, name, document_type, version, status, created_at
FROM documents
WHERE (created_at, id) < (%s, %s)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

The cursor contains the last row’s ordering values. The next request might look conceptually like:

```text
GET /documents?limit=20&after=cursor-value
```

The cursor is usually encoded rather than exposing raw database values directly. It should represent the complete ordering key, including the tie-breaker.

## Offset versus keyset

| Property | `LIMIT`/`OFFSET` | Keyset/cursor |
|---|---|---|
| Implementation | Simple | More involved |
| Numbered page jumps | Natural | Not natural |
| Large-page-number performance | Degrades with offset | Usually stable |
| Behavior during inserts/deletes | Can shift rows | More stable relative to cursor |
| Client state | Page number | Cursor token |
| Best use | Small or moderate collections | Large feeds and high-volume APIs |

Keyset pagination is not automatically better for every endpoint. It introduces cursor encoding, ordering rules, and a different client contract.

## Day 8 decision

Do not implement cursor pagination yet. The current endpoint uses:

```text
limit
offset
sort_by
sort_order
```

This is an appropriate first pagination design because it is explicit, bounded, easy to test, and consistent with the existing API contract. The code already uses deterministic ordering and a maximum page size, which are useful foundations for a future cursor design.

## Key takeaway

Offset pagination is a practical starting point, not a universal solution. At large offsets, the database may do substantial work to skip rows that the client never receives. Keyset/cursor pagination exists to continue from a known ordering position instead of walking past a large offset.
