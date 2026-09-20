# Day 9 / Task 17 — Interview review questions on query design, failures, and retries

## Objective

Review the most important backend interview questions raised in this day’s work.

These are not just theoretical points; they reflect the architecture and safety principles already established in the project.

## 11. Why shouldn't every filter combination become a repository method?

A repository should not explode into a large set of methods such as:

- get_documents_by_type()
- get_documents_paginated()
- get_documents_sorted()
- get_documents_by_type_paginated()
- get_documents_by_type_sorted_paginated()
- and so on

This creates combinatorial growth.

Why it is a problem:

- the repository becomes hard to maintain
- each new filter or sort adds more method variants
- the code repeats query logic across many methods
- the API contract and repository contract become harder to reason about

The better design is to represent the query as structured input and let the repository build one SQL query from that input.

This is the key reason behind the query object idea: one abstraction to support many combinations.

## 12. What is a query object?

A query object is a structured representation of a database read request.

Conceptually:

DocumentQuery
- document_type
- status
- limit
- offset
- sort_field
- sort_order

Instead of creating one repository method per combination, the service assembles a normalized query object and passes it to the repository.

Benefits:

- fewer repository methods
- easier to validate inputs centrally
- better consistency across filter and sort combinations
- easier to test

The query object is still just data. It is not a new database layer or a new router pattern. It is an internal representation of the request intent.

## 13. Where should query validation happen?

Validation should happen as early as possible, but in the correct layer.

The usual architecture is:

- router: HTTP parameter parsing and request shape validation
- service: business validation and orchestration
- repository: SQL generation and database execution

For the Day 8/Day 9 design:

- router accepts raw query strings
- service validates business meaning and constraints
- repository assumes the query is already valid

Examples:

- limit must be an integer ≥ 1
- offset must be an integer ≥ 0
- sort field must be in an allowlist
- document_type values should be constrained if necessary

This ensures invalid input is rejected before it reaches database execution.

## 14. Where should SQL construction happen?

SQL construction should happen in the repository.

That is where database concern belongs.

The repository is responsible for:

- building SQL strings
- binding parameters
- handling query composition
- mapping rows to domain objects

This keeps the router from turning into a database layer and keeps the service focused on orchestration and business rules.

The service should prepare the query intent; the repository should translate the intent into PostgreSQL-safe SQL.

## 15. Why should SQL remain outside the router?

Because the router should own HTTP concerns, not persistence concerns.

Bad example:

@app.get("/documents")
def get_documents():
    cursor.execute("SELECT ...")

This violates the layering contract.

Problems:

- router mixes HTTP and SQL concerns
- database logic becomes harder to test
- validation is harder to isolate
- security review becomes harder
- architecture becomes brittle

The correct flow is:

HTTP query params
    ↓
router
    ↓
service validation/orchestration
    ↓
repository
    ↓
SQL + PostgreSQL

This preserves the earlier architecture and makes the system maintainable.

## 16. How do you safely construct dynamic ORDER BY?

This is a critical backend security concept.

Never do this:

query = f"SELECT * FROM documents ORDER BY {sort_field}"

Because the user could supply arbitrary column names or SQL fragments.

Instead:

- validate user input against an allowlist
- map the allowed string to a trusted SQL identifier
- use a safe internal representation

Conceptually:

ALLOWED_SORT_FIELDS = {
    "created_at": "created_at",
    "name": "name",
}

Then:

user input
    ↓
validation
    ↓
allowlist
    ↓
safe SQL column

This is one of the clearest examples of why values and identifiers must be treated differently.

Values can be parameterized:

WHERE document_type = %s

But identifiers like column names cannot be safely inserted the same way; they must come from a controlled mapping.

## 17. What happens if PostgreSQL becomes unavailable?

The application must not pretend that the request succeeded.

If PostgreSQL is down:

- the repository throws a database exception or connection failure
- the service should propagate that failure
- the API must return an error response
- the application should not return a fake success payload

Example of the wrong behavior:

{
  "status": "success"
}

This is misleading because the data was never actually loaded.

The correct behavior is to surface a failure such as a 503 or a centralized error response.

This is essential for reliability and honesty in backend systems.

## 18. Why are database timeouts important?

A database request should not wait forever.

Without a timeout:

- a hung database connection can block the request thread
- the API can become unresponsive
- users may wait indefinitely for a response that never arrives
- operational incidents can cascade across services

Timeouts define a boundary:

request
    ↓
database operation
    ↓
timeout
    ↓
failure handling

This is a fundamental reliability concept. The application should fail quickly and intentionally rather than hanging indefinitely.

## 19. What is idempotency?

Idempotency means repeating the same operation has the same effect as doing it once.

Example:

DELETE /documents/{id}

If a client sends the same delete request twice because of a network issue, the outcome should be logically the same as a single delete if the system is designed that way.

The problem is that clients often retry after a connection failure and do not know whether the original request actually completed.

This is why idempotency matters in real APIs.

Idempotency is conceptual here; the project is not redesigning DELETE semantics, but the interview concept is important.

## 20. Why can retries create problems?

Retries can create duplicate work or unintended side effects.

Examples:

- a client retries a POST that already created a record
- a delete is retried after the first delete but before the client got the response
- a write operation is repeated and creates multiple entities

This means retries must be considered during API design.

Some operations are naturally idempotent (for example, a well-designed delete or a set-the-same-value operation), while others are not.

The key lesson is:

- a network failure does not guarantee the request did not happen
- retries can amplify non-idempotent behavior
- backend designs must account for eventual correctness and failure recovery

## Final review

The big theme across Day 9 is this:

- avoid combinatorial repository methods
- express the request as a query object
- keep validation in the correct layers
- keep SQL in the repository
- do not allow untrusted SQL identifiers
- fail honestly when PostgreSQL is unavailable
- respect timeouts
- think about idempotency and retried requests

These concepts are all core to production backend engineering.
