PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS asteroids (
    asteroid_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    absolute_magnitude_h REAL,
    estimated_diameter_min_km REAL,
    estimated_diameter_max_km REAL,
    is_potentially_hazardous INTEGER NOT NULL CHECK (is_potentially_hazardous IN (0, 1))
);

CREATE TABLE IF NOT EXISTS close_approaches (
    close_approach_id INTEGER PRIMARY KEY AUTOINCREMENT,
    asteroid_id TEXT NOT NULL,
    close_approach_date TEXT NOT NULL,
    relative_velocity_kps REAL,
    miss_distance_km REAL,
    orbiting_body TEXT,

    UNIQUE (asteroid_id, close_approach_date),

    FOREIGN KEY (asteroid_id)
        REFERENCES asteroids (asteroid_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS orbital_parameters (
    asteroid_id TEXT PRIMARY KEY,

    orbit_id TEXT,
    orbit_determination_date TEXT,
    first_observation_date TEXT,
    last_observation_date TEXT,
    data_arc_in_days INTEGER,
    observations_used INTEGER,
    orbit_uncertainty TEXT,
    minimum_orbit_intersection REAL,
    jupiter_tisserand_invariant REAL,
    epoch_osculation REAL,

    eccentricity REAL,
    semi_major_axis REAL,
    inclination REAL,
    ascending_node_longitude REAL,
    orbital_period REAL,
    perihelion_distance REAL,
    perihelion_argument REAL,
    aphelion_distance REAL,
    perihelion_time REAL,
    mean_anomaly REAL,
    mean_motion REAL,
    equinox TEXT,

    orbit_class_type TEXT,
    orbit_class_description TEXT,
    orbit_class_range TEXT,

    FOREIGN KEY (asteroid_id)
        REFERENCES asteroids (asteroid_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    duration_seconds REAL,
    status TEXT NOT NULL CHECK (status IN ('STARTED', 'SUCCESS', 'FAILED')),
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    asteroid_count INTEGER DEFAULT 0,
    close_approach_count INTEGER DEFAULT 0,
    orbital_parameter_count INTEGER DEFAULT 0,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS ingestion_failures (
    failure_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    failed_at TEXT NOT NULL,
    error_message TEXT NOT NULL,

    FOREIGN KEY (run_id)
        REFERENCES ingestion_runs (run_id)
        ON DELETE CASCADE
);
