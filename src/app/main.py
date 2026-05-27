"""
Streamlit entry point — TasteTrail AI restaurant recommendations.

Run from project root:
    PYTHONPATH=src streamlit run src/app/main.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

_SRC_ROOT = Path(__file__).resolve().parents[1]
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

import streamlit as st
from pydantic import ValidationError

from app.config import settings
from app.data.repository import DataStoreError
from app.models.preferences import UserPreferences
from app.models.restaurant import BudgetBand
from app.services.orchestrator import get_orchestrator
from app.data.form_options import get_location_options
from app.ui.render import render_loading_html, render_results
from app.ui.theme import inject_theme, render_hero, render_nav

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# UI labels → backend BudgetBand
BUDGET_UI_OPTIONS = ["Budget", "Medium", "Premium"]
BUDGET_UI_TO_BAND = {
    "Budget": BudgetBand.LOW,
    "Medium": BudgetBand.MEDIUM,
    "Premium": BudgetBand.HIGH,
}


@st.cache_resource(show_spinner=False)
def _load_use_case():
    return get_orchestrator()


@st.cache_data(show_spinner=False)
def _get_location_options(_data_path: str) -> list[str]:
    return get_location_options(data_path=Path(_data_path))


def _default_location_index(options: list[str], preferred: str = "Bellandur") -> int:
    if not options:
        return 0
    preferred_key = preferred.casefold()
    for index, option in enumerate(options):
        if option.casefold() == preferred_key:
            return index
    return 0


def _render_data_missing_banner() -> None:
    st.error(
        "Restaurant data is not available.\n\n"
        "**Local:** run `python scripts/ingest.py` to create "
        "`data/processed/restaurants.parquet`.\n\n"
        "**Streamlit Cloud:** commit that file to the repo (see "
        "`docs/deployment-plan.md`).",
        icon="⚠️",
    )


def _render_missing_api_key_banner() -> None:
    st.warning(
        "Groq API key is not configured. Recommendations will fail until you set "
        "`LLM_API_KEY` or `GROQ_API_KEY` in `.env` (local) or Streamlit **Secrets** (Cloud).",
        icon="🔑",
    )


def _build_preferences_from_form(
    location: str,
    budget_ui: str,
    cuisine: str,
    min_rating: float,
    additional: str,
    top_k: int,
) -> UserPreferences:
    additional_trimmed = additional.strip() if additional else None
    if additional_trimmed and len(additional_trimmed) > settings.additional_preferences_max_length:
        additional_trimmed = additional_trimmed[: settings.additional_preferences_max_length]

    cuisine_value = cuisine.strip()
    if not cuisine_value or cuisine_value.lower() in ("all cuisines", "all"):
        cuisine_value = "Indian"

    return UserPreferences(
        location=location,
        budget=BUDGET_UI_TO_BAND[budget_ui],
        cuisine=cuisine_value,
        min_rating=min_rating,
        additional_preferences=additional_trimmed,
        top_k=int(top_k),
    )


def _show_validation_errors(exc: ValidationError) -> None:
    for err in exc.errors():
        field = ".".join(str(part) for part in err.get("loc", ()))
        message = err.get("msg", "Invalid value")
        st.error(f"**{field or 'input'}**: {message}")


def main() -> None:
    st.set_page_config(
        page_title="TasteTrail AI",
        page_icon="🍴",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    inject_theme()
    render_nav()
    render_hero()

    if not settings.has_llm_api_key:
        _render_missing_api_key_banner()

    try:
        use_case = _load_use_case()
    except DataStoreError:
        _render_data_missing_banner()
        st.stop()

    location_options = _get_location_options(str(settings.data_path.resolve()))
    if not location_options:
        st.error("No locality metadata found in restaurant data. Re-run ingestion.")
        st.stop()

    st.markdown('<div class="tt-form-shell">', unsafe_allow_html=True)

    with st.form("preferences_form"):
        col_left, col_right = st.columns(2)

        with col_left:
            location = st.selectbox(
                "AREA",
                options=location_options,
                index=_default_location_index(location_options),
                label_visibility="visible",
            )
            budget_ui = st.radio(
                "BUDGET RANGE",
                options=BUDGET_UI_OPTIONS,
                index=1,
                horizontal=True,
                label_visibility="visible",
            )
            cuisine = st.text_input(
                "PREFERRED CUISINES",
                value="",
                placeholder="Search or select cuisines… (e.g. Italian, North Indian)",
                label_visibility="visible",
            )

        with col_right:
            rating_col, value_col = st.columns([4, 1])
            with rating_col:
                min_rating = st.slider(
                    "MINIMUM RATING",
                    min_value=0.0,
                    max_value=5.0,
                    value=4.0,
                    step=0.1,
                    label_visibility="visible",
                )
            with value_col:
                st.markdown(
                    f'<div class="tt-rating-value" style="padding-top:1.6rem">{min_rating:.1f} ★</div>',
                    unsafe_allow_html=True,
                )
            top_k = st.number_input(
                "NUMBER OF RESULTS",
                min_value=1,
                max_value=20,
                value=5,
                step=1,
                label_visibility="visible",
            )
            additional = st.text_area(
                "ADDITIONAL PREFERENCES",
                placeholder="Describe your perfect dining experience…",
                height=100,
                label_visibility="visible",
            )

        submitted = st.form_submit_button("✦  Get AI Recommendations", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if not submitted:
        return

    if not settings.has_llm_api_key:
        st.error(
            "Cannot fetch recommendations without a Groq API key. "
            "Add `LLM_API_KEY` to Streamlit Secrets or `.env`, then reload the app.",
            icon="🔑",
        )
        return

    try:
        preferences = _build_preferences_from_form(
            location=location,
            budget_ui=budget_ui,
            cuisine=cuisine,
            min_rating=min_rating,
            additional=additional,
            top_k=top_k,
        )
    except (ValidationError, KeyError) as exc:
        if isinstance(exc, ValidationError):
            _show_validation_errors(exc)
        else:
            st.error("Invalid form input.")
        return

    placeholder = st.empty()
    with placeholder.container():
        st.markdown(render_loading_html(), unsafe_allow_html=True)

    try:
        response = use_case.execute(preferences)
    except Exception:
        placeholder.empty()
        st.error(
            "Something went wrong while fetching recommendations. "
            "Check your Groq API key (Streamlit Secrets or `.env`) and app logs, then try again.",
            icon="❌",
        )
        return

    placeholder.empty()
    render_results(response, st)


if __name__ == "__main__":
    main()
