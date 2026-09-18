# Day 8 / Task 15 — Deliberate database test data

## Objective

Tests must create data that makes the expected behavior observable.

Weak test data:

```text
document A
document B
```

If the values do not distinguish ordering or filtering behavior, a test may pass without proving the intended query.

## Data for filtering

Filtering data should contain both matching and non-matching records:

| Name | Type |
|---|---|
| API Requirement | requirement |
| Database Requirement | requirement |
| Architecture Spec | design |

Then:

```text
GET /documents?document_type=requirement
```

can prove that the design document is excluded.

## Data for pagination

Pagination data should be distinct and inserted in a known sequence:

```text
Page Document 0
Page Document 1
Page Document 2
Page Document 3
```

The request:

```text
GET /documents?limit=2&offset=2
```

has an observable expected page rather than only a count assertion.

## Data for ordering

Do not assume creation order proves `created_at DESC`. The PostgreSQL integration test deliberately updates the records to distinct timestamps:

```text
Older Requirement   -> 2026-01-01
Middle Requirement  -> 2026-01-02
Newest Requirement  -> 2026-01-03
```

It then requests:

```text
GET /documents?sort_by=created_at&sort_order=desc
```

and expects:

```text
Newest Requirement
Middle Requirement
Older Requirement
```

The values make the sort behavior observable and do not rely on timestamp coincidence.

## Testing habit

Good test data is part of the test design. It should:

- expose the intended branch or query condition
- distinguish matching from non-matching rows
- make order explicit
- avoid dependence on unspecified behavior
- support a precise assertion

## Key takeaway

A test that happens to pass is not enough. The fixtures must be constructed so that an incorrect filter, order, or page calculation produces a visible failure.
