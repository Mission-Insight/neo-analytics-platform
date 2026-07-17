# Epic 7 Progress — Engineering Excellence & Production Readiness

Tracks progress through Epic 7 (tickets NEO-309–NEO-318, NEO-370). Updated as each story/subtask completes.

**Epic goal:** transform the functional prototype into a maintainable, testable, reliable, professionally engineered product — automated testing, logging, config management, CI/CD, containerization, documentation, and performance review, while preserving existing functionality.

---

## Story status

| Ticket | Story | Status |
|---|---|---|
| NEO-309 | 7.1 Technical Debt Assessment | Done |
| NEO-310 | 7.2 Code Refactoring | Done |
| NEO-311 | 7.3 Automated Testing | Done |
| NEO-312 | 7.4 Logging & Observability | Done |
| NEO-313 | 7.5 Configuration Management | Done |
| NEO-314 | 7.6 Continuous Integration | In Progress |
| NEO-315 | 7.7 Dockerization | To Do |
| NEO-316 | 7.8 Documentation Excellence | To Do |
| NEO-317 | 7.9 Performance Review | To Do |
| NEO-318 | 7.10 Engineering Readiness Review | To Do |
| NEO-370 | 7.11 Engineering Retrospective | To Do |

---

## 7.1 Technical Debt Assessment (NEO-309)

Goal: identify and prioritize technical debt across the repository.

| Ticket | Subtask | Status |
|---|---|---|
| NEO-319 | 7.1.1 Review Entire Repository | Done |
| NEO-320 | 7.1.2 Create Technical Debt Register | Done |
| NEO-321 | 7.1.3 Prioritize Refactoring Work | Done |
| NEO-322 | 7.1.4 Review Findings | Done |

### 7.1.1 Review Entire Repository — findings (2026-07-15)

Reviewed every module in `src/`, both test files, `sql/schema.sql`, and confirmed `scripts/` is empty.

**Duplication**
- Model weights hardcoded independently in `src/models/risk_score.py` (`_DEFAULT_WEIGHTS`), `src/models/weights.json`, and `src/dashboard/config.py` (`WEIGHT_*`) — no sync mechanism.
- Two independent DB connection implementations: `src/db/connection.py` and `src/dashboard/db.py` (the latter reimplements its own `.env` loading/validation instead of reusing `src/config.py`).
- `sys.path.insert(0, ...)` + `st.set_page_config(...)` boilerplate repeated verbatim in `app.py` and all 4 files under `src/dashboard/pages/`.
- Lookup-or-raise pattern duplicated between `complete_ingestion_run` and `fail_ingestion_run` in `src/db/log_ingestion.py`.
- Chart color-palette dicts redefined per-file across `app.py`, `2_Explorer.py`, `3_Analytics.py` instead of one shared palette module.

**Long functions / files**
- `src/dashboard/pages/3_Analytics.py` — 500-line top-level script, largely untestable procedural code covering ~7 distinct analytical sections.
- `fetch_neows_feed` in `src/etl/fetch_neows.py` (~110 lines) mixes retry/backoff, rate-limit handling, and validation/logging.
- `src/models/risk_score.py` is the best-decomposed module in the codebase — use as the internal style reference during refactoring.

**Inconsistent naming**
- `tests/test_parse_orbital_parameters.py` actually tests `transform_orbital_parameters` (from `src/transform/transform_neows.py`) — no `parse_orbital_parameters` function exists.
- Transaction commit responsibility is inconsistent: `insert_orbital_parameters` calls `conn.commit()` itself while `insert_asteroids`/`insert_close_approaches` rely on the caller — this is also a correctness gap, since `run_pipeline._run_chunk`'s rollback-on-failure can't undo the orbital insert once it's already committed.
- Two unrelated `config.py` modules (`src/config.py` and `src/dashboard/config.py`) with the same filename but disjoint content — easy to import the wrong one.

**Dead code**
- `scripts/` is empty (only `.gitkeep`) despite being listed in the README's project structure table.
- `requirements.txt` lists stdlib modules as pip packages (`datetime`, `argparse`, `time`, `logging`); no version pins anywhere in the file.

### 7.1.2 Create Technical Debt Register — output (2026-07-15)

Findings from 7.1.1 converted into a formal register: [technical_debt_register.md](technical_debt_register.md), 12 items (TD-01–TD-12), each with issue/impact/recommendation/priority.

- **High priority (2):** TD-06 (`3_Analytics.py` untestable 500-line script, blocks 7.3), TD-08 (`insert_orbital_parameters` commits mid-transaction — real correctness bug, not just style)
- **Medium priority (5):** TD-01 (weights duplicated 3x), TD-02 (duplicate DB connection code), TD-07 (`fetch_neows_feed` mixes concerns), TD-10 (two unrelated `config.py` files), TD-12 (unpinned/stdlib deps in `requirements.txt`, blocks 7.6 CI)
- **Low priority (5):** TD-03 (page boilerplate), TD-04 (log_ingestion lookup duplication), TD-05 (chart palette duplication), TD-09 (misnamed test file), TD-11 (empty `scripts/`)

### 7.1.3 Prioritize Refactoring Work — output (2026-07-15)

Satisfied by the categorization already produced in 7.1.2: every item in [technical_debt_register.md](technical_debt_register.md) is tagged High/Medium/Low, with a summary table breaking down the counts (2 High, 5 Medium, 5 Low). No separate artifact needed — the register doubles as the prioritized work order for 7.2 Code Refactoring, starting with TD-06 and TD-08.

### 7.1.4 Review Findings — outcome (2026-07-15)

Walked the technical debt register with the product owner, tier by tier (High → Medium → Low). All 12 items (TD-01–TD-12) confirmed as-is — no reclassifications, no drops. Register priorities are final; 7.2 Code Refactoring should sequence work starting with TD-06 and TD-08.

7.1 Technical Debt Assessment is now fully complete (all 4 subtasks done).

---

## 7.2 Code Refactoring (NEO-310)

Goal: improve readability and maintainability. Acceptance criteria: intended behavior must not change.

| Ticket | Subtask | Status |
|---|---|---|
| NEO-323 | 7.2.1 Extract duplicated code | Done |
| NEO-324 | 7.2.2 Improve module organization | Done |
| NEO-325 | 7.2.3 Improve naming consistency | Done |
| NEO-326 | 7.2.4 Reduce oversized functions | Done |
| NEO-327 | 7.2.5 Remove dead code | Done |
| NEO-328 | 7.2.6 Run regression validation | Done |

All 12 items from [technical_debt_register.md](technical_debt_register.md) applied in one pass (2026-07-15), scoped to subtasks as follows:

- **7.2.1 Extract duplicated code:** TD-01 (weights now sourced from `risk_score.get_weights()`, `dashboard/ui_settings.py` no longer duplicates them), TD-02 (removed `dashboard/db.py`, dashboard now imports `src/db/connection.py`), TD-03 (added `layout.configure_page()`, removes 5x `st.set_page_config` duplication), TD-04 (extracted `_get_started_at()` in `log_ingestion.py`), TD-05 (new `src/dashboard/palette.py` centralizes chart colors).
- **7.2.2 Improve module organization:** covered by TD-02 and TD-10 (see below) — one canonical DB connection module, one canonical config module per package.
- **7.2.3 Improve naming consistency:** TD-09 (`tests/test_parse_orbital_parameters.py` → `test_transform_orbital_parameters.py`), TD-10 (`src/dashboard/config.py` → `src/dashboard/ui_settings.py`, no more same-name collision with `src/config.py`).
- **7.2.4 Reduce oversized functions:** TD-06 (`3_Analytics.py` decomposed into 8 named section functions), TD-07 (`fetch_neows_feed` split into `_request_with_retries()` and `_log_dataset_size()`, constants promoted module-level to match the naming pattern already used in `fetch_orbital_parameters.py`).
- **7.2.5 Remove dead code:** TD-11 (removed empty `scripts/` dir and its README table entry), TD-12 (`requirements.txt` stripped of stdlib pseudo-packages, all real deps pinned to installed versions; also caught and fixed a real gap — `altair` was used throughout the dashboard but missing from `requirements.txt` entirely).
- **7.2.6 Run regression validation:** `pytest` (11/11 passed), `flake8 src tests` (clean, the project's configured linter), `py_compile` across every touched module (clean). `black --check` was also run; it flagged pre-existing formatting in code untouched by this refactor (the project has no `pyproject.toml` pinning Black's line-length to the 120 chars flake8 already enforces) — not a regression, left alone as out of scope. Dashboard pages (`app.py`, all 4 pages) were not run end-to-end in Streamlit; per standing preference the user verifies UI behavior themselves.

### TD-08 scope decision (2026-07-15)

Reviewed with the product owner: TD-08 (mid-transaction commit bug) doesn't fit any of the 6 subtask titles and its fix technically changes failure-path behavior, which is in tension with the "no behavior change" acceptance criteria. Decision: include it in 7.2 anyway, since the behavior it changes is a bug, not documented/intended behavior. Fixed as part of 7.2.1/7.2.3 work (removed the internal `conn.commit()` from `insert_orbital_parameters`).

---

## 7.3 Automated Testing (NEO-311)

Goal: introduce professional testing practices. Only 7.3.7 had an explicit description ("measure test coverage, target 70-80%"); the rest followed their titles.

| Ticket | Subtask | Status |
|---|---|---|
| NEO-329 | 7.3.1 Create tests directory structure | Done |
| NEO-330 | 7.3.2 Write parser unit tests | Done |
| NEO-331 | 7.3.3 Write database tests | Done |
| NEO-332 | 7.3.4 Write risk engine tests | Done |
| NEO-333 | 7.3.5 Write dashboard service tests (not Streamlit UI) | Done |
| NEO-334 | 7.3.6 Create representative test fixtures | Done |
| NEO-335 | 7.3.7 Measure test coverage | Done |
| NEO-336 | 7.3.8 Document testing strategy | Done |

**7.3.1** — restructured `tests/` into subpackages mirroring `src/` (`parsing/`, `transform/`, `db/`, `models/`, `dashboard/`, plus `fixtures/`), with a root `conftest.py` and a dashboard-specific `conftest.py`.

**7.3.6** — built first since other test files depend on it: `tests/fixtures/sample_data.py` defines 4 representative asteroids (far/slow, close/fast/hazardous, multi-approach for aggregation testing, and one with no close approaches/no orbital row for `is_scorable=False`/`LEFT JOIN` NULL coverage), plus a `seed_sample_data()` helper. `tests/conftest.py` adds a `db_conn` fixture (in-memory SQLite built from the real `sql/schema.sql`, not a hand-maintained copy) and a `seeded_conn` fixture layering the sample data on top.

**7.3.2** — moved the existing parser tests into `tests/parsing/`, added `tests/parsing/test_utils.py` for `safe_float` (previously only exercised indirectly).

**7.3.3** — new `tests/db/` covering `connection.py` (via a temp-file monkeypatch, never touching the real dev database), `init_db.py`, and all three `load_*` insert functions (insert + upsert-on-conflict + empty-list paths), plus `log_ingestion.py`. Includes a dedicated regression test for TD-08: `test_insert_orbital_parameters_does_not_commit_internally` — fails if the removed internal `conn.commit()` ever comes back.

**7.3.4** — `tests/models/test_risk_score.py`: unit tests for every pure helper (`_minmax`, `_add_*_feature`, `_handle_missing_data`, `_compute_feature_ranges`, `_normalize_features`, `_apply_formula`, `_rank_scores`), `get_weights()` (default file, missing-file fallback, and both validation-error paths), and an end-to-end test against `seeded_conn`. Expected risk scores for the sample dataset were computed with an independent script (not by re-deriving the source formula) and hardcoded as golden values, so the test can actually catch a formula bug rather than just a wiring bug.

**7.3.5** — `tests/dashboard/test_data_service.py` covers all 14 functions in `data_service.py`. Two things had to be solved to make this work: (1) `data_service.py` opens a fresh connection per call, and separate `:memory:` SQLite connections don't share state, so `tests/dashboard/conftest.py` uses a **file-backed** temp DB instead; (2) every function is `@st.cache_data`-decorated, which memoizes across the whole pytest process — an autouse fixture calls `st.cache_data.clear()` before/after each test to prevent cross-test cache poisoning.

**7.3.7** — installed `pytest-cov`. Coverage scope was a genuine judgment call: whole-`src/` coverage measured 42%, dragged down by Streamlit UI rendering (untestable by assertion, verified manually in-browser) and ETL/pipeline code that no subtask asked for. Reviewed with the product owner — decision: scope the 70-80% target to the modules 7.3.2-7.3.5 actually targeted (parsing, transform, db, models, dashboard/data_service), excluding UI and ETL/pipeline via `.coveragerc`. Result: **98%** (312 statements, 5 missed) on the scoped core, well past target.

**7.3.8** — `docs/testing_strategy.md`: scope and rationale for what's tested vs. deliberately excluded, directory layout, the two DB-fixture strategies and when each applies, the `st.cache_data` gotcha and its fix, and the TD-08 regression test.

Final state: 72/72 tests passing, flake8 clean.

---

## 7.5 Configuration Management (NEO-313)

Goal: remove hard-coded values. No subtask had a description; followed each title.

| Ticket | Subtask | Status |
|---|---|---|
| NEO-338 | 7.5.1 Centralize configuration | Done |
| NEO-339 | 7.5.2 Separate development settings | Done |
| NEO-340 | 7.5.3 Validate missing configuration | Done |
| NEO-341 | 7.5.4 Document configuration | Done |

Scope decision made without a blocking question (consistent with prior stories, flagged here for visibility): `src/config.py` now owns all *deployment* config (secrets + operational tuning). Two other kinds of "configurable" values stay where they are, deliberately out of scope — `src/dashboard/ui_settings.py` (presentation constants: app title, icon, dataset window labels) and `src/models/weights.json` (model parameters, already centralized in 7.2/TD-01). Neither is a deployment concern, so moving them into `.env` would be config sprawl, not config management.

**7.5.1** — Centralized operational constants that were hardcoded and, in the case of HTTP retry/timeout settings, duplicated almost identically across `src/etl/fetch_neows.py` and `src/etl/fetch_orbital_parameters.py`. Moved into `src/config.py` as environment-overridable values with defaults exactly matching the prior hardcoded numbers (behavior-preserving): HTTP timeout/retries/backoff/delay, pipeline chunk size/delay, and logging level/rotation size/backup count. Both ETL files and `run_pipeline.py`/`logging.py` now import from `src/config.py` instead of defining their own copies.

**7.5.2** — "Separate development settings" was interpreted as: the test suite shouldn't need real production secrets to run. Previously, merely importing `src.db.connection` (which nearly every test does transitively) required a real `.env` with `NASA_API_KEY` set, even for tests that never touch the NASA API. `tests/conftest.py` now loads the real `.env` first if one exists (so a developer's real credentials always win), then fills any gaps with safe dummy values via `os.environ.setdefault`. Verified by temporarily hiding `.env` entirely and confirming all 72 tests still passed, then restoring it and confirming the real-credentials path is unaffected. No `APP_ENV`/environment-switching mechanism was introduced — there's no actual second deployment environment yet, so that would be speculative.

**7.5.3** — Added validation for the newly-centralized values: invalid integer/float env vars (e.g. `HTTP_MAX_RETRIES=abc`) now raise a clear `ValueError` naming the variable, instead of a confusing raw `int()` stack trace; `LOG_LEVEL` is checked against the 5 valid Python logging levels. The pre-existing required-secret checks (`NASA_API_KEY`/`DATABASE_PATH`/`BASE_URL`) were left as-is — already correct, and not new logic from this story. Added `tests/test_config.py` for the new validation helpers (`_get_int_env`/`_get_float_env`); did not attempt to test the import-time required-secret checks, since that needs subprocess-level isolation to test safely and the logic is a pre-existing, trivial one-liner.

**7.5.4** — `docs/configuration.md`: the three-way config/presentation/model-parameter split, every variable with its default and purpose, the validation behavior, and the test-environment fallback mechanism. `.env.example` updated with all new optional variables (commented out, showing defaults). README points to the new doc.

Final state: 78/78 tests passing (6 new), flake8 clean, all existing behavior preserved (defaults unchanged from prior hardcoded values).

---

## 7.6 Continuous Integration (NEO-314)

Goal: teach modern engineering workflow.

| Ticket | Subtask | Status |
|---|---|---|
| NEO-342 | 7.6.1 Create GitHub Actions workflow | Done |
| NEO-343 | 7.6.2 Install dependencies automatically | Done |
| NEO-344 | 7.6.3 Execute automated tests | Done |
| NEO-345 | 7.6.4 Run linting | Done |
| NEO-346 | 7.6.5 Require successful CI before merge | To Do — GitHub branch-protection setting, deferred with the user's agreement |
| NEO-347 | 7.6.6 Verify pipeline execution | In Progress — first real run failed, fix identified (see below) |

Before starting, checked actual repo state rather than assuming: no `.github/workflows/` existed. The *ingredients* 7.6.2-7.6.4 need already existed from earlier stories (pinned `requirements.txt` from 7.2/7.5, the full pytest suite from 7.3, the pre-existing `.flake8` config) but nothing was wired into an automated pipeline yet.

**7.6.1-7.6.4 (2026-07-16)** — all four done in one workflow file, `.github/workflows/ci.yml`: triggers on every push and pull request, one job (`test`) with steps for checkout, Python 3.10 setup (with pip caching), `pip install -r requirements.txt`, `flake8 .`, and `pytest --cov --cov-report=term-missing`. Deliberately did not add a `black --check` step — the project has pre-existing formatting debt untouched by this epic (see 7.2 session notes) that would fail CI on the very first run through no fault of new work.

Validated locally end-to-end rather than trusting the YAML alone: parsed the workflow file with PyYAML to confirm valid syntax (note — PyYAML parses the bare `on:` key as the boolean `True` due to YAML 1.1's boolean-literal quirk; this is a well-known PyYAML artifact, not a bug — GitHub's own parser handles `on:` correctly, which is why every real-world GitHub Actions workflow uses this exact syntax). Then ran the exact three commands the workflow will run (`pip install`, `flake8 .`, `pytest --cov`) with `.env` temporarily removed, simulating exactly what a CI runner will see (no secrets file). All three passed — this is the payoff of the 7.5.2 test-isolation work: the suite needs zero secrets configured in GitHub for CI to go green. `.env` restored and confirmed the real-credentials path still works afterward.

**Deferred to a later session** (with the user's agreement): 7.6.5 (branch protection requiring CI) is a GitHub repo-admin setting, not a code change.

### 7.6.6 first real run — failure and fix (2026-07-16)

The user pushed the branch themselves and the first real CI run failed at the "Run linting (flake8)" step with `Process completed with exit code 127` (shell for "command not found"). Root cause: `flake8` was never listed in `requirements.txt` — it worked locally throughout this entire epic only because it happened to already be installed in the pre-existing dev venv from before Epic 7 started, so the gap was invisible to every local validation run. CI's "Install dependencies" step only runs `pip install -r requirements.txt`, which never installed it, so `flake8 .` wasn't found on PATH.

Fix: added `flake8==7.3.0` (the version already installed locally) to `requirements.txt`. Verified properly this time — not just `pip show`, but installing into a completely bare venv with nothing else present and confirming `flake8 .` both installs and runs clean against the repo. (A full from-scratch reinstall of every pinned dependency was also attempted to mirror the CI job exactly, but hit a Windows long-path filesystem limitation local to this machine's temp directory — unrelated to the actual fix and not something the Ubuntu-based GitHub runner will hit, so the narrower bare-venv verification of just the missing package stands in for it.)

Same gap exists for `black` (also installed locally, also missing from `requirements.txt`) but CI doesn't invoke `black`, so it isn't blocking — left for the user to decide since it's not part of this failure.

**Lesson for future validation:** local "it works on my machine" checks in an already-populated dev venv can't catch a dependency that's missing from `requirements.txt` but happens to already be installed locally. A real CI failure surfaced what local validation structurally could not.

---

## Session log

- **2026-07-15** — Kicked off Epic 7. Reviewed codebase structure and baseline gaps (no CI, no Docker, tests only cover `parsing/`). Completed 7.1.1 repository review; findings above. Created this tracking doc. Completed 7.1.2 — created `docs/technical_debt_register.md` with 12 prioritized items. Completed 7.1.3 — confirmed the register's existing High/Medium/Low tagging already satisfies this subtask. Completed 7.1.4 — reviewed the full register with the product owner; all 12 items confirmed with no changes. **7.1 Technical Debt Assessment complete.** Completed 7.2 Code Refactoring — applied all 12 TD items across the 6 subtasks (including TD-08, scoped in with the product owner despite the strict no-behavior-change bar); pytest 11/11 passing, flake8 clean, py_compile clean on every touched module. **7.2 Code Refactoring complete**, pending the user's own manual pass over the dashboard pages. Completed 7.3 Automated Testing — restructured `tests/` to mirror `src/`, built shared representative fixtures and two DB-fixture strategies, wrote unit/integration tests for parsing, db, the risk engine, and the dashboard data service (61 new tests, 72 total), added a TD-08 regression test, installed pytest-cov and scoped the 70-80% coverage target to core logic (98% achieved) after reviewing the scope question with the product owner, and documented it all in `docs/testing_strategy.md`. **7.3 Automated Testing complete.** Completed 7.5 Configuration Management — centralized previously-duplicated HTTP/pipeline/logging constants into `src/config.py` as environment-overridable values with unchanged defaults, decoupled the test suite from needing real secrets (verified by running the full suite with `.env` temporarily removed), added validation for the new config values, and documented everything in `docs/configuration.md`. **7.5 Configuration Management complete.**
- **2026-07-16** — Started 7.6 Continuous Integration — created `.github/workflows/ci.yml` covering 7.6.1-7.6.4 (checkout, Python setup, install deps, lint, test), validated end-to-end locally with `.env` hidden to confirm CI needs no secrets to go green. 7.6.5 (branch protection) and 7.6.6 (verify a real pipeline run, requires pushing) deferred to a later session with the user's agreement — nothing pushed yet.
