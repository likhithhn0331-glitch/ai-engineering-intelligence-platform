# Day 9 / Task 3 — Important architecture boundary

## Objective

The architecture established on Day 8 must remain intact.

```text
Router
   ↓
Service
   ↓
Repository
   ↓
PostgreSQL
```

The boundaries remain:

### Router owns HTTP concerns

- query parameters from the request
- validation of input shapes and ranges
- HTTP response mapping
- status codes and response serialization

This layer is still the HTTP adapter. It translates network input to application calls.

### Service owns business concerns

- business validation
- orchestration of the read workflow
- constructing the query specification from validated HTTP input
- delegating to the repository

The service is not responsible for SQL generation. It is responsible for ensuring the domain request is valid.

### Repository owns data access concerns

- SQL strings
- query construction
- database execution
- binding values as parameters
- record mapping into domain objects

This is the persistence boundary. It is where the object model becomes SQL and the database rows become domain objects again.

## Why this matters

If the router starts building SQL, the system violates the layering contract. The route becomes a database layer, and the repository loses its meaning.

If the service starts writing SQL, the service becomes tightly coupled to PostgreSQL details and loses focus on business logic.

If the repository starts handling HTTP concerns, it becomes a hybrid layer and becomes harder to test and maintain.

## Architectural boundary in practice

The current request flow should look like:

```text
HTTP request
   ↓
FastAPI route
   ↓
Query parameters and validation
   ↓
Service validates the business intent
   ↓
DocumentQuery object
   ↓
Repository SQL generation
   ↓
PostgreSQL execution
   ↓
Domain objects
   ↓
Response model
```

In other words, the route still owns the HTTP contract, the service still owns business intent, and the repository still owns persistence and SQL.

## Why this boundary is desirable

This boundary gives the project several practical advantages:

- cleaner testing
- easier replacement of persistence strategies
- more explicit responsibilities
- reduced accidental coupling
- safer query design
- easier maintenance as the application grows

## Key takeaway

The Day 8 query architecture should remain layered. HTTP concerns stay in the router, business rules stay in the service, and SQL stays in the repository.
