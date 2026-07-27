from src.db.load_asteroids import insert_asteroids
from src.db.load_orbital_parameters import insert_orbital_parameters


def _sample_orbital_record(asteroid_id="1", **overrides):
    record = {
        "asteroid_id": asteroid_id,
        "orbit_id": "1",
        "orbit_determination_date": None,
        "first_observation_date": None,
        "last_observation_date": None,
        "data_arc_in_days": None,
        "observations_used": None,
        "orbit_uncertainty": None,
        "minimum_orbit_intersection": None,
        "jupiter_tisserand_invariant": None,
        "epoch_osculation": None,
        "eccentricity": 0.1,
        "semi_major_axis": 1.5,
        "inclination": 5.0,
        "ascending_node_longitude": None,
        "orbital_period": 400.0,
        "perihelion_distance": None,
        "perihelion_argument": None,
        "aphelion_distance": None,
        "perihelion_time": None,
        "mean_anomaly": None,
        "mean_motion": None,
        "equinox": None,
        "orbit_class_type": "APO",
        "orbit_class_description": "Apollo",
        "orbit_class_range": None,
    }
    record.update(overrides)
    return record


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


def test_insert_orbital_parameters_inserts_record(db_conn):
    _insert_parent_asteroid(db_conn)
    insert_orbital_parameters(db_conn, [_sample_orbital_record()])
    db_conn.commit()

    row = db_conn.execute(
        "SELECT asteroid_id, eccentricity, orbit_class_type FROM orbital_parameters"
    ).fetchone()
    assert row == ("1", 0.1, "APO")


def test_insert_orbital_parameters_upserts_on_conflict(db_conn):
    _insert_parent_asteroid(db_conn)
    insert_orbital_parameters(db_conn, [_sample_orbital_record()])
    insert_orbital_parameters(db_conn, [_sample_orbital_record(eccentricity=0.9)])
    db_conn.commit()

    rows = db_conn.execute("SELECT eccentricity FROM orbital_parameters").fetchall()
    assert rows == [(0.9,)]


def test_insert_orbital_parameters_does_not_commit_internally(db_conn):
    """
    Regression test for TD-08: insert_orbital_parameters must not commit on
    its own — the caller (run_pipeline._run_chunk) owns the transaction
    boundary so a later failure can roll this insert back too.
    """
    _insert_parent_asteroid(db_conn)
    db_conn.commit()

    insert_orbital_parameters(db_conn, [_sample_orbital_record()])
    db_conn.rollback()

    count = db_conn.execute("SELECT COUNT(*) FROM orbital_parameters").fetchone()[0]
    assert count == 0


def test_insert_orbital_parameters_handles_empty_list(db_conn):
    insert_orbital_parameters(db_conn, [])

    count = db_conn.execute("SELECT COUNT(*) FROM orbital_parameters").fetchone()[0]
    assert count == 0
