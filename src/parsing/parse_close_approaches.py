from src.parsing.utils import safe_float


def parse_close_approaches(asteroid: dict) -> list[dict]:
    asteroid_id = asteroid.get("id")
    close_approaches = asteroid.get("close_approach_data") or []

    records = []

    for approach in close_approaches:
        relative_velocity = approach.get("relative_velocity") or {}
        miss_distance = approach.get("miss_distance") or {}

        records.append(
            {
                "asteroid_id": asteroid_id,
                "close_approach_date": approach.get("close_approach_date"),
                "relative_velocity_kps": safe_float(
                    relative_velocity.get("kilometers_per_second")
                ),
                "miss_distance_km": safe_float(
                    miss_distance.get("kilometers")
                ),
                "orbiting_body": approach.get("orbiting_body"),
            }
        )

    return records
