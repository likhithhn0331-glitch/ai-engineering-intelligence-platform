# Day 9 / Task 13 — Reliability tests

## Objective

Add targeted tests where appropriate and reason through reliability scenarios.

The important concern is not to test everything at once. The focus is on verifying the system does not silently lie about success or perform unsafe work.

## Test A — database unavailable

Scenario:

- the repository attempts to reach PostgreSQL
- the database is unavailable
- the request should fail instead of returning fake success

Expected behavior:

- request fails
- HTTP status is a real failure code
- application returns an honest error response

This is already aligned with the current exception handling in `src/main.py` and the database connection boundary in `src/db/connection.py`.

## Test B — repository throws an unexpected exception

Scenario:

- repository or persistence layer raises an unexpected exception
- the app should still respect the central global error handling

Expected behavior:

- the exception is not swallowed silently
- the app returns a generic HTTP 500 response
- the error is logged by the global exception handler

This is the project’s existing centralized error handling strategy.

## Test C — invalid query parameters

Scenario:

- `limit=0`
- `limit=101`
- `offset=-1`
- unsupported sort values

Expected behavior:

- FastAPI validation fails before the system reaches a database operation
- the request is rejected with HTTP 422
- the application does not make an unsafe or unnecessary database call

This protects both the API contract and the database boundary.

## Test D — valid query abstraction produces the same result as the previous implementation

Scenario:

- a refactor introduces a query object or a cleaner internal query builder
- the behavior must remain the same as before

Expected behavior:

- same filter results
- same ordering semantics
- same pagination boundaries
- same validation behavior
- same HTTP contract

This is the essence of safe refactoring: internal structure may change while behavior remains stable.

## Why they matter

These tests cover the reliability story that is often discussed in interviews:

- failure paths must be honest
- validation must happen before unsafe work
- unexpected exceptions must not become fake success
- query refactors must preserve behavior

## Key takeaway

Reliability tests are not just about “more tests.” They validate the difference between a healthy system and one that hides problems behind a misleading response.
