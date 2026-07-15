from typing import TypeVar

import streamlit as st

from src.dashboard.config import (
    APP_ICON,
    APP_TITLE,
    DATA_SOURCE,
    DATASET_END,
    DATASET_START,
    WEIGHT_DIAMETER,
    WEIGHT_ENCOUNTER_FREQUENCY,
    WEIGHT_MISS_DISTANCE,
    WEIGHT_VELOCITY,
)


_T = TypeVar("_T")


def chart_color(palette: dict[str, _T]) -> _T:
    """Pick a value (a hex color, or a nested set of them) from a {'light': ..., 'dark': ...} pair."""
    try:
        theme_type = st.context.theme.type
    except Exception:
        theme_type = "light"
    return palette.get(theme_type, palette["light"])


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

        st.markdown("**Model weights**")
        st.caption(f"Size · {WEIGHT_DIAMETER:.2f}")
        st.caption(f"Proximity · {WEIGHT_MISS_DISTANCE:.2f}")
        st.caption(f"Velocity · {WEIGHT_VELOCITY:.2f}")
        st.caption(f"Frequency · {WEIGHT_ENCOUNTER_FREQUENCY:.2f}")
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
