# Day 9 / Task 2 — Introduce the concept of a query specification

## Objective

The repository should not grow into a method-per-combination API. Instead, represent a query as structured data.

Conceptually:

```text
DocumentQuery
    document_type
    status
    limit
    offset
    sort_field
    sort_order
```

This object captures a full query request as one value, which the repository then translates into SQL.

## Why this is better than many repository methods

A repository that exposes many specialized methods creates combinatorial growth:

```python
get_all_documents()
get_documents_by_type()
get_documents_paginated()
get_documents_by_type_paginated()
get_documents_sorted()
get_documents_by_type_sorted()
get_documents_by_type_sorted_paginated()
```

The number of methods grows very quickly as new filters, sorting options, or pagination controls are added.

A query specification solves this by collecting the request into one structure. The repository still has one primary read method, but it receives all of the query options in one object.

## Conceptual flow

```text
Router
   ↓
Query parameters
   ↓
Service
   ↓
DocumentQuery
   ↓
Repository
   ↓
SQL
```

This is the important design idea:

- the HTTP layer parses parameters
- the service validates and composes a query object
- the repository interprets the query object and writes SQL

The repository method may look like this:

```python
def list_documents(self, query: DocumentQuery):
    ...
```

instead of:

```python
def get_documents_by_type_sorted_paginated(type_, sort_field, sort_order, limit, offset):
    ...
```

## The query specification shape

A minimal query object could be:

```python
class DocumentQuery:
    def __init__(
        self,
        document_type=None,
        status=None,
        limit=None,
        offset=0,
        sort_field="created_at",
        sort_order="asc",
    ):
        self.document_type = document_type
        self.status = status
        self.limit = limit
        self.offset = offset
        self.sort_field = sort_field
        self.sort_order = sort_order
```

This object is not a database record. It is a request descriptor for a read operation.

A more sophisticated version may separate concerns into nested objects:

```python
class DocumentFilters:
    document_type = None
    status = None

class Pagination:
    limit = 20
    offset = 0

class Sorting:
    field = "created_at"
    direction = "desc"

class DocumentQuery:
    filters = DocumentFilters()
    sorting = Sorting()
    pagination = Pagination()
```

Either style is acceptable. The important idea is the same: represent the query as structured data, not as a growing list of specialized repository methods.

## How the service uses it

The service can translate HTTP parameters into a `DocumentQuery` object:

```python
query = DocumentQuery(
    document_type="requirement",
    status="created",
    limit=20,
    offset=40,
    sort_field="created_at",
    sort_order="desc",
)
```

Then it passes the object to the repository:

```python
return self.document_repository.list_documents(query)
```

This keeps the repository contract stable even when the query dimensions expand.

## How the repository uses it

The repository receives a structured query and translates it into SQL:

```python
conditions = []
values = []

if query.document_type is not None:
    conditions.append("document_type = %s")
    values.append(query.document_type)

if query.status is not None:
    conditions.append("status = %s")
    values.append(query.status)

where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

query_sql = (
    "SELECT id, name, document_type, version, status "
    f"FROM documents{where_clause} "
    f"ORDER BY {query.sort_field} {query.sort_order.upper()}, id ASC"
)

if query.limit is not None:
    query_sql += " LIMIT %s OFFSET %s"
    values.extend([query.limit, query.offset])
elif query.offset:
    query_sql += " OFFSET %s"
    values.append(query.offset)
```

This is the same logic as the Day 8 implementation, except that it is expressed as a single query specification instead of a long list of separate method parameters.

## Why this is a cleaner abstraction

Using a query object gives the system a few practical benefits:

- one repository read method for many valid queries
- clearer request semantics
- easier testing of different query scenarios
- easier future extension without creating methods by combinatorial explosion
- a cleaner separation between API input and SQL generation

The query object becomes the contract for a read operation.

## Relationship to the existing architecture

The current implementation already has the right layering:

```text
Router -> Service -> Repository -> PostgreSQL
```

The query specification simply makes the handoff between service and repository more explicit and less fragile.

Instead of passing a huge list of independent parameters, the service can pass one structured request object.

This does not remove the layered architecture. It strengthens it.

## Interview insight

This is an interview-friendly answer because it demonstrates:

- understanding of code growth
- recognition of repeated query combinations
- ability to abstract a request object
- preservation of clean layering

In other words, it is not just “add another filter.” It is “recognize that filter, sort, and pagination are a single query concern that should be represented as structured data.”

## Key takeaway

Represent the query as structured data rather than as a separate repository method for every combination.

The repository should receive a `DocumentQuery` and transform that object into SQL. That keeps the architecture scalable and preserves the separation between HTTP, service logic, and persistence.
