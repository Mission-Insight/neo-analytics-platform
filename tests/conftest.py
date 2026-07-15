import os
from pathlib import Path

from dotenv import load_dotenv

# Load the real .env first (if present) so a developer's real credentials are
# never shadowed, then fill in safe dummy values for anything still missing.
# This lets the suite run on a fresh clone with no .env configured at all —
# nothing under test ever makes a real NASA API call or opens DATABASE_PATH
# directly, everything is monkeypatched to a temp/in-memory database instead.
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
os.environ.setdefault("NASA_API_KEY", "test-api-key")
os.environ.setdefault("DATABASE_PATH", "test.db")
os.environ.setdefault("BASE_URL", "https://example.invalid/test")

import sqlite3  # noqa: E402

import pytest  # noqa: E402

from tests.fixtures.sample_data import seed_sample_data  # noqa: E402

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "sql" / "schema.sql"


@pytest.fixture
def db_conn():
    """
    In-memory SQLite connection initialized from the real sql/schema.sql,
    so tests exercise the same schema the application ships with instead of
    a hand-maintained copy that could drift from it.
    """
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    yield conn
    conn.close()


@pytest.fixture
def seeded_conn(db_conn):
    """db_conn pre-loaded with the representative sample dataset."""
    seed_sample_data(db_conn)
    return db_conn
