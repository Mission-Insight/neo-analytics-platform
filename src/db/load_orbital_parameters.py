import logging
import sqlite3

logger = logging.getLogger(__name__)


def insert_orbital_parameters(
    conn: sqlite3.Connection,
    orbital_parameters: list[dict],
) -> None:
    if not orbital_parameters:
        logger.warning("No orbital parameter records to insert.")
        return

    sql = """
    INSERT INTO orbital_parameters (
        asteroid_id,
        orbit_class_type,
        orbit_class_description,
        eccentricity,
        semi_major_axis,
        inclination,
        orbital_period,
        perihelion_distance,
        aphelion_distance
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(asteroid_id) DO UPDATE SET
        orbit_class_type = excluded.orbit_class_type,
        orbit_class_description = excluded.orbit_class_description,
        eccentricity = excluded.eccentricity,
        semi_major_axis = excluded.semi_major_axis,
        inclination = excluded.inclination,
        orbital_period = excluded.orbital_period,
        perihelion_distance = excluded.perihelion_distance,
        aphelion_distance = excluded.aphelion_distance;
    """

    params = [
        (
            orbit.get("asteroid_id"),
            orbit.get("orbit_class_type"),
            orbit.get("orbit_class_description"),
            orbit.get("eccentricity"),
            orbit.get("semi_major_axis"),
            orbit.get("inclination"),
            orbit.get("orbital_period"),
            orbit.get("perihelion_distance"),
            orbit.get("aphelion_distance"),
        )
        for orbit in orbital_parameters
    ]

    conn.executemany(sql, params)

    logger.info(
        "Inserted or updated %s orbital parameter records.",
        len(orbital_parameters),
    )
