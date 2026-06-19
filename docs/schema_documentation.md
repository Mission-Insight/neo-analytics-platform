# Neo Analytics Database Schema Documentation

## Asteroids

### Purpose

Stores one record per unique Near-Earth Object (NEO).

This table serves as the primary entity table and contains physical characteristics and hazard classifications for each asteroid.

### Primary Key

| Column      | Type | Description                     |
| ----------- | ---- | ------------------------------- |
| asteroid_id | TEXT | Unique NASA asteroid identifier |

### Important Columns

| Column                    | Description                |
| ------------------------- | -------------------------- |
| name                      | Asteroid designation/name  |
| absolute_magnitude_h      | Brightness measurement     |
| estimated_diameter_min_km | Minimum estimated diameter |
| estimated_diameter_max_km | Maximum estimated diameter |
| is_potentially_hazardous  | Hazard classification flag |

### Relationships

```text
Asteroids (1)
    |
    | asteroid_id
    |
    +----< Close Approaches (many)

Asteroids (1)
    |
    | asteroid_id
    |
    +----< Orbital Parameters (1)
```

### Design Rationale

The asteroid entity is stored separately to eliminate duplication because the same asteroid may appear in multiple close approaches.

---

## Close Approaches

### Purpose

Stores every recorded close approach event for an asteroid.

An asteroid may have multiple close approaches over time.

### Primary Key

| Column      | Type    |
| ----------- | ------- |
| approach_id | INTEGER |

### Foreign Key

| Column      |
| ----------- |
| asteroid_id |

References:

```text
asteroids.asteroid_id
```

### Important Columns

| Column                | Description         |
| --------------------- | ------------------- |
| close_approach_date   | Date of approach    |
| relative_velocity_kps | Relative velocity   |
| miss_distance_km      | Distance from Earth |
| orbiting_body         | Usually Earth       |

### Relationship

```text
One asteroid
      |
      | 1:M
      |
Many close approaches
```

### Design Rationale

Close approach events are stored in a separate table because a single asteroid can generate many approach records.

This structure satisfies normalization principles and avoids repeating asteroid information.

---

## Orbital Parameters

### Purpose

Stores orbital characteristics describing the trajectory of each asteroid.

### Primary Key

| Column      |
| ----------- |
| asteroid_id |

### Foreign Key

| Column      |
| ----------- |
| asteroid_id |

References:

```text
asteroids.asteroid_id
```

### Important Columns

| Column              | Description                    |
| ------------------- | ------------------------------ |
| eccentricity        | Orbit shape                    |
| semi_major_axis     | Orbit size                     |
| inclination         | Orbit tilt                     |
| orbital_period      | Time to complete orbit         |
| perihelion_distance | Closest distance to the Sun    |
| aphelion_distance   | Farthest distance from the Sun |
| orbit_class_type    | Orbit classification           |

### Relationship

```text
One asteroid
      |
      | 1:1
      |
One orbital parameter record
```

### Design Rationale

Orbital characteristics are separated from the asteroid entity because they represent a distinct domain of information and can grow independently from the physical asteroid attributes.

---

## Ingestion Runs

### Purpose

Tracks ETL pipeline executions for auditing and monitoring.

### Primary Key

| Column |
| ------ |
| run_id |

### Important Columns

| Column         | Description                    |
| -------------- | ------------------------------ |
| start_date     | Requested ingestion start date |
| end_date       | Requested ingestion end date   |
| started_at     | Pipeline start timestamp       |
| completed_at   | Pipeline completion timestamp  |
| status         | Success or failure             |
| records_loaded | Number of records processed    |

### Design Rationale

Provides operational observability and supports troubleshooting, auditing, and performance monitoring.

---

## Overall Schema Design

The database follows Third Normal Form (3NF):

* Asteroid information stored once
* Close approach events stored separately
* Orbital parameters stored separately
* Operational logging isolated from analytical data

This design minimizes duplication, maintains referential integrity through foreign keys, and supports future migration from SQLite to PostgreSQL.

---

# Database Normalization Rationale

## Why Not Store Giant JSON Blobs?

The NASA NeoWs API returns data as nested JSON documents. While it would have been possible to store the raw JSON response directly in a database table, the project instead transforms the data into a normalized relational schema consisting of the following tables:

* asteroids
* close_approaches
* orbital_parameters
* ingestion_runs

This design was chosen to improve queryability, data integrity, analytical performance, and long-term maintainability.

---

## Queryability

A normalized schema makes it easy to query individual attributes without parsing JSON documents.

For example, answering questions such as:

* Which asteroids are potentially hazardous?
* What was the closest approach recorded this month?
* Which orbital class appears most frequently?

can be accomplished using straightforward SQL queries.

If the data were stored as JSON blobs, every query would require extracting values from nested JSON structures, making analysis more complex and less efficient.

### Example

Normalized query:

```sql
SELECT asteroid_id, miss_distance_km
FROM close_approaches
ORDER BY miss_distance_km ASC;
```

The equivalent query against JSON data would require JSON extraction functions and significantly more processing.

---

## Data Integrity

Normalization allows relationships to be enforced through primary and foreign keys.

Examples:

* Every close approach must reference a valid asteroid.
* Every orbital parameter record must reference a valid asteroid.
* Duplicate asteroid records can be prevented through primary key constraints.

These protections help ensure that the database remains accurate and internally consistent.

If JSON blobs were stored directly, the database would have no knowledge of these relationships and could not enforce referential integrity.

---

## Analytics Performance

Analytical workloads benefit from structured columns.

Numeric fields such as:

* eccentricity
* semi_major_axis
* orbital_period
* miss_distance_km

can be filtered, aggregated, and indexed efficiently.

Examples include:

* calculating average asteroid size
* identifying the closest approaches
* grouping asteroids by orbital class
* building dashboards and visualizations

JSON-based storage would require repeatedly parsing large documents before performing calculations, increasing computational overhead.

---

## Maintainability

Separating data into logical tables improves readability and maintainability.

Each table has a clear responsibility:

| Table              | Responsibility                    |
| ------------------ | --------------------------------- |
| asteroids          | Physical asteroid characteristics |
| close_approaches   | Approach events                   |
| orbital_parameters | Orbital mechanics data            |
| ingestion_runs     | ETL monitoring and auditing       |

This structure makes the system easier to understand, debug, extend, and migrate.

Future enhancements such as PostgreSQL migration, dashboard development, or machine learning workflows can be implemented without redesigning the schema.

---

## Conclusion

The database was normalized to improve queryability, enforce data integrity, optimize analytical performance, and support long-term maintainability.

While raw JSON files are still retained for archival and debugging purposes, the relational schema provides a more effective foundation for analytics and reporting.

---

# ETL Separation of Concerns Rationale

## Purpose

The ETL pipeline is separated into distinct layers so that each part of the system has one clear responsibility.

The main layers are:

- Fetching
- Parsing / transformation
- Persistence
- Pipeline orchestration

This separation makes the project easier to understand, test, debug, maintain, and extend.

---

## Fetching Layer

The fetching layer is responsible for retrieving data from NASA's NeoWs API.

Example files:

- `fetch_neows.py`
- `fetch_orbital_parameters.py`

This layer handles:

- API requests
- Request parameters
- Timeouts
- HTTP errors
- API response retrieval

It should not be responsible for database inserts or analytical interpretation.

Keeping fetching separate means API logic can be updated without changing the database layer.

---

## Parsing and Transformation Layer

The parsing and transformation layer converts raw NASA JSON data into clean Python dictionaries that match the database schema.

Example files:

- `parse_asteroids.py`
- `parse_close_approaches.py`
- `transform_neows.py`

This layer handles:

- Extracting nested JSON fields
- Renaming fields into database-friendly names
- Flattening nested structures
- Preparing records for insertion

It should not make API requests or write directly to the database.

Keeping parsing separate makes it easier to test whether raw data is being converted correctly.

---

## Persistence Layer

The persistence layer is responsible for writing cleaned records into SQLite.

Example files:

- `load_asteroids.py`
- `load_close_approaches.py`
- `load_orbital_parameters.py`
- `connection.py`

This layer handles:

- Database connections
- SQL insert statements
- Foreign key relationships
- Duplicate prevention
- Transaction-safe loading

It should not fetch data from NASA or reshape raw JSON.

Keeping persistence separate makes it easier to change the database system later, such as migrating from SQLite to PostgreSQL.

---

## Pipeline Orchestration

The pipeline orchestration layer coordinates the full workflow.

Example file:

- `run_pipeline.py`

This layer controls the sequence:

1. Initialize the database
2. Fetch raw data
3. Parse and transform records
4. Insert records into the database
5. Log ingestion success or failure

The orchestrator should remain high-level and readable. It should call specialized functions rather than contain all business logic directly.

---

## Benefits of Separation

This architecture provides several benefits:

| Benefit | Explanation |
|---|---|
| Maintainability | Each file has a focused purpose and can be updated independently. |
| Testability | Fetching, parsing, and loading logic can be tested separately. |
| Debuggability | Errors are easier to isolate because each layer has a clear responsibility. |
| Reusability | Parsing and loading functions can be reused in future workflows. |
| Scalability | The project can grow without becoming one large, fragile script. |
| Database portability | The persistence layer can be changed if the project moves from SQLite to PostgreSQL. |

---

## Conclusion

The ETL pipeline is separated into fetching, parsing, persistence, and orchestration layers to keep the architecture clean and maintainable.

This structure supports professional data engineering practices and makes the project easier to explain, troubleshoot, and extend.