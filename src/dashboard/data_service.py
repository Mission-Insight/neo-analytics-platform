import streamlit as st

from src.dashboard.db import get_connection
from src.models.risk_score import compute_risk_scores
from src.models.risk_score import explain_score as _explain_score


@st.cache_data
def get_all_scores() -> list[dict]:
    """
    Centralized data retrieval for all dashboard pages.
    Opens a connection, computes risk scores for every asteroid, and closes
    the connection. Cached by Streamlit so repeated calls across pages/reruns
    don't re-hit the database.
    """
    conn = get_connection()
    try:
        return compute_risk_scores(conn)
    finally:
        conn.close()


@st.cache_data
def get_asteroid(asteroid_id: str) -> dict | None:
    """Return a single asteroid's record by ID, or None if no match exists."""
    for row in get_all_scores():
        if row["asteroid_id"] == asteroid_id:
            return row
    return None


@st.cache_data
def search_asteroids(query: str) -> list[dict]:
    """
    Return asteroid records whose name contains query (case-insensitive).
    Powers the dashboard's search-by-name/designation workflow.
    """
    if not query:
        return []
    q = query.lower()
    return [row for row in get_all_scores() if q in row["name"].lower()]


@st.cache_data
def get_rankings() -> list[dict]:
    """
    Return all scorable asteroids ordered by descending risk score (rank 1 first).
    Non-scorable asteroids are excluded. Powers the Risk Rankings page.
    """
    return [row for row in get_all_scores() if row["is_scorable"]]


@st.cache_data
def get_top_risk(n: int = 10) -> list[dict]:
    """Return the n highest-risk scorable asteroids. Powers the Home spotlight/top list."""
    return get_rankings()[:n]


@st.cache_data
def get_summary_metrics() -> dict:
    """
    Scorable-population summary metrics: scorable asteroid count, PHO count, and PHO rate.
    Powers the Risk Rankings page's scope indicator (curated top-N vs. full scorable population).
    """
    scorable = get_rankings()
    phos = [r for r in scorable if r["is_potentially_hazardous"]]
    return {
        "scorable_count": len(scorable),
        "pho_count": len(phos),
        "pho_rate": len(phos) / len(scorable) if scorable else 0.0,
    }


@st.cache_data
def get_approach_statistics() -> dict:
    """
    Aggregate close-approach statistics across all asteroids, scorable and non-scorable.
    Powers the Explorer/Analytics event-count displays.
    """
    rows = get_all_scores()
    return {
        "total_approaches": sum(row["approach_count"] for row in rows),
        "asteroids_with_approaches": sum(1 for row in rows if row["approach_count"] > 0),
    }


@st.cache_data
def get_size_distribution() -> list[float]:
    """Return known diameters (km) across all asteroids. Powers the size distribution chart."""
    return [row["diameter_km"] for row in get_all_scores() if row["diameter_km"] is not None]


@st.cache_data
def get_risk_distribution() -> list[float]:
    """Return risk scores across all scorable asteroids. Powers the risk distribution chart."""
    return [row["risk_score"] for row in get_rankings()]


@st.cache_data
def get_score_explanation(asteroid_id: str) -> dict | None:
    """
    Return the risk score breakdown (weights, normalized values, per-feature
    contributions) for a single asteroid, or None if it has no score. Powers
    the Explorer profile's risk breakdown.
    """
    row = get_asteroid(asteroid_id)
    if row is None or not row["is_scorable"]:
        return None
    return _explain_score(row)


@st.cache_data
def get_close_approaches(asteroid_id: str) -> list[dict]:
    """
    Return all recorded close-approach events for a single asteroid, sorted by
    date. Powers the Explorer profile's historical approaches table.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT close_approach_date, miss_distance_km, relative_velocity_kps, orbiting_body
            FROM close_approaches
            WHERE asteroid_id = ?
            ORDER BY close_approach_date
            """,
            (asteroid_id,),
        ).fetchall()
    finally:
        conn.close()

    columns = ["close_approach_date", "miss_distance_km", "relative_velocity_kps", "orbiting_body"]
    return [dict(zip(columns, row)) for row in rows]


@st.cache_data
def get_all_close_approaches() -> list[dict]:
    """
    Return every recorded close-approach event across all asteroids, sorted by
    date. Powers the Analytics page's close-approach timeline and distance charts.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT ca.asteroid_id, a.name, a.is_potentially_hazardous, ca.close_approach_date,
                   ca.miss_distance_km, ca.relative_velocity_kps, ca.orbiting_body
            FROM close_approaches ca
            JOIN asteroids a ON a.asteroid_id = ca.asteroid_id
            ORDER BY ca.close_approach_date
            """
        ).fetchall()
    finally:
        conn.close()

    columns = [
        "asteroid_id",
        "name",
        "is_potentially_hazardous",
        "close_approach_date",
        "miss_distance_km",
        "relative_velocity_kps",
        "orbiting_body",
    ]
    return [dict(zip(columns, row)) for row in rows]


@st.cache_data
def get_feature_matrix() -> list[dict]:
    """
    Return one row per asteroid with the candidate predictive features used in
    the Epic 4 correlation analysis: absolute magnitude, diameter, hazard
    status, orbital parameters, and per-asteroid close-approach aggregates.
    Powers the Analytics page's correlation matrix and relationship scatters.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT
                a.asteroid_id,
                a.absolute_magnitude_h,
                a.estimated_diameter_max_km,
                a.is_potentially_hazardous,
                op.minimum_orbit_intersection,
                op.eccentricity,
                op.inclination,
                op.semi_major_axis,
                op.perihelion_distance,
                op.aphelion_distance,
                op.jupiter_tisserand_invariant,
                MIN(ca.miss_distance_km) AS min_miss_distance_km,
                MAX(ca.relative_velocity_kps) AS max_relative_velocity_kps
            FROM asteroids a
            LEFT JOIN orbital_parameters op ON op.asteroid_id = a.asteroid_id
            LEFT JOIN close_approaches ca ON ca.asteroid_id = a.asteroid_id
            GROUP BY a.asteroid_id
            """
        ).fetchall()
    finally:
        conn.close()

    columns = [
        "asteroid_id",
        "absolute_magnitude_h",
        "estimated_diameter_max_km",
        "is_potentially_hazardous",
        "minimum_orbit_intersection",
        "eccentricity",
        "inclination",
        "semi_major_axis",
        "perihelion_distance",
        "aphelion_distance",
        "jupiter_tisserand_invariant",
        "min_miss_distance_km",
        "max_relative_velocity_kps",
    ]
    return [dict(zip(columns, row)) for row in rows]


@st.cache_data
def get_high_level_metrics() -> dict:
    """
    Executive-level dataset metrics across the full asteroid population (scorable
    and non-scorable): asteroid count, hazardous count, average size, and total
    close-approach count. Powers the Home page's executive summary bar.
    """
    rows = get_all_scores()
    hazardous = [row for row in rows if row["is_potentially_hazardous"]]
    sized = [row for row in rows if row["diameter_km"] is not None]

    return {
        "asteroid_count": len(rows),
        "hazardous_count": len(hazardous),
        "average_size_km": (
            sum(row["diameter_km"] for row in sized) / len(sized) if sized else 0.0
        ),
        "approach_count": get_approach_statistics()["total_approaches"],
    }
