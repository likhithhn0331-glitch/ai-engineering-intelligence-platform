# PostgreSQL Deep Revision

## 3.1 Relational Database Fundamentals

### Database
A database is a logical collection of structured data managed by a database system. In this project, PostgreSQL is the database system managing the application data.

### Table
A table is a structured collection of rows and columns. In this project, the key table is:

```sql
documents
```

The table stores document metadata.

### Row
A row is a single record in a table. In this project, one row represents one document.

### Column
A column is one attribute of the record. The current document table includes:

- id
- name
- document_type
- version
- status
- created_at
- updated_at

## 3.2 Primary Key

Each document needs a unique identifier, and the current schema uses:

```sql
id VARCHAR(255) PRIMARY KEY
```

Why it matters:

- uniqueness: no two rows can share the same ID
- identity: the row can be referred to reliably
- lookup: the system can fetch a document by ID quickly and precisely
- indexing: the database can build the index for the primary key automatically
- constraint enforcement: the database guarantees the ID is valid and unique

Why not use the document name as the primary key?

- names are not guaranteed to be unique
- names can change over time
- names are business data, not stable identity

## 3.3 NOT NULL

The schema includes fields that should always exist for a valid document:

```sql
name VARCHAR(255) NOT NULL
document_type VARCHAR(255) NOT NULL
version VARCHAR(255) NOT NULL
status VARCHAR(255) NOT NULL
```

Why these should be `NOT NULL`:

- The application expects a document to have a name
- The document type is required to classify the resource
- The version is required to know the document revision state
- The status is required for the document lifecycle

If any of these were missing, the record would not represent a valid document in the current application.

## 3.4 DEFAULT

The schema has default values for fields that should be populated automatically by the database:

```sql
status VARCHAR(255) NOT NULL DEFAULT 'created'
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

Why defaults matter:

- status defaults to `created` when the application does not explicitly set it
- created_at is set automatically when the row is inserted
- updated_at is set automatically when the row is created and later updated

This keeps the database layer responsible for some correctness guarantees instead of making every application call remember to set those values.

## 3.5 SQL CRUD Mapping

The repository follows the same CRUD pattern as the database operations below.

### INSERT

```sql
INSERT INTO documents (id, name, document_type, version, status, created_at, updated_at)
VALUES ('doc-001', 'engine-requirement', 'requirement', '1.0', 'created', NOW(), NOW());
```

### SELECT

```sql
SELECT *
FROM documents;
```

### SELECT by ID

```sql
SELECT *
FROM documents
WHERE id = 'doc-001';
```

### UPDATE

```sql
UPDATE documents
SET version = '2.0', updated_at = NOW()
WHERE id = 'doc-001';
```

### DELETE

```sql
DELETE FROM documents
WHERE id = 'doc-001';
```

## Repository mapping to SQL

This is the implementation logic the project follows:

- `DocumentRepository.create_document()` → `INSERT`
- `DocumentRepository.list_documents()` → `SELECT * FROM documents`
- `DocumentRepository.get_document()` → `SELECT ... WHERE id = ...`
- `DocumentRepository.update_document()` → `UPDATE documents SET ... WHERE id = ...`
- `DocumentRepository.delete_document()` → `DELETE FROM documents WHERE id = ...`

This is the same CRUD mapping the system is expected to explain in an interview.

## Interview explanation summary

The project uses a PostgreSQL relational model with a single documents table. Each row represents one document. The primary key is the document ID, which provides uniqueness and reliable lookup. Core fields are required, and timestamps/status default values are enforced at the database layer so invalid data is less likely to be inserted. The repository translates the application operations directly into SQL CRUD commands, which is the correct persistence pattern for a relational database.
