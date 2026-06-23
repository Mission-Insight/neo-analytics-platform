import sqlite3

from src.config import DB_PATH


def get_connection() -> sqlite3.Connection:
    """
    Create and return a SQLite database connection.

    Foreign key enforcement is enabled for every connection.
    """

    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON;")

    return connection
