# Day 9 / Task 18 — End-to-end request flow and interview questions

## Objective

Prepare a strong, interview-ready explanation of the request path for `GET /documents` and the main failure/validation scenarios.

This is the final Day 9 conceptual checkpoint: you should be able to walk through the full path from HTTP request to PostgreSQL and back, explain failure handling, and explain how the design avoids repository method explosion.

## Walk-through: GET /documents from request to PostgreSQL

A clear answer should look like this:

HTTP Request
    ↓
FastAPI Router
    ↓
Pydantic validation
    ↓
DocumentQuery
    ↓
DocumentService
    ↓
DocumentRepository
    ↓
Validated query construction
    ↓
Parameterized SQL
    ↓
PostgreSQL
    ↓
Rows
    ↓
Domain/API representation
    ↓
HTTP response

## Explanation

### 1. HTTP request

The client sends a request such as:

- GET /documents
- GET /documents?limit=20&offset=0
- GET /documents?document_type=requirement
- GET /documents?sort=created_at&order=desc

These are raw HTTP query parameters.

### 2. FastAPI router

The router receives the request and extracts the HTTP values.

The router should not perform database work directly.

Its job is to parse the request and pass the data into the service layer.

### 3. Pydantic validation

If the project uses Pydantic models or request parameter validation, these values are checked for shape and constraints.

Examples:

- limit must be an integer
- offset must be non-negative
- sort field must be known
- order must be allowed (asc/desc)

This ensures invalid data is rejected before deeper layers execute.

### 4. DocumentQuery

The service or route can convert the validated values into a structured query object, conceptually:

DocumentQuery
- document_type
- status
- limit
- offset
- sort_field
- sort_order

This is a clean representation of the read intent.

### 5. DocumentService

The service owns orchestration and business validation.

It decides whether the query is acceptable and whether it should be passed down unchanged or normalized.

It should not build raw SQL strings.

### 6. DocumentRepository

The repository is the database boundary.

It is responsible for:

- composing the SQL query
- binding parameters safely
- running the query against PostgreSQL
- mapping rows back to application objects

This is where the actual database logic lives.

### 7. Validated query construction

The repository translates the DocumentQuery into a SQL statement with logic for:

- filtering
- ordering
- pagination
- safe parameter binding

Examples:

- WHERE document_type = %s
- ORDER BY created_at DESC
- LIMIT %s OFFSET %s

The construction uses validated values, not arbitrary concatenation.

### 8. Parameterized SQL

This is a mandatory security and correctness principle.

Values are provided as bind parameters rather than string-concatenated into the SQL statement.

This prevents SQL injection and keeps the query code robust.

### 9. PostgreSQL

PostgreSQL executes the query and returns rows.

At this point, the database is doing the actual filtering, ordering, and limiting work.

### 10. Rows

The returned rows are raw database results.

They may be tuples or dictionaries depending on the driver.

### 11. Domain/API representation

The repository maps database rows into the application’s domain or API representation.

This can include:

- converting DB fields to API-friendly names
- adding required metadata
- returning exactly the structure expected by the API layer

### 12. HTTP response

The service or route sends the final list of documents back as an HTTP response.

At this point the response is shaped for clients and the request is complete.

## What happens if the database fails?

This is one of the most important reliability questions.

If PostgreSQL is unavailable or the repository throws an exception:

- the repository fails
- the service cannot produce a trustworthy result
- the API should return a real error response
- the application should not return a fake success payload

Example of wrong behavior:

{
  "status": "success"
}

This is incorrect because persistence failed.

The system should fail honestly with a proper error code and message, such as a 503 or centralized API error response.

## What happens if the client sends an invalid sort field?

The request should be rejected before the database query is executed.

Example:

GET /documents?sort=super_secret_field

The correct behavior is:

- router captures the raw query parameter
- service or validation layer checks it against an allowlist
- invalid values are rejected
- the request fails with a validation error

This protects against arbitrary SQL identifier injection.

The safe pattern is:

- allowlist sort fields
- map to trusted SQL column names
- never insert raw user input into ORDER BY

## How would you avoid creating 20 repository methods for every filter/sort/pagination combination?

Use a query object or a single query specification.

Instead of writing a new repository method for each combination, define a structured query representation such as:

DocumentQuery
- document_type
- status
- limit
- offset
- sort_field
- sort_order

Then:

- the router parses HTTP params
- the service validates them
- the service builds a DocumentQuery
- the repository interprets that object and builds one flexible SQL query

This avoids combinatorial method explosion while still preserving clear boundaries.

## Why this matters in interviews

This is the kind of answer that demonstrates strong backend engineering instincts:

- you know the request flow
- you know the boundary between router/service/repository
- you understand validation and security
- you understand how to fail honestly when persistence breaks
- you know how to avoid brittle, repetitive repository APIs

## Final takeaway

The strongest answer is not just “it works.”

The strongest answer is:

- the architecture is layered
- validation happens before database execution
- query construction is centralized in the repository
- SQL is parameterized and safe
- failure is represented honestly
- the design scales without becoming combinatorial sprawl
