from pathlib import Path
from datetime import datetime
import argparse
import json
import logging
import time

import requests

from src.config import NASA_API_KEY
from src.config import BASE_URL
from src.logging import setup_logging

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_KEYS = {
    "links",
    "element_count",
    "near_earth_objects",
}

logger = logging.getLogger(__name__)


def fetch_neows_feed(start_date: str, end_date: str) -> dict:
    logger.info(
        "REQUEST START | start_date=%s | end_date=%s",
        start_date,
        end_date,
    )

    params = {
        "start_date": start_date,
        "end_date": end_date,
        "api_key": NASA_API_KEY,
    }

    max_retries = 3
    base_delay = 1

    response = None
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                "REQUEST ATTEMPT | attempt=%s | max_retries=%s",
                attempt,
                max_retries,
            )

            response = requests.get(
                BASE_URL,
                params=params,
                timeout=30,
            )

            # response.status_code =

            handle_http_error(
                response=response,
                start_date=start_date,
                end_date=end_date,
            )

            logger.info(
                "REQUEST SUCCESS | status_code=%s | attempt=%s",
                response.status_code,
                attempt,
            )

            logger.info(
                "RESPONSE SIZE | bytes=%s",
                len(response.content),
            )

            break

        except requests.RequestException as exc:
            if attempt == max_retries:
                logger.error(
                    "REQUEST FAILURE | retries_exhausted=True | error=%s",
                    exc,
                    exc_info=True,
                )
                raise

            delay = base_delay * (2 ** (attempt - 1))

            logger.warning(
                "REQUEST RETRY | attempt=%s | next_delay_seconds=%s | error=%s",
                attempt,
                delay,
                exc,
            )

            time.sleep(delay)

    if response is None:
        raise RuntimeError("No response received after all retry attempts.")

    data = response.json()

    validate_response_shape(data)

    logger.info(
        "RESPONSE RECORD COUNT | element_count=%s",
        data["element_count"],
    )

    if data["element_count"] == 0:
        logger.warning("NASA API returned zero near-Earth objects")

    elif data["element_count"] < 10:
        logger.warning(
            "NASA API returned an unusually small dataset: %s objects",
            data["element_count"],
        )

    return data


def validate_response_shape(data: dict) -> None:
    """
    Validate expected NeoWs response structure.
    """

    missing_keys = REQUIRED_KEYS - data.keys()

    if missing_keys:
        logger.error(
            "Response missing required keys: %s",
            missing_keys,
        )

        raise ValueError(f"Response missing required keys: {missing_keys}")

    logger.info("Response schema validation passed")


def handle_http_error(
    response: requests.Response,
    start_date: str,
    end_date: str,
) -> None:
    status_code = response.status_code

    error_context = {
        "endpoint": BASE_URL,
        "start_date": start_date,
        "end_date": end_date,
        "timestamp": datetime.now().isoformat(),
        "status_code": status_code,
    }

    if status_code == 400:
        logger.error("HTTP 400 Bad Request | context=%s", error_context)
        raise ValueError("Bad request: check request parameters.")

    if status_code in {401, 403}:
        logger.error(
            "HTTP %s Authorization Error | context=%s", status_code, error_context
        )

        raise PermissionError("NASA API key is invalid, missing, or not authorized.")

    if status_code == 429:
        logger.error("HTTP 429 Too Many Requests | context=%s", error_context)
        raise requests.HTTPError(
            "Rate limit exceeded. Try again later.", response=response
        )

    if status_code >= 500:
        logger.error("HTTP %s Server Error | context=%s", status_code, error_context)
        raise requests.HTTPError(
            "NASA API server error. Try again later.", response=response
        )

    response.raise_for_status()


def save_raw_data(
    data: dict,
    start_date: str,
) -> Path:
    date_obj = datetime.strptime(
        start_date,
        "%Y-%m-%d",
    )

    raw_dir = (
        PROJECT_ROOT
        / "data"
        / "raw"
        / date_obj.strftime("%Y")
        / date_obj.strftime("%m")
        / date_obj.strftime("%d")
    )

    raw_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime("%H%M%S")

    output_file = raw_dir / f"neows_feed_{timestamp}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    logger.info(
        "Saved raw data to %s",
        output_file,
    )

    return output_file


def main() -> None:
    setup_logging()

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--start-date",
        required=True,
        help="Start date in YYYY-MM-DD format",
    )

    parser.add_argument(
        "--end-date",
        required=True,
        help="End date in YYYY-MM-DD format",
    )

    args = parser.parse_args()

    try:
        data = fetch_neows_feed(
            start_date=args.start_date,
            end_date=args.end_date,
        )

        save_raw_data(data, args.start_date)

        logger.info("NeoWs fetch completed successfully")

    except requests.RequestException as exc:
        logger.error(
            "NeoWs fetch failed because the API request failed: %s",
            exc,
            exc_info=True,
        )
        raise

    except Exception as exc:
        logger.error(
            "NeoWs fetch failed unexpectedly: %s",
            exc,
            exc_info=True,
        )
        raise


if __name__ == "__main__":
    main()
