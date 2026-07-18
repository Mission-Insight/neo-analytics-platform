# Docker Usage

## Prerequisites

- **Docker Desktop** installed and running. On Windows this requires **WSL 2**, which Docker Desktop's installer sets up automatically. After installing, a restart may be required, and the first launch can take a minute or two to finish starting its engine before `docker` commands will work.
- A `.env` file configured (see [configuration.md](configuration.md)). Every user runs the container with their own — API keys are never baked into the image.
- To see real data on the dashboard: an existing local database (`data/database/neows.db`), or run the ingestion pipeline inside the container first (see below). A fresh clone has neither, since `data/` is gitignored.

## Building the image

From the project root:

```bash
docker build -t neo-analytics-platform .
```

Rebuild any time `Dockerfile`, `.dockerignore`, or `requirements.txt` change — an existing image doesn't update itself.

## Running the dashboard

Must be run from the project root — the volume mount below is relative to wherever the shell currently is, and pointing it anywhere else silently mounts the wrong location.

**PowerShell / Git Bash / macOS / Linux:**
```bash
docker run -p 8501:8501 --env-file .env -v "${PWD}/data/database:/app/data/database" neo-analytics-platform
```

**Windows Command Prompt (cmd.exe):** `${PWD}` doesn't exist there — use `%cd%` instead:
```cmd
docker run -p 8501:8501 --env-file .env -v "%cd%/data/database:/app/data/database" neo-analytics-platform
```

Then open **http://localhost:8501**.

What each flag does:
- `-p 8501:8501` — maps the container's Streamlit port to the same port on your machine
- `--env-file .env` — injects your local `.env` as environment variables inside the container, without ever copying the file itself into the image
- `-v ".../data/database:/app/data/database"` — mounts your real local database directory into the container, so the app reads/writes the actual file on disk rather than a stale copy baked into the image

## Running the ingestion pipeline inside the container

The image's default command launches the dashboard, but the same image can run the pipeline instead by overriding the command:

```bash
docker run --env-file .env -v "${PWD}/data/database:/app/data/database" neo-analytics-platform python -m src.run_pipeline --start-date 2024-01-01 --end-date 2026-12-31
```

Since this uses the same volume mount, data written by the pipeline is immediately visible the next time the dashboard container runs.

## What's deliberately excluded from the image

Per `.dockerignore`:
- `.env` — secrets, passed in at runtime instead (see above)
- `venv/`, `data/database/`, `data/raw/`, `logs/` — host-specific or generated at runtime, not something the image should carry a frozen copy of
- Dev-only content not needed to run the app: `tests/`, `notebooks/`, `.git/`, `.github/`, `.vscode/`, `.pytest_cache/`, `.coverage`

## Stopping the container

`Ctrl+C` in the terminal it's running in. Or, from another terminal: `docker ps` to find its ID, then `docker stop <id>`.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `docker: command not found` (or "term not recognized") | Docker Desktop isn't installed, or a terminal opened before install/PATH updated | Install Docker Desktop; open a **new** terminal window afterward |
| `failed to connect to the docker API` (`npipe` error) | Docker Desktop app isn't actually running | Launch Docker Desktop from the Start menu; wait for the whale icon to settle before retrying |
| `invalid env file (.env): variable 'X' contains whitespaces` | A key in `.env` has leading/trailing whitespace around it (e.g. `BASE_URL ` instead of `BASE_URL`) | Remove the whitespace around the key name in `.env` — leave the value itself untouched |
| `ValueError: NASA_API_KEY was not found` inside the app | `--env-file .env` was left off the `docker run` command | Add `--env-file .env` |
| `sqlite3.OperationalError: unable to open database file` | The `-v` volume mount is missing, the command wasn't run from the project root, or `data/database/` doesn't exist yet | Add the `-v` flag; run from the project root; if the database genuinely doesn't exist yet, run the pipeline first (see above) |
| `FileNotFoundError` for a file under `docs/` | Shouldn't happen — `docs/` is intentionally included in the image because `4_Model_Card.py` reads `docs/risk_model_card.md` at runtime | If this recurs after editing `.dockerignore`, check that `docs/` wasn't re-excluded |
