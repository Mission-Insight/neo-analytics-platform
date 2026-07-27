import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parents[2] / ".env")

_DB_PATH = os.getenv("DATABASE_PATH")

if not _DB_PATH:
    raise ValueError(
        "DATABASE_PATH not found in environment. "
        "Make sure .env exists in the project root and contains DATABASE_PATH=<path>."
    )

DB_PATH = Path(_DB_PATH)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn
