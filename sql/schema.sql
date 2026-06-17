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

    orbit_class_type TEXT,
    orbit_class_description TEXT,

    eccentricity REAL,
    semi_major_axis REAL,
    inclination REAL,
    orbital_period REAL,
    perihelion_distance REAL,
    aphelion_distance REAL,

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
