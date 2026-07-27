import sqlite3
from datetime import datetime, timezone


def calculate_duration_seconds(started_at: str, completed_at: str) -> float:
    start = datetime.fromisoformat(started_at)
    end = datetime.fromisoformat(completed_at)

    return (end - start).total_seconds()


def get_utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def start_ingestion_run(
    conn: sqlite3.Connection,
    start_date: str,
    end_date: str,
) -> int:
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO ingestion_runs (
            started_at,
            status,
            start_date,
            end_date
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            get_utc_timestamp(),
            "STARTED",
            start_date,
            end_date,
        ),
    )

    run_id = cursor.lastrowid

    if run_id is None:
        raise RuntimeError("Failed to create ingestion run record.")

    return run_id


def _get_started_at(conn: sqlite3.Connection, run_id: int) -> str:
    row = conn.execute(
        """
        SELECT started_at
        FROM ingestion_runs
        WHERE run_id = ?
        """,
        (run_id,),
    ).fetchone()

    if row is None:
        raise RuntimeError("Ingestion run record not found.")

    return row[0]


def complete_ingestion_run(
    conn: sqlite3.Connection,
    run_id: int,
    asteroid_count: int,
    close_approach_count: int,
    orbital_parameter_count: int,
) -> None:
    completed_at = get_utc_timestamp()

    started_at = _get_started_at(conn, run_id)
    duration_seconds = calculate_duration_seconds(started_at, completed_at)

    conn.execute(
        """
        UPDATE ingestion_runs
        SET
            completed_at = ?,
            duration_seconds = ?,
            status = ?,
            asteroid_count = ?,
            close_approach_count = ?,
            orbital_parameter_count = ?
        WHERE run_id = ?
        """,
        (
            completed_at,
            duration_seconds,
            "SUCCESS",
            asteroid_count,
            close_approach_count,
            orbital_parameter_count,
            run_id,
        ),
    )


def fail_ingestion_run(
    conn: sqlite3.Connection,
    run_id: int,
    error_message: str,
) -> None:
    completed_at = get_utc_timestamp()

    started_at = _get_started_at(conn, run_id)
    duration_seconds = calculate_duration_seconds(started_at, completed_at)

    conn.execute(
        """
        UPDATE ingestion_runs
        SET
            completed_at = ?,
            duration_seconds = ?,
            status = ?,
            error_message = ?
        WHERE run_id = ?
        """,
        (
            completed_at,
            duration_seconds,
            "FAILED",
            error_message,
            run_id,
        ),
    )

    conn.execute(
        """
        INSERT INTO ingestion_failures (
            run_id,
            failed_at,
            error_message
        )
        VALUES (?, ?, ?)
        """,
        (
            run_id,
            completed_at,
            error_message,
        ),
    )
