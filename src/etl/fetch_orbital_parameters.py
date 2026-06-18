from __future__ import annotations

import logging
import time
from typing import Any

import requests

from src.config import NASA_API_KEY

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30
REQUEST_DELAY_SECONDS = 0.25


def extract_asteroid_ids(feed_data: dict) -> list[str]:
    asteroid_ids = []

    near_earth_objects = feed_data.get("near_earth_objects", {})

    for asteroid_list in near_earth_objects.values():
        for asteroid in asteroid_list:
            asteroid_id = asteroid.get("id")

            if asteroid_id:
                asteroid_ids.append(asteroid_id)

    return sorted(set(asteroid_ids))


def fetch_asteroid_detail(asteroid_id: str) -> dict[str, Any]:
    url = f"https://api.nasa.gov/neo/rest/v1/neo/{asteroid_id}"

    response = requests.get(
        url,
        params={"api_key": NASA_API_KEY},
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()
    return response.json()


def fetch_orbital_parameters_for_feed(feed_data: dict) -> list[dict[str, Any]]:
    asteroid_ids = extract_asteroid_ids(feed_data)
    orbital_records = []

    logger.info("Fetching orbital data for %s asteroids.", len(asteroid_ids))

    for asteroid_id in asteroid_ids:
        detail_data = fetch_asteroid_detail(asteroid_id)
        orbital_data = detail_data.get("orbital_data")

        if orbital_data is None:
            logger.warning("No orbital data found for asteroid %s.", asteroid_id)
            continue

        orbital_records.append(
            {
                "asteroid_id": asteroid_id,
                **orbital_data,
            }
        )

        time.sleep(REQUEST_DELAY_SECONDS)

    return orbital_records
