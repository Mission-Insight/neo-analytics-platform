from typing import TypeVar

import streamlit as st

from src.dashboard.data_service import get_weights
from src.dashboard.ui_settings import (
    APP_ICON,
    APP_LAYOUT,
    APP_SIDEBAR_STATE,
    APP_TITLE,
    DATA_SOURCE,
    DATASET_END,
    DATASET_START,
)


_T = TypeVar("_T")


def configure_page(page_title: str) -> None:
    """Shared st.set_page_config call for every dashboard page."""
    st.set_page_config(
        page_title=page_title,
        page_icon=APP_ICON,
        layout=APP_LAYOUT,
        initial_sidebar_state=APP_SIDEBAR_STATE,
    )


def chart_color(palette: dict[str, _T]) -> _T:
    """Pick a value (a hex color, or a nested set of them) from a {'light': ..., 'dark': ...} pair."""
    try:
        theme_type = st.context.theme.type
    except Exception:
        theme_type = "light"
    if theme_type in palette:
        return palette[theme_type]
    return palette["light"]


def render_page_header(title: str, subtitle: str = "") -> None:
    st.title(title)
    if subtitle:
        st.caption(subtitle)
    st.divider()


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(f"## {APP_ICON} {APP_TITLE}")
        st.caption("Near-Earth Object Risk Scoring Platform")
        st.divider()

        st.markdown("**Dataset**")
        st.caption(f"Window: {DATASET_START} → {DATASET_END}")
        st.caption(f"Source: {DATA_SOURCE}")
        st.divider()

        weights = get_weights()
        st.markdown("**Model weights**")
        st.caption(f"Size · {weights['size']:.2f}")
        st.caption(f"Proximity · {weights['proximity']:.2f}")
        st.caption(f"Velocity · {weights['velocity']:.2f}")
        st.caption(f"Frequency · {weights['frequency']:.2f}")
        st.divider()

        st.caption(
            "Risk scores are **not** impact probability estimates. "
            "See the **Model Card** page for full limitations."
        )


def render_footer() -> None:
    st.divider()
    st.caption(
        "⚠️ Risk scores reflect a weighted composite of observable physical and orbital "
        "characteristics within the 2024–2026 dataset window. They are not predictions "
        "of collision probability. Absence from this list does not imply safety."
    )
