# Day 8 / Task 16 — Transaction concept

## Objective

Understand where transactions belong without building a complicated transaction system for Day 8.

The current document operations are mostly single-row CRUD actions. The existing `database_connection()` context manager already establishes the connection lifecycle and commits successful repository blocks, while rolling back failures and closing the connection.

The broader concept becomes important when one service operation performs multiple writes.

## The atomic operation question

Ask:

> If a service operation requires three database writes, should they all succeed independently?

If the writes represent one logical business operation, independent commits are unsafe. A failure after the first or second write can leave partially applied state.

The desired transaction is:

```text
BEGIN
write A
write B
write C
COMMIT
```

If any write fails:

```text
ROLLBACK
```

The system should expose either the complete operation or none of it.

## Example

Imagine a future service operation that:

1. creates a document
2. records an audit event
3. creates an initial processing job

These writes may be logically atomic. If the document is created but the audit event fails, the system may no longer have a reliable history. If the job is created without the document, the worker may receive an invalid reference.

The service should orchestrate the operation, while a transaction-aware repository or unit-of-work boundary should ensure all writes share one database transaction.

## Connection context

A transaction requires the writes to use the same database connection. Opening and committing three independent connections does not create one atomic transaction:

```text
connection A: write A, COMMIT
connection B: write B, COMMIT
connection C: write C, fails
```

At that point, the first two writes remain committed.

The correct shape is one connection and one transaction:

```text
connection
    BEGIN
    write A
    write B
    write C
    COMMIT or ROLLBACK
    close
```

## Current project boundary

Day 8 does not add a multi-write transaction workflow. Querying with `SELECT`, filtering, ordering, and pagination does not require a new transaction abstraction.

The existing connection boundary already:

- opens a connection
- yields it to repository code
- commits a successful block
- rolls back on database errors
- closes the connection

Future multi-write operations should be designed so the service/repository collaboration can provide one shared transaction context.

## Key takeaway

Transactions belong at the database interaction boundary, but the need for a transaction is determined by the service operation’s business atomicity. Day 8 requires understanding this principle, not prematurely implementing a complex transaction system.
