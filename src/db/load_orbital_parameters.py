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
        orbit_id,
        orbit_determination_date,
        first_observation_date,
        last_observation_date,
        data_arc_in_days,
        observations_used,
        orbit_uncertainty,
        minimum_orbit_intersection,
        jupiter_tisserand_invariant,
        epoch_osculation,
        eccentricity,
        semi_major_axis,
        inclination,
        ascending_node_longitude,
        orbital_period,
        perihelion_distance,
        perihelion_argument,
        aphelion_distance,
        perihelion_time,
        mean_anomaly,
        mean_motion,
        equinox,
        orbit_class_type,
        orbit_class_description,
        orbit_class_range
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(asteroid_id) DO UPDATE SET
        orbit_id = excluded.orbit_id,
        orbit_determination_date = excluded.orbit_determination_date,
        first_observation_date = excluded.first_observation_date,
        last_observation_date = excluded.last_observation_date,
        data_arc_in_days = excluded.data_arc_in_days,
        observations_used = excluded.observations_used,
        orbit_uncertainty = excluded.orbit_uncertainty,
        minimum_orbit_intersection = excluded.minimum_orbit_intersection,
        jupiter_tisserand_invariant = excluded.jupiter_tisserand_invariant,
        epoch_osculation = excluded.epoch_osculation,
        eccentricity = excluded.eccentricity,
        semi_major_axis = excluded.semi_major_axis,
        inclination = excluded.inclination,
        ascending_node_longitude = excluded.ascending_node_longitude,
        orbital_period = excluded.orbital_period,
        perihelion_distance = excluded.perihelion_distance,
        perihelion_argument = excluded.perihelion_argument,
        aphelion_distance = excluded.aphelion_distance,
        perihelion_time = excluded.perihelion_time,
        mean_anomaly = excluded.mean_anomaly,
        mean_motion = excluded.mean_motion,
        equinox = excluded.equinox,
        orbit_class_type = excluded.orbit_class_type,
        orbit_class_description = excluded.orbit_class_description,
        orbit_class_range = excluded.orbit_class_range;
    """

    params = [
        (
            orbit.get("asteroid_id"),
            orbit.get("orbit_id"),
            orbit.get("orbit_determination_date"),
            orbit.get("first_observation_date"),
            orbit.get("last_observation_date"),
            orbit.get("data_arc_in_days"),
            orbit.get("observations_used"),
            orbit.get("orbit_uncertainty"),
            orbit.get("minimum_orbit_intersection"),
            orbit.get("jupiter_tisserand_invariant"),
            orbit.get("epoch_osculation"),
            orbit.get("eccentricity"),
            orbit.get("semi_major_axis"),
            orbit.get("inclination"),
            orbit.get("ascending_node_longitude"),
            orbit.get("orbital_period"),
            orbit.get("perihelion_distance"),
            orbit.get("perihelion_argument"),
            orbit.get("aphelion_distance"),
            orbit.get("perihelion_time"),
            orbit.get("mean_anomaly"),
            orbit.get("mean_motion"),
            orbit.get("equinox"),
            orbit.get("orbit_class_type"),
            orbit.get("orbit_class_description"),
            orbit.get("orbit_class_range"),
        )
        for orbit in orbital_parameters
    ]

    conn.executemany(sql, params)

    logger.info(
        "Inserted or updated %s orbital parameter records.",
        len(orbital_parameters),
    )
