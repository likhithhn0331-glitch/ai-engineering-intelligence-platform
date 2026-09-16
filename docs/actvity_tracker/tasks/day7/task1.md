# Day 7 / Task 1 — Verify repository state and pytest execution

## Task

Validate the repository state using the actual Git and test commands instead of assuming the README is sufficient. The project README lists API and PostgreSQL integration tests, but the task explicitly requires confirming the current branch, current commit, working tree, and real pytest result.

## Commands run

```bash
git --no-pager status --short --branch
git --no-pager log --oneline --decorate -n 10
.\.venv\Scripts\python.exe -m pytest -q
```

## Git status result

```text
## main...origin/main
A  docs/actvity_tracker/tasks/day7/task1.md
```

Interpretation:
- Current branch: main
- Repository is tracking origin/main as the remote default branch
- Working tree is not clean: the file for this task (`docs/actvity_tracker/tasks/day7/task1.md`) is present as a new addition in the working tree/index.

## Git log result

```text
69a704b (HEAD -> main, origin/main, origin/HEAD) Commit 5: feat: add PostgreSQL persistence, migration workflow, and failure validation • replace in-memory document persistence with PostgreSQL-backed repository behavior • add environment-based DATABASE_URL configuration with .env example • introduce migration-driven schema creation with schema_migrations tracking • centralize database connection lifecycle handling with rollback/close discipline • preserve FastAPI centralized exception handling and API contract • add PostgreSQL integration and deliberate-failure pytest coverage • document architecture, notes, and verification reports • update README with the current architecture and validation status
c7ce4f0 Commit 5: feat: add PostgreSQL-backed document persistence and migration flow • replace in-memory document repository with PostgreSQL-backed repository • add environment-based DATABASE_URL config and .env.example guidance • add dedicated database connection boundary with lifecycle cleanup • add schema migration runner and reproducible documents table creation • preserve centralized FastAPI exception handling and API contract • add end-to-end PostgreSQL integration tests • add project documentation and pytest reports for PostgreSQL work
217dadc Commit 4: feat(day2): add document collection/retrieval/deletion API flow and documentation • expand API tests for GET /documents, GET /documents/{id}, and DELETE /documents/{id} • verify success and 404 behaviors through the service/repository architecture • document layered design decisions in docs/actvity_tracker/day2.md • update README with Day 2 API behavior and architecture notes
75e3d99 Commit 3: docs: add Day 1 implementation report • Add docs/actvity_tracker/day1.md containing detailed theory (exceptions → HTTP mapping),   per-file code explanations, software architecture, testing approach and run instructions,   pytest report reference, and recommended next steps.
47693c3 Commit 2: chore: add centralized FastAPI exception handlers and tests • Add global exception handlers in src/main.py:   DocumentNotFoundError→404, InvalidDocumentError→400, RequestValidationError→422, Exception→500 (logged) • Remove per-route try/except so service exceptions bubble to global handlers • Add pytest suite under tests/ for root, health, create, validation, and missing-document cases • Add pytest run report at docs/pytest_reports/report_1.md and update README with changes
79f5f42 Commit 1: feat: implement layered document architecture • add FastAPI document router for API layer • wire HTTP requests through DocumentService and DocumentRepository • implement in-memory document storage • add document model, validation, and exception handling • update README with architecture and endpoint documentation
b0452ce Initial commit
```

## Pytest execution result

The repository README states the suite includes `tests/test_api.py` and `tests/test_postgres_integration.py`, but the task required validating the actual runtime result rather than trusting documentation.

```text
....................                                                     [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  C:\likhi\Interview\ai-engineering-intelligence-platform\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

.venv\Lib\site-packages\starlette\testclient.py:53
  C:\likhi\Interview\ai-engineering-intelligence-platform\.venv\Lib\site-packages\starlette\testclient.py:53: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = Callable[[], AbstractContextManager[anyio.abc.BlockingPortal]]

tests/test_api.py::test_invalid_request_validation_error
  C:\likhi\Interview\ai-engineering-intelligence-platform\.venv\Lib\site-packages\starlette\_exception_handler.py:59: StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
    response = await handler(conn, exc)  # type: ignore[arg-type]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
20 passed, 3 warnings in 8.54s
```

## Recorded results

- Current commit: 69a704b
- Current branch: main
- Tests passed: 20
- Tests failed: 0
- Warnings: 3
- Working tree: not clean — new file added: `docs/actvity_tracker/tasks/day7/task1.md`

## Solution summary

The README was not treated as proof of a passing suite. The project was validated by running the repository's established pytest command, which completed successfully with 20 passing tests and no failing tests. The warnings are real deprecation warnings from the FastAPI/Starlette stack and should be tracked separately from the functional test outcome.

This task confirms that:
- The current project state is on `main` at commit `69a704b`.
- The test suite is active and passing in the current environment.
- The working tree is not clean because the task file itself is newly added.
- The presence of test files in the repository is not sufficient by itself; only the actual pytest run confirms the current status.
