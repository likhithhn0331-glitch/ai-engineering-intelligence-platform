Document Service at 10× Scale — Design Notes

Scope and assumptions
- Baseline: current service (FastAPI -> Service -> Repository -> PostgreSQL). Traffic expected to increase 10× (requests/sec and concurrent clients).
- Workload mix: read-heavy endpoints (GET /documents, GET /documents/{id}) with write bursts (POST/PUT/DELETE) during working hours.
- DB: single primary Postgres instance today; max_connections default likely low (e.g., 100).

Short answer: first things that break
1. DB connection pool saturation (app instances + DB max connections mismatch).
2. Slow queries and missing indexes that increase DB latency and hold connections longer.
3. FastAPI worker saturation (CPU/event-loop blocking) if handlers do blocking work or long DB calls.
4. Increased error rates/timeouts and cascading retries causing further pressure.

Per-tier analysis and mitigations
1) Client / Load Balancer
- Breaks: misconfigured LB timeouts, healthcheck noise, uneven load distribution.
- Mitigations: set conservative idle and request timeouts, use connection draining for deployments, route sticky sessions only if needed (avoid otherwise), use autoscaling groups behind LB.

2) FastAPI instances
- Breaks: event loop blocking, thread exhaustion, too many concurrent DB connection attempts.
- Mitigations:
  - Run multiple FastAPI workers (uvicorn+gunicorn or uvicorn workers) with async handlers.
  - Ensure no blocking CPU-bound work in request path; push heavy work to background jobs/workers.
  - Configure worker autoscaling based on CPU + request queue length + latency SLOs.
  - Use bulkheads: separate instance pools for read-heavy and write-heavy routes if behavior differs.

3) Connection pooling and DB concurrency
- Breaks: exhausting Postgres max_connections; large number of short-lived connections; waiting for free connection increases latency.
- Mitigations:
  - Use a connection pooler (PgBouncer) in transaction-pooling mode in front of Postgres; tune pool sizes.
  - Compute per-app pool size: pool_per_app = floor((DB_max_connections - reserved_for_maintenance) / num_app_instances). Reserve ~10-20 connections for maintenance/replica writes.
  - Prefer reusing connections: use a pool per process, not per-request.
  - Use statement_timeout at DB and connection timeouts at client to fail fast.

4) Reads: indexes, read replicas, cache
- Breaks: read load overwhelms primary; table scans make queries slow.
- Mitigations:
  - Ensure proper indexes: primary key on id (already present), index on created_at for ordering, and any column used in WHERE/ORDER.
  - Add read replicas for scaling read traffic and route read-only queries to replicas through a read router or LB.
  - Add an in-memory cache (Redis) for hot GET /documents and GET /documents/{id} results. Use cache-aside pattern with short TTL and explicit invalidation on writes.
  - Consider materialized views or denormalized read tables for expensive aggregations.

5) Writes: primary scaling and consistency
- Breaks: write throughput hitting primary, lock contention on hot rows, long-running transactions blocking others.
- Mitigations:
  - Keep transactions short: avoid long multi-step transactions holding locks.
  - Add optimistic concurrency control for document updates (version column + WHERE version = expected_version). Return 409 or instruct client to retry on zero rows affected.
  - Use batching/queueing for non-critical writes (background workers) and idempotent operations.
  - If writes grow beyond vertical scaling, consider logical sharding/horizontal partitioning by document id namespace.

6) Reliability patterns: timeouts, retries, backpressure
- Breaks: clients or services retry aggressively, causing retry storms.
- Mitigations:
  - Global request timeouts and per-call DB timeouts. Expose read and write timeouts separately.
  - Retries only for idempotent reads; for writes use safe retry with idempotency keys or exponential backoff + jitter.
  - Implement circuit breakers for downstream DB layer: short-circuit when DB error rate spikes and return 503 quickly.
  - Implement backpressure: when internal queue/connection pool is saturated, respond with 429 or 503 rather than queueing indefinitely.

7) Health checks and orchestration
- Liveness vs readiness endpoints: keep readiness to verify DB connection pool sanity and schema migrations applied; liveness should be lightweight.
- Ensure orchestrator (K8s, ASG) uses readiness probes before traffic.

8) Observability and SLOs
- Key metrics to emit:
  - API: requests/sec, latency p50/p95/p99, error rate by endpoint
  - DB: active connections, wait queue length for pool, query duration distribution, rows scanned
  - Cache: hit/miss rates, eviction rate
  - System: CPU, memory, event-loop latency
- Logging: structured logs with request id and trace id. Integrate distributed tracing (OpenTelemetry) to measure end-to-end latency and identify DB slow queries.
- Alerts: high error rate (>1% over 5m), P95 latency above SLO, DB connection pool near capacity (>80%), cache hit rate drop.

Capacity planning and sizing notes
- Connection pool sizing example formula:
  DB_max_connections = 200 (example)
  reserved = 10
  app_instances = 10
  pool_per_instance = floor((DB_max_connections - reserved) / app_instances) = ~19
  Use PgBouncer to multiplex many app connections onto fewer DB connections.
- Query latency budget: aim for DB p95 < 100ms for simple read; tune indexes and prepared statements.

Short-term actions (safe, low-effort)
- Add PgBouncer in front of Postgres (transaction pooling) and configure per-app pool sizes.
- Add statement_timeout and connection timeouts to avoid stuck queries consuming connections.
- Add Redis cache for GET /documents and GET /documents/{id} with cache-aside pattern and short TTL.
- Add metrics (Prometheus) for DB pool usage and expose them to monitoring.
- Implement optimistic concurrency for updates using version field and return 409 on conflicts.

Medium-term actions (requires design and infra)
- Add read replicas and read routing; validate replication lag and failover behavior.
- Add autoscaling for FastAPI instances based on queue latency and DB pool saturation signals.
- Introduce background worker system for heavy or non-critical writes (Celery, RQ, or serverless functions).
- Implement request-level circuit breaker and bulkhead isolation patterns.

Security and correctness notes
- Keep SQL parameterization (already in place) and continue to avoid string interpolation.
- Ensure cache privacy: do not cache responses with sensitive content or user-specific data without proper keys.

Observability/Playbooks
- Playbook for DB saturation: detect pool near capacity → enable ephemeral circuit-breaker → return 503 → trigger paging to DB on-call → investigate slow queries and scale replicas or add PgBouncer.

Appendix — Design trade-offs
- Read replicas reduce read load but increase complexity (replication lag, read-after-write consistency). Use cache or read-routing with TTL invalidation to reduce stale reads.
- PgBouncer reduces DB connection usage but requires careful pooling mode (transaction vs session) depending on app behavior (avoid session state on DB connections).

References / Next steps
- Implement short-term changes first: PgBouncer, statement_timeout, Redis caching, optimistic concurrency, and metrics.
- Add tests that simulate DB connection pool exhaustion and assert graceful degradation (503 / 429) rather than silent fallback.

Prepared by: automated design notes
Date: 2026-09-16
