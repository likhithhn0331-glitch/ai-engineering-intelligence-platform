# Day 8 / Task 10 — Add filtering

## Objective

Add one meaningful filter based on the existing document model:

```text
GET /documents?document_type=requirement
```

This filter narrows the collection to documents whose `document_type` exactly matches `requirement`.

## SQL representation

The repository expresses the filter with a parameterized condition:

```sql
SELECT id, name, document_type, version, status
FROM documents
WHERE document_type = %s
ORDER BY created_at ASC, id ASC;
```

The value `requirement` is supplied separately to psycopg. It is not inserted into the SQL string.

## Combining with pagination

Filtering and pagination work together:

```text
GET /documents?document_type=requirement&limit=20&offset=0
```

Conceptually:

```sql
SELECT id, name, document_type, version, status
FROM documents
WHERE document_type = %s
ORDER BY created_at ASC, id ASC
LIMIT %s
OFFSET %s;
```

The logical order is:

1. select rows from `documents`
2. keep only matching document types
3. order the matching rows
4. skip the requested offset
5. return up to the requested limit

The page is therefore page two of the filtered requirements, not page two of all documents.

## Why one filter is enough

Day 8 is about introducing a clear query boundary, not adding an uncontrolled search language. One well-designed filter demonstrates:

- query parameters at the API boundary
- service forwarding
- repository-owned SQL
- parameterized values
- database-side filtering

Additional filters can be added later when a real product requirement justifies them.

The project also supports `status` and `name_contains` from the broader query implementation, but `document_type` is the core filter for this task.

## Filtering in PostgreSQL

Filtering in SQL is preferable to loading every row and filtering in Python:

```python
# Avoid this for the PostgreSQL path.
all_documents = repository.list_all_documents()
requirements = [
    document for document in all_documents
    if document.document_type == "requirement"
]
```

Database-side filtering reduces rows transferred to the application and reduces application memory and processing work. PostgreSQL can also use suitable indexes as the table grows.

## Implementation status

`document_type` filtering is already implemented in `GET /documents` and in the repository’s PostgreSQL query path. The API and integration tests cover filtered collection behavior.

No code changes were needed for this task.
