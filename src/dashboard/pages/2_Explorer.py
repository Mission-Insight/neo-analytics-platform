import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))

import altair as alt  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from src.dashboard.ui_settings import APP_TITLE  # noqa: E402
from src.dashboard.data_service import (  # noqa: E402
    get_asteroid,
    get_close_approaches,
    get_score_explanation,
    search_asteroids,
)
from src.dashboard.layout import (  # noqa: E402
    chart_color,
    configure_page,
    render_footer,
    render_page_header,
    render_sidebar,
)
from src.dashboard.palette import AMBER, BLUE, DARK_GREEN, GREEN  # noqa: E402

configure_page(f"Explorer — {APP_TITLE}")

# Categorical slots 1, 2, 3, 4, in the same descending-weight order used on
# the Model Card (size, proximity, velocity, frequency) — fixed order, never
# cycled.
_BREAKDOWN_COLORS = {
    "size": BLUE,
    "proximity": GREEN,
    "velocity": AMBER,
    "frequency": DARK_GREEN,
}
_BREAKDOWN_LABELS = {
    "size": "Size",
    "proximity": "Proximity",
    "velocity": "Velocity",
    "frequency": "Frequency",
}


def _search(query: str) -> list[dict]:
    """Search by exact ID or name substring, merged and deduplicated by ID."""
    results = {}

    by_id = get_asteroid(query)
    if by_id is not None:
        results[by_id["asteroid_id"]] = by_id

    for row in search_asteroids(query):
        results[row["asteroid_id"]] = row

    return list(results.values())


def _fmt(value: float | None, unit: str = "", decimals: int = 4) -> str:
    return f"{value:.{decimals}f}{unit}" if value is not None else "Not available"


def _render_risk_breakdown(asteroid_id: str) -> None:
    explanation = get_score_explanation(asteroid_id)
    if explanation is None:
        st.caption("Risk breakdown unavailable — this asteroid could not be scored.")
        return

    st.markdown("**Risk Breakdown**")
    st.caption(f"Composite risk score: **{explanation['risk_score']:.3f}**")

    order = ["size", "proximity", "velocity", "frequency"]
    breakdown_df = pd.DataFrame(
        [
            {
                "row": "Risk Score",
                "feature": _BREAKDOWN_LABELS[f],
                "order": i,
                "raw_normalized": explanation["normalized"][f],
                "weight": explanation["weights"][f],
                "contribution": explanation["contributions"][f],
            }
            for i, f in enumerate(order)
        ]
    )

    color_scale = alt.Scale(
        domain=[_BREAKDOWN_LABELS[f] for f in order],
        range=[chart_color(_BREAKDOWN_COLORS[f]) for f in order],
    )
    bar = (
        alt.Chart(breakdown_df)
        .mark_bar(size=18)
        .encode(
            x=alt.X("contribution:Q", stack="zero", title="Contribution to Risk Score"),
            y=alt.Y("row:N", axis=None, title=""),
            color=alt.Color(
                "feature:N", scale=color_scale, sort=None, legend=alt.Legend(title="Feature")
            ),
            order=alt.Order("order:Q"),
            tooltip=[
                alt.Tooltip("feature:N", title="Feature"),
                alt.Tooltip("contribution:Q", title="Contribution", format=".3f"),
                alt.Tooltip("weight:Q", title="Weight", format=".2f"),
                alt.Tooltip("raw_normalized:Q", title="Normalized value", format=".3f"),
            ],
        )
        .properties(height=110)
    )
    st.altair_chart(bar, use_container_width=True)

    detail_rows = [
        {
            "Feature": _BREAKDOWN_LABELS[f],
            "Normalized Value": round(explanation["normalized"][f], 3),
            "Weight": explanation["weights"][f],
            "Contribution": round(explanation["contributions"][f], 3),
        }
        for f in order
    ]
    st.dataframe(detail_rows, use_container_width=True, hide_index=True)


def _render_profile(row: dict) -> None:
    st.divider()
    st.subheader(row["name"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Diameter", _fmt(row["diameter_km"], " km", 3))
    c2.metric("Hazardous Status", "Yes" if row["is_potentially_hazardous"] else "No")
    c3.metric("Risk Rank", f"#{row['rank']}" if row["rank"] is not None else "Not scorable")

    if row["is_potentially_hazardous"]:
        st.warning("Potentially Hazardous Object (PHO)", icon="⚠️")

    _render_risk_breakdown(row["asteroid_id"])

    st.markdown("**Orbital Data**")
    orbital_rows = [
        {"Parameter": "Eccentricity", "Value": _fmt(row["eccentricity"])},
        {"Parameter": "Inclination", "Value": _fmt(row["inclination"], "°", 2)},
        {"Parameter": "Orbital Period", "Value": _fmt(row["orbital_period"], " days", 1)},
        {"Parameter": "Semi-Major Axis", "Value": _fmt(row["semi_major_axis"], " AU")},
        {"Parameter": "Perihelion Distance", "Value": _fmt(row["perihelion_distance"], " AU")},
    ]
    st.dataframe(orbital_rows, use_container_width=True, hide_index=True)

    st.markdown("**Close Approach History**")
    approaches = get_close_approaches(row["asteroid_id"])
    if approaches:
        approach_rows = [
            {
                "Date": a["close_approach_date"],
                "Miss Distance (km)": (
                    f"{a['miss_distance_km']:,.0f}" if a["miss_distance_km"] is not None else "—"
                ),
                "Velocity (km/s)": (
                    f"{a['relative_velocity_kps']:.2f}"
                    if a["relative_velocity_kps"] is not None
                    else "—"
                ),
                "Orbiting Body": a["orbiting_body"],
            }
            for a in approaches
        ]
        st.dataframe(approach_rows, use_container_width=True, hide_index=True)
    else:
        st.caption("No recorded close approaches for this asteroid in the dataset window.")


render_sidebar()
render_page_header("Explorer", "Search and inspect individual asteroids")

query = st.text_input("Search by asteroid name or ID", placeholder="e.g. 433 Eros or 2000433")

if query:
    matches = _search(query)
    if matches:
        st.caption(f"{len(matches)} match{'es' if len(matches) != 1 else ''}")
        table_rows = [
            {
                "ID": r["asteroid_id"],
                "Name": r["name"],
                "Rank": r["rank"],
                "Risk Score": round(r["risk_score"], 3) if r["risk_score"] is not None else None,
                "PHO": "●" if r["is_potentially_hazardous"] else "",
            }
            for r in matches
        ]
        st.dataframe(table_rows, use_container_width=True, hide_index=True)

        selected_id = st.selectbox(
            "View profile",
            options=[m["asteroid_id"] for m in matches],
            format_func=lambda aid: next(m["name"] for m in matches if m["asteroid_id"] == aid),
        )
        _render_profile(next(m for m in matches if m["asteroid_id"] == selected_id))
    else:
        st.warning(f"No asteroids found matching '{query}'.")
else:
    st.caption("Enter a name or ID above to search.")

render_footer()
