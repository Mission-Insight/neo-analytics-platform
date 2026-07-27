from src.parsing.parse_close_approaches import parse_close_approaches


def test_parse_close_approaches_returns_structured_records():
    sample = {
        "id": "12345",
        "close_approach_data": [
            {
                "close_approach_date": "2025-01-01",
                "relative_velocity": {
                    "kilometers_per_second": "12.34"
                },
                "miss_distance": {
                    "kilometers": "456789.0"
                },
                "orbiting_body": "Earth",
            }
        ],
    }

    result = parse_close_approaches(sample)

    assert result == [
        {
            "asteroid_id": "12345",
            "close_approach_date": "2025-01-01",
            "relative_velocity_kps": 12.34,
            "miss_distance_km": 456789.0,
            "orbiting_body": "Earth",
        }
    ]


def test_parse_close_approaches_handles_missing_fields():
    result = parse_close_approaches({"id": "12345", "close_approach_data": [{}]})

    assert result == [
        {
            "asteroid_id": "12345",
            "close_approach_date": None,
            "relative_velocity_kps": None,
            "miss_distance_km": None,
            "orbiting_body": None,
        }
    ]


def test_parse_close_approaches_handles_null_list():
    result = parse_close_approaches({
        "id": "12345",
        "close_approach_data": None,
    })

    assert result == []


def test_parse_close_approaches_handles_null_nested_values():
    result = parse_close_approaches({
        "id": "12345",
        "close_approach_data": [
            {
                "relative_velocity": None,
                "miss_distance": None,
            }
        ],
    })

    assert result == [
        {
            "asteroid_id": "12345",
            "close_approach_date": None,
            "relative_velocity_kps": None,
            "miss_distance_km": None,
            "orbiting_body": None,
        }
    ]
