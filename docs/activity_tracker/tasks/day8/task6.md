# Day 8 / Task 6 — Parameterized SQL

## Task

Parameterized SQL is mandatory at the database boundary. Never build SQL by concatenating request data into a query string.

Unsafe example:

```python
query = f"SELECT * FROM documents WHERE name = '{name}'"
```

Safe conceptual form:

```python
cursor.execute(
    "SELECT * FROM documents WHERE name = %s",
    (name,),
)
```

The exact placeholder API depends on the PostgreSQL driver. This project uses psycopg, whose PostgreSQL placeholders are `%s`.

## Why string concatenation is dangerous

If request input is inserted directly into SQL text, the input can change the meaning of the query instead of remaining data.

For example, an attacker could submit a value containing SQL syntax:

```text
' OR '1'='1
```

With unsafe string construction, the resulting SQL might become logically equivalent to:

```sql
SELECT *
FROM documents
WHERE name = '' OR '1' = '1';
```

The condition is true for every row, so the query can return documents that were not intended to match. Other injection payloads can attempt to alter data or execute additional statements, depending on the driver and query context.

The root error is mixing two different things:

- SQL structure
- user-controlled data

## How parameterization works

The safe query keeps the SQL structure fixed:

```python
query = "SELECT id, name FROM documents WHERE name = %s"
cursor.execute(query, (name,))
```

The driver sends the value through its parameter mechanism and handles quoting and escaping according to PostgreSQL rules. A value containing quotes or SQL keywords remains a value compared with `name`; it does not become part of the SQL grammar.

The repository follows this pattern for filters:

```python
conditions.append("document_type = %s")
values.append(document_type)

conditions.append("status = %s")
values.append(status)

conditions.append("name ILIKE %s")
values.append(f"%{name_contains}%")
```

Then it executes:

```python
cursor.execute(query, tuple(values))
```

The condition templates are application-controlled. The filter values are parameters.

## What must be parameterized

Values must be parameters:

```sql
WHERE document_type = %s
WHERE status = %s
WHERE name ILIKE %s
LIMIT %s
OFFSET %s
```

This applies to strings, numbers, dates, IDs, search patterns, and values supplied by an HTTP client.

Do not manually add quotes around `%s`:

```python
# Incorrect
cursor.execute("WHERE name = '%s'", (name,))
```

Use the placeholder without SQL quotes:

```python
# Correct
cursor.execute("WHERE name = %s", (name,))
```

The driver handles the value representation.

## Identifiers are different

PostgreSQL parameters represent values, not SQL identifiers. This is not valid as a general way to choose a column:

```sql
ORDER BY %s
```

For dynamic identifiers such as a sort column, the application must use an allow-list. The repository maps known public names to known SQL identifiers:

```python
sort_columns = {
    "id": "id",
    "name": "name",
    "document_type": "document_type",
    "version": "version",
    "status": "status",
    "created_at": "created_at",
}
```

Only the selected value from this fixed mapping is placed into the query. The client cannot provide arbitrary SQL syntax as a column name.

The sort direction is handled the same way by accepting only `asc` or `desc` and converting it to the corresponding SQL keyword.

## Parameter order matters

The order of values must match the order of placeholders:

```python
query = """
    SELECT id, name
    FROM documents
    WHERE document_type = %s
      AND status = %s
"""
values = ("requirement", "created")
cursor.execute(query, values)
```

If the order is reversed, the query is still syntactically valid but produces incorrect results. Building `conditions` and `values` together helps preserve this correspondence.

## Parameterization and `ILIKE`

The repository uses a parameter for the complete search pattern:

```python
values.append(f"%{name_contains}%")
```

and SQL:

```sql
WHERE name ILIKE %s
```

This is safer than inserting the search text directly into:

```sql
WHERE name ILIKE '%request-text%'
```

The wildcard characters are part of the bound value. PostgreSQL still interprets them as pattern characters for `ILIKE`, while the request text remains data.

## Parameterization is not validation

Parameterization protects SQL structure, but it does not replace application validation.

The API separately validates:

- `limit` range
- `offset` range
- allowed sort fields
- allowed sort directions
- minimum search length

These controls serve different purposes:

- parameterization prevents SQL injection
- validation enforces the API contract
- authorization determines whether the caller may access the data
- business logic determines whether the query is meaningful

All are required at their appropriate boundaries.

## Query path in this project

```text
HTTP request data
        ↓
FastAPI validates query types and ranges
        ↓
DocumentService forwards intent
        ↓
DocumentRepository builds fixed SQL structure
        ↓
psycopg binds values to %s placeholders
        ↓
PostgreSQL executes SQL and treats values as data
```

This design keeps raw SQL in the repository and prevents route code from becoming a string-building database layer.

## Key takeaway

The rule is simple:

> Data should be supplied as parameters, not concatenated into SQL strings.

Parameterized SQL protects filter values. Allow-lists protect dynamic identifiers such as sort columns. Together they keep the PostgreSQL boundary explicit, safe, and testable.
