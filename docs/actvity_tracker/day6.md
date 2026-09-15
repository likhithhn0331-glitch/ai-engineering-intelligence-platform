# Day 6 — Verification of PostgreSQL Persistence

## Purpose

This exercise verifies that document data is not only being accepted by the API, but is truly persisted in PostgreSQL. This is the critical distinction between:

- API → Service → Repository → PostgreSQL
- and a transient in-memory Python dictionary

The goal is to prove persistence across application lifecycle restarts.

## Experiment steps

### Step 1 — Create a document through the API

Request:

```http
POST /documents
Content-Type: application/json
```

Body:

```json
{
  "name": "engine-requirement",
  "document_type": "requirement",
  "version": "1.0"
}
```

Expected behavior:

- HTTP status: `201 Created`
- response contains the generated document ID
- response includes the document metadata

Example response:

```json
{
  "id": "doc-001",
  "name": "engine-requirement",
  "document_type": "requirement",
  "version": "1.0",
  "status": "created"
}
```

Record the returned document ID because it will be used for all subsequent checks.

### Step 2 — Retrieve the created document

Request:

```http
GET /documents/{id}
```

Expected behavior:

- HTTP status: `200 OK`
- the same document is returned
- the data matches the inserted record

This confirms the repository can read the newly created row from PostgreSQL.

### Step 3 — Inspect PostgreSQL directly

Run the following SQL:

```sql
SELECT *
FROM documents;
```

Expected behavior:

- the row with the created document ID is present
- `name`, `document_type`, `version`, and `status` match the API request
- `created_at` and `updated_at` are populated by the database

This confirms persistence at the database layer, not merely in Python memory.

### Step 4 — Stop the FastAPI application

This simulates an application restart or process shutdown.

### Step 5 — Restart the FastAPI application

Start the app again using the normal startup flow.

### Step 6 — Retrieve the same document again

Request:

```http
GET /documents/{id}
```

Expected behavior:

- HTTP status: `200 OK`
- the same document is returned
- the document still exists after the app restart

## Expected conclusion

If the same document is still available after restarting the FastAPI app, then the persistence path is proven to be:

API
↓
Service
↓
Repository
↓
PostgreSQL

rather than:

API
↓
Python dictionary

This distinction is critical in technical interviews because it demonstrates real database persistence rather than in-memory state that disappears when the process restarts.

## Why this matters

A Python dictionary survives only while the application process is alive. Once the process restarts, the data disappears. PostgreSQL stores the data outside the process memory space and keeps it durable across restarts.

This experiment proves that the project is using actual relational persistence and not ephemeral runtime state.

## Project-specific validation in this repo

The current repository already includes:

- PostgreSQL migration setup
- `DATABASE_URL` configuration
- database connection boundary
- SQL-backed repository implementation
- PostgreSQL integration tests

The practical validation for this project is to create a document via API, verify the DB row exists in PostgreSQL, restart the app, and confirm the same document is still accessible after restart.

## Summary

This Day 6 validation is designed to confirm the software is truly storing document data in PostgreSQL instead of a transient in-memory dictionary. The document should remain available after the application restarts, which is the defining proof of persistence.

## Interview-critical verification wording

This is the exact reasoning an interviewer is looking for:

- Do not merely run `POST /documents` and `GET /documents` and assume persistence is working.
- You must verify the data still exists in the database itself.
- The argument is not “the API returned a document”; the argument is “the document was persisted in PostgreSQL and survived application restart.”
- This proves the path is:

API
↓
Service
↓
Repository
↓
PostgreSQL

and not:

API
↓
Python dictionary

The persistence check is therefore a real system-level validation, not just a happy-path API smoke test.

## Required evidence in this project

To satisfy the persistence requirement in this project, the following evidence is expected:

1. Create a document through `POST /documents` and record its returned ID.
2. Confirm the same document is retrievable through `GET /documents/{id}`.
3. Query PostgreSQL directly with `SELECT * FROM documents;` and confirm the row exists.
4. Stop the FastAPI app.
5. Restart the FastAPI app.
6. Call `GET /documents/{id}` again and confirm the same document still exists.

If all six steps succeed, the persistence mechanism is proven to be database-backed rather than memory-backed.
