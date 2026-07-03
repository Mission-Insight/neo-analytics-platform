from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urlparse

import requests

from src.config import NASA_API_KEY

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30
REQUEST_DELAY_SECONDS = 1.0
MAX_RETRIES = 3
RATE_LIMIT_BACKOFF_SECONDS = 60


def extract_self_links(feed_data: dict) -> list[str]:
    self_links = []

    near_earth_objects = feed_data.get("near_earth_objects", {})

    for asteroid_list in near_earth_objects.values():
        for asteroid in asteroid_list:
            self_link = asteroid.get("links", {}).get("self")

            if self_link:
                self_links.append(self_link)

    return sorted(set(self_links))


def remove_query_params(url: str) -> str:
    parsed = urlparse(url)

    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def fetch_asteroid_detail(self_link: str) -> dict[str, Any]:
    clean_url = remove_query_params(self_link)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(
                clean_url,
                params={"api_key": NASA_API_KEY},
                timeout=REQUEST_TIMEOUT,
            )
        except requests.exceptions.ConnectionError as exc:
            if attempt < MAX_RETRIES:
                delay = 2 ** (attempt - 1) * 5
                logger.warning(
                    "Network error for %s (attempt %s/%s). Waiting %ss. Error: %s",
                    clean_url,
                    attempt,
                    MAX_RETRIES,
                    delay,
                    exc,
                )
                time.sleep(delay)
                continue
            raise

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", RATE_LIMIT_BACKOFF_SECONDS))
            if attempt < MAX_RETRIES:
                logger.warning(
                    "Rate limit hit for %s (attempt %s/%s). Waiting %ss.",
                    clean_url,
                    attempt,
                    MAX_RETRIES,
                    retry_after,
                )
                time.sleep(retry_after)
                continue
            raise requests.HTTPError(
                f"Rate limit exceeded after {MAX_RETRIES} attempts.",
                response=response,
            )

        response.raise_for_status()
        return response.json()

    raise RuntimeError(f"Failed to fetch {clean_url} after {MAX_RETRIES} attempts.")


def fetch_orbital_parameters_for_feed(feed_data: dict) -> list[dict[str, Any]]:
    self_links = extract_self_links(feed_data)
    orbital_records = []

    logger.info("Fetching orbital data for %s asteroids.", len(self_links))

    for self_link in self_links:
        detail_data = fetch_asteroid_detail(self_link)

        asteroid_id = detail_data.get("id")
        orbital_data = detail_data.get("orbital_data")

        if not asteroid_id or orbital_data is None:
            logger.warning("Missing orbital data for self link: %s", self_link)
            continue

        orbital_records.append(
            {
                "asteroid_id": asteroid_id,
                **orbital_data,
            }
        )

        time.sleep(REQUEST_DELAY_SECONDS)

    return orbital_records
