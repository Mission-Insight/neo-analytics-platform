import sqlite3


def _fetch_raw_data(conn: sqlite3.Connection) -> list[dict]:
    """
    Join asteroids, close_approaches, and orbital_parameters into a
    unified modeling dataset. One row per asteroid.

    Close approach fields are aggregated per asteroid:
      - min_miss_distance_km: closest recorded approach
      - max_relative_velocity_kps: fastest recorded approach
      - approach_count: total number of recorded approaches

    Orbital parameter fields are included as-is (left join, may be NULL).
    """
    rows = conn.execute(
        """
        SELECT
            a.asteroid_id,
            a.name,
            a.estimated_diameter_min_km,
            a.estimated_diameter_max_km,
            a.is_potentially_hazardous,

            COUNT(ca.close_approach_id)      AS approach_count,
            MIN(ca.miss_distance_km)         AS min_miss_distance_km,
            MAX(ca.relative_velocity_kps)    AS max_relative_velocity_kps,

            op.eccentricity,
            op.inclination,
            op.orbital_period,
            op.semi_major_axis,
            op.perihelion_distance

        FROM asteroids a
        LEFT JOIN close_approaches ca
            ON ca.asteroid_id = a.asteroid_id
        LEFT JOIN orbital_parameters op
            ON op.asteroid_id = a.asteroid_id
        GROUP BY
            a.asteroid_id,
            a.name,
            a.estimated_diameter_min_km,
            a.estimated_diameter_max_km,
            a.is_potentially_hazardous,
            op.eccentricity,
            op.inclination,
            op.orbital_period,
            op.semi_major_axis,
            op.perihelion_distance
        """
    ).fetchall()

    columns = [
        "asteroid_id",
        "name",
        "estimated_diameter_min_km",
        "estimated_diameter_max_km",
        "is_potentially_hazardous",
        "approach_count",
        "min_miss_distance_km",
        "max_relative_velocity_kps",
        "eccentricity",
        "inclination",
        "orbital_period",
        "semi_major_axis",
        "perihelion_distance",
    ]

    return [dict(zip(columns, row)) for row in rows]


def _add_diameter_feature(rows: list[dict]) -> list[dict]:
    """
    Add diameter_km to each row: average of min and max diameter estimates.
    NULL if either source field is missing.
    """
    for row in rows:
        min_km = row["estimated_diameter_min_km"]
        max_km = row["estimated_diameter_max_km"]

        if min_km is not None and max_km is not None:
            row["diameter_km"] = (min_km + max_km) / 2.0
        else:
            row["diameter_km"] = None

    return rows


def _add_encounter_frequency_feature(rows: list[dict]) -> list[dict]:
    """
    Add encounter_frequency to each row: total number of recorded close
    approaches per asteroid. 0 for asteroids with no approach records.
    """
    for row in rows:
        row["encounter_frequency"] = row["approach_count"]
    return rows


def _add_miss_distance_feature(rows: list[dict]) -> list[dict]:
    """
    Add miss_distance_km to each row: minimum miss distance across all
    recorded close approaches. NULL if no close approach records exist.
    Strategy: minimum (closest recorded approach = worst-case proximity).
    """
    for row in rows:
        row["miss_distance_km"] = row["min_miss_distance_km"]
    return rows


def _add_velocity_feature(rows: list[dict]) -> list[dict]:
    """
    Add velocity_kps to each row: maximum relative velocity across all
    recorded close approaches. NULL if no close approach records exist.
    Strategy rationale: see docs/risk_model_design.md section 5.2.3.
    """
    for row in rows:
        row["velocity_kps"] = row["max_relative_velocity_kps"]
    return rows


def _handle_missing_data(rows: list[dict]) -> list[dict]:
    """
    Stamp each row with is_scorable: True only when all three continuous
    scoring features are present. Asteroids missing velocity or miss
    distance have no close approach records and cannot be scored.
    encounter_frequency is excluded from this check because COUNT never
    returns NULL — it is always 0 or a positive integer.
    """
    for row in rows:
        row["is_scorable"] = (
            row["diameter_km"] is not None
            and row["velocity_kps"] is not None
            and row["miss_distance_km"] is not None
        )
    return rows


_W_SIZE = 0.40
_W_PROXIMITY = 0.30
_W_VELOCITY = 0.20
_W_FREQUENCY = 0.10


def _compute_risk_scores(rows: list[dict]) -> list[dict]:
    for row in rows:
        if not row["is_scorable"]:
            row["risk_score"] = None
            continue
        row["risk_score"] = (
            _W_SIZE * row["diameter_norm"]
            + _W_PROXIMITY * row["miss_distance_norm"]
            + _W_VELOCITY * row["velocity_norm"]
            + _W_FREQUENCY * row["encounter_frequency_norm"]
        )
    return rows


def _build_features(rows: list[dict]) -> list[dict]:
    """
    Apply all feature engineering steps in sequence.
    Each subtask (5.2.2–5.2.5) adds one call here.
    """
    rows = _add_diameter_feature(rows)
    rows = _add_velocity_feature(rows)
    rows = _add_miss_distance_feature(rows)
    rows = _add_encounter_frequency_feature(rows)
    rows = _handle_missing_data(rows)
    ranges = _compute_feature_ranges(rows)
    rows = _normalize_features(rows, ranges)
    rows = _compute_risk_scores(rows)
    return rows


def _minmax(value: float, lo: float, hi: float) -> float:
    if hi == lo:
        return 0.0
    return (value - lo) / (hi - lo)


def _compute_feature_ranges(rows: list[dict]) -> dict:
    """
    Compute min and max for each scoring feature across all scorable rows.
    Non-scorable rows are excluded so NULL values don't skew the range.
    encounter_frequency is included even though it is never NULL — its range
    is still computed from scorable rows for consistency.
    """
    scorable = [r for r in rows if r["is_scorable"]]
    features = ["diameter_km", "velocity_kps", "miss_distance_km", "encounter_frequency"]
    return {
        f: {
            "min": min(r[f] for r in scorable),
            "max": max(r[f] for r in scorable),
        }
        for f in features
    }


def _normalize_features(rows: list[dict], ranges: dict) -> list[dict]:
    """
    Apply min-max normalization to each scoring feature.
    miss_distance_norm is inverted (1 - normalized) so that closer = higher risk.
    Non-scorable rows receive None for all normalized fields.
    Strategy rationale: see docs/risk_model_design.md section 5.3.
    """
    for row in rows:
        if not row["is_scorable"]:
            row["diameter_norm"] = None
            row["velocity_norm"] = None
            row["miss_distance_norm"] = None
            row["encounter_frequency_norm"] = None
            continue

        r = ranges
        row["diameter_norm"] = _minmax(
            row["diameter_km"], r["diameter_km"]["min"], r["diameter_km"]["max"]
        )
        row["velocity_norm"] = _minmax(
            row["velocity_kps"], r["velocity_kps"]["min"], r["velocity_kps"]["max"]
        )
        row["miss_distance_norm"] = 1.0 - _minmax(
            row["miss_distance_km"], r["miss_distance_km"]["min"], r["miss_distance_km"]["max"]
        )
        row["encounter_frequency_norm"] = _minmax(
            row["encounter_frequency"],
            r["encounter_frequency"]["min"],
            r["encounter_frequency"]["max"],
        )

    return rows
