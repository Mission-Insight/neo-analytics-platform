import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3]))

import streamlit as st  # noqa: E402

from src.dashboard.ui_settings import APP_TITLE  # noqa: E402
from src.dashboard.layout import (  # noqa: E402
    configure_page,
    render_footer,
    render_page_header,
    render_sidebar,
)

configure_page(f"Model Card — {APP_TITLE}")

_MODEL_CARD_PATH = Path(__file__).parents[3] / "docs" / "risk_model_card.md"

render_sidebar()
render_page_header("Model Card", "NEO Risk Scoring Model — methodology and limitations")

st.markdown(_MODEL_CARD_PATH.read_text(encoding="utf-8"))

render_footer()
