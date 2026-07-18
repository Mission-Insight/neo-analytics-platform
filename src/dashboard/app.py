import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from src.dashboard.config import APP_ICON, APP_LAYOUT, APP_SIDEBAR_STATE, APP_TITLE  # noqa: E402
from src.dashboard.data_service import (  # noqa: E402
    get_high_level_metrics,
    get_risk_distribution,
    get_size_distribution,
    get_top_risk,
)
from src.dashboard.layout import (  # noqa: E402
    chart_color,
    render_footer,
    render_page_header,
    render_sidebar,
)

# Categorical slots 1 (blue) and 5 (violet) from the dashboard's reference
# palette; each chart is a single series so no legend is needed.
_SIZE_CHART_COLOR = {"light": "#2a78d6", "dark": "#3987e5"}
_RISK_CHART_COLOR = {"light": "#4a3aa7", "dark": "#9085e9"}

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout=APP_LAYOUT,
    initial_sidebar_state=APP_SIDEBAR_STATE,
)


def _threat_label(row: dict) -> str:
    parts = []
    if row["diameter_norm"] > 0.5:
        parts.append("exceptional size")
    if row["miss_distance_norm"] > 0.85:
        parts.append("very close approach")
    elif row["miss_distance_norm"] > 0.6:
        parts.append("close approach")
    if row["velocity_norm"] > 0.7:
        parts.append("very high velocity")
    elif row["velocity_norm"] > 0.4:
        parts.append("high velocity")
    if not parts:
        parts.append("moderate multi-feature profile")
    label = ", ".join(parts[:2])
    return label[0].upper() + label[1:]


def _build_narrative(metrics: dict, rank1: dict) -> str:
    pho_rate = (
        metrics["hazardous_count"] / metrics["asteroid_count"] * 100
        if metrics["asteroid_count"]
        else 0.0
    )
    return (
        f"This dataset tracks **{metrics['asteroid_count']:,} near-Earth asteroids** recorded "
        f"between 2024 and 2026, of which **{metrics['hazardous_count']:,} ({pho_rate:.1f}%)** "
        f"are classified as potentially hazardous. Estimated diameters average "
        f"**{metrics['average_size_km']:.2f} km** across **{metrics['approach_count']:,} recorded "
        f"close approaches**. The highest-ranked object, **{rank1['name']}**, tops the list with a "
        f"risk score of **{rank1['risk_score']:.3f}** — {_threat_label(rank1).lower()}."
    )


def main():
    render_sidebar()
    render_page_header("Home", "Near-Earth Object risk rankings for 2024–2026")

    metrics = get_high_level_metrics()
    top10 = get_top_risk(10)
    rank1 = top10[0]

    # ── Summary narrative ────────────────────────────────────────────────────
    st.markdown(_build_narrative(metrics, rank1))

    st.divider()

    # ── Summary bar ──────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Asteroids", f"{metrics['asteroid_count']:,}")
    c2.metric("Hazardous (PHOs)", f"{metrics['hazardous_count']:,}")
    c3.metric("Average Size", f"{metrics['average_size_km']:.2f} km")
    c4.metric("Close Approaches", f"{metrics['approach_count']:,}")

    st.divider()

    # ── Rank-1 spotlight + Top-10 table ──────────────────────────────────────
    left, right = st.columns([1, 2])

    with left:
        st.subheader("Rank 1 Spotlight")
        st.metric(
            label=rank1["name"],
            value=f"{rank1['risk_score']:.3f}",
            help="Composite risk score ∈ [0, 1]",
        )
        st.caption(_threat_label(rank1))
        st.caption(
            f"Diameter: {rank1['diameter_km']:.2f} km  ·  "
            f"Miss distance: {rank1['miss_distance_km']:,.0f} km  ·  "
            f"Velocity: {rank1['velocity_kps']:.1f} km/s"
        )
        if rank1["is_potentially_hazardous"]:
            st.warning("Potentially Hazardous Object (PHO)", icon="⚠️")

    with right:
        st.subheader("Top 10 Risk Rankings")
        table_rows = [
            {
                "Rank": r["rank"],
                "Name": r["name"],
                "Score": round(r["risk_score"], 3),
                "Diameter (km)": (
                    round(r["diameter_km"], 3) if r["diameter_km"] else None
                ),
                "Miss Dist (km)": f"{r['miss_distance_km']:,.0f}",
                "Velocity (km/s)": round(r["velocity_kps"], 1),
                "PHO": "●" if r["is_potentially_hazardous"] else "",
            }
            for r in top10
        ]
        st.dataframe(table_rows, use_container_width=True, hide_index=True)

    st.divider()

    # ── Key charts ────────────────────────────────────────────────────────────
    st.subheader("Key Distributions")
    chart_left, chart_right = st.columns(2)

    with chart_left:
        # Diameters span ~4 orders of magnitude (metres to ~17 km), so linear
        # bins bury everything but the smallest asteroids in one bar. Bin on a
        # log scale instead — same data, same counts, just a readable spread.
        sizes = np.array(get_size_distribution())
        edges = np.logspace(np.log10(sizes.min()), np.log10(sizes.max()), 21)
        counts, edges = np.histogram(sizes, bins=edges)
        size_df = pd.DataFrame(
            {
                "bin_start": edges[:-1],
                "bin_end": edges[1:],
                "count": counts,
                "range_label": [
                    f"{edges[i]:.3f}–{edges[i + 1]:.3f} km" for i in range(len(counts))
                ],
            }
        )
        size_chart = (
            alt.Chart(size_df)
            .mark_bar(color=chart_color(_SIZE_CHART_COLOR))
            .encode(
                x=alt.X("bin_start:Q", scale=alt.Scale(type="log"), title="Diameter (km, log scale)"),
                x2="bin_end:Q",
                y=alt.Y("count:Q", title="Asteroids"),
                tooltip=[
                    alt.Tooltip("range_label:N", title="Diameter"),
                    alt.Tooltip("count:Q", title="Count"),
                ],
            )
            .properties(title="Size Distribution", height=300)
        )
        st.altair_chart(size_chart, use_container_width=True)

    with chart_right:
        risk_df = pd.DataFrame({"risk_score": get_risk_distribution()})
        risk_chart = (
            alt.Chart(risk_df)
            .mark_bar(color=chart_color(_RISK_CHART_COLOR))
            .encode(
                x=alt.X("risk_score:Q", bin=alt.Bin(maxbins=25), title="Risk Score"),
                y=alt.Y("count():Q", title="Asteroids"),
                tooltip=[
                    alt.Tooltip("risk_score:Q", bin=alt.Bin(maxbins=25), title="Risk Score"),
                    alt.Tooltip("count():Q", title="Count"),
                ],
            )
            .properties(title="Risk Score Distribution", height=300)
        )
        st.altair_chart(risk_chart, use_container_width=True)

    render_footer()


main()
