# Day 9 / Task 7 — Refactor repository query handling only if there is a real benefit

## Objective

The intended flow is:

```text
DocumentService
       ↓
DocumentQuery
       ↓
DocumentRepository
       ↓
safe SQL
       ↓
PostgreSQL
```

This is a good design pattern, but it should only be adopted when it improves the current code.

## Current code status

The repository already supports a single, structured query method in practice:

```python
def list_documents(
    self,
    document_type=None,
    status=None,
    name_contains=None,
    limit=None,
    offset=0,
    sort_by="created_at",
    sort_order="asc",
):
```

This is already a single repository entry point for a broad set of query inputs.

The repository builds:

- filter conditions
- sort ordering
- pagination
- parameter binding
- row mapping

This is conceptually close to a query object already. The difference is only whether the method arguments are passed as positional/keyword values or as a single object.

## When a refactor is justified

A refactor is justified when the query parameters become complex enough that the repository method is hard to maintain or reason about.

Examples:

- many optional filters
- repeated custom sorting logic
- multiple query combinations that are otherwise identical
- added query-specific validation that is not naturally part of route validation

At that point, a `DocumentQuery` object starts to add clarity.

## What the refactor should preserve

The refactor should keep the same high-level architecture:

```text
Router -> Service -> Repository -> SQL -> PostgreSQL
```

It should not change the public API contract or create multiple repository methods for each possible filter combination.

The repository should continue to be the only place where SQL is assembled and values are bound.

## Recommended adaptation

If a query object is introduced later, it should be introduced as a small data container rather than a new service pattern.

Conceptually:

```python
class DocumentQuery(BaseModel):
    document_type: str | None = None
    status: str | None = None
    limit: int | None = None
    offset: int = 0
    sort_field: str = "created_at"
    sort_order: str = "asc"
```

Then the repository can interpret it without any duplication:

```python
def list_documents(self, query: DocumentQuery):
    # interpret query.document_type, query.status, etc.
    ...
```

This keeps the repository capable of interpreting a single structured request while preserving a single query method.

## Why this is not necessary right now

The current implementation is already easy to read, and the API contract is stable.

A refactor for the sake of refactoring would risk:

- changing the public query behavior
- introducing bugs in validation or ordering
- making the route and repository harder to trace during debugging

Because the code is already clean, the engineering decision is to keep the current repository method unless the codebase grows in a way that makes a query object clearly better.

## Key takeaway

The repository query handling is already close to the desired abstraction. The right move is not to force a new query representation today; it is to refine the boundary only where the current implementation genuinely benefits from it.
