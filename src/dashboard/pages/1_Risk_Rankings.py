import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from src.dashboard.ui_settings import APP_TITLE  # noqa: E402
from src.dashboard.data_service import get_rankings  # noqa: E402
from src.dashboard.layout import (  # noqa: E402
    configure_page,
    render_footer,
    render_page_header,
    render_sidebar,
)

configure_page(f"Risk Rankings — {APP_TITLE}")

render_sidebar()
render_page_header("Risk Rankings", "Full ranked list of scorable asteroids")

rankings = get_rankings()
min_size = min(r["diameter_km"] for r in rankings)
max_size = max(r["diameter_km"] for r in rankings)
max_score = max(r["risk_score"] for r in rankings)

f1, f2, f3 = st.columns([1, 2, 2])
with f1:
    pho_only = st.checkbox("Potentially hazardous only")
with f2:
    size_range = st.slider(
        "Size range (km)",
        min_value=float(min_size),
        max_value=float(max_size),
        value=(float(min_size), float(max_size)),
    )
with f3:
    score_threshold = st.slider(
        "Minimum risk score", min_value=0.0, max_value=float(max_score), value=0.0
    )

filtered = [
    r
    for r in rankings
    if (not pho_only or r["is_potentially_hazardous"])
    and size_range[0] <= r["diameter_km"] <= size_range[1]
    and r["risk_score"] >= score_threshold
]
st.caption(f"Showing {len(filtered):,} of {len(rankings):,} scorable asteroids")

# Clicking any column header sorts by that column (built into st.dataframe),
# so score/size/velocity are all sortable without extra controls.
table_rows = [
    {
        "Rank": r["rank"],
        "Name": r["name"],
        "Score": round(r["risk_score"], 3),
        "Size (km)": round(r["diameter_km"], 3),
        "Velocity (km/s)": round(r["velocity_kps"], 1),
    }
    for r in filtered
]
st.dataframe(table_rows, use_container_width=True, hide_index=True)

st.download_button(
    "Download CSV",
    data=pd.DataFrame(table_rows).to_csv(index=False),
    file_name="neo_risk_rankings.csv",
    mime="text/csv",
)

render_footer()
