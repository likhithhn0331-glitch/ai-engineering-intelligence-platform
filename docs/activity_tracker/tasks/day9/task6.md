# Day 9 / Task 6 — Introduce a query representation only if it improves the current code

## Objective

A query specification is useful when the repository method signature becomes crowded or the code starts accumulating special-case methods.

The current implementation already has a single repository method:

```python
def list_documents(
    self,
    document_type=None,
    status=None,
    name_contains=None,
    limit=None,
    offset=0,
    sort_by="created_at",
    sort_order="asc",
):
```

This is not yet a problem. It is a clean, single-entry query API.

## When a query object makes sense

A query object becomes useful when the query dimensions are repeated or become conceptually large. For example, if the repository moves further toward a richer query language, a request object can make the API easier to reason about.

Conceptually:

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

This object acts as a request specification rather than a storage record.

## How it fits the project

The service can turn HTTP parameters into a `DocumentQuery` object:

```python
query = DocumentQuery(
    document_type=document_type,
    status=status_filter,
    limit=limit,
    offset=offset,
    sort_field=sort_by,
    sort_order=sort_order,
)
```

Then the repository consumes it:

```python
return self.document_repository.list_documents(query)
```

This preserves the layered flow:

```text
HTTP
  ↓
Router
  ↓
Service
  ↓
DocumentQuery
  ↓
Repository
  ↓
SQL
```

This is the cleanest abstraction when the query grows beyond a few parameters.

## Why not do it blindly

A query object should not be added just because it looks elegant in theory. A repository method with a handful of arguments is still a perfectly valid abstraction when the concern is still clear.

The current code already shows a good design: the method is explicit, bounded, and connected to the HTTP contract. Introducing a new object in the current code would be a refactor for its own sake unless it improves clarity or future maintainability.

## Pydantic/model conventions

The project already uses Pydantic models in `src/models/pydantic_model.py`.

For a query object, the project should prefer the existing conventions rather than introducing a completely different framework abstraction.

A clean fit would be a lightweight Pydantic model such as:

```python
from pydantic import BaseModel

class DocumentQuery(BaseModel):
    document_type: str | None = None
    status: str | None = None
    limit: int | None = None
    offset: int = 0
    sort_field: str = "created_at"
    sort_order: str = "asc"
```

This matches the project’s existing modeling style and keeps the request shape explicit.

The advantage is the same as a plain Python class, but it also benefits from validation rules already used in the project.

## Recommendation for this codebase

The current implementation is already clean enough that a query object is optional rather than required.

The best practice is:

- do not introduce a new abstraction while the current repository method remains easy to understand
- add a `DocumentQuery` model only if the project adds more query dimensions or if the service-to-repository handoff becomes harder to manage

This is the right engineering tradeoff: improve the repository boundary only where the implementation actually benefits.

## Key takeaway

A query representation is a useful abstraction, but not a mandatory one. The current Day 8 implementation is already structured well enough that the project should avoid unnecessary refactoring.
