import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from src.dashboard.ui_settings import APP_TITLE  # noqa: E402
from src.dashboard.data_service import (  # noqa: E402
    get_all_close_approaches,
    get_all_scores,
    get_feature_matrix,
)
from src.dashboard.layout import (  # noqa: E402
    chart_color,
    configure_page,
    render_footer,
    render_page_header,
    render_sidebar,
)
from src.dashboard.palette import BLUE, DIVERGING, GREEN, RED  # noqa: E402

configure_page(f"Analytics — {APP_TITLE}")

_TIMELINE_COLOR = BLUE
_DISTANCE_COLOR = GREEN

# Categorical slots 1 (blue) and 6 (red) — non-hazardous vs. hazardous, a
# fixed 2-series identity comparison, not the reserved status palette.
_POPULATION_COLORS = {
    "Non-Hazardous": BLUE,
    "Hazardous": RED,
}

# For the correlation matrix's -1..+1 scale.
_CORR_DIVERGING = DIVERGING

_FEATURE_LABELS = {
    "absolute_magnitude_h": "Absolute Magnitude (H)",
    "estimated_diameter_max_km": "Max Diameter (km)",
    "is_potentially_hazardous": "Hazardous Status",
    "minimum_orbit_intersection": "MOID",
    "eccentricity": "Eccentricity",
    "inclination": "Inclination",
    "semi_major_axis": "Semi-Major Axis",
    "perihelion_distance": "Perihelion Distance",
    "aphelion_distance": "Aphelion Distance",
    "jupiter_tisserand_invariant": "Jupiter Tisserand Invariant",
    "min_miss_distance_km": "Min Miss Distance (km)",
    "max_relative_velocity_kps": "Max Velocity (km/s)",
}


def _population_density_chart(hazardous, non_hazardous, bins, x_title, log_scale=False):
    """Overlaid density histograms comparing hazardous vs. non-hazardous NEOs."""
    haz_density, edges = np.histogram(hazardous, bins=bins, density=True)
    non_density, _ = np.histogram(non_hazardous, bins=bins, density=True)

    groups = [
        (f"Non-Hazardous (n={len(non_hazardous):,})", non_density),
        (f"Hazardous (n={len(hazardous):,})", haz_density),
    ]
    df = pd.concat(
        [
            pd.DataFrame(
                {
                    "bin_start": edges[:-1],
                    "bin_end": edges[1:],
                    "density": density,
                    "group": label,
                }
            )
            for label, density in groups
        ],
        ignore_index=True,
    )

    color_scale = alt.Scale(
        domain=[g[0] for g in groups],
        range=[
            chart_color(_POPULATION_COLORS["Non-Hazardous"]),
            chart_color(_POPULATION_COLORS["Hazardous"]),
        ],
    )
    x_encode = alt.X(
        "bin_start:Q",
        title=x_title,
        scale=alt.Scale(type="log") if log_scale else alt.Undefined,
    )
    return (
        alt.Chart(df)
        .mark_bar(opacity=0.65)
        .encode(
            x=x_encode,
            x2="bin_end:Q",
            y=alt.Y("density:Q", title="Density", stack=None),
            color=alt.Color("group:N", scale=color_scale, sort=None, legend=alt.Legend(title="Population")),
            tooltip=[
                alt.Tooltip("group:N", title="Population"),
                alt.Tooltip("density:Q", title="Density", format=".4f"),
            ],
        )
        .properties(height=300)
    )


def _correlation_heatmap(corr_matrix: pd.DataFrame):
    """Diverging-color correlation matrix (blue = negative, red = positive)."""
    long_df = corr_matrix.reset_index(names="feature_y").melt(
        id_vars="feature_y", var_name="feature_x", value_name="correlation"
    )

    stops = chart_color(_CORR_DIVERGING)
    color_scale = alt.Scale(domain=[-1, 0, 1], range=[stops["low"], stops["mid"], stops["high"]])
    order = corr_matrix.columns.tolist()

    base = alt.Chart(long_df).encode(
        x=alt.X("feature_x:N", title=None, sort=order),
        y=alt.Y("feature_y:N", title=None, sort=order),
    )
    rects = base.mark_rect().encode(
        color=alt.Color("correlation:Q", scale=color_scale, legend=alt.Legend(title="r")),
        tooltip=[
            alt.Tooltip("feature_y:N", title="Feature"),
            alt.Tooltip("feature_x:N", title="vs."),
            alt.Tooltip("correlation:Q", title="r", format=".2f"),
        ],
    )
    text = base.mark_text(fontSize=9).encode(
        text=alt.Text("correlation:Q", format=".2f"),
        color=alt.condition(
            "abs(datum.correlation) > 0.6", alt.value("white"), alt.value("#0b0b0b")
        ),
    )
    return (rects + text).properties(width=500, height=500)


def _relationship_scatter(df: pd.DataFrame, x_field, y_field, x_title, y_title, log_x=False, log_y=False):
    """Scatter of two features colored by hazard status, with a correlation annotation."""
    plot_df = df[[x_field, y_field, "is_potentially_hazardous"]].dropna().copy()
    plot_df["Population"] = plot_df["is_potentially_hazardous"].map(
        {0: "Non-Hazardous", 1: "Hazardous"}
    )
    r = plot_df[x_field].corr(plot_df[y_field])

    color_scale = alt.Scale(
        domain=["Non-Hazardous", "Hazardous"],
        range=[
            chart_color(_POPULATION_COLORS["Non-Hazardous"]),
            chart_color(_POPULATION_COLORS["Hazardous"]),
        ],
    )
    chart = (
        alt.Chart(plot_df)
        .mark_circle(size=30, opacity=0.6)
        .encode(
            x=alt.X(
                f"{x_field}:Q",
                title=x_title,
                scale=alt.Scale(type="log") if log_x else alt.Undefined,
            ),
            y=alt.Y(
                f"{y_field}:Q",
                title=y_title,
                scale=alt.Scale(type="log") if log_y else alt.Undefined,
            ),
            color=alt.Color("Population:N", scale=color_scale, legend=alt.Legend(title="Population")),
            tooltip=[
                alt.Tooltip("Population:N"),
                alt.Tooltip(f"{x_field}:Q", title=x_title, format=",.3f"),
                alt.Tooltip(f"{y_field}:Q", title=y_title, format=",.3f"),
            ],
        )
        .properties(height=380)
    )
    st.altair_chart(chart, use_container_width=True)
    st.caption(f"Pearson r = {r:.3f}")


def _filter_by_date_range(approaches: pd.DataFrame) -> pd.DataFrame:
    min_date = approaches["close_approach_date"].min().date()
    max_date = approaches["close_approach_date"].max().date()
    date_range = st.date_input(
        "Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date
    )
    if len(date_range) == 2:
        start_date, end_date = date_range
        approaches = approaches[
            (approaches["close_approach_date"] >= pd.Timestamp(start_date))
            & (approaches["close_approach_date"] <= pd.Timestamp(end_date))
        ]
    st.caption(f"{len(approaches):,} close approaches in the selected range")
    return approaches


def _render_timeline(approaches: pd.DataFrame) -> None:
    st.subheader("Approach Timeline")

    monthly = (
        approaches.set_index("close_approach_date")
        .resample("MS")
        .size()
        .reset_index(name="count")
        .rename(columns={"close_approach_date": "month"})
    )

    timeline = (
        alt.Chart(monthly)
        .mark_line(point=True, color=chart_color(_TIMELINE_COLOR))
        .encode(
            x=alt.X("month:T", title="Month"),
            y=alt.Y("count:Q", title="Close Approaches"),
            tooltip=[
                alt.Tooltip("month:T", title="Month", format="%b %Y"),
                alt.Tooltip("count:Q", title="Approaches"),
            ],
        )
        .properties(height=320)
    )
    st.altair_chart(timeline, use_container_width=True)


def _render_distance_distribution(approaches: pd.DataFrame) -> None:
    st.subheader("Miss Distance Distribution")

    # Miss distances span ~3 orders of magnitude (thousands to tens of millions of
    # km), so bin on a log scale — same technique as the Home page's size chart.
    distances = approaches["miss_distance_km"].dropna().to_numpy()
    dist_edges = np.logspace(np.log10(distances.min()), np.log10(distances.max()), 26)
    dist_counts, dist_edges = np.histogram(distances, bins=dist_edges)
    distance_df = pd.DataFrame(
        {
            "bin_start": dist_edges[:-1],
            "bin_end": dist_edges[1:],
            "count": dist_counts,
            "range_label": [
                f"{dist_edges[i]:,.0f}–{dist_edges[i + 1]:,.0f} km" for i in range(len(dist_counts))
            ],
        }
    )

    distance_chart = (
        alt.Chart(distance_df)
        .mark_bar(color=chart_color(_DISTANCE_COLOR))
        .encode(
            x=alt.X("bin_start:Q", scale=alt.Scale(type="log"), title="Miss Distance (km, log scale)"),
            x2="bin_end:Q",
            y=alt.Y("count:Q", title="Close Approaches"),
            tooltip=[
                alt.Tooltip("range_label:N", title="Miss Distance"),
                alt.Tooltip("count:Q", title="Count"),
            ],
        )
        .properties(height=320)
    )
    st.altair_chart(distance_chart, use_container_width=True)


def _render_closest_approaches(approaches: pd.DataFrame) -> None:
    st.subheader("Closest Recorded Approaches")

    closest = approaches.nsmallest(20, "miss_distance_km")
    closest_rows = [
        {
            "Name": row["name"],
            "Date": row["close_approach_date"].strftime("%Y-%m-%d"),
            "Miss Distance (km)": f"{row['miss_distance_km']:,.0f}",
            "Velocity (km/s)": (
                f"{row['relative_velocity_kps']:.2f}"
                if pd.notna(row["relative_velocity_kps"])
                else "—"
            ),
            "Orbiting Body": row["orbiting_body"],
        }
        for _, row in closest.iterrows()
    ]
    st.dataframe(closest_rows, use_container_width=True, hide_index=True)


def _render_population_comparisons(asteroids: pd.DataFrame, all_approaches: pd.DataFrame) -> None:
    st.divider()
    st.header("Scientific Insights")
    st.caption(
        "Findings from the Epic 4 exploratory analysis, reproduced here against the "
        "full dataset (not scoped to the date range selected above)."
    )

    hazardous_asteroids = asteroids[asteroids["is_potentially_hazardous"] == 1]
    non_hazardous_asteroids = asteroids[asteroids["is_potentially_hazardous"] == 0]

    hazardous_ca = all_approaches[all_approaches["is_potentially_hazardous"] == 1]
    non_hazardous_ca = all_approaches[all_approaches["is_potentially_hazardous"] == 0]

    st.subheader("Diameter: Hazardous vs. Non-Hazardous")
    haz_diam = hazardous_asteroids["diameter_km"].dropna().to_numpy()
    non_diam = non_hazardous_asteroids["diameter_km"].dropna().to_numpy()
    diam_bins = np.logspace(
        np.log10(asteroids["diameter_km"].dropna().min()),
        np.log10(asteroids["diameter_km"].dropna().max()),
        25,
    )
    st.altair_chart(
        _population_density_chart(haz_diam, non_diam, diam_bins, "Diameter (km, log scale)", log_scale=True),
        use_container_width=True,
    )

    st.subheader("Velocity: Hazardous vs. Non-Hazardous")
    haz_vel = hazardous_ca["relative_velocity_kps"].dropna().to_numpy()
    non_vel = non_hazardous_ca["relative_velocity_kps"].dropna().to_numpy()
    vel_bins = np.linspace(0, all_approaches["relative_velocity_kps"].max() + 1, 35)
    st.altair_chart(
        _population_density_chart(haz_vel, non_vel, vel_bins, "Relative Velocity (km/s)"),
        use_container_width=True,
    )

    st.subheader("Miss Distance: Hazardous vs. Non-Hazardous")
    haz_dist = hazardous_ca["miss_distance_km"].dropna().to_numpy()
    non_dist = non_hazardous_ca["miss_distance_km"].dropna().to_numpy()
    dist_bins = np.logspace(
        np.log10(all_approaches["miss_distance_km"].dropna().min()),
        np.log10(all_approaches["miss_distance_km"].dropna().max()),
        25,
    )
    st.altair_chart(
        _population_density_chart(haz_dist, non_dist, dist_bins, "Miss Distance (km, log scale)", log_scale=True),
        use_container_width=True,
    )

    st.markdown(
        "**Interpretation.** Hazardous asteroids are systematically larger, faster, and closer-passing "
        "than non-hazardous ones — but each gap follows directly from how PHO status is defined, not "
        "from an independent physical difference. NASA's classification requires a minimum orbit "
        "intersection distance (MOID) ≤ 0.05 AU *and* a size above roughly 140 m (H ≤ 22), so the "
        "criteria themselves select for larger, closer-passing objects. Velocity is a secondary effect: "
        "eccentric, Earth-crossing orbits are more likely to be classified hazardous *and* tend to "
        "produce faster encounters. Notably, the single closest recorded approach in the dataset "
        "belongs to a **non-hazardous** asteroid — proximity on a given pass and MOID-based "
        "classification are related but not identical."
    )


def _render_correlation_analysis(features: pd.DataFrame) -> None:
    st.subheader("Correlation Analysis")
    st.caption(
        "Pearson correlation across 12 candidate features (Epic 4, section 4.6). "
        "Values near ±1 indicate a strong relationship; near 0 indicates none."
    )

    feature_cols = [c for c in features.columns if c != "asteroid_id"]
    corr_matrix = features[feature_cols].corr().rename(columns=_FEATURE_LABELS, index=_FEATURE_LABELS)
    st.altair_chart(_correlation_heatmap(corr_matrix), use_container_width=True)

    st.markdown("**Size vs. Velocity**")
    _relationship_scatter(
        features,
        "estimated_diameter_max_km",
        "max_relative_velocity_kps",
        "Max Diameter (km, log scale)",
        "Max Velocity (km/s)",
        log_x=True,
    )

    st.markdown("**Size vs. Miss Distance**")
    _relationship_scatter(
        features,
        "estimated_diameter_max_km",
        "min_miss_distance_km",
        "Max Diameter (km, log scale)",
        "Min Miss Distance (km, log scale)",
        log_x=True,
        log_y=True,
    )

    st.markdown(
        "**Interpretation.** Absolute magnitude (H) is the single strongest predictor of hazard "
        "status (r ≈ −0.38) — a direct consequence of the H ≤ 22 size criterion built into the PHO "
        "definition. Eccentricity (r ≈ +0.24) and MOID (r ≈ −0.21) are the strongest orbital "
        "predictors, but no single feature separates the two populations cleanly; a real classifier "
        "would need to combine several. The three strongest correlations in the matrix — semi-major "
        "axis, aphelion distance, and the Tisserand parameter — are **structural**, not independent "
        "physical signals: they're mathematically linked by Keplerian orbital mechanics, so feeding "
        "all three into a model would be redundant. The two scatter plots tell a size-independence "
        "story: size vs. velocity (r ≈ 0.07) and size vs. miss distance (r ≈ −0.01) both show "
        "essentially no relationship — an asteroid's size says nothing about how fast or how close it "
        "passes. This is exactly why the risk model (docs/risk_model_design.md) treats diameter, "
        "velocity, and proximity as separate, non-redundant scoring inputs."
    )


def _render_outlier_investigation(
    features: pd.DataFrame,
    asteroids: pd.DataFrame,
    all_approaches: pd.DataFrame,
) -> None:
    st.subheader("Outlier Investigation")
    st.caption(
        "Notable objects surfaced by the Epic 4 outlier methodology (section 4.7): "
        "IQR fencing for size and velocity, percentile thresholding for proximity "
        "(the standard 1.5× IQR fence falls below zero for miss distance)."
    )

    diam = features["estimated_diameter_max_km"].dropna()
    q1, q3 = diam.quantile(0.25), diam.quantile(0.75)
    size_fence = q3 + 3 * (q3 - q1)
    size_outliers = (
        features[features["estimated_diameter_max_km"] > size_fence]
        .merge(asteroids[["asteroid_id", "name"]], on="asteroid_id", how="left")
        .sort_values("estimated_diameter_max_km", ascending=False)
    )
    st.markdown(f"**Size Outliers** — {len(size_outliers):,} asteroids above the 3× IQR fence ({size_fence:.3f} km)")
    st.dataframe(
        [
            {
                "Name": row["name"],
                "Diameter (km)": round(row["estimated_diameter_max_km"], 3),
                "Abs. Magnitude (H)": (
                    round(row["absolute_magnitude_h"], 2)
                    if pd.notna(row["absolute_magnitude_h"])
                    else None
                ),
                "PHO": "●" if row["is_potentially_hazardous"] else "",
            }
            for _, row in size_outliers.iterrows()
        ],
        use_container_width=True,
        hide_index=True,
    )

    vel = all_approaches["relative_velocity_kps"].dropna()
    q1v, q3v = vel.quantile(0.25), vel.quantile(0.75)
    vel_fence = q3v + 1.5 * (q3v - q1v)
    vel_outliers = all_approaches[all_approaches["relative_velocity_kps"] > vel_fence].sort_values(
        "relative_velocity_kps", ascending=False
    )
    st.markdown(
        f"**Velocity Outliers** — {len(vel_outliers):,} close approaches above the "
        f"1.5× IQR fence ({vel_fence:.2f} km/s)"
    )
    st.dataframe(
        [
            {
                "Name": row["name"],
                "Date": row["close_approach_date"],
                "Velocity (km/s)": round(row["relative_velocity_kps"], 2),
                "Miss Distance (km)": f"{row['miss_distance_km']:,.0f}",
                "PHO": "●" if row["is_potentially_hazardous"] else "",
            }
            for _, row in vel_outliers.iterrows()
        ],
        use_container_width=True,
        hide_index=True,
    )

    dist = all_approaches["miss_distance_km"].dropna()
    p5 = dist.quantile(0.05)
    dist_outliers = all_approaches[all_approaches["miss_distance_km"] <= p5].sort_values("miss_distance_km")
    st.markdown(
        f"**Proximity Outliers** — {len(dist_outliers):,} close approaches at or below "
        f"the 5th percentile ({p5:,.0f} km)"
    )
    st.dataframe(
        [
            {
                "Name": row["name"],
                "Date": row["close_approach_date"],
                "Miss Distance (km)": f"{row['miss_distance_km']:,.0f}",
                "Velocity (km/s)": (
                    round(row["relative_velocity_kps"], 2)
                    if pd.notna(row["relative_velocity_kps"])
                    else None
                ),
                "PHO": "●" if row["is_potentially_hazardous"] else "",
            }
            for _, row in dist_outliers.iterrows()
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown(
        "**Interpretation.** None of the flagged outliers are measurement errors — all three groups "
        "are physically plausible objects and events, not data-quality problems. Size outliers sit on "
        "a smooth extension of the expected log-normal diameter distribution with no discontinuity; "
        "velocity outliers are consistent with known high-eccentricity and high-inclination orbits "
        "(the correlations above); and proximity outliers are confirmed close-approach solutions from "
        "JPL orbital fits, not sensor anomalies. The one caveat: a small number of records are "
        "duplicated under alias catalog IDs — the same physical object gets a provisional and a "
        "permanent designation before the catalog reconciles — which slightly inflates the velocity "
        "and proximity outlier counts above. No outlier in this investigation represents a collision "
        "risk; the risk model's own limitations (docs/risk_model_card.md, L1) already make clear that "
        "ranking is about relative threat character, not impact prediction."
    )


render_sidebar()
render_page_header("Analytics", "Close-approach analytics and model diagnostics")

approaches = pd.DataFrame(get_all_close_approaches())
approaches["close_approach_date"] = pd.to_datetime(approaches["close_approach_date"])
approaches = _filter_by_date_range(approaches)

if approaches.empty:
    st.info("No close approaches recorded in the selected date range.")
    render_footer()
    st.stop()

_render_timeline(approaches)
_render_distance_distribution(approaches)
_render_closest_approaches(approaches)

asteroids = pd.DataFrame(get_all_scores())
all_approaches = pd.DataFrame(get_all_close_approaches())
_render_population_comparisons(asteroids, all_approaches)

features = pd.DataFrame(get_feature_matrix())
_render_correlation_analysis(features)
_render_outlier_investigation(features, asteroids, all_approaches)

render_footer()
