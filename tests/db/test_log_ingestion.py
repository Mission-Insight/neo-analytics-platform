import pytest

from src.db.log_ingestion import (
    calculate_duration_seconds,
    complete_ingestion_run,
    fail_ingestion_run,
    start_ingestion_run,
)


def test_calculate_duration_seconds():
    duration = calculate_duration_seconds(
        "2025-01-01T00:00:00+00:00", "2025-01-01T00:01:30+00:00"
    )
    assert duration == 90.0


def test_start_ingestion_run_creates_record(db_conn):
    run_id = start_ingestion_run(db_conn, "2025-01-01", "2025-01-07")
    db_conn.commit()

    row = db_conn.execute(
        "SELECT status, start_date, end_date FROM ingestion_runs WHERE run_id = ?",
        (run_id,),
    ).fetchone()
    assert row == ("STARTED", "2025-01-01", "2025-01-07")


def test_complete_ingestion_run_updates_record(db_conn):
    run_id = start_ingestion_run(db_conn, "2025-01-01", "2025-01-07")
    db_conn.commit()

    complete_ingestion_run(
        db_conn,
        run_id,
        asteroid_count=5,
        close_approach_count=10,
        orbital_parameter_count=5,
    )
    db_conn.commit()

    row = db_conn.execute(
        "SELECT status, asteroid_count, close_approach_count, orbital_parameter_count "
        "FROM ingestion_runs WHERE run_id = ?",
        (run_id,),
    ).fetchone()
    assert row == ("SUCCESS", 5, 10, 5)


def test_complete_ingestion_run_raises_for_unknown_run(db_conn):
    with pytest.raises(RuntimeError):
        complete_ingestion_run(db_conn, 999, 0, 0, 0)


def test_fail_ingestion_run_updates_record_and_logs_failure(db_conn):
    run_id = start_ingestion_run(db_conn, "2025-01-01", "2025-01-07")
    db_conn.commit()

    fail_ingestion_run(db_conn, run_id, "boom")
    db_conn.commit()

    run_row = db_conn.execute(
        "SELECT status, error_message FROM ingestion_runs WHERE run_id = ?",
        (run_id,),
    ).fetchone()
    assert run_row == ("FAILED", "boom")

    failure_row = db_conn.execute(
        "SELECT run_id, error_message FROM ingestion_failures WHERE run_id = ?",
        (run_id,),
    ).fetchone()
    assert failure_row == (run_id, "boom")


def test_fail_ingestion_run_raises_for_unknown_run(db_conn):
    with pytest.raises(RuntimeError):
        fail_ingestion_run(db_conn, 999, "boom")
