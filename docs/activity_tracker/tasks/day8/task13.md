# Day 8 / Task 13 — Do not put SQL in the router

## Anti-pattern

Do not turn a route into a database layer:

```python
@app.get("/documents")
def get_documents():
    cursor.execute("SELECT * FROM documents")
    return cursor.fetchall()
```

This combines HTTP handling, SQL, connection management, raw database records, and response behavior in one function.

## Correct implementation

The route should only receive HTTP input and delegate:

```python
@router.get("/documents", response_model=list[DocumentResponse])
async def list_documents(
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: DocumentService = Depends(get_document_service),
):
    documents = service.list_documents(limit=limit, offset=offset)
    return [to_response(document) for document in documents]
```

The service forwards the request:

```python
def list_documents(self, limit=None, offset=0):
    return self.document_repository.list_documents(
        limit=limit,
        offset=offset,
    )
```

The repository owns SQL:

```python
query = """
    SELECT id, name, document_type, version, status
    FROM documents
    ORDER BY created_at ASC, id ASC
    LIMIT %s OFFSET %s
"""
cursor.execute(query, (limit, offset))
```

## Benefits

Keeping SQL out of the router provides:

- one database boundary
- centralized transaction and connection lifecycle
- reusable repository methods
- simpler route tests
- clearer dependency direction
- easier replacement of PostgreSQL or test doubles
- lower risk of SQL injection caused by ad hoc string construction

## Verification

The Day 8 query tests exercise the route through HTTP, but the route does not need to know how PostgreSQL performs the query. PostgreSQL integration tests verify the repository path against the real database.

## Key takeaway

The router expresses “what the client requested.” The repository decides “how PostgreSQL answers it.” Mixing these responsibilities would undo the separation established during CRUD implementation.
