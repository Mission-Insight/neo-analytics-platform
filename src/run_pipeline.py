import argparse
import logging

from src.db.init_db import initialize_database
from src.etl.fetch_neows import fetch_neows_feed
from src.logging import setup_logging
from src.parsing.parse_asteroids import parse_asteroid
from src.parsing.parse_close_approaches import parse_close_approaches
from src.parsing.parse_orbital_parameters import parse_orbital_parameters
from src.db.connection import get_connection

setup_logging()
logger = logging.getLogger(__name__)


def parse_neows_feed(raw_data: dict) -> tuple[list[dict], list[dict], list[dict]]:
    asteroid_records = []
    close_approach_records = []
    orbital_parameter_records = []

    near_earth_objects = raw_data.get("near_earth_objects", {})

    for asteroids_on_date in near_earth_objects.values():
        for asteroid in asteroids_on_date:
            asteroid_records.append(parse_asteroid(asteroid))
            close_approach_records.extend(parse_close_approaches(asteroid))
            orbital_parameter_records.append(parse_orbital_parameters(asteroid))

    return asteroid_records, close_approach_records, orbital_parameter_records


def run_pipeline(start_date: str, end_date: str) -> None:
    logger.info("Starting Neo Analytics pipeline.")

    logger.info("Initializing database.")
    initialize_database()

    logger.info("Fetching NeoWs data from %s to %s.", start_date, end_date)
    raw_data = fetch_neows_feed(start_date, end_date)

    logger.info("Parsing NeoWs data.")
    asteroids, close_approaches, orbital_parameters = parse_neows_feed(raw_data)

    logger.info("Parsed %s asteroid records.", len(asteroids))
    logger.info("Parsed %s close approach records.", len(close_approaches))
    logger.info("Parsed %s orbital parameter records.", len(orbital_parameters))

    logger.info("Inserting parsed records into the database.")
    with get_connection() as conn:
        cur = conn.cursor()

        if asteroids:
            asteroid_sql = """
            INSERT INTO asteroids (
                asteroid_id, name, absolute_magnitude_h,
                estimated_diameter_min_km, estimated_diameter_max_km,
                is_potentially_hazardous
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(asteroid_id) DO UPDATE SET
                name=excluded.name,
                absolute_magnitude_h=excluded.absolute_magnitude_h,
                estimated_diameter_min_km=excluded.estimated_diameter_min_km,
                estimated_diameter_max_km=excluded.estimated_diameter_max_km,
                is_potentially_hazardous=excluded.is_potentially_hazardous;
            """

            asteroid_params = [
                (
                    a.get("asteroid_id"),
                    a.get("name"),
                    a.get("absolute_magnitude_h"),
                    a.get("estimated_diameter_min_km"),
                    a.get("estimated_diameter_max_km"),
                    a.get("is_potentially_hazardous"),
                )
                for a in asteroids
            ]

            cur.executemany(asteroid_sql, asteroid_params)

        if orbital_parameters:
            orbital_sql = """
            INSERT INTO orbital_parameters (
                asteroid_id, orbit_class_type, orbit_class_description,
                eccentricity, semi_major_axis, inclination, orbital_period,
                perihelion_distance, aphelion_distance
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(asteroid_id) DO UPDATE SET
                orbit_class_type=excluded.orbit_class_type,
                orbit_class_description=excluded.orbit_class_description,
                eccentricity=excluded.eccentricity,
                semi_major_axis=excluded.semi_major_axis,
                inclination=excluded.inclination,
                orbital_period=excluded.orbital_period,
                perihelion_distance=excluded.perihelion_distance,
                aphelion_distance=excluded.aphelion_distance;
            """

            orbital_params = [
                (
                    o.get("asteroid_id"),
                    o.get("orbit_class_type"),
                    o.get("orbit_class_description"),
                    o.get("eccentricity"),
                    o.get("semi_major_axis"),
                    o.get("inclination"),
                    o.get("orbital_period"),
                    o.get("perihelion_distance"),
                    o.get("aphelion_distance"),
                )
                for o in orbital_parameters
            ]

            cur.executemany(orbital_sql, orbital_params)

        if close_approaches:
            # To avoid inserting duplicates when re-running the pipeline,
            # delete any existing approach for the same
            # asteroid & date before inserting.
            delete_ca_sql = (
                "DELETE FROM close_approaches WHERE asteroid_id = ? "
                " AND close_approach_date = ?"
            )
            insert_ca_sql = """
            INSERT INTO close_approaches (
                asteroid_id, close_approach_date, relative_velocity_kps,
                miss_distance_km, orbiting_body
            ) VALUES (?, ?, ?, ?, ?)
            """

            for ca in close_approaches:
                cur.execute(
                    delete_ca_sql,
                    (ca.get("asteroid_id"), ca.get("close_approach_date")),
                )
                cur.execute(
                    insert_ca_sql,
                    (
                        ca.get("asteroid_id"),
                        ca.get("close_approach_date"),
                        ca.get("relative_velocity_kps"),
                        ca.get("miss_distance_km"),
                        ca.get("orbiting_body"),
                    ),
                )

        conn.commit()
        logger.info("Inserted records into database.")

    logger.info("Pipeline completed successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Neo Analytics pipeline.")

    parser.add_argument(
        "--start-date",
        required=True,
        help="Start date in YYYY-MM-DD format.",
    )

    parser.add_argument(
        "--end-date",
        required=True,
        help="End date in YYYY-MM-DD format.",
    )

    args = parser.parse_args()

    try:
        run_pipeline(args.start_date, args.end_date)
    except Exception:
        logger.exception("Pipeline execution failed.")
        raise


if __name__ == "__main__":
    main()
