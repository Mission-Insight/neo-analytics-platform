# Technical Debt Register

Register of technical debt identified during [7.1.1 Review Entire Repository](epic_7_progress.md#711-review-entire-repository--findings-2026-07-15) (NEO-319). Each item lists the issue, its impact, a recommendation, and a priority. Prioritization rationale and sequencing live in 7.1.3.

Priority scale: **High** (correctness risk or blocks other Epic 7 stories) · **Medium** (maintainability/drift risk) · **Low** (cosmetic/cleanup).

---

## Duplication

| ID | Issue | Impact | Recommendation | Priority |
|---|---|---|---|---|
| TD-01 | Model weights hardcoded independently in `src/models/risk_score.py` (`_DEFAULT_WEIGHTS`), `src/models/weights.json`, and `src/dashboard/config.py` (`WEIGHT_*`) | No sync mechanism — changing scoring weights silently desyncs the dashboard sidebar display from the actual model, misleading users about what's being scored | Make `weights.json` the single source of truth; have the dashboard read it (via `risk_score._load_weights()` or a shared accessor) instead of hardcoding a copy | Medium |
| TD-02 | Two independent DB connection implementations: `src/db/connection.py` and `src/dashboard/db.py` (the latter reimplements its own `.env` loading and `DATABASE_PATH` validation) | Two sources of truth for DB config; a fix or env var rename applied to one can silently miss the other | Delete `src/dashboard/db.py`; import `get_connection`/`DB_PATH` from `src/db/connection.py` and `src/config.py` | Medium |
| TD-03 | `sys.path.insert(0, ...)` + `st.set_page_config(...)` boilerplate repeated verbatim across `app.py` and all 4 files in `src/dashboard/pages/` | Copy-paste drift risk; every new page repeats the same fragile path hack | Extract a shared `bootstrap_page()` helper in `src/dashboard/layout.py`; consider packaging so the path hack isn't needed at all | Low |
| TD-04 | Lookup-or-raise pattern (`SELECT started_at ... WHERE run_id = ?` + not-found check + duration calc) duplicated between `complete_ingestion_run` and `fail_ingestion_run` in `src/db/log_ingestion.py` | Minor maintenance cost; low risk since both call sites are in one file | Extract a private `_get_started_at(conn, run_id)` helper | Low |
| TD-05 | Chart color-palette dicts (e.g. `_TIMELINE_COLOR`, `_POPULATION_COLORS`) redefined per-file across `app.py`, `2_Explorer.py`, `3_Analytics.py`, with identical hex values copy-pasted | Palette changes require hunting across multiple files; risk of visual inconsistency if one copy is missed | Centralize in a shared palette module (e.g. `src/dashboard/palette.py`) and import everywhere | Low |

## Long functions / files

| ID | Issue | Impact | Recommendation | Priority |
|---|---|---|---|---|
| TD-06 | `src/dashboard/pages/3_Analytics.py` is a 500-line top-level script — mostly module-level procedural code, not wrapped in functions | Directly blocks 7.3 Automated Testing: this logic can't be unit tested without running Streamlit; also hardest file in the repo to safely modify | Decompose into functions per section (timeline, distance distribution, population comparisons, correlation matrix, scatters, outlier tables) so each can be tested independently of Streamlit rendering | High |
| TD-07 | `fetch_neows_feed` in `src/etl/fetch_neows.py` (~110 lines) mixes retry/backoff control flow, rate-limit handling, and response validation/logging in one function | Hard to unit test retry logic in isolation; increases risk when modifying one concern (e.g. backoff timing) without affecting another (e.g. logging) | Split into smaller functions: request-with-retry, rate-limit handling, response validation — already partially done for `validate_response_shape`/`handle_http_error`, extend the same pattern to the retry loop | Medium |

## Inconsistent naming

| ID | Issue | Impact | Recommendation | Priority |
|---|---|---|---|---|
| TD-08 | `insert_orbital_parameters` calls `conn.commit()` itself; `insert_asteroids`/`insert_close_approaches` don't and rely on the caller | **Correctness bug, not just style**: `run_pipeline._run_chunk` wraps all three inserts in try/except with rollback-on-failure, but the orbital-parameters commit happens mid-transaction — a later failure (e.g. in `insert_close_approaches`) can't roll back the already-committed orbital insert, leaving the database in a partially-written state despite the run being marked failed | Remove the internal `conn.commit()` from `insert_orbital_parameters`; let `_run_chunk` own the single commit/rollback boundary, consistent with the other two insert functions | High |
| TD-09 | `tests/test_parse_orbital_parameters.py` actually tests `transform_orbital_parameters` (from `src/transform/transform_neows.py`) — no `parse_orbital_parameters` function exists anywhere | Misleading test file name actively hinders 7.3 Automated Testing: new contributors will look for `parse_orbital_parameters` and not find it, or assume transform logic is untested | Rename to `tests/test_transform_orbital_parameters.py` | Low |
| TD-10 | Two unrelated `config.py` modules (`src/config.py` and `src/dashboard/config.py`) share a filename but hold disjoint, unrelated content | Easy to import the wrong `config` module, especially with editor auto-import; the name gives no signal about which one holds env/secrets vs. UI constants | Rename `src/dashboard/config.py` to something distinguishing, e.g. `src/dashboard/ui_settings.py` | Medium |

## Dead code

| ID | Issue | Impact | Recommendation | Priority |
|---|---|---|---|---|
| TD-11 | `scripts/` is empty (only `.gitkeep`) despite being listed in the README's project structure table as holding "utility and automation scripts" | Cosmetic — misleads readers of the README into thinking scripts exist | Either populate with real utility scripts as they're needed, or remove the directory and its README reference until there's real content | Low |
| TD-12 | `requirements.txt` lists stdlib modules as pip packages (`datetime`, `argparse`, `time`, `logging`); no version pins on any dependency | Blocks reproducible builds and 7.6 CI: unpinned deps mean CI/local/prod can silently drift to different library versions; stdlib entries are harmless but signal the file was never cleaned up | Remove the stdlib entries; pin real dependencies (`pandas`, `numpy`, `requests`, `streamlit`, `pytest`, `python-dotenv`, `matplotlib`, `nbqa`) to at least major.minor versions | Medium |

---

## Summary

| Priority | Count | IDs |
|---|---|---|
| High | 2 | TD-06, TD-08 |
| Medium | 5 | TD-01, TD-02, TD-07, TD-10, TD-12 |
| Low | 5 | TD-03, TD-04, TD-05, TD-09, TD-11 |

12 items registered. Sequencing and prioritization for refactoring work happens in 7.1.3.
