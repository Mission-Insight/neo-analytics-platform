from src.transform.transform_neows import transform_orbital_parameters


def test_parse_orbital_parameters_returns_structured_metadata():
    sample = {
        "asteroid_id": "12345",
        "eccentricity": "0.123",
        "semi_major_axis": "1.456",
        "inclination": "3.21",
        "orbital_period": "456.7",
        "perihelion_distance": "0.987",
        "aphelion_distance": "1.923",
        "orbit_class": {
            "orbit_class_type": "APO",
            "orbit_class_description": (
                "Near-Earth asteroid orbits similar to that of 1862 Apollo"
            ),
        },
    }

    result = transform_orbital_parameters([sample])

    assert result == [
        {
            "asteroid_id": "12345",
            "orbit_id": None,
            "orbit_determination_date": None,
            "first_observation_date": None,
            "last_observation_date": None,
            "data_arc_in_days": None,
            "observations_used": None,
            "orbit_uncertainty": None,
            "minimum_orbit_intersection": None,
            "jupiter_tisserand_invariant": None,
            "epoch_osculation": None,
            "eccentricity": "0.123",
            "semi_major_axis": "1.456",
            "inclination": "3.21",
            "ascending_node_longitude": None,
            "orbital_period": "456.7",
            "perihelion_distance": "0.987",
            "perihelion_argument": None,
            "aphelion_distance": "1.923",
            "perihelion_time": None,
            "mean_anomaly": None,
            "mean_motion": None,
            "equinox": None,
            "orbit_class_type": "APO",
            "orbit_class_description": "Near-Earth asteroid orbits similar to that "
            "of 1862 Apollo",
            "orbit_class_range": None,
        }
    ]


def test_parse_orbital_parameters_handles_missing_fields():
    result = transform_orbital_parameters([])

    assert result == []


def test_parse_orbital_parameters_handles_null_orbital_data():
    result = transform_orbital_parameters(
        [
            {
                "asteroid_id": "12345",
            }
        ]
    )

    assert result == [
        {
            "asteroid_id": "12345",
            "orbit_id": None,
            "orbit_determination_date": None,
            "first_observation_date": None,
            "last_observation_date": None,
            "data_arc_in_days": None,
            "observations_used": None,
            "orbit_uncertainty": None,
            "minimum_orbit_intersection": None,
            "jupiter_tisserand_invariant": None,
            "epoch_osculation": None,
            "eccentricity": None,
            "semi_major_axis": None,
            "inclination": None,
            "ascending_node_longitude": None,
            "orbital_period": None,
            "perihelion_distance": None,
            "perihelion_argument": None,
            "aphelion_distance": None,
            "perihelion_time": None,
            "mean_anomaly": None,
            "mean_motion": None,
            "equinox": None,
            "orbit_class_type": None,
            "orbit_class_description": None,
            "orbit_class_range": None,
        }
    ]


def test_parse_orbital_parameters_handles_null_orbit_class():
    result = transform_orbital_parameters(
        [
            {
                "asteroid_id": "12345",
                "orbit_class": {},
            }
        ]
    )

    assert result == [
        {
            "asteroid_id": "12345",
            "orbit_id": None,
            "orbit_determination_date": None,
            "first_observation_date": None,
            "last_observation_date": None,
            "data_arc_in_days": None,
            "observations_used": None,
            "orbit_uncertainty": None,
            "minimum_orbit_intersection": None,
            "jupiter_tisserand_invariant": None,
            "epoch_osculation": None,
            "eccentricity": None,
            "semi_major_axis": None,
            "inclination": None,
            "ascending_node_longitude": None,
            "orbital_period": None,
            "perihelion_distance": None,
            "perihelion_argument": None,
            "aphelion_distance": None,
            "perihelion_time": None,
            "mean_anomaly": None,
            "mean_motion": None,
            "equinox": None,
            "orbit_class_type": None,
            "orbit_class_description": None,
            "orbit_class_range": None,
        }
    ]
