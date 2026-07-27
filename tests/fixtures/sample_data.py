"""
Representative sample records shared across db/, models/, and dashboard/
tests. Shaped like the output of src/parsing and src/transform (i.e.
DB-ready), covering:

  - 2000433: a single close approach, far and slow (low risk)
  - 3600001: a single close approach, close and fast, hazardous (high risk)
  - 3600002: two close approaches, exercises MIN/MAX/COUNT aggregation
  - 3600003: no close approaches and no orbital parameters row, exercises
    the risk engine's is_scorable=False path and LEFT JOIN NULLs
"""

from src.db.load_asteroids import insert_asteroids
from src.db.load_close_approaches import insert_close_approaches
from src.db.load_orbital_parameters import insert_orbital_parameters

SAMPLE_ASTEROIDS = [
    {
        "asteroid_id": "2000433",
        "name": "433 Eros",
        "absolute_magnitude_h": 10.4,
        "estimated_diameter_min_km": 11.0,
        "estimated_diameter_max_km": 25.0,
        "is_potentially_hazardous": 0,
    },
    {
        "asteroid_id": "3600001",
        "name": "(2024 AB1)",
        "absolute_magnitude_h": 21.5,
        "estimated_diameter_min_km": 0.3,
        "estimated_diameter_max_km": 0.7,
        "is_potentially_hazardous": 1,
    },
    {
        "asteroid_id": "3600002",
        "name": "(2024 CD2)",
        "absolute_magnitude_h": 24.8,
        "estimated_diameter_min_km": 0.05,
        "estimated_diameter_max_km": 0.12,
        "is_potentially_hazardous": 0,
    },
    {
        "asteroid_id": "3600003",
        "name": "(2024 EF3)",
        "absolute_magnitude_h": 19.9,
        "estimated_diameter_min_km": 0.4,
        "estimated_diameter_max_km": 0.9,
        "is_potentially_hazardous": 0,
    },
]

SAMPLE_CLOSE_APPROACHES = [
    {
        "asteroid_id": "2000433",
        "close_approach_date": "2025-01-15",
        "relative_velocity_kps": 5.2,
        "miss_distance_km": 50_000_000.0,
        "orbiting_body": "Earth",
    },
    {
        "asteroid_id": "3600001",
        "close_approach_date": "2025-03-10",
        "relative_velocity_kps": 25.7,
        "miss_distance_km": 120_000.0,
        "orbiting_body": "Earth",
    },
    {
        "asteroid_id": "3600002",
        "close_approach_date": "2025-02-01",
        "relative_velocity_kps": 8.1,
        "miss_distance_km": 3_000_000.0,
        "orbiting_body": "Earth",
    },
    {
        "asteroid_id": "3600002",
        "close_approach_date": "2025-05-20",
        "relative_velocity_kps": 12.4,
        "miss_distance_km": 900_000.0,
        "orbiting_body": "Earth",
    },
]

SAMPLE_ORBITAL_PARAMETERS = [
    {
        "asteroid_id": "2000433",
        "orbit_id": "659",
        "orbit_determination_date": "2024-05-01 00:00:00",
        "first_observation_date": "1893-01-01",
        "last_observation_date": "2024-04-01",
        "data_arc_in_days": 47000,
        "observations_used": 9000,
        "orbit_uncertainty": "0",
        "minimum_orbit_intersection": 0.15,
        "jupiter_tisserand_invariant": 4.582,
        "epoch_osculation": 2460000.5,
        "eccentricity": 0.2229,
        "semi_major_axis": 1.4579,
        "inclination": 10.828,
        "ascending_node_longitude": 304.401,
        "orbital_period": 643.1,
        "perihelion_distance": 1.1334,
        "perihelion_argument": 178.9,
        "aphelion_distance": 1.7825,
        "perihelion_time": 2459900.5,
        "mean_anomaly": 45.2,
        "mean_motion": 0.5598,
        "equinox": "J2000",
        "orbit_class_type": "AMO",
        "orbit_class_description": "Amor",
        "orbit_class_range": "1.017 AU < q < 1.3 AU",
    },
    {
        "asteroid_id": "3600001",
        "orbit_id": "12",
        "orbit_determination_date": "2024-11-01 00:00:00",
        "first_observation_date": "2024-01-05",
        "last_observation_date": "2024-10-20",
        "data_arc_in_days": 289,
        "observations_used": 210,
        "orbit_uncertainty": "4",
        "minimum_orbit_intersection": 0.008,
        "jupiter_tisserand_invariant": 5.1,
        "epoch_osculation": 2460500.5,
        "eccentricity": 0.55,
        "semi_major_axis": 1.28,
        "inclination": 25.4,
        "ascending_node_longitude": 88.3,
        "orbital_period": 410.2,
        "perihelion_distance": 0.576,
        "perihelion_argument": 200.1,
        "aphelion_distance": 1.984,
        "perihelion_time": 2460400.2,
        "mean_anomaly": 130.7,
        "mean_motion": 0.8776,
        "equinox": "J2000",
        "orbit_class_type": "APO",
        "orbit_class_description": "Apollo",
        "orbit_class_range": "a > 1.0 AU; q < 1.017 AU",
    },
    {
        "asteroid_id": "3600002",
        "orbit_id": "7",
        "orbit_determination_date": "2025-01-01 00:00:00",
        "first_observation_date": "2024-12-01",
        "last_observation_date": "2025-05-25",
        "data_arc_in_days": 175,
        "observations_used": 96,
        "orbit_uncertainty": "6",
        "minimum_orbit_intersection": 0.021,
        "jupiter_tisserand_invariant": 4.9,
        "epoch_osculation": 2460700.5,
        "eccentricity": 0.41,
        "semi_major_axis": 1.62,
        "inclination": 6.2,
        "ascending_node_longitude": 150.9,
        "orbital_period": 752.0,
        "perihelion_distance": 0.956,
        "perihelion_argument": 45.6,
        "aphelion_distance": 2.284,
        "perihelion_time": 2460650.1,
        "mean_anomaly": 89.1,
        "mean_motion": 0.4787,
        "equinox": "J2000",
        "orbit_class_type": "APO",
        "orbit_class_description": "Apollo",
        "orbit_class_range": "a > 1.0 AU; q < 1.017 AU",
    },
    # 3600003 intentionally has no row here — exercises the LEFT JOIN NULL
    # path for orbital fields.
]


def seed_sample_data(
    conn,
    asteroids=None,
    close_approaches=None,
    orbital_parameters=None,
) -> None:
    """Insert the representative sample records (or a caller-supplied subset/override)."""
    insert_asteroids(conn, SAMPLE_ASTEROIDS if asteroids is None else asteroids)
    insert_close_approaches(
        conn, SAMPLE_CLOSE_APPROACHES if close_approaches is None else close_approaches
    )
    insert_orbital_parameters(
        conn,
        SAMPLE_ORBITAL_PARAMETERS if orbital_parameters is None else orbital_parameters,
    )
    conn.commit()
