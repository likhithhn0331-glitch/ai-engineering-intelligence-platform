# Deliberate Database Failures

## Purpose

This exercise is meant to validate the application under failure conditions, not just on the happy path. In a real backend system, the database can reject bad operations, and the application must handle those failures in a controlled, consistent way.

The goal is to understand how the database enforces correctness and how the repository and service layers should respond.

## Failure 1 — Duplicate Primary Key

### Scenario

Try inserting the same document ID twice.

```sql
INSERT INTO documents (id, name, document_type, version, status)
VALUES ('doc-001', 'first', 'requirement', '1.0', 'created');

INSERT INTO documents (id, name, document_type, version, status)
VALUES ('doc-001', 'second', 'requirement', '2.0', 'created');
```

### Expected result

The second insert fails because `id` is the primary key.

### Why this matters

This is a database-level constraint violation. The database rejects the duplicate because it enforces uniqueness at the storage layer.

### Application interpretation

The repository should surface this as a database error. The application may translate it into an application-level validation or domain error depending on the contract. In the current project, duplicate document names are handled in the service layer before the repository is called, but this is still an important database failure mode to understand.

## Failure 2 — Missing Required Field

### Scenario

Insert data without a required column.

```sql
INSERT INTO documents (id, name, document_type, version)
VALUES ('doc-002', 'missing-status', 'requirement', '1.0');
```

### Expected result

This fails because `status` is `NOT NULL`.

### Why this matters

The database prevents incomplete records. This ensures invalid data does not enter the table.

### Application interpretation

The service layer can validate before the insert, but the database still enforces the rule. This is a strong example of database-level correctness guarantees.

## Failure 3 — Invalid Data

### Scenario

Insert invalid or unsupported data.

```sql
INSERT INTO documents (id, name, document_type, version, status)
VALUES ('doc-003', 'bad-type', 'unsupported-type', '1.0', 'created');
```

### Expected result

If a `CHECK` constraint is present, this fails. Otherwise, the application should reject it before storage.

### Why this matters

This distinguishes:

- application validation: business logic verifies allowed values before writing
- database validation: the database enforces structural correctness and constraints

For this project, the service layer validates `document_type` against the allowed set:

- `requirement`
- `design`
- `test`

The database can also enforce this through a `CHECK` constraint, but the current project keeps the validation at the service layer for simplicity.

## Failure 4 — Update Nonexistent Document

### Scenario

Update a row that does not exist.

```sql
UPDATE documents
SET version = '2.0'
WHERE id = 'does-not-exist';
```

### Expected result

No rows are updated.

### Critical interview question

How does the repository determine whether anything was updated?

The repository should inspect the result of the update operation and determine whether any row matched the `WHERE` clause.

Typical patterns:

- `UPDATE ... RETURNING ...`
- row count check
- fetch-after-update pattern when required

In this project, the repository uses the result of the database operation to determine whether a document existed and whether the update succeeded.

This is important because a missing document should be treated as a business-level not-found condition and then translated into a `DocumentNotFoundError` and a `404` response.

## Failure 5 — Delete Nonexistent Document

### Scenario

Delete a row that does not exist.

```sql
DELETE FROM documents
WHERE id = 'does-not-exist';
```

### Expected result

No row is removed.

### Application interpretation

The repository must detect that no row matched and then signal the application that the document was not found.

This is translated into the existing contract:

- repository returns no match / None
- service raises `DocumentNotFoundError`
- global exception handler returns `404 Not Found`

This matches the project’s current API contract for missing documents.

## Why this matters in interviews

The goal is not to memorize SQL syntax alone; it is to understand how database constraints and application behavior fit together.

A strong backend answer is:

- the database enforces integrity at the storage layer
- the application validates business rules before insertion/update
- repository methods check whether the database operation affected rows
- missing rows are translated into `DocumentNotFoundError` and `404`

This is a very important signal of production-minded backend design.

## Summary

These deliberate failure tests show that the database is not just storing data — it is enforcing correctness. The project benefits from both application validation and database constraints, and the repository must map update/delete failures into the same domain error flow already used by the application.
