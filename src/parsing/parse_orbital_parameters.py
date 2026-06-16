def parse_orbital_parameters(asteroid: dict) -> dict:
    """
    Extract orbital class and orbital characteristics
    from a single NASA NeoWs asteroid object.
    """

    orbital_data = asteroid.get("orbital_data") or {}
    orbit_class = orbital_data.get("orbit_class") or {}

    return {
        "asteroid_id": asteroid.get("id"),
        "orbit_class_type": orbit_class.get("orbit_class_type"),
        "orbit_class_description": orbit_class.get("orbit_class_description"),
        "eccentricity": orbital_data.get("eccentricity"),
        "semi_major_axis": orbital_data.get("semi_major_axis"),
        "inclination": orbital_data.get("inclination"),
        "orbital_period": orbital_data.get("orbital_period"),
        "perihelion_distance": orbital_data.get("perihelion_distance"),
        "aphelion_distance": orbital_data.get("aphelion_distance"),
    }
