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
| NEO-314 | 7.6 Continuous Integration | Done |
| NEO-315 | 7.7 Dockerization | Done |
| NEO-316 | 7.8 Documentation Excellence | Done |
| NEO-317 | 7.9 Performance Review | Done |
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
| NEO-346 | 7.6.5 Require successful CI before merge | Done |
| NEO-347 | 7.6.6 Verify pipeline execution | Done |

Before starting, checked actual repo state rather than assuming: no `.github/workflows/` existed. The *ingredients* 7.6.2-7.6.4 need already existed from earlier stories (pinned `requirements.txt` from 7.2/7.5, the full pytest suite from 7.3, the pre-existing `.flake8` config) but nothing was wired into an automated pipeline yet.

**7.6.1-7.6.4 (2026-07-16)** — all four done in one workflow file, `.github/workflows/ci.yml`: triggers on every push and pull request, one job (`test`) with steps for checkout, Python 3.10 setup (with pip caching), `pip install -r requirements.txt`, `flake8 .`, and `pytest --cov --cov-report=term-missing`. Deliberately did not add a `black --check` step — the project has pre-existing formatting debt untouched by this epic (see 7.2 session notes) that would fail CI on the very first run through no fault of new work.

Validated locally end-to-end rather than trusting the YAML alone: parsed the workflow file with PyYAML to confirm valid syntax (note — PyYAML parses the bare `on:` key as the boolean `True` due to YAML 1.1's boolean-literal quirk; this is a well-known PyYAML artifact, not a bug — GitHub's own parser handles `on:` correctly, which is why every real-world GitHub Actions workflow uses this exact syntax). Then ran the exact three commands the workflow will run (`pip install`, `flake8 .`, `pytest --cov`) with `.env` temporarily removed, simulating exactly what a CI runner will see (no secrets file). All three passed — this is the payoff of the 7.5.2 test-isolation work: the suite needs zero secrets configured in GitHub for CI to go green. `.env` restored and confirmed the real-credentials path still works afterward.

**7.6.5 (2026-07-17)** — done by the user directly in GitHub (repo-admin setting, not a code change): branch protection on `main` now requires the "Lint & Test" check to pass before merging.

### 7.6.6 first real run — failure and fix (2026-07-17)

The user pushed the branch themselves and the first real CI run failed at the "Run linting (flake8)" step with `Process completed with exit code 127` (shell for "command not found"). Root cause: `flake8` was never listed in `requirements.txt` — it worked locally throughout this entire epic only because it happened to already be installed in the pre-existing dev venv from before Epic 7 started, so the gap was invisible to every local validation run. CI's "Install dependencies" step only runs `pip install -r requirements.txt`, which never installed it, so `flake8 .` wasn't found on PATH.

Fix: added `flake8==7.3.0` (the version already installed locally) to `requirements.txt`. Verified properly this time — not just `pip show`, but installing into a completely bare venv with nothing else present and confirming `flake8 .` both installs and runs clean against the repo. (A full from-scratch reinstall of every pinned dependency was also attempted to mirror the CI job exactly, but hit a Windows long-path filesystem limitation local to this machine's temp directory — unrelated to the actual fix and not something the Ubuntu-based GitHub runner will hit, so the narrower bare-venv verification of just the missing package stands in for it.)

Same gap exists for `black` (also installed locally, also missing from `requirements.txt`) but CI doesn't invoke `black`, so it isn't blocking — left for the user to decide since it's not part of this failure.

**Lesson for future validation:** local "it works on my machine" checks in an already-populated dev venv can't catch a dependency that's missing from `requirements.txt` but happens to already be installed locally. A real CI failure surfaced what local validation structurally could not.

After the fix, the user re-pushed and confirmed the pipeline went green — 7.6.6 done. 7.6 Continuous Integration is now fully complete (all 6 subtasks done).

---

## 7.7 Dockerization (NEO-315)

Goal: reproducible execution.

| Ticket | Subtask | Status |
|---|---|---|
| NEO-348 | 7.7.1 Create Dockerfile | Done |
| NEO-349 | 7.7.2 Build container | Done |
| NEO-350 | 7.7.3 Launch application inside container | Done |
| NEO-351 | 7.7.4 Mount local database | Done |
| NEO-352 | 7.7.5 Document Docker usage | Done |

**7.7.1 (2026-07-17)** — `Dockerfile` (new, repo root): pinned to `python:3.10.11-slim` matching the local dev Python version, installs `requirements.txt` before copying source (layer-caching), launches the Streamlit dashboard by default with `--server.address=0.0.0.0` (required — Streamlit's default bind is localhost-only, unreachable from outside the container) and `--server.headless=true`. `.dockerignore` (new) created alongside it as a required companion, not optional — without it `COPY . .` would bake `.env` (API key) and `venv/` straight into the image. Docker isn't installed in this environment, so none of 7.7.2 onward could be validated directly — all verification happened on the user's machine.

**7.7.2** — Built via `docker build -t neo-analytics-platform .` on the user's machine; verified via `docker images` showing `neo-analytics-platform:latest` with a valid image ID (941MB total, 208MB content size — plausible for a Python image carrying pandas/numpy/matplotlib/streamlit/altair).

**7.7.3** — Ran via `docker run -p 8501:8501 --env-file .env neo-analytics-platform`. Along the way, found and fixed three real bugs, none of which would have surfaced without an actual container run:
- Docker Desktop wasn't installed under the standard `Program Files` path but per-user under `AppData\Local\Programs\DockerDesktop` — findable via `Get-Command docker`, not a bug, just needed locating.
- The user's local `.env` had `BASE_URL ` with a trailing space before the `=`. `python-dotenv` silently trims this (why it never surfaced as a problem running locally), but Docker's `--env-file` parser rejects it outright. Fixed directly in `.env` via a targeted `sed` that only touched the key name, never exposing the actual secret value.
- `.dockerignore` excluded the entire `docs/` folder as "dev-only," but `src/dashboard/pages/4_Model_Card.py` reads `docs/risk_model_card.md` at runtime — a genuine runtime dependency, not just documentation. Fixed by removing `docs/` from `.dockerignore` entirely (232K total, negligible size cost) rather than attempting a negation-pattern carve-out that has known cross-version quirks and couldn't be verified without Docker available locally.

After both fixes: container runs, all 5 dashboard tabs are reachable, Model Card renders correctly. The other 4 tabs correctly show `sqlite3.OperationalError: unable to open database file` — expected, since `data/database/` is also excluded from the image (anticipating 7.7.4's volume mount) and no DB file exists inside the container yet.

**7.7.4** — Used a Docker volume mount (`-v`) rather than baking a copy of the database into the image, so the containerized app reads/writes the real local `data/database/` directly instead of a frozen, stale snapshot that would vanish when the container stops. Confirmed `DATABASE_PATH` in `.env` is a relative path (not a Windows absolute path, which wouldn't resolve inside a Linux container) before proceeding. Mounted the whole `data/database/` directory rather than just the `.db` file, since SQLite can create companion `-journal`/`-wal`/`-shm` files alongside it that need to live in the same place. User confirmed all 4 previously-failing tabs (Home, Risk Rankings, Explorer, Analytics) now load real local data correctly.

**Known limitations in the command used, not yet resolved — for 7.7.5 to cover:**
- `${PWD}` syntax works in PowerShell/Git Bash/Unix shells but fails outright in plain Windows Command Prompt (`%CD%` there instead)
- Must be run from the project root, or the mount silently points at the wrong location
- Assumes `data/database/neows.db` already exists locally — it's gitignored, so a fresh clone has none and would need to run the ingestion pipeline first
- Assumes the image was already built locally under the tag `neo-analytics-platform`
- Assumes the runner has their own valid `.env` (intentional/correct, not a bug — just worth documenting explicitly rather than leaving implicit)

**7.7.5** — `docs/docker.md` (new): prerequisites (Docker Desktop + WSL 2), build/run commands with both PowerShell/Git Bash and cmd.exe variants, running the ingestion pipeline inside a container via command override, what's deliberately excluded from the image and why, and a troubleshooting table covering every real failure hit in 7.7.2-7.7.4 (Docker Desktop not on PATH, engine not running, `.env` whitespace, missing `--env-file`, missing volume mount). `README.md` updated with a "Run with Docker" quick-start section pointing to it, and the stale "Docker" entry removed from the roadmap's "Potential future technologies" list since it's no longer future work.

7.7 Dockerization is now fully complete (all 5 subtasks done).

---

## 7.8 Documentation Excellence (NEO-316)

Goal: make the project understandable.

| Ticket | Subtask | Status |
|---|---|---|
| NEO-353 | 7.8.1 Refine README as necessary | Done |
| NEO-354 | 7.8.2 Update architecture diagram(s) | Done |
| NEO-355 | 7.8.3 Document installation | Done |
| NEO-356 | 7.8.4 Document project structure | Done |
| NEO-357 | 7.8.5 Document developer workflow | Done |
| NEO-358 | 7.8.6 Document testing | Done |
| NEO-359 | 7.8.7 Document future roadmap | Done |

Before writing anything, surveyed the existing docs against the current codebase rather than assuming they were current. Found that Epic 7's own refactoring (7.2's TD-02 and TD-10) had broken the accuracy of `docs/dashboard_architecture.md` — it still described `src/dashboard/db.py` and `src/dashboard/config.py`, both renamed/deleted months earlier in this same epic, and had a whole section titled "Known inconsistency, documented rather than silently fixed" describing a problem TD-02 had already fixed. `docs/architecture.md` had the same issue at the module-path level (`db.py`, `parse_data.py` — neither exists; actual code lives in `src/db/`, `src/parsing/`). The README's roadmap section had matching stale references plus described Epic 7 as entirely still-aspirational.

**7.8.2** — Fixed first, since other docs reference it. `docs/architecture.md`: corrected every "Primary module" reference to the actual current package paths, added a new "Quality & Deployment Infrastructure" component covering config/testing/CI/Docker (none of which existed when this doc was originally written), updated the Development Tooling list. `docs/dashboard_architecture.md`: fixed the UI layer table and the layered-overview ASCII diagram to reference `src/db/connection.py` and `src/dashboard/ui_settings.py` instead of the deleted/renamed files, added the missing `palette.py` entry, and rewrote the "known inconsistency" section to correctly describe it as **resolved** (by TD-02 deleting the duplicate module, not just documented around).

**7.8.1 + 7.8.4** — README: expanded the Project Structure section from a 5-line top-level list into an annotated tree showing the actual `src/`/`tests/` subpackage layout, `sql/`, `.github/workflows/`, and `Dockerfile`. Added a Documentation Index grouping all 16 files in `docs/` by category (engineering / data & schema / risk model / Epic 7 process) — previously undiscoverable without browsing the folder. Fixed the roadmap's stale module references for NEO-2/3/5/6, and replaced NEO-7's aspirational "Key objectives" list with an actual per-sub-story status checklist (7.1-7.7 done, 7.8 in progress at time of writing, 7.9-7.11 pending).

**7.8.3 + 7.8.6** — Verified rather than rewrote: installation steps (clone → venv → deps → env config → validation → Docker) were already accurate and complete from prior stories (7.5.4, 7.7.5). Testing was already thoroughly covered by `docs/testing_strategy.md` (7.3.8). Added pointers from the README's "Run tests" section to that doc, and a `pytest --cov` example, rather than duplicating its content.

**7.8.5** — New content; nothing previously documented the actual contribution workflow. Added a "Developer Workflow" section to the README: the `feature/neo-<epic>-<description>` branch naming convention actually used throughout this repo's history, the validation commands to run before pushing (matching exactly what CI runs), and what branch protection on `main` actually requires (passing "Lint & Test" check + at least one approval) before a PR can merge.

**7.8.7** — Covered by the same roadmap rewrite as 7.8.1 — NEO-7's status checklist reflects actual progress rather than a static aspirational list, and the "Potential future technologies" list (already trimmed of "Docker" in 7.7.5) accurately reflects what's still genuinely future (FastAPI, PostgreSQL, cloud infrastructure) versus what's now shipped.

Final state: 78/78 tests passing, flake8 clean (docs-only changes, but re-verified per habit), no broken cross-references in any updated doc.

---

## 7.9 Performance Review (NEO-317)

Goal: teach performance engineering — measure before optimizing, confirm findings with data rather than assumption, and only change what the numbers justify.

| Ticket | Subtask | Status |
|---|---|---|
| NEO-360 | 7.9.1 Measure dashboard startup | Done |
| NEO-361 | 7.9.2 Measure query latency | Done |
| NEO-362 | 7.9.3 Identify bottlenecks | Done |
| NEO-363 | 7.9.4 Optimize slow operations | Done |
| NEO-364 | 7.9.5 Re-measure improvements | Done |

Dataset at measurement time: 4,084 asteroids, 5,551 close-approach records, 4,084 orbital-parameter records (`data/database/neows.db`, 2.2 MB).

**7.9.1 — Measured dashboard startup.** Timed end-to-end from process launch to the first successful HTTP response, using a locally-run `streamlit run` (Docker isn't reachable from this environment, so this was measured directly on the host rather than in-container). Two distinct numbers matter, and they're very different: a **cold** run (first-ever import of `streamlit`/`altair`/`pandas` in a session, before the OS has any of those files in its disk cache) took ~13-22 seconds; a **warm** run (OS disk cache already populated, which is the realistic case for every start after the first) took ~1.1-1.2 seconds consistently across three separate runs. Broke the warm number down further by timing each import in isolation: `streamlit` ~0.42s, `altair` ~0.24s, `pandas` ~0.39s — together accounting for essentially all of the ~1.1s startup cost. Also measured a *second* request against an already-running server (the realistic case for every page load after the first): ~100-140ms, confirming Python's module-level import caching means the ~1s import cost is paid once per server process, not once per request.

**7.9.2 — Measured query latency.** Timed the three data-service functions that scan the full dataset (the ones with the largest result sets): `compute_risk_scores` (backs `get_all_scores`, the central cached data source every page depends on) at ~57ms cold (SQL fetch ~25ms + pure-Python feature-building ~10ms + overhead), `get_all_close_approaches` at ~23ms, and `get_feature_matrix` at ~20ms. For comparison, isolated the cost of things that could plausibly add up: opening a new SQLite connection (~0.1ms — negligible, confirms the current per-function-call connection pattern isn't a real cost), and a single indexed single-asteroid lookup (`get_close_approaches` for one asteroid, ~0.04ms).

**7.9.3 — Identified bottlenecks.** Ran `EXPLAIN QUERY PLAN` on every multi-table join in `data_service.py`/`risk_score.py` to check for full table scans; all three confirmed `SEARCH ... USING INDEX` on the join columns (SQLite's implicit indexes from `PRIMARY KEY` and the `UNIQUE(asteroid_id, close_approach_date)` constraint already cover every join in use — no missing index was found). The real finding: **the database is not the bottleneck.** At 20-60ms, query latency is roughly 20-50x smaller than the ~1.1s warm startup cost, which is dominated almost entirely by importing `streamlit`/`altair`/`pandas` — a fixed cost of the chosen visualization stack that can't be reduced without removing chart/dataframe functionality. Tested one candidate query rewrite (pre-aggregating `close_approaches` in a subquery before joining, instead of aggregating inline across a 3-way join) against `compute_risk_scores`'s hot query — an initial sequential A/B test suggested a ~26% improvement, but a more rigorous interleaved 50-iteration test (alternating old/new on every iteration, to cancel out disk-cache and OS-scheduling drift between blocks) showed no real difference within measurement noise. The same rewrite applied to `get_feature_matrix`'s structurally similar query made it measurably *slower*. Concluded this rewrite was a false lead from an underpowered test and did not apply it — a deliberate example of not shipping a "looks smart" change that doesn't survive rigorous re-measurement. The one genuine gap found: `render_sidebar()` — called by every one of the 5 dashboard pages at module level, i.e. on every single Streamlit rerun (every widget interaction, not just once per session) — calls `get_weights()`, which re-reads and re-validates `weights.json` from disk on every call. Unlike every other data-access path in `data_service.py`, this one had no `@st.cache_data` caching, making it the only genuinely uncached, frequently-hit operation in the app.

**7.9.4 — Optimized slow operations.** Added a cached wrapper `get_weights()` to `src/dashboard/data_service.py` (decorated with `@st.cache_data`, matching the pattern already used for every other data-access function in that module) and repointed `src/dashboard/layout.py`'s import from `src.models.risk_score.get_weights` to `src.dashboard.data_service.get_weights`. Deliberately did *not* add the caching directly inside `src/models/risk_score.py` — that module has no Streamlit dependency by design (it's imported by the standalone pipeline and unit-tested independently of the dashboard), and `tests/models/test_risk_score.py` relies on `get_weights()` re-reading from a monkeypatched path on every call to test the missing-file-fallback and validation-error cases; caching at that layer would have broken those tests. Caching one layer up in the dashboard preserves both. No changes made to the SQL queries or the risk-scoring pipeline — 7.9.3 established there was nothing there worth changing.

**7.9.5 — Re-measured improvements.** Confirmed the fix works as intended: simulated 20 sidebar reruns calling `data_service.get_weights()` — the first call (cache miss) cost ~1.1ms, but every subsequent call (cache hit) dropped to ~0.02ms median, a ~50-80x reduction on the operation this fix actually targets. Re-ran the full end-to-end startup and warm-request measurements from 7.9.1 against the fixed code to confirm no regression: startup to first response ~1.2s (unchanged), warm repeat requests ~77-104ms (consistent with, and if anything modestly better than, the ~100-140ms baseline — expected, since the redundant per-rerun file read is now eliminated). Re-ran the full test suite and flake8 after the change: 78/78 passing, clean. Overall conclusion for the story: the application was already well-optimized for its current data scale — proper index usage, no N+1 query patterns, and effective `st.cache_data` caching everywhere except one path. That one gap is now closed. The dominant cost of dashboard startup (library imports) is an accepted, documented, architectural cost of the stack rather than a bug — the correct performance-engineering conclusion here isn't "make everything faster," it's "measure carefully, fix the one real gap, and don't manufacture work where the numbers don't support it."

Files touched: `src/dashboard/data_service.py`, `src/dashboard/layout.py`.

---

## Session log

- **2026-07-15** — Kicked off Epic 7. Reviewed codebase structure and baseline gaps (no CI, no Docker, tests only cover `parsing/`). Completed 7.1.1 repository review; findings above. Created this tracking doc. Completed 7.1.2 — created `docs/technical_debt_register.md` with 12 prioritized items. Completed 7.1.3 — confirmed the register's existing High/Medium/Low tagging already satisfies this subtask. Completed 7.1.4 — reviewed the full register with the product owner; all 12 items confirmed with no changes. **7.1 Technical Debt Assessment complete.** Completed 7.2 Code Refactoring — applied all 12 TD items across the 6 subtasks (including TD-08, scoped in with the product owner despite the strict no-behavior-change bar); pytest 11/11 passing, flake8 clean, py_compile clean on every touched module. **7.2 Code Refactoring complete**, pending the user's own manual pass over the dashboard pages. Completed 7.3 Automated Testing — restructured `tests/` to mirror `src/`, built shared representative fixtures and two DB-fixture strategies, wrote unit/integration tests for parsing, db, the risk engine, and the dashboard data service (61 new tests, 72 total), added a TD-08 regression test, installed pytest-cov and scoped the 70-80% coverage target to core logic (98% achieved) after reviewing the scope question with the product owner, and documented it all in `docs/testing_strategy.md`. **7.3 Automated Testing complete.** Completed 7.5 Configuration Management — centralized previously-duplicated HTTP/pipeline/logging constants into `src/config.py` as environment-overridable values with unchanged defaults, decoupled the test suite from needing real secrets (verified by running the full suite with `.env` temporarily removed), added validation for the new config values, and documented everything in `docs/configuration.md`. **7.5 Configuration Management complete.**
- **2026-07-16** — Started 7.6 Continuous Integration — created `.github/workflows/ci.yml` covering 7.6.1-7.6.4 (checkout, Python setup, install deps, lint, test), validated end-to-end locally with `.env` hidden to confirm CI needs no secrets to go green. 7.6.5 (branch protection) and 7.6.6 (verify a real pipeline run, requires pushing) deferred to a later session with the user's agreement — nothing pushed yet.
- **2026-07-17** — Cleaned up `.gitignore` before the user's first commit/push (untracked `.coverage` and the `data/` output CSVs that had been accidentally committed). User pushed and set up branch protection (7.6.5) themselves. First real CI run failed at the lint step (exit 127 — `flake8` missing from `requirements.txt`, invisible to local checks since it was already installed in the dev venv); fixed by pinning `flake8==7.3.0`, verified in a truly bare venv this time. User re-pushed and confirmed green. **7.6 Continuous Integration complete** (all 6 subtasks done). Resolved the open Epic 5 PR's merge conflict with `main` (both branches had independently diverged and redone early epics' work) and backported the CI workflow + a `requirements.txt` fix (same stdlib-pseudo-package bug found in the exit-1 install failure) to both `feature/neo-5-risk-scoring` and `feature/neo-6-dashboard`, since neither had the workflow file or working dependencies yet. Started 7.7 Dockerization — created `Dockerfile`/`.dockerignore` (7.7.1). User installed Docker Desktop and, with guidance, built the image (7.7.2) and launched the container (7.7.3), surfacing and fixing three real bugs along the way: a trailing space in `.env`'s `BASE_URL` key (Docker's `--env-file` parser is stricter than `python-dotenv`), and `docs/` being wrongly excluded from the image despite `4_Model_Card.py` reading a file from it at runtime. Dashboard confirmed running inside the container; database-dependent tabs correctly fail pending 7.7.4. Mounted the local database as a Docker volume (7.7.4) — user confirmed all previously-failing tabs now load real data. Documented Docker usage (7.7.5) in `docs/docker.md`, covering every real failure hit in 7.7.2-7.7.4. **7.7 Dockerization complete** (all 5 subtasks done). Completed 7.8 Documentation Excellence — found and fixed real staleness that Epic 7's own refactoring had introduced into `docs/architecture.md` and `docs/dashboard_architecture.md` (both still referenced modules renamed/deleted in 7.2), rewrote the README's roadmap section to replace stale module paths and an aspirational Epic 7 description with an accurate per-story status checklist, added a Documentation Index for the 16 files now in `docs/`, expanded the project structure section into an actual package tree, and added a new Developer Workflow section covering branching convention, pre-push validation, and PR/CI requirements. **7.8 Documentation Excellence complete** (all 7 subtasks done).
- **2026-07-20** — Completed 7.9 Performance Review. Measured dashboard startup (~1.1-1.2s warm, dominated by `streamlit`/`altair`/`pandas` import cost; ~13-22s cold on first-ever run before the OS disk cache is populated) and query latency for every full-scan data-service function (20-60ms range). Confirmed via `EXPLAIN QUERY PLAN` that every join already uses the correct index — no full table scans. Rigorously A/B tested a candidate query rewrite for the hottest query and found, under interleaved measurement, that it was not actually faster (an initial sequential test had suggested a 26% win that didn't replicate) — did not apply it. Found and fixed one genuine gap: `get_weights()` was re-reading and re-validating `weights.json` from disk on every Streamlit rerun across all 5 pages (the only uncached, frequently-hit operation in the app), fixed by adding a `@st.cache_data` wrapper in `data_service.py` rather than caching inside the Streamlit-independent `risk_score.py` module (which would have broken its existing unit tests). Re-measured after the fix: ~50-80x faster on cache hits, no regression in end-to-end startup or warm-request timing, 78/78 tests still passing. **7.9 Performance Review complete** (all 5 subtasks done).
