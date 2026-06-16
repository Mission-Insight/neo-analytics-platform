from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "neows.db"


def get_connection() -> sqlite3.Connection:
    """
    Create and return a SQLite database connection.

    Foreign key enforcement is enabled for every connection.
    """

    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON;")

    return connection
