-- 1. Largest asteroids by estimated max diameter
SELECT
    asteroid_id,
    name,
    estimated_diameter_max_km,
    is_potentially_hazardous
FROM asteroids
ORDER BY estimated_diameter_max_km DESC
LIMIT 10;


-- 2. Nearest close approaches
SELECT
    a.name,
    ca.close_approach_date,
    ca.miss_distance_km,
    ca.relative_velocity_kps,
    ca.orbiting_body
FROM close_approaches ca
JOIN asteroids a
    ON ca.asteroid_id = a.asteroid_id
ORDER BY ca.miss_distance_km ASC
LIMIT 10;


-- 3. Potentially hazardous objects
SELECT
    asteroid_id,
    name,
    absolute_magnitude_h,
    estimated_diameter_max_km
FROM asteroids
WHERE is_potentially_hazardous = 1
ORDER BY estimated_diameter_max_km DESC
LIMIT 10;


-- 4. Asteroids with orbital class data
SELECT
    a.name,
    op.orbit_class_type,
    op.eccentricity,
    op.semi_major_axis,
    op.inclination
FROM asteroids a
JOIN orbital_parameters op
    ON a.asteroid_id = op.asteroid_id
LIMIT 10;


-- 5. Count records by table
SELECT 'asteroids' AS table_name, COUNT(*) AS record_count
FROM asteroids
UNION ALL
SELECT 'close_approaches', COUNT(*)
FROM close_approaches
UNION ALL
SELECT 'orbital_parameters', COUNT(*)
FROM orbital_parameters
UNION ALL
SELECT 'ingestion_runs', COUNT(*)
FROM ingestion_runs;


-- Close approaches with no matching asteroid
SELECT
    ca.*
FROM close_approaches ca
LEFT JOIN asteroids a
    ON ca.asteroid_id = a.asteroid_id
WHERE a.asteroid_id IS NULL;


-- Orbital parameters with no matching asteroid
SELECT
    op.*
FROM orbital_parameters op
LEFT JOIN asteroids a
    ON op.asteroid_id = a.asteroid_id
WHERE a.asteroid_id IS NULL;


-- Summary orphan check
SELECT
    'close_approaches_orphans' AS check_name,
    COUNT(*) AS orphan_count
FROM close_approaches ca
LEFT JOIN asteroids a
    ON ca.asteroid_id = a.asteroid_id
WHERE a.asteroid_id IS NULL

UNION ALL

SELECT
    'orbital_parameters_orphans',
    COUNT(*)
FROM orbital_parameters op
LEFT JOIN asteroids a
    ON op.asteroid_id = a.asteroid_id
WHERE a.asteroid_id IS NULL;


-- Compare latest ingestion run counts to inserted table counts
SELECT
    'asteroids' AS table_name,
    latest.asteroid_count AS latest_run_count,
    COUNT(a.asteroid_id) AS database_count
FROM (
    SELECT asteroid_count
    FROM ingestion_runs
    WHERE status = 'SUCCESS'
    ORDER BY run_id DESC
    LIMIT 1
) latest
CROSS JOIN asteroids a

UNION ALL

SELECT
    'close_approaches',
    latest.close_approach_count,
    COUNT(ca.close_approach_id)
FROM (
    SELECT close_approach_count
    FROM ingestion_runs
    WHERE status = 'SUCCESS'
    ORDER BY run_id DESC
    LIMIT 1
) latest
CROSS JOIN close_approaches ca

UNION ALL

SELECT
    'orbital_parameters',
    latest.orbital_parameter_count,
    COUNT(op.asteroid_id)
FROM (
    SELECT orbital_parameter_count
    FROM ingestion_runs
    WHERE status = 'SUCCESS'
    ORDER BY run_id DESC
    LIMIT 1
) latest
CROSS JOIN orbital_parameters op;
