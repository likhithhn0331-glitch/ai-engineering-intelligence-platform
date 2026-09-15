# Database Transactions and ACID

## Why transactions matter

A database transaction is a unit of work that groups multiple operations into one logical outcome.

In the document API, a transaction is relevant when we think about operations like:
- creating a document
- updating a document
- deleting a document
- performing related writes across multiple tables or checks

The key idea is that the system should not partially succeed in a way that leaves the database in an invalid state.

## Transaction pattern

### Successful transaction

```sql
BEGIN;

-- operation 1
INSERT INTO documents (id, name, document_type, version, status)
VALUES ('doc-123', 'engine-requirement', 'requirement', '1.0', 'created');

-- operation 2
UPDATE documents
SET version = '1.1'
WHERE id = 'doc-123';

COMMIT;
```

If both operations succeed, the transaction is committed and the change is permanently recorded.

### Failed transaction

```sql
BEGIN;

-- operation 1
INSERT INTO documents (id, name, document_type, version, status)
VALUES ('doc-123', 'engine-requirement', 'requirement', '1.0', 'created');

-- operation 2 fails because of validation, constraint, or runtime issue
UPDATE documents
SET version = 'broken-value'
WHERE id = 'does-not-exist';

ROLLBACK;
```

In this case, the database discards the changes from the transaction, leaving it in the pre-transaction state.

## ACID properties

### A — Atomicity
All operations in the transaction succeed together, or none of them are applied.

Example:
- create the record and update related audit information
- if one step fails, rollback the whole transaction

### C — Consistency
The database moves from one valid state to another valid state.

Example:
- primary keys remain unique
- required fields are not null
- data values remain within expected conditions

### I — Isolation
Concurrent transactions do not interfere with each other in incorrect ways.

Example:
- transaction A should not accidentally overwrite transaction B's uncommitted changes
- one user should not see half-written data from another transaction

### D — Durability
Once a transaction is committed, the data is expected to survive failures such as crashes or restarts.

Example:
- committed document rows remain in PostgreSQL storage after the application restarts

## Why this matters for this project

This project does not need a highly complex transaction-heavy workflow today, but the concept is essential.

The important understanding is:
- the repository should treat database writes as a unit of work
- failures should not leave the database partially updated
- a commit means the data is durable and valid
- a rollback means the original state is kept intact

## Interview explanation

A strong explanation is:

> A transaction is a database operation group that either fully succeeds or fully fails. PostgreSQL uses ACID guarantees to ensure atomicity, consistency, isolation, and durability. This is important because it prevents partial writes and keeps the database in a valid state even when errors occur.

## Practical takeaway

For this project's current scope:
- we are not building multi-step complex distributed transactions
- we are learning the underlying concept so we can explain database correctness and failure handling confidently
- the repository and connection layer should respect database write integrity and rollback behavior when errors occur

No algorithm change was required for this topic because the architectural flow remains:

FastAPI -> Service -> Repository -> PostgreSQL

The important adjustment is conceptual understanding, not a code redesign.
