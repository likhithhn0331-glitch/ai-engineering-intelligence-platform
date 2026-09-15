# Persistence Verification and Request Tracing

## Goal

The goal is not to add a major feature. The goal is to prove that the current architecture works end-to-end with PostgreSQL persistence.

## Task 8.1 — Verify repository boundary

The repository interface is responsible for the following methods:

- create
- get_all
- get_by_id
- update
- delete

These methods should be understood as the boundary between the service layer and the database layer.

The repository is responsible for translating application-level operations into SQL and mapping database rows back into domain results.

## Task 8.2 — Trace one request: POST /documents

The request flow is:

HTTP Request
↓
FastAPI Router
↓
Pydantic validation
↓
DocumentService
↓
DocumentRepository
↓
Database connection
↓
PostgreSQL
↓
Repository result
↓
Service
↓
API response

This means the API request does not directly write to the database. The flow is structured and layered so the application logic stays separated from persistence concerns.

## Trace a GET request

The flow for `GET /documents/{document_id}` is:

Router
↓
Service
↓
Repository
↓
SQL SELECT
↓
PostgreSQL
↓
row
↓
domain object
↓
response

The key idea is that the repository returns either a row result or a not-found condition, and the service or exception handling translates it into the correct API behavior.

## Trace an UPDATE

The flow for `PUT /documents/{document_id}` is:

Request
↓
validation
↓
service
↓
repository
↓
UPDATE SQL
↓
database
↓
updated document
↓
response

If the document ID does not exist, the repository should detect that condition and raise `DocumentNotFoundError`.

The correct flow is:

Repository detects absence
↓
DocumentNotFoundError
↓
Global FastAPI exception handler
↓
HTTP 404

This preserves the API contract and keeps route-level exception translation out of the business logic.

## Verify DELETE

The delete flow should be validated manually:

1. Call `DELETE /documents/{id}`
2. Confirm success status
3. Call `GET /documents/{id}`
4. Confirm the result is `404`
5. Inspect PostgreSQL directly
6. Confirm the row is actually deleted

This proves the row is no longer in the database, not just that the API returned a success payload.

## Restart persistence test

This is mandatory and is the clearest proof of real persistence.

Procedure:

1. Start PostgreSQL
2. Start FastAPI
3. Create a document
4. Retrieve the document
5. Stop FastAPI
6. Start FastAPI again
7. Retrieve the same document
8. Confirm it still exists

Definition of success:

The document survives the application restart.

This distinguishes real database persistence from an in-memory dictionary implementation.

## PostgreSQL integration tests

The project includes a dedicated integration test file:

- `tests/test_postgres_integration.py`

The tests cover:
- PostgreSQL is used when `DATABASE_URL` is valid
- create → fetch
- multiple creates → list
- create → update → fetch
- create → delete → fetch
- missing document → 404

The fixture truncates the `documents` table between tests to keep isolation clean.

## Execution requirement

The project should run:

```bash
python -m pytest -q tests/test_postgres_integration.py
python -m pytest -q
```

Using the Python executable appropriate to the local environment.

## Do not fabricate results

This rule is essential.

The project must record actual outcomes:

- full test suite count
- number of passed tests
- failed tests
- warnings
- cause of any failure
- fix applied
- retest result

Example structure:

```text
Full test suite:
X passed
Y failed
Z warnings

Failure:
Cause:
Fix:
Retest:
Result:
```

This rule applies throughout the project so the engineering record remains trustworthy.

## Final takeaway

The persistence verification task proves more than API behavior. It proves that the architecture functions as intended:

FastAPI
↓
Service
↓
Repository
↓
Database connection
↓
PostgreSQL

and that real rows remain stored and retrievable after restart.
