# Testing Strategy

## Scope

Automated tests cover the platform's core logic: data parsing/transforming, database
persistence, the risk scoring engine, and the dashboard's data access layer
(`src/dashboard/data_service.py`). This is deliberately **not** the same as "all of
`src/`" — two categories of code are out of scope for automated tests and are excluded
from the coverage measurement (see `.coveragerc`):

- **Streamlit UI rendering** (`src/dashboard/app.py`, `layout.py`, `pages/*`,
  `palette.py`, `ui_settings.py`) — these render widgets and charts; verifying them
  means looking at the running app, not asserting on return values. They're checked
  manually in the browser.
- **ETL network calls and pipeline orchestration** (`src/etl/*`, `src/run_pipeline.py`,
  `src/logging.py`) — these primarily coordinate NASA API calls, retries, and
  multi-step ingestion runs. No subtask in Epic 7.3 targeted them, so they weren't
  built out this round; they're reasonable candidates for a future testing pass
  (would need `requests` mocking rather than a real database).

## Coverage target

**70-80%**, measured only against the in-scope modules listed above (see `.coveragerc`
`omit` list). As of 2026-07-15 the in-scope modules sit at **98%** (312 statements, 5
missed — see `docs/epic_7_progress.md` for the exact breakdown). Run:

```bash
pytest --cov --cov-report=term-missing
```

## Directory structure

`tests/` mirrors `src/`'s package layout, so a source file's tests are always at the
matching path:

```text
tests/
  conftest.py                 # shared fixtures (see below)
  fixtures/
    sample_data.py            # representative sample dataset + DB seeding helper
  parsing/                    # mirrors src/parsing/
  transform/                  # mirrors src/transform/
  db/                         # mirrors src/db/
  models/                     # mirrors src/models/
  dashboard/
    conftest.py               # dashboard-specific fixtures (see below)
    test_data_service.py      # mirrors src/dashboard/data_service.py
```

## Test types

- **Pure unit tests** (parsing, transform, and the risk engine's feature/normalization
  helpers in `src/models/risk_score.py`) call functions directly with plain dicts —
  no database, no I/O.
- **Database integration tests** (`tests/db/`, and the end-to-end tests in
  `tests/models/test_risk_score.py`) run against a real SQLite connection built from
  the actual `sql/schema.sql` — not a hand-maintained copy of it — so schema drift
  gets caught. Two strategies are used depending on what's being tested:
  - **`db_conn` fixture** (`tests/conftest.py`): a single in-memory (`:memory:`)
    connection, passed directly into the function under test. Cheap and fully
    isolated — used whenever the test can hold one connection for its whole
    lifetime (which covers every `src/db/` function, since they all accept a
    `conn` parameter rather than opening their own).
  - **`seeded_db_path` fixture** (`tests/dashboard/conftest.py`): a **file-backed**
    temp database. `data_service.py` opens a fresh connection per call
    (`get_connection()`), and separate `:memory:` connections don't share state, so
    dashboard service tests need a real file every connection can see.
- **`seeded_conn` / dashboard `_data_service_isolation`**: both layers seed the same
  representative dataset (`tests/fixtures/sample_data.py`) so risk-engine and
  dashboard-service tests exercise realistic, shared scenarios rather than each
  reinventing ad hoc data.

## Representative test fixtures

`tests/fixtures/sample_data.py` defines four asteroids chosen to exercise the risk
engine's edge cases in one dataset:

| Asteroid | Purpose |
|---|---|
| `2000433` | Single close approach, far and slow — low risk baseline |
| `3600001` | Single close approach, close and fast, hazardous — high risk |
| `3600002` | Two close approaches — exercises MIN/MAX/COUNT aggregation |
| `3600003` | No close approaches, no orbital parameters row — exercises `is_scorable=False` and `LEFT JOIN` NULL handling |

Expected risk scores for this dataset were computed independently (a standalone
script, not by re-running the source formula) and hardcoded as golden values in
`tests/models/test_risk_score.py`'s end-to-end test — this catches regressions in the
formula itself, not just wiring bugs that a self-referential test would miss.

## Streamlit caching in tests

`src/dashboard/data_service.py` decorates every function with `@st.cache_data`, which
memoizes across calls **for the lifetime of the pytest process**, keyed only by
arguments — most of these functions take none. Without resetting it, the first test
to call e.g. `get_all_scores()` would poison every later test with its result. The
`_data_service_isolation` autouse fixture in `tests/dashboard/conftest.py` calls
`st.cache_data.clear()` before and after every test in that package to prevent this.

## Regression coverage for prior fixes

`tests/db/test_load_orbital_parameters.py::test_insert_orbital_parameters_does_not_commit_internally`
guards against TD-08 (Epic 7.2) resurfacing: `insert_orbital_parameters` must not
commit its own transaction, since the pipeline's rollback-on-failure depends on the
caller owning that boundary.

## Running the suite

```bash
pytest                                        # run all tests
pytest tests/models                           # run one area
pytest --cov --cov-report=term-missing        # with coverage
```
