import logging
import sqlite3

logger = logging.getLogger(__name__)


def insert_close_approaches(
    conn: sqlite3.Connection,
    close_approaches: list[dict],
) -> None:
    if not close_approaches:
        logger.warning("No close approach records to insert.")
        return

    sql = """
    INSERT INTO close_approaches (
        asteroid_id,
        close_approach_date,
        relative_velocity_kps,
        miss_distance_km,
        orbiting_body
    )
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(asteroid_id, close_approach_date) DO UPDATE SET
        relative_velocity_kps = excluded.relative_velocity_kps,
        miss_distance_km = excluded.miss_distance_km,
        orbiting_body = excluded.orbiting_body;
    """

    params = [
        (
            approach.get("asteroid_id"),
            approach.get("close_approach_date"),
            approach.get("relative_velocity_kps"),
            approach.get("miss_distance_km"),
            approach.get("orbiting_body"),
        )
        for approach in close_approaches
    ]

    conn.executemany(sql, params)

    logger.info(
        "Inserted or updated %s close approach records.",
        len(close_approaches),
    )
