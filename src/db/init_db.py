from pathlib import Path

from src.db.connection import get_connection

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"


def initialize_database() -> None:
    with get_connection() as conn:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as schema_file:
            conn.executescript(schema_file.read())

    print("Database initialized successfully.")


if __name__ == "__main__":
    initialize_database()
