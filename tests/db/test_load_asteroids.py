from src.db.load_asteroids import insert_asteroids


def test_insert_asteroids_inserts_records(db_conn):
    insert_asteroids(
        db_conn,
        [
            {
                "asteroid_id": "1",
                "name": "Test",
                "absolute_magnitude_h": 20.0,
                "estimated_diameter_min_km": 0.1,
                "estimated_diameter_max_km": 0.3,
                "is_potentially_hazardous": 1,
            }
        ],
    )
    db_conn.commit()

    row = db_conn.execute(
        "SELECT asteroid_id, name, is_potentially_hazardous FROM asteroids"
    ).fetchone()
    assert row == ("1", "Test", 1)


def test_insert_asteroids_upserts_on_conflict(db_conn):
    base = {
        "asteroid_id": "1",
        "name": "Original",
        "absolute_magnitude_h": 20.0,
        "estimated_diameter_min_km": 0.1,
        "estimated_diameter_max_km": 0.3,
        "is_potentially_hazardous": 0,
    }
    insert_asteroids(db_conn, [base])
    insert_asteroids(db_conn, [{**base, "name": "Updated", "is_potentially_hazardous": 1}])
    db_conn.commit()

    rows = db_conn.execute(
        "SELECT asteroid_id, name, is_potentially_hazardous FROM asteroids"
    ).fetchall()
    assert rows == [("1", "Updated", 1)]


def test_insert_asteroids_handles_empty_list(db_conn):
    insert_asteroids(db_conn, [])

    count = db_conn.execute("SELECT COUNT(*) FROM asteroids").fetchone()[0]
    assert count == 0
