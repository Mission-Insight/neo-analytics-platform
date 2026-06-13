```mermaid
erDiagram

    ASTEROIDS ||--o{ CLOSE_APPROACHES : has
    ASTEROIDS ||--o| ORBITAL_PARAMETERS : has

    ASTEROIDS {
        TEXT asteroid_id PK
        TEXT self_link
        TEXT name
        REAL absolute_magnitude_h
        REAL estimated_diameter_min_km
        REAL estimated_diameter_max_km
        INTEGER is_potentially_hazardous
    }

    CLOSE_APPROACHES {
        INTEGER approach_id PK
        TEXT asteroid_id FK
        TEXT close_approach_date
        REAL relative_velocity_kph
        REAL miss_distance_km
        TEXT orbiting_body
    }

    ORBITAL_PARAMETERS {
        TEXT asteroid_id PK,FK
        TEXT orbit_class
        REAL eccentricity
        REAL inclination
        REAL orbital_period
    }

    INGESTION_LOG {
        INTEGER ingestion_id PK
        TEXT source_file
        TEXT ingestion_timestamp
        INTEGER rows_processed
        TEXT status
        REAL duration_seconds
    }