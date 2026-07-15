import sqlite3

import pytest

from src.db.load_asteroids import insert_asteroids
from src.db.load_close_approaches import insert_close_approaches


def _insert_parent_asteroid(conn, asteroid_id="1"):
    insert_asteroids(
        conn,
        [
            {
                "asteroid_id": asteroid_id,
                "name": "Test",
                "absolute_magnitude_h": 20.0,
                "estimated_diameter_min_km": 0.1,
                "estimated_diameter_max_km": 0.3,
                "is_potentially_hazardous": 0,
            }
        ],
    )


def test_insert_close_approaches_inserts_records(db_conn):
    _insert_parent_asteroid(db_conn)
    insert_close_approaches(
        db_conn,
        [
            {
                "asteroid_id": "1",
                "close_approach_date": "2025-01-01",
                "relative_velocity_kps": 10.0,
                "miss_distance_km": 100000.0,
                "orbiting_body": "Earth",
            }
        ],
    )
    db_conn.commit()

    row = db_conn.execute(
        "SELECT asteroid_id, close_approach_date, relative_velocity_kps FROM close_approaches"
    ).fetchone()
    assert row == ("1", "2025-01-01", 10.0)


def test_insert_close_approaches_upserts_on_conflict(db_conn):
    _insert_parent_asteroid(db_conn)
    base = {
        "asteroid_id": "1",
        "close_approach_date": "2025-01-01",
        "relative_velocity_kps": 10.0,
        "miss_distance_km": 100000.0,
        "orbiting_body": "Earth",
    }
    insert_close_approaches(db_conn, [base])
    insert_close_approaches(db_conn, [{**base, "relative_velocity_kps": 12.5}])
    db_conn.commit()

    rows = db_conn.execute("SELECT relative_velocity_kps FROM close_approaches").fetchall()
    assert rows == [(12.5,)]


def test_insert_close_approaches_enforces_foreign_key(db_conn):
    with pytest.raises(sqlite3.IntegrityError):
        insert_close_approaches(
            db_conn,
            [
                {
                    "asteroid_id": "does-not-exist",
                    "close_approach_date": "2025-01-01",
                    "relative_velocity_kps": 10.0,
                    "miss_distance_km": 100000.0,
                    "orbiting_body": "Earth",
                }
            ],
        )


def test_insert_close_approaches_handles_empty_list(db_conn):
    insert_close_approaches(db_conn, [])

    count = db_conn.execute("SELECT COUNT(*) FROM close_approaches").fetchone()[0]
    assert count == 0
