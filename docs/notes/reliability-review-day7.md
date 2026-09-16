Reliability Review — Day 7

Scope
- Files inspected:
  - src/db/connection.py
  - src/repositories/document_repository.py
  - src/main.py
  - tests/test_postgres_integration.py (fixtures)

Summary
This review verifies connection lifecycle, transaction safety, SQL safety, resource cleanup, error translation, and responsibilities. Overall the code is well-structured and uses parameterized SQL and context managers; however a few reliability and architectural weaknesses were identified and are documented below with evidence and recommended hardenings.

4.1 Database failure behavior
Findings / Evidence
- Connection-time failure:
  - In src/db/connection.py, connecting is wrapped in try/except; any exception on connect raises DatabaseUnavailableError("Database is unavailable."). This means a connect-time failure becomes DatabaseUnavailableError.
  - If psycopg is not present, DatabaseConfigurationError is raised earlier.
- Operational failure inside transaction:
  - database_connection contextmanager rolls back on exceptions and (after the recent change) commits automatically on normal exit.
  - If an exception is a psycopg.Error, connection.py converts it to DatabaseUnavailableError; non-psycopg exceptions are re-raised as-is.
- Where the exception goes:
  - DocumentRepository does NOT catch DatabaseUnavailableError; repository methods catch DatabaseConfigurationError and RuntimeError in their postgres branches (this is inconsistent).
  - FastAPI has an exception handler for DatabaseUnavailableError in src/main.py which maps it to HTTP 503 and returns exc.message.

Answers to the checklist questions
- What exception occurs when PostgreSQL is unreachable?
  - At connect time: DatabaseUnavailableError (raised by database_connection). Internally the original psycopg error is wrapped/attached as __cause__.
- Where does that exception go?
  - It bubbles up to the caller. DocumentRepository currently does not catch DatabaseUnavailableError, so it propagates to the FastAPI exception handler in src/main.py.
- What HTTP response does the client receive?
  - HTTP 503 Service Unavailable with JSON {"detail": exc.message} (message is the DatabaseUnavailableError.message, currently the generic "Database is unavailable.").
- Does the connection get closed?
  - Yes: database_connection has a finally: connection.close() ensuring closure even on exception.
- Does the transaction get rolled back?
  - Yes: on exception database_connection attempts connection.rollback(). Also commit is attempted only on normal exit (current behavior after the change).
- Could the API expose internal database details?
  - Currently exc.message is generic; database_connection wraps psycopg errors into DatabaseUnavailableError with a generic message, so internal DB details are not exposed via the DatabaseUnavailableError path. The generic Exception handler in src/main.py returns "Internal server error" and logs details only to server logs.

Risks / Notes
- Inconsistent exception handling in the repository: DocumentRepository catches DatabaseConfigurationError and RuntimeError, but not DatabaseUnavailableError. This makes behavior inconsistent between configuration-time failures (fallback to in-memory) and runtime DB failures (503). This may be intended, but it should be deliberate.
- Catching RuntimeError is too broad; it risks converting unrelated runtime errors into a fallback and hiding root causes.

4.2 SQL safety
Findings / Evidence
- All SQL in src/repositories/document_repository.py uses parameterized queries with %s placeholders and tuples for parameters (e.g. cursor.execute(..., (document_id,))). This prevents SQL injection.
- SQL files (migrations and schema) are static and not interpolated with user input.

Conclusion: SQL parameterization is implemented correctly.

4.3 Resource cleanup
Findings / Evidence
- repository uses: with database_connection() as connection: and with connection.cursor() as cursor: — cursors and connections are cleaned up by context managers and by finally in database_connection.
- database_connection ensures rollback on exception and close() in finally. After the recent change it also commits on normal exit.

Conclusion: Resource cleanup is implemented correctly; exception paths attempt rollback and always close connection.

4.4 Repository responsibilities
Findings / Evidence
- Route layer (src/api/document_routes.py) handles HTTP concerns and validation.
- Service layer performs business logic (src/services/document_service.py).
- Repository handles persistence (src/repositories/document_repository.py) and currently decides at runtime whether to use Postgres or fall back to the in-memory dict.
- Database layer (src/db/connection.py) handles connection lifecycle and error translation.

Notes
- The repository contains logic to switch to the in-memory fallback when DatabaseConfigurationError or RuntimeError are encountered. This mixes availability-policy decisions into the persistence layer. Choosing to fallback silently has implications on data consistency and must be explicit.

4.5 Architectural smell(s) and improvement opportunities
1) Broad exception handling in the repository
  - Symptom: repository catches RuntimeError (too broad) and then disables Postgres (self.use_postgres = False). It does not catch DatabaseUnavailableError.
  - Risk: unrelated runtime errors may cause silent fallback to in-memory storage, hiding failures and producing hard-to-diagnose data inconsistencies.
  - Recommendation: narrow the exception types caught by repository to only configuration/initialization errors (DatabaseConfigurationError) when it makes sense to fallback to in-memory. Let operational DatabaseUnavailableError bubble to the API so the client gets a 503, or explicitly handle DatabaseUnavailableError where fallback is a deliberate, well-documented choice.

2) Duplicate responsibility for commit
  - Symptom: document_repository calls connection.commit() in several methods while database_connection now commits automatically on normal exit.
  - Risk: redundant commits are usually harmless, but they confuse ownership of transaction lifecycle and can hide intent.
  - Recommendation: pick one strategy and be consistent. Prefer centralizing commit/rollback in database_connection (callers should not call commit). Remove connection.commit() calls from repository once centralized commit is accepted.

3) Error translation consistency
  - Symptom: database_connection wraps psycopg.Error into DatabaseUnavailableError, but other non-psycopg exceptions are re-raised. Repository catches RuntimeError, not DatabaseUnavailableError.
  - Recommendation: Define a clear error-translation policy: database layer should raise DatabaseConfigurationError (when DB is not configured), DatabaseUnavailableError (when DB is unreachable or returned a low-level error), and let repository and service decide whether to fallback or fail. Repository should not catch generic RuntimeError.

4) Explicit operational policy for fallback
  - Symptom: repository silently switches to in-memory storage when it thinks DB is unavailable in some paths. This can lead to silent data divergence.
  - Recommendation: If fallback is supported, make it explicit and logged, and ensure it is allowed only in non-production modes or with clear telemetry. Prefer failing early (503) for production when persistence is lost.

Concrete action suggestions (small, targeted changes)
- Change in repository exception handling:
  - Replace catches of (DatabaseConfigurationError, RuntimeError) with (DatabaseConfigurationError,) — so only configuration missing leads to fallback. Do not silently swallow runtime errors.
- Remove manual connection.commit() calls in repository after adopting automatic commit in database_connection. Keep commit calls out of repository to avoid duplicate responsibilities.
- Add logging at the point of fallback to in-memory storage (high-severity log line) so operator can see it in logs and tests can assert on intended behavior.
- Add a short comment in src/db/connection.py explaining the decision to centralize commit/rollback there and the expected caller behavior (don’t call connection.commit()).

Testing suggestions
- Add tests that simulate transient DatabaseUnavailableError (e.g. mock database_connection to raise DatabaseUnavailableError during an operation) and assert that endpoints return 503 rather than silently succeeding or falling back.
- Add tests that ensure SQL queries use parameterization (this can be verified indirectly by ensuring no formatting-based queries are present or via code reviews).

Final conclusion
- The codebase already follows many good patterns: parameterized SQL, context managers, and centralized connection lifecycle. The primary weaknesses are inconsistent error handling in the repository (too broad RuntimeError catch and mixed fallback policy) and unclear ownership of commit responsibilities after centralizing commit in database_connection.
- Recommended immediate small hardenings: narrow repository exception catches, add explicit logging for fallback, and remove repository-level commits (or document/align the strategy).

Appendix — locations referenced
- src/db/connection.py — database_connection contextmanager (connect/rollback/commit/close)
- src/repositories/document_repository.py — uses database_connection; currently calls connection.commit() and catches DatabaseConfigurationError and RuntimeError
- src/main.py — FastAPI exception handlers (DocumentNotFoundError, InvalidDocumentError, DatabaseUnavailableError, generic Exception)
- tests/test_postgres_integration.py — integration tests and TRUNCATE fixture

Reviewer: automated reliability review (notes generated)
Date: 2026-09-16
