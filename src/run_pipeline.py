import argparse
import logging

from src.db.init_db import initialize_database
from src.etl.fetch_neows import fetch_neows_feed
from src.logging import setup_logging
from src.parsing.parse_asteroids import parse_asteroid
from src.parsing.parse_close_approaches import parse_close_approaches
from src.parsing.parse_orbital_parameters import parse_orbital_parameters

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
