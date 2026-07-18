import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))

import streamlit as st  # noqa: E402

from src.dashboard.config import APP_ICON, APP_LAYOUT, APP_SIDEBAR_STATE, APP_TITLE  # noqa: E402
from src.dashboard.layout import render_footer, render_page_header, render_sidebar  # noqa: E402

st.set_page_config(
    page_title=f"Model Card — {APP_TITLE}",
    page_icon=APP_ICON,
    layout=APP_LAYOUT,
    initial_sidebar_state=APP_SIDEBAR_STATE,
)

_MODEL_CARD_PATH = Path(__file__).parents[3] / "docs" / "risk_model_card.md"

render_sidebar()
render_page_header("Model Card", "NEO Risk Scoring Model — methodology and limitations")

st.markdown(_MODEL_CARD_PATH.read_text(encoding="utf-8"))

render_footer()
