from src.parsing.parse_asteroids import parse_asteroid


def test_parse_asteroid_returns_structured_dictionary():
    sample = {
        "id": "12345",
        "name": "Test Asteroid",
        "absolute_magnitude_h": 22.1,
        "estimated_diameter": {
            "kilometers": {
                "estimated_diameter_min": 0.1,
                "estimated_diameter_max": 0.3,
            }
        },
        "is_potentially_hazardous_asteroid": False,
    }

    result = parse_asteroid(sample)

    assert result == {
        "asteroid_id": "12345",
        "name": "Test Asteroid",
        "absolute_magnitude_h": 22.1,
        "estimated_diameter_min_km": 0.1,
        "estimated_diameter_max_km": 0.3,
        "is_potentially_hazardous": 0,
    }


def test_parse_asteroid_handles_missing_fields():
    result = parse_asteroid({})

    assert result == {
        "asteroid_id": None,
        "name": None,
        "absolute_magnitude_h": None,
        "estimated_diameter_min_km": None,
        "estimated_diameter_max_km": None,
        "is_potentially_hazardous": 0,
    }


def test_parse_asteroid_handles_empty_payload():
    result = parse_asteroid({})

    assert result["asteroid_id"] is None
    assert result["name"] is None
