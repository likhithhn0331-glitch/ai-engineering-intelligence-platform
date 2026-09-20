# Day 9 / Task 12 — Idempotency concept through `DELETE /documents/{id}`

## Objective

Understand the idempotency concept using the existing API.

Consider:

```text
DELETE /documents/{id}
```

If a client retries the request, what happens?

## The problem scenario

```text
first request
   ↓
delete
network failure
   ↓
client does not know whether it succeeded
retry
   ↓
delete again
```

A delete operation is often expected to be idempotent at the API level: repeating the same request should not create new side effects beyond the first successful delete.

The first request may have succeeded even though the client never received the response. Then the second request may find the resource already gone and return a not-found result.

That is a reasonable retry outcome because the resource is already in the desired final state.

## Idempotency in plain terms

An idempotent operation is one where repeating it does not produce a different final state beyond the first successful call.

For `DELETE`, the final state is usually “the resource is absent.” Repeating the delete does not create a different end state.

## Why this matters in interviews

This concept is often asked because it tests whether the candidate understands client retries, distributed systems, and API reliability.

The important point is not to redesign DELETE today. The important point is to understand that repeated requests may happen and the API contract should be consistent and predictable.

## What we are not doing here

We are not redesigning the API to add retry-safe semantics or a compensation mechanism. We are only understanding the concept and recognizing that retries require thoughtful handling.

## Key takeaway

Idempotency is the idea that a request may be repeated without creating a surprising new state. It is especially relevant to deletion, payment actions, and any operation where clients may retry after network ambiguity.
