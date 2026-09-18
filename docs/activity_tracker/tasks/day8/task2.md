# Day 8 / Task 2 — SQL filtering with `WHERE`

## Task

Study how PostgreSQL narrows a result set before the rows are returned to the application.

The basic query is:

```sql
SELECT *
FROM documents
WHERE document_type = 'requirement';
```

The next condition is:

```sql
SELECT *
FROM documents
WHERE status = 'created';
```

Multiple conditions can be combined:

```sql
SELECT *
FROM documents
WHERE document_type = 'requirement'
  AND status = 'created';
```

The key idea is:

> `WHERE` filters rows before the result is returned.

## What `WHERE` does

`SELECT` describes the columns to return. `FROM` identifies the table to read. `WHERE` applies a condition to each candidate row and keeps only rows for which the condition evaluates to true.

For example, assume `documents` contains:

| id | name | document_type | status |
|---|---|---|---|
| doc-001 | Engine Requirements | requirement | created |
| doc-002 | System Design | design | created |
| doc-003 | Test Plan | test | archived |
| doc-004 | API Requirements | requirement | archived |

This query:

```sql
SELECT *
FROM documents
WHERE document_type = 'requirement';
```

returns `doc-001` and `doc-004`. The `design` and `test` rows are removed from the result by the database before PostgreSQL sends the result set to the application.

The filter does not modify or delete rows. It only controls which rows are visible in this particular query result.

## One condition

Filtering by document type:

```sql
SELECT id, name, document_type, version, status
FROM documents
WHERE document_type = 'requirement';
```

Filtering by status:

```sql
SELECT id, name, document_type, version, status
FROM documents
WHERE status = 'created';
```

The comparison operator `=` means exact equality. A row with `document_type = 'Requirement'` is not necessarily equal to `'requirement'` because ordinary PostgreSQL text comparisons are case-sensitive.

The application currently exposes these filters through the collection endpoint:

```text
GET /documents?document_type=requirement
GET /documents?status=created
```

The API passes the values as parameters. It does not concatenate request text into SQL.

## Multiple conditions with `AND`

`AND` requires every condition to be true:

```sql
SELECT *
FROM documents
WHERE document_type = 'requirement'
  AND status = 'created';
```

This is an intersection. A row must be both:

1. a requirement; and
2. in the created state.

Using the sample data, only `doc-001` matches. `doc-004` has the correct document type but the wrong status, so it is excluded.

The repository creates the equivalent query when both API filters are supplied:

```text
GET /documents?document_type=requirement&status=created
```

Conceptually, the repository generates:

```sql
SELECT id, name, document_type, version, status
FROM documents
WHERE document_type = %s
  AND status = %s
ORDER BY created_at ASC, id ASC;
```

The values are bound separately:

```python
cursor.execute(query, ("requirement", "created"))
```

This preserves the filtering behavior while preventing the request from becoming executable SQL.

## How this maps to the application

The filtering request follows the established architecture:

```text
HTTP query string
        ↓
FastAPI query parameter parsing
        ↓
DocumentService.list_documents()
        ↓
DocumentRepository.list_documents()
        ↓
PostgreSQL SELECT ... WHERE ...
        ↓
filtered Document objects
        ↓
DocumentResponse list
```

### API layer

`src/api/document_routes.py` accepts:

- `document_type`
- `status`

The route does not write SQL. It passes the filter intent to the service.

### Service layer

`src/services/document_service.py` forwards the filters to the repository. The service remains independent of PostgreSQL syntax.

### Repository layer

`src/repositories/document_repository.py` translates the filter intent into SQL conditions:

```python
conditions.append("document_type = %s")
values.append(document_type)

conditions.append("status = %s")
values.append(status)
```

The condition text is controlled by the application, while the values are supplied through psycopg parameter binding.

### Database layer

`database_connection()` opens the PostgreSQL connection, the repository executes the query, and the connection is closed after the operation. PostgreSQL performs the filtering and returns only matching rows.

## Filtering before returning results

The important performance distinction is between database filtering and application filtering.

Database filtering:

```sql
SELECT *
FROM documents
WHERE document_type = 'requirement';
```

PostgreSQL examines the table, applies the condition, and returns only matching rows.

Application filtering would look like:

```python
all_documents = repository.list_all_documents()
requirements = [
    document for document in all_documents
    if document.document_type == "requirement"
]
```

Application filtering requires the database to send every row first. That increases:

- database-to-application network traffic
- application memory usage
- Python processing time
- latency for large tables

The repository implementation uses SQL filtering for the PostgreSQL path, so filtering occurs where the data is stored.

## Combining the current filters

The query path can combine the document type and status filters with the existing name search:

```text
GET /documents?document_type=requirement&status=created&name_contains=api
```

The resulting SQL shape is:

```sql
SELECT id, name, document_type, version, status
FROM documents
WHERE document_type = %s
  AND status = %s
  AND name ILIKE %s
ORDER BY created_at ASC, id ASC;
```

Every supplied filter adds another `AND` condition. If a filter is omitted, its condition is omitted. This avoids treating a missing filter as a special database value.

The query can then add ordering and pagination:

```sql
...
ORDER BY created_at ASC, id ASC
LIMIT %s OFFSET %s;
```

Filtering logically narrows the candidate set first; pagination applies to the ordered matching result.

## `AND` versus `OR`

`AND` narrows the result:

```sql
WHERE document_type = 'requirement'
  AND status = 'created'
```

`OR` broadens the result:

```sql
WHERE document_type = 'requirement'
   OR document_type = 'design'
```

The current API uses `AND` semantics when several filters are supplied. That is appropriate for search criteria such as “created requirements.” An `OR` search would be a different API behavior and should be designed explicitly rather than inferred from multiple query parameters.

When `AND` and `OR` are mixed, parentheses should make intent explicit:

```sql
WHERE status = 'created'
  AND (document_type = 'requirement' OR document_type = 'design');
```

Without parentheses, SQL operator precedence can produce a result different from the intended business rule.

## `NULL` and filtering

`NULL` means an unknown or absent value; it is not equal to an empty string.

This does not match rows where `document_type` is `NULL`:

```sql
WHERE document_type = NULL;
```

Use `IS NULL` instead:

```sql
WHERE document_type IS NULL;
```

The current schema marks `document_type`, `status`, and the other document fields as `NOT NULL`, so the normal document queries do not need `IS NULL`. Understanding the distinction is still important when querying other tables or future nullable columns.

## Parameterization and safety

Unsafe SQL construction would place request input directly into the query string:

```python
# Do not do this with request input.
query = f"SELECT * FROM documents WHERE status = '{status}'"
```

The safe form uses a placeholder:

```python
query = "SELECT * FROM documents WHERE status = %s"
cursor.execute(query, (status,))
```

The database driver sends the SQL structure and the value separately. A value such as `created' OR '1'='1` remains a value to compare, not a new SQL expression.

This is why filtering belongs in the repository: it centralizes the SQL boundary and makes parameterized execution the default implementation path.

## Query planning and indexes

PostgreSQL may use a sequential scan or an index scan to evaluate a `WHERE` clause. The planner chooses based on table statistics, estimated selectivity, available indexes, and query cost.

For a growing table, a useful index could be:

```sql
CREATE INDEX documents_type_status_idx
ON documents (document_type, status);
```

An index is not required for the query to be correct. It is a performance structure that may help PostgreSQL find matching rows faster. Index design should be based on measured access patterns and `EXPLAIN`, not added automatically for every column.

To inspect a plan:

```sql
EXPLAIN
SELECT id, name, document_type, version, status
FROM documents
WHERE document_type = 'requirement'
  AND status = 'created';
```

`EXPLAIN ANALYZE` executes the query while collecting runtime statistics, so it should be used carefully on write statements or expensive production queries.

## Validation and evidence

The existing API test verifies that `document_type` filtering is applied through `GET /documents`.

The PostgreSQL integration test verifies a live database query combining:

- `document_type = 'requirement'`
- `name_contains` matching
- sorting
- `LIMIT`
- `OFFSET`

The repository already supports `status` as another exact `WHERE` condition, so no new production code was required for this task. The SQL filtering capability was introduced in the Day 8 query implementation and is documented here as a focused concept.

Run the tests with:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest -q tests\test_postgres_integration.py
```

## Key takeaway

`WHERE` is the database-side selection step:

```text
FROM documents
        ↓
candidate rows
        ↓
WHERE document_type = 'requirement'
  AND status = 'created'
        ↓
matching rows only
```

The application should express query intent through the service and repository boundaries, while PostgreSQL performs the filtering before returning the result. This preserves the API contract and keeps data reduction close to the data source.
