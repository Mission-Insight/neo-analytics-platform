# Configuration

The project draws a line between three different kinds of "configurable" values, each
owned by a different file. Knowing which one a value belongs to tells you whether it's
safe to change without a code change, and whether it belongs in version control.

| Kind | Lives in | Examples | In version control? |
|---|---|---|---|
| Secrets / deployment config | `.env` (loaded by `src/config.py`) | API key, database path, base URL, HTTP/logging/pipeline tuning | No — `.env` is gitignored; `.env.example` documents the shape |
| App presentation constants | `src/dashboard/ui_settings.py` | App title, icon, dataset window labels | Yes — these aren't secrets or per-environment, they're app content |
| Model parameters | `src/models/weights.json` | Risk scoring weights (size/proximity/velocity/frequency) | Yes — versioned alongside the model that uses them |

This document covers the first category — everything loaded through `src/config.py`.

## Required

These have no default. The app raises a clear `ValueError` at startup if any is missing.

| Variable | Purpose |
|---|---|
| `NASA_API_KEY` | NASA NeoWs API authentication |
| `DATABASE_PATH` | Path to the local SQLite database file |
| `BASE_URL` | NeoWs feed endpoint base URL |

## Optional (operational tuning)

Everything below has a default that matches the values the code used to hardcode
before this story — setting none of them changes nothing. They exist so retry/timeout
behavior, pipeline chunking, and logging can be tuned per environment without a code
change.

| Variable | Default | Purpose |
|---|---|---|
| `HTTP_TIMEOUT_SECONDS` | `30` | Timeout for NASA API requests |
| `HTTP_MAX_RETRIES` | `3` | Max attempts before giving up on a request |
| `HTTP_RETRY_BASE_DELAY_SECONDS` | `1` | Base delay for exponential backoff between retries (NeoWs feed fetch only) |
| `HTTP_RATE_LIMIT_BACKOFF_SECONDS` | `60` | Fallback wait time on a 429 response with no `Retry-After` header |
| `HTTP_REQUEST_DELAY_SECONDS` | `1.0` | Delay between per-asteroid orbital detail requests, to avoid hammering the API |
| `PIPELINE_MAX_CHUNK_DAYS` | `7` | Max days per ingestion chunk (NeoWs feed requests are capped at ~7 days by NASA) |
| `PIPELINE_CHUNK_DELAY_SECONDS` | `5` | Delay between chunks in a multi-chunk pipeline run |
| `LOG_LEVEL` | `INFO` | One of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `LOG_MAX_BYTES` | `1000000` | Log file size before rotation |
| `LOG_BACKUP_COUNT` | `5` | Number of rotated log files kept |

All of these previously existed as hardcoded constants — duplicated, in the case of
the HTTP settings, across both `src/etl/fetch_neows.py` and
`src/etl/fetch_orbital_parameters.py`. They're now defined once in `src/config.py` and
imported everywhere they're used.

## Validation

Invalid values fail fast with a clear error rather than a confusing stack trace later:

- Missing required variables raise `ValueError` naming exactly which one and where to
  set it.
- Optional integer/float variables (e.g. `HTTP_MAX_RETRIES=abc`) raise `ValueError`
  identifying the variable and the bad value, instead of a raw `int()`/`float()`
  `ValueError` pointing at `src/config.py` with no context.
- `LOG_LEVEL` is checked against the five valid Python logging levels.

## Test environment

The test suite (`tests/conftest.py`) loads the real `.env` first if one exists — a
developer's real credentials are never shadowed — then fills in safe dummy values
(`os.environ.setdefault`) for anything still missing. This means `pytest` runs
successfully on a completely fresh clone with no `.env` configured at all: nothing
under test makes a real NASA API call or opens `DATABASE_PATH` directly, every test
that touches a database is pointed at a temp/in-memory one instead (see
`docs/testing_strategy.md`).
