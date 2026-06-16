def parse_asteroid(asteroid: dict) -> dict:
    estimated_diameter = asteroid.get("estimated_diameter") or {}
    diameter_km = estimated_diameter.get("kilometers") or {}

    return {
        "asteroid_id": asteroid.get("id"),
        "name": asteroid.get("name"),
        "absolute_magnitude_h": asteroid.get("absolute_magnitude_h"),
        "estimated_diameter_min_km": diameter_km.get("estimated_diameter_min"),
        "estimated_diameter_max_km": diameter_km.get("estimated_diameter_max"),
        "is_potentially_hazardous": int(
            asteroid.get("is_potentially_hazardous_asteroid") or False
        ),
    }
