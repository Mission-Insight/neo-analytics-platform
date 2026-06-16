from src.parsing.parse_orbital_parameters import parse_orbital_parameters


def test_parse_orbital_parameters_returns_structured_metadata():
    sample = {
        "id": "12345",
        "orbital_data": {
            "eccentricity": "0.123",
            "semi_major_axis": "1.456",
            "inclination": "3.21",
            "orbital_period": "456.7",
            "perihelion_distance": "0.987",
            "aphelion_distance": "1.923",
            "orbit_class": {
                "orbit_class_type": "APO",
                "orbit_class_description":
                    "Near-Earth asteroid orbits similar to that of 1862 Apollo",
            },
        },
    }

    result = parse_orbital_parameters(sample)

    assert result == {
        "asteroid_id": "12345",
        "orbit_class_type": "APO",
        "orbit_class_description":
            "Near-Earth asteroid orbits similar to that of 1862 Apollo",
        "eccentricity": "0.123",
        "semi_major_axis": "1.456",
        "inclination": "3.21",
        "orbital_period": "456.7",
        "perihelion_distance": "0.987",
        "aphelion_distance": "1.923",
    }


def test_parse_orbital_parameters_handles_missing_fields():
    result = parse_orbital_parameters({})

    assert result == {
        "asteroid_id": None,
        "orbit_class_type": None,
        "orbit_class_description": None,
        "eccentricity": None,
        "semi_major_axis": None,
        "inclination": None,
        "orbital_period": None,
        "perihelion_distance": None,
        "aphelion_distance": None,
    }


def test_parse_orbital_parameters_handles_null_orbital_data():
    result = parse_orbital_parameters({
        "id": "12345",
        "orbital_data": None,
    })

    assert result == {
        "asteroid_id": "12345",
        "orbit_class_type": None,
        "orbit_class_description": None,
        "eccentricity": None,
        "semi_major_axis": None,
        "inclination": None,
        "orbital_period": None,
        "perihelion_distance": None,
        "aphelion_distance": None,
    }


def test_parse_orbital_parameters_handles_null_orbit_class():
    result = parse_orbital_parameters({
        "id": "12345",
        "orbital_data": {
            "orbit_class": None,
        },
    })

    assert result == {
        "asteroid_id": "12345",
        "orbit_class_type": None,
        "orbit_class_description": None,
        "eccentricity": None,
        "semi_major_axis": None,
        "inclination": None,
        "orbital_period": None,
        "perihelion_distance": None,
        "aphelion_distance": None,
    }
