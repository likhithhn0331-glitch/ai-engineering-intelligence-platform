# Day 9 / Task 1 — Combinatorial query growth and the need for a better abstraction

## Objective

Imagine a repository with many specialized query methods:

```python
get_all_documents()
get_documents_by_type()
get_documents_paginated()
get_documents_by_type_paginated()
get_documents_sorted()
get_documents_by_type_sorted()
get_documents_by_type_sorted_paginated()
```

At first this looks reasonable. Each method appears to satisfy one business request. But over time the number of combinations grows quickly.

This is a classic abstraction problem: the repository is turning many valid combinations of query concerns into separate methods.

## Why this grows badly

The list above is already mixing several independent concerns:

- filtering
- sorting
- pagination
- projection or selection
- maybe default behavior

As soon as the product adds more query dimensions, the number of methods grows combinatorially.

For example, if the system adds:

- `status`
- `name_contains`
- `created_after`
- `created_before`
- `version`
- `page size`
- `sort direction`

then the method list explodes. New combinations do not reflect new domain concepts; they reflect the Cartesian product of already-known capabilities.

The problem is not that each method is individually wrong. The problem is that the API surface is expressing every useful combination as a separate function.

## The real design issue

The repository is trying to encode every valid combination of query parameters as one dedicated method. This causes:

- code duplication
- a bloated repository interface
- inconsistent behavior between query combinations
- a harder time testing every path
- high maintenance cost when business rules evolve

The architecture becomes less scalable because the repository is doing ad hoc query composition instead of representing a query as a single object or data structure.

## Better abstraction: query criteria / query options

Instead of creating a dedicated method for each combination, define a single abstraction that represents the query request:

```python
class DocumentQuery:
    def __init__(
        self,
        document_type=None,
        status=None,
        name_contains=None,
        sort_by="created_at",
        sort_order="asc",
        limit=None,
        offset=0,
    ):
        self.document_type = document_type
        self.status = status
        self.name_contains = name_contains
        self.sort_by = sort_by
        self.sort_order = sort_order
        self.limit = limit
        self.offset = offset
```

Then the repository method becomes more general:

```python
def list_documents(self, query: DocumentQuery):
    ...
```

This is a much better abstraction because the query object captures the actual request parameters in one place.

It lets the repository handle:

- filter conditions
- ordering
- limit and offset
- optional defaults
- validation of the resolved query

The caller can compose one query object without creating a new repository method every time.

## Why this is a better design

This approach preserves separation of concerns:

- router parses HTTP parameters
- service constructs a query object
- repository translates the object into SQL

The repository can now support many valid combinations without a combinatorial explosion in the public API.

### Example

```python
query = DocumentQuery(
    document_type="requirement",
    status="created",
    sort_by="created_at",
    sort_order="desc",
    limit=20,
    offset=40,
)

results = repo.list_documents(query)
```

This encodes one request: “return created requirement documents ordered by created_at descending, page 3.”

The same repository method is reused for all valid combinations instead of creating a new repository function for every combination.

## Alternative abstraction: a filter/options object

Another common variation is a generic options object or criteria object:

```python
class DocumentFilters:
    document_type = None
    status = None
    name_contains = None
```

and a separate pagination/sort configuration:

```python
class SortOptions:
    field = "created_at"
    direction = "desc"

class PaginationOptions:
    limit = 20
    offset = 40
```

Then the repository method looks like:

```python
repo.list_documents(filters, sort_options, pagination)
```

This is especially useful when query concerns are distinct concepts that may be reused independently.

The key idea is the same: one cohesive request object or set of options, not one repository method per combination.

## Why this matters for interviews

This is a valuable backend interview topic because it shows the difference between:

- “I can add one more special-case method” and
- “I recognize a query composition problem and abstract the request itself.”

Good engineering design is not simply adding methods until every call works. It is understanding how to unify repeated dimensions of behavior into one coherent abstraction.

## Relation to Day 8 implementation

The repository already partially follows this direction: it accepts multiple query inputs and builds a single SQL query from them.

For example, the repository method is conceptually:

```python
list_documents(
    document_type=None,
    status=None,
    name_contains=None,
    limit=None,
    offset=0,
    sort_by="created_at",
    sort_order="asc",
)
```

This is already a step toward the better abstraction. The repository is not exposing a separate method for every combination; it is accepting a set of query concerns and translating them into one SQL statement.

The next step, if the codebase grows, is to formalize that argument set into a dedicated query object so that the API surface remains stable while the request shape becomes more explicit and more reusable.

## What not to do

Do not create a method for every combination such as:

```python
get_documents_by_type_paginated_sorted_by_name_desc()
```

This becomes unmaintainable very quickly.

Instead, represent the request as a query specification and let one repository method apply it.

## Good mental model

Think of the repository method as taking a request description, not a collection of hard-coded special cases.

The query object or options struct is the request description:

```python
DocumentQuery(
    filters=..., 
    sort=..., 
    pagination=...
)
```

Then the repository transforms that request into SQL.

## Key takeaway

The repository should not grow into an ever-increasing list of combinatorial query methods. The better abstraction is a single query object or option set that groups together:

- filter criteria
- ordering criteria
- pagination settings

This gives the system one clear query entry point while preserving a clean separation between router, service, and repository responsibilities.
