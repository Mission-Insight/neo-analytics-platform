import logging
import sqlite3

logger = logging.getLogger(__name__)


def insert_asteroids(
    conn: sqlite3.Connection,
    asteroids: list[dict],
) -> None:
    """
    Insert normalized asteroid records into the asteroids table.
    Existing asteroid records are updated.
    """

    if not asteroids:
        logger.warning("No asteroid records to insert.")
        return

    sql = """
    INSERT INTO asteroids (
        asteroid_id,
        name,
        absolute_magnitude_h,
        estimated_diameter_min_km,
        estimated_diameter_max_km,
        is_potentially_hazardous
    )
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(asteroid_id) DO UPDATE SET
        name = excluded.name,
        absolute_magnitude_h = excluded.absolute_magnitude_h,
        estimated_diameter_min_km = excluded.estimated_diameter_min_km,
        estimated_diameter_max_km = excluded.estimated_diameter_max_km,
        is_potentially_hazardous = excluded.is_potentially_hazardous;
    """

    params = [
        (
            asteroid.get("asteroid_id"),
            asteroid.get("name"),
            asteroid.get("absolute_magnitude_h"),
            asteroid.get("estimated_diameter_min_km"),
            asteroid.get("estimated_diameter_max_km"),
            asteroid.get("is_potentially_hazardous"),
        )
        for asteroid in asteroids
    ]

    conn.executemany(sql, params)

    logger.info("Inserted or updated %s asteroid records.", len(asteroids))
