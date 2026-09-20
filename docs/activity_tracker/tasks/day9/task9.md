# Day 9 / Task 9 — Test regression for query refactoring

## Objective

Day 8 query behavior should continue to pass after any refactor.

The important rule is simple:

> Refactoring the query implementation must not change the API contract.

## Existing regression checks

The project already has API tests and PostgreSQL integration tests covering the Day 8 behavior:

- default query behavior
- explicit limit
- offset paging
- invalid pagination values
- filtering by `document_type`
- sorting by an allow-listed field
- deterministic ordering using real timestamps

These tests validate the external contract and ensure the repository remains the only place where SQL construction is implemented.

## Why the tests matter

A refactor from direct method parameters to a `DocumentQuery` object is safe only if:

- the HTTP contract still behaves the same
- responses still contain the same fields
- validation still rejects invalid inputs
- filtering still reduces the result set
- ordering remains deterministic
- pagination remains bounded and predictable

If the API behavior changes, the refactor is not neutral and should not be considered complete.

## Value of regression testing

Regression tests protect against three common refactor mistakes:

1. changing the external API contract accidentally
2. breaking validation by moving checks around
3. altering ordering or pagination semantics in ways the client does not expect

This is exactly why Day 8 tests are valuable: they keep the query feature anchored to the external contract.

## Key takeaway

The query abstraction should be refactored only if the behavior remains the same. A refactor is correct if the tests still pass without changing the public contract.
