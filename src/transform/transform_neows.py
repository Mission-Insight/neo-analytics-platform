def transform_orbital_parameters(
    orbital_records: list[dict],
) -> list[dict]:
    transformed = []

    for orbital_data in orbital_records:
        orbit_class = orbital_data.get("orbit_class", {})

        transformed.append(
            {
                "asteroid_id": orbital_data.get("asteroid_id"),
                "orbit_id": orbital_data.get("orbit_id"),
                "orbit_determination_date": orbital_data.get(
                    "orbit_determination_date"
                ),
                "first_observation_date": orbital_data.get("first_observation_date"),
                "last_observation_date": orbital_data.get("last_observation_date"),
                "data_arc_in_days": orbital_data.get("data_arc_in_days"),
                "observations_used": orbital_data.get("observations_used"),
                "orbit_uncertainty": orbital_data.get("orbit_uncertainty"),
                "minimum_orbit_intersection": orbital_data.get(
                    "minimum_orbit_intersection"
                ),
                "jupiter_tisserand_invariant": orbital_data.get(
                    "jupiter_tisserand_invariant"
                ),
                "epoch_osculation": orbital_data.get("epoch_osculation"),
                "eccentricity": orbital_data.get("eccentricity"),
                "semi_major_axis": orbital_data.get("semi_major_axis"),
                "inclination": orbital_data.get("inclination"),
                "ascending_node_longitude": orbital_data.get(
                    "ascending_node_longitude"
                ),
                "orbital_period": orbital_data.get("orbital_period"),
                "perihelion_distance": orbital_data.get("perihelion_distance"),
                "perihelion_argument": orbital_data.get("perihelion_argument"),
                "aphelion_distance": orbital_data.get("aphelion_distance"),
                "perihelion_time": orbital_data.get("perihelion_time"),
                "mean_anomaly": orbital_data.get("mean_anomaly"),
                "mean_motion": orbital_data.get("mean_motion"),
                "equinox": orbital_data.get("equinox"),
                "orbit_class_type": orbit_class.get("orbit_class_type"),
                "orbit_class_description": orbit_class.get("orbit_class_description"),
                "orbit_class_range": orbit_class.get("orbit_class_range"),
            }
        )

    return transformed
