from pathlib import Path
from datetime import datetime
import json
import requests

from src.config import NASA_API_KEY

BASE_URL = "https://api.nasa.gov/neo/rest/v1/feed"
PROJECT_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_KEYS = {
    "links",
    "element_count",
    "near_earth_objects",
}


def fetch_neows_feed(start_date: str, end_date: str) -> dict:
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "api_key": NASA_API_KEY,
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    validate_response_shape(data)

    return data


def validate_response_shape(data: dict) -> None:
    """
    Validate expected NeoWs response structure.
    """

    if not isinstance(data, dict):
        raise TypeError(
            f"Expected response data to be dict, got {type(data).__name__}."
        )

    missing_keys = REQUIRED_KEYS - data.keys()

    if missing_keys:
        raise ValueError(f"Missing expected response keys: {missing_keys}")

    if not isinstance(data["links"], dict):
        raise TypeError("Expected 'links' to be a dict.")

    if not isinstance(data["element_count"], int):
        raise TypeError("Expected 'element_count' to be an int.")

    if not isinstance(data["near_earth_objects"], dict):
        raise TypeError("Expected 'near_earth_objects' to be a dict.")

    print("Response shape validation passed.")


def build_raw_storage_dir(date_str: str) -> Path:
    year, month, day = date_str.split("-")
    raw_dir = PROJECT_ROOT / "data" / "raw" / year / month / day
    raw_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir


def save_raw_response(data: dict, start_date: str) -> Path:
    raw_dir = build_raw_storage_dir(start_date)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_path = raw_dir / f"neows_{timestamp}.json"

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    return output_path


def validate_saved_file_integrity(
    original_data: dict,
    file_path: Path,
) -> None:
    """
    Reload saved JSON and verify integrity against original object.
    """

    with file_path.open("r", encoding="utf-8") as file:
        reloaded_data = json.load(file)

    if reloaded_data != original_data:
        raise ValueError("Saved JSON file failed integrity validation.")

    print("File integrity validation passed.")


def main():
    start_date = "2026-05-01"
    end_date = "2026-05-07"

    data = fetch_neows_feed(start_date, end_date)

    output_path = save_raw_response(
        data,
        start_date,
    )

    validate_saved_file_integrity(
        data,
        output_path,
    )

    print(f"Raw response saved to: {output_path}")


if __name__ == "__main__":
    main()
