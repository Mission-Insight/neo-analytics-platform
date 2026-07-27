from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

NASA_API_KEY = os.getenv("NASA_API_KEY")
DB_PATH = os.getenv("DATABASE_PATH")
B_URL = os.getenv("BASE_URL")

if not NASA_API_KEY:
    raise ValueError(
        "NASA_API_KEY was not found. Make sure your .env file"
        "exists in the project root and contains NASA_API_KEY=your_api_key_here."
    )

if not DB_PATH:
    raise ValueError(
        "DATABASE_PATH was not found. Make sure your .env file"
        "exists in the project root and contains DATABASE_PATH=your_database_path_here."
    )

if not B_URL:
    raise ValueError(
        "BASE_URL was not found. Make sure your .env file"
        "exists in the project root and contains BASE_URL=your_base_url_here."
    )

DB_PATH = Path(DB_PATH)
BASE_URL: str = B_URL


def _get_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"{name} must be an integer, got {raw!r}.")


def _get_float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        raise ValueError(f"{name} must be a number, got {raw!r}.")


# ── HTTP request tuning (NASA API calls) ────────────────────────────────────
HTTP_TIMEOUT_SECONDS = _get_int_env("HTTP_TIMEOUT_SECONDS", 30)
HTTP_MAX_RETRIES = _get_int_env("HTTP_MAX_RETRIES", 3)
HTTP_RETRY_BASE_DELAY_SECONDS = _get_int_env("HTTP_RETRY_BASE_DELAY_SECONDS", 1)
HTTP_RATE_LIMIT_BACKOFF_SECONDS = _get_int_env("HTTP_RATE_LIMIT_BACKOFF_SECONDS", 60)
HTTP_REQUEST_DELAY_SECONDS = _get_float_env("HTTP_REQUEST_DELAY_SECONDS", 1.0)

# ── Pipeline chunking ────────────────────────────────────────────────────────
PIPELINE_MAX_CHUNK_DAYS = _get_int_env("PIPELINE_MAX_CHUNK_DAYS", 7)
PIPELINE_CHUNK_DELAY_SECONDS = _get_int_env("PIPELINE_CHUNK_DELAY_SECONDS", 5)

# ── Logging ────────────────────────────────────────────────────────────────
_VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
if LOG_LEVEL not in _VALID_LOG_LEVELS:
    raise ValueError(
        f"LOG_LEVEL must be one of {sorted(_VALID_LOG_LEVELS)}, got {LOG_LEVEL!r}."
    )

LOG_MAX_BYTES = _get_int_env("LOG_MAX_BYTES", 1_000_000)
LOG_BACKUP_COUNT = _get_int_env("LOG_BACKUP_COUNT", 5)
