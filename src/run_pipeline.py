import argparse
import logging
import time
from datetime import date, timedelta

from src.db.connection import get_connection
from src.db.init_db import initialize_database
from src.db.load_asteroids import insert_asteroids
from src.db.load_close_approaches import insert_close_approaches
from src.db.load_orbital_parameters import insert_orbital_parameters
from src.db.log_ingestion import (
    complete_ingestion_run,
    fail_ingestion_run,
    start_ingestion_run,
)
from src.config import PIPELINE_CHUNK_DELAY_SECONDS, PIPELINE_MAX_CHUNK_DAYS
from src.etl.fetch_neows import fetch_neows_feed
from src.logging import setup_logging
from src.models.risk_score import compute_risk_scores
from src.parsing.parse_asteroids import parse_asteroid
from src.parsing.parse_close_approaches import parse_close_approaches
from src.etl.fetch_orbital_parameters import fetch_orbital_parameters_for_feed
from src.transform.transform_neows import transform_orbital_parameters

setup_logging()
logger = logging.getLogger(__name__)


MAX_CHUNK_DAYS = PIPELINE_MAX_CHUNK_DAYS
CHUNK_DELAY_SECONDS = PIPELINE_CHUNK_DELAY_SECONDS


def _date_chunks(start_date: str, end_date: str):
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    current = start
    while current <= end:
        chunk_end = min(current + timedelta(days=MAX_CHUNK_DAYS - 1), end)
        yield current.isoformat(), chunk_end.isoformat()
        current = chunk_end + timedelta(days=1)


def parse_neows_feed(raw_data: dict) -> tuple[list[dict], list[dict]]:
    asteroid_records = []
    close_approach_records = []

    near_earth_objects = raw_data.get("near_earth_objects", {})

    for asteroids_on_date in near_earth_objects.values():
        for asteroid in asteroids_on_date:
            asteroid_records.append(parse_asteroid(asteroid))
            close_approach_records.extend(parse_close_approaches(asteroid))

    return asteroid_records, close_approach_records


def _run_chunk(start_date: str, end_date: str) -> None:
    logger.info("Fetching NeoWs data from %s to %s.", start_date, end_date)
    raw_data = fetch_neows_feed(start_date, end_date)

    logger.info("Parsing NeoWs data.")
    asteroids, close_approaches = parse_neows_feed(raw_data)

    logger.info("Fetching detailed orbital parameter data.")
    raw_orbital_parameters = fetch_orbital_parameters_for_feed(raw_data)

    logger.info("Transforming orbital parameter data.")
    orbital_parameters = transform_orbital_parameters(raw_orbital_parameters)

    logger.info("Parsed %s asteroid records.", len(asteroids))
    logger.info("Parsed %s close approach records.", len(close_approaches))
    logger.info("Parsed %s orbital parameter records.", len(orbital_parameters))

    logger.info("Inserting parsed records into the database.")

    with get_connection() as conn:
        run_id = start_ingestion_run(conn, start_date, end_date)
        conn.commit()

        try:
            insert_asteroids(conn, asteroids)
            insert_orbital_parameters(conn, orbital_parameters)
            insert_close_approaches(conn, close_approaches)

            complete_ingestion_run(
                conn,
                run_id,
                len(asteroids),
                len(close_approaches),
                len(orbital_parameters),
            )

            conn.commit()

        except Exception as error:
            conn.rollback()

            fail_ingestion_run(
                conn,
                run_id,
                str(error),
            )
            conn.commit()

            logger.exception("Database transaction failed. Rolled back changes.")
            raise

    logger.info("Inserted records into database.")


def run_pipeline(start_date: str, end_date: str) -> None:
    logger.info("Starting Neo Analytics pipeline.")

    logger.info("Initializing database.")
    initialize_database()

    chunks = list(_date_chunks(start_date, end_date))
    logger.info(
        "Date range %s to %s spans %s chunk(s) of up to %s days.",
        start_date,
        end_date,
        len(chunks),
        MAX_CHUNK_DAYS,
    )

    for i, (chunk_start, chunk_end) in enumerate(chunks, 1):
        logger.info(
            "Processing chunk %s/%s: %s to %s.",
            i,
            len(chunks),
            chunk_start,
            chunk_end,
        )
        _run_chunk(chunk_start, chunk_end)

        if i < len(chunks):
            logger.info(
                "Chunk %s/%s complete. Waiting %ss before next chunk.",
                i,
                len(chunks),
                CHUNK_DELAY_SECONDS,
            )
            time.sleep(CHUNK_DELAY_SECONDS)

    logger.info("Computing risk scores.")
    with get_connection() as conn:
        scored = compute_risk_scores(conn)
    scorable = sum(1 for r in scored if r["risk_score"] is not None)
    logger.info(
        "Risk scores computed: %s/%s asteroids scored.", scorable, len(scored)
    )

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
        start = date.fromisoformat(args.start_date)
        end = date.fromisoformat(args.end_date)
    except ValueError:
        logger.error("Dates must be in YYYY-MM-DD format.")
        raise

    if end < start:
        logger.error("--end-date must not be before --start-date.")
        raise ValueError("--end-date must not be before --start-date.")

    try:
        run_pipeline(args.start_date, args.end_date)
    except Exception:
        logger.exception("Pipeline execution failed.")
        raise


if __name__ == "__main__":
    main()
