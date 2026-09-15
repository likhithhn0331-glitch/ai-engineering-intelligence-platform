# Deliberate Database Failures Test Report

## Summary

This test suite validates the failure-handling behavior expected from the PostgreSQL-backed document repository and API.

Command run:

```bash
.\.venv\Scripts\python.exe -m pytest tests/test_deliberate_database_failures.py -q
```

Result:
- 5 tests passed
- 0 failed
- Exit code: 0

## What was tested

1. Duplicate primary key rejection
   - Inserts the same document ID twice.
   - Confirms PostgreSQL raises a `UniqueViolation`.

2. Missing required field rejection
   - Inserts a row without a required `name` field.
   - Confirms PostgreSQL raises a `NotNullViolation`.

3. Invalid document type validation
   - Calls `POST /documents` with an unsupported `document_type`.
   - Confirms the API returns HTTP 400.

4. Update nonexistent document
   - Calls `PUT /documents/does-not-exist`.
   - Confirms the API returns HTTP 404.

5. Delete nonexistent document
   - Calls `DELETE /documents/does-not-exist`.
   - Confirms the API returns HTTP 404.

## Pass condition

A test is considered passed when the observed PostgreSQL or API behavior matches the expected contract:
- database constraint violations are raised as expected
- API validation returns the correct HTTP status and message
- not-found paths return a 404 response with the expected error detail

## Notes

The suite is configured to skip automatically if the PostgreSQL connection is not available or `DATABASE_URL` is not set.

Warnings shown during execution were dependency deprecation warnings from FastAPI/Starlette and did not affect test validity.
