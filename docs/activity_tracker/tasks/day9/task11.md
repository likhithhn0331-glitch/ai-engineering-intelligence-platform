# Day 9 / Task 11 — Timeouts and external operations

## Objective

Understand why external operations should not wait indefinitely.

For a database request, the conceptual flow is:

```text
request
  ↓
database operation
  ↓
timeout
  ↓
failure handling
```

The important idea is not to build a distributed timeout infrastructure today. The important idea is to understand the principle.

## Why timeouts matter

A database call can hang for several reasons:

- network connectivity issues
- overloaded database server
- lock waits
- deadlocks or stalls
- slow query execution
- degraded infrastructure conditions

If the application waits forever, the client also waits forever, and the system becomes stuck.

Timeouts provide a bounded wait. They allow the system to fail fast and return an honest response instead of blocking indefinitely.

## In the current project

The repository currently uses a straightforward database connection boundary and centralized error handling. A database failure becomes a `DatabaseUnavailableError` and then an HTTP 503.

That is a simple but important reliability pattern.

It is not a full distributed timeout system, but it is the correct mindset: an external dependency must not be allowed to stall the application indefinitely.

## Operational principle

Every external system call should ideally have:

- a timeout budget
- a defined failure response
- a fallback or retry policy if appropriate
- clear observability for slow requests

The application can then fail a request quickly and communicate the real result to the caller.

## Key takeaway

A timed-out database request is not a success. It is an external failure. The application should handle it consistently and transparently, rather than leaving the client waiting forever.
