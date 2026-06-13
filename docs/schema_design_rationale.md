# Schema Design Rationale

## Purpose

This document explains the reasoning behind the relational database schema designed for the NASA NeoWs analytics platform.

The schema transforms nested JSON API responses into a normalized relational model that supports efficient querying, data integrity, and future analytical workloads.

---

# Normalization Choices

## Separation of Asteroids and Close Approaches

The NeoWs API contains asteroid records that include nested `close_approach_data`.

Rather than storing close approach information inside the asteroid table, the design separates these concepts into two tables:

* `asteroids`
* `close_approaches`

This decision was made because a single asteroid may have multiple close approach events.

Example:

```text
Apophis
├── Approach 1
├── Approach 2
├── Approach 3
└── Approach 4
```

Storing close approaches inside the asteroid table would create repeating groups and violate First Normal Form (1NF).

The one-to-many relationship is instead represented through a foreign key:

```text
close_approaches.asteroid_id
    →
asteroids.asteroid_id
```

---

## Separation of Orbital Parameters

Orbital characteristics are stored in a dedicated `orbital_parameters` table.

Examples include:

* orbit_class
* eccentricity
* inclination
* orbital_period

These values describe the asteroid itself rather than a specific close approach event.

Separating orbital data prevents repeated storage of identical orbital values across multiple approach records.

This reduces redundancy and improves maintainability.

---

## Ingestion Metadata Isolation

Operational ETL information is stored separately in the `ingestion_log` table.

Examples include:

* ingestion timestamp
* rows processed
* processing duration
* execution status

These values describe the ingestion process rather than the asteroid data.

Keeping operational metadata separate avoids mixing business data with pipeline monitoring information.

---

# Key Strategy

## Asteroid Primary Key

The `asteroids` table uses NASA's provided asteroid identifier:

```text
asteroid_id
```

This value is stable across API requests and naturally identifies a unique asteroid.

Using the NASA identifier avoids the need to generate surrogate keys for asteroid records.

---

## Close Approach Primary Key

The `close_approaches` table uses:

```text
approach_id
```

as an auto-generated surrogate key.

The NeoWs feed payload does not provide a dedicated close-approach identifier.

Using a generated key ensures every close-approach record can be uniquely referenced.

---

## Orbital Parameter Primary Key

The `orbital_parameters` table uses:

```text
asteroid_id
```

as both:

* Primary Key
* Foreign Key

This enforces a one-to-one relationship between an asteroid and its orbital parameter record.

---

## Ingestion Log Primary Key

The `ingestion_log` table uses:

```text
ingestion_id
```

as an auto-generated primary key.

Each ingestion attempt represents a unique operational event and therefore requires a unique identifier.

---

# Denormalization Tradeoffs Avoided

## Avoided Repeating Asteroid Data

An alternative design would duplicate asteroid information for every close approach.

Example:

```text
Apophis + Approach 1
Apophis + Approach 2
Apophis + Approach 3
```

This would cause:

* duplicate asteroid names
* duplicate diameter values
* duplicate hazard classifications

The normalized design stores asteroid information once and references it through foreign keys.

---

## Avoided Repeating Orbital Parameters

Orbital characteristics remain relatively static.

Embedding them in every close-approach record would create unnecessary duplication and increase storage requirements.

Separating orbital data eliminates this redundancy.

---

## Avoided Mixing Operational and Business Data

The ingestion log is intentionally separated from asteroid-related tables.

Combining ETL metadata with asteroid records would complicate queries and violate separation of concerns.

---

# Benefits of the Final Design

The final schema provides:

* normalized relational structure
* reduced data redundancy
* strong referential integrity
* support for future analytical workloads
* simplified ETL maintenance
* improved data quality controls

The design follows common data-engineering practices and provides a scalable foundation for future expansion of the NeoWs analytics platform.
