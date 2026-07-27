from src.db.connection import get_connection


def test_get_connection_enables_foreign_keys(tmp_path, monkeypatch):
    monkeypatch.setattr("src.db.connection.DB_PATH", tmp_path / "test.db")

    conn = get_connection()
    try:
        assert conn.execute("PRAGMA foreign_keys;").fetchone()[0] == 1
    finally:
        conn.close()


def test_get_connection_creates_database_file(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr("src.db.connection.DB_PATH", db_path)

    conn = get_connection()
    conn.close()

    assert db_path.exists()
