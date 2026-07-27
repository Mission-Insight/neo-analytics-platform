import sqlite3

from src.db.init_db import initialize_database


def test_initialize_database_creates_expected_tables(monkeypatch, capsys):
    conn = sqlite3.connect(":memory:")
    monkeypatch.setattr("src.db.init_db.get_connection", lambda: conn)

    initialize_database()

    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert {
        "asteroids",
        "close_approaches",
        "orbital_parameters",
        "ingestion_runs",
        "ingestion_failures",
    } <= tables

    conn.close()
