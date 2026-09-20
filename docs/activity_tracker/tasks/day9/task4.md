# Day 9 / Task 4 — Safe query construction and allow-listing

## Objective

Continue the Day 8 security principle: values may be parameterized, but SQL identifiers must come from an allow-list.

## Safe parameterized values

For ordinary values, use parameter binding:

```sql
WHERE document_type = %s
WHERE status = %s
WHERE name ILIKE %s
LIMIT %s
OFFSET %s
```

The value is passed separately from the SQL text:

```python
cursor.execute(
    "SELECT * FROM documents WHERE document_type = %s",
    ("requirement",),
)
```

This protects user data from being treated as executable SQL.

## Unsafe pattern to avoid

This is the wrong approach:

```python
query = f"SELECT * FROM documents WHERE document_type = '{document_type}'"
```

This mixes user input into the SQL string and allows input to change the query meaning.

## SQL identifiers are different

Values are not the same as identifiers. Column names and sort keys are not ordinary values.

Examples:

```text
created_at
name
document_type
```

These are SQL identifiers, not data. They should not be inserted directly from user input into a SQL fragment.

## Allow-list approach

A controlled mapping keeps the query safe:

```python
ALLOWED_SORT_FIELDS = {
    "created_at": "created_at",
    "name": "name",
}
```

The flow is:

```text
user input
   ↓
validation
   ↓
allowlist
   ↓
safe SQL fragment
```

This is the core idea behind Day 8’s ordering requirement.

## Why this matters

The route may accept `sort_by=created_at` or `sort_by=name`, but it must not accept arbitrary text and place it directly into:

```sql
ORDER BY <user_input>
```

That would create a risk because the SQL identifier is not being treated like a value. It is being treated like a column name and must be controlled.

## Safe pattern in code

```python
allowed_sort_fields = {
    "created_at": "created_at",
    "name": "name",
}

sort_field = allowed_sort_fields.get(user_input)
if sort_field is None:
    raise ValueError("Unsupported sort field")
```

Then:

```python
query = f"SELECT * FROM documents ORDER BY {sort_field} DESC"
```

This is safe because the value is explicitly selected from a known mapping. The user input is not being directly interpolated into the SQL string.

## Keep the Day 8 security model

The Day 8 project explicitly required:

- value parameterization for filter values
- allow-listing for sort columns
- validation before database access

This should not be weakened later. The query specification pattern does not remove the need for safe SQL construction. It only organizes the request shape more cleanly.

## Relationship to query specification

The query specification may contain the sort field as a value:

```python
DocumentQuery(
    sort_field="created_at",
    sort_order="desc",
)
```

The repository still must enforce the allow-list before using `sort_field` in SQL:

```python
safe_sort_field = ALLOWED_SORT_FIELDS.get(query.sort_field)
if safe_sort_field is None:
    raise ValueError("Unsupported sort field")
```

The object does not remove the need for validation; it makes the same security model easier to reason about.

## Key takeaway

- value parameters should be bound as `%s`
- SQL identifiers must come from a fixed allow-list
- the router and service may validate and shape the request
- the repository must still enforce the security boundary before constructing SQL

This preserves the Day 8 protective design while allowing a cleaner query abstraction.
