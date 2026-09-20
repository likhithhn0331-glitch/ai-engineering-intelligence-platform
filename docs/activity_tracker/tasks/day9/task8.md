# Day 9 / Task 8 — Preserve API behavior

## Objective

The query refactor must not change the external behavior of `GET /documents`.

The existing API behavior must continue to work:

```text
GET /documents
GET /documents?limit=...
GET /documents?offset=...
GET /documents?document_type=...
GET /documents?sort=...&order=...
```

The project’s Day 8 contract is explicit. A refactor should not alter that contract.

## The contract that must remain stable

The route still returns a list of `DocumentResponse` objects:

```json
[
  {
    "id": "doc-001",
    "name": "Engine Requirements",
    "document_type": "requirement",
    "version": "1.0",
    "status": "created"
  }
]
```

The query options may change which rows are returned, but the response shape does not change.

## The service must remain thin and stable

The service method should continue to act as the business entry point:

```python
service.list_documents(...)
```

It should still forward the input to the repository in a predictable way.

The key point is that the query abstraction must remain an implementation detail. The public API should not gain new routes or new response structures without explicit product intent.

## What not to do

Do not add extra endpoints like:

```text
GET /documents/query
GET /documents/search
GET /documents/filtered
```

Do not change the meaning of an existing route because the internal implementation is being refactored.

The refactor is internal. The public contract is external and must not move.

## Regression protection

The Day 8 tests act as the regression guard for the contract.

The critical behavior to preserve is:

- API still returns valid `DocumentResponse` rows
- default behavior remains stable
- pagination remains bounded and validated
- filtering still narrows matches
- ordering is still deterministic and safe
- invalid input still returns HTTP validation errors

Any refactor that changes those behaviors should be rejected unless the product explicitly approves the change.

## Key takeaway

Refactoring the query execution path is valid only if it preserves the established API contract. The architecture can change internally, but the interface must stay stable.
