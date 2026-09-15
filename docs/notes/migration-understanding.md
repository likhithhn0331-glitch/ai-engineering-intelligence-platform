# Migration Understanding

## Overview

The project uses a migration-based schema setup rather than manual table creation.

The flow is:

Developer
↓
Migration file
↓
Migration runner
↓
Database
↓
schema_migrations

## What the migration does

A migration is a small, versioned SQL file that describes a schema change.

In this project:
- `migrations/001_create_documents_table.sql` defines the `documents` table
- the migration runner in `src/database.py` reads and applies pending migrations
- PostgreSQL tracks applied migration names in a `schema_migrations` table

This prevents the same migration from being executed repeatedly.

## Why migration-based setup is better than manual table creation

A manual table creation process is fragile because the schema is created once in a local database and then forgotten.

Migrations are better because they make the schema:
- reproducible
- versioned
- reviewable
- deployable
- consistent across environments

## Why versioning matters

When the project grows, multiple developers may need to add or modify schema changes.

A migration system gives a clear history:
- what changed
- when it changed
- which environment it was applied to
- whether it was already executed

This is much more reliable than asking everyone to remember a one-off SQL script run in a local database.

## Why schema_migrations matters

The `schema_migrations` table stores the name or version of each migration that has already been applied.

Before running a migration, the system checks whether it already exists in that table.

If it has already been applied, it is skipped. If not, it is executed.

This keeps database setup idempotent and safe to run repeatedly.

## Interview explanation

A strong interview answer is:

> A migration is better than manually creating the table because it makes the database schema repeatable and controlled. Instead of relying on a developer's memory, the project stores the schema change in versioned SQL files that can be run in any environment. That keeps the database consistent, makes review easy, and avoids accidental duplicate table creation or drift between local and deployed environments.

## Practical takeaway

This project intentionally keeps the schema minimal and aligned with the current API contract:
- id
- name
- document_type
- version
- status
- created_at
- updated_at

The code is not introducing speculative future fields; it implements the current required record shape and keeps migration management reproducible.

No algorithm change was required here because this is a persistence and deployment discipline improvement, not a service or API redesign.
