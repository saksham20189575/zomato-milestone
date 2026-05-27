"""Presentation helpers for TasteTrail AI recommendation results."""

from __future__ import annotations

import html
from typing import TYPE_CHECKING, Any

from app.models.recommendation import Recommendation, RecommendationResponse
from app.models.restaurant import BudgetBand
from app.presentation.metrics import match_percentage

if TYPE_CHECKING:
    import streamlit as st

BUDGET_DISPLAY = {
    BudgetBand.LOW: "Budget",
    BudgetBand.MEDIUM: "Medium",
    BudgetBand.HIGH: "Premium",
}


def format_cost(estimated_cost: float | None) -> str:
    if estimated_cost is None:
        return "N/A"
    return f"₹{estimated_cost:,.0f} for two"


def format_cuisines(cuisines: list[str]) -> str:
    if not cuisines:
        return "N/A"
    return ", ".join(cuisines)


def truncate_location(location: str, max_len: int = 22) -> str:
    if len(location) <= max_len:
        return location
    return location[: max_len - 3].rstrip() + "..."


def render_recommendation_card_html(rec: Recommendation, *, total: int) -> str:
    restaurant = rec.restaurant
    name = html.escape(restaurant.name)
    location = html.escape(truncate_location(restaurant.location))
    explanation = html.escape(rec.explanation)
    rating = f"{restaurant.rating:.1f}"
    cost = html.escape(format_cost(restaurant.estimated_cost))
    budget = BUDGET_DISPLAY.get(restaurant.budget_band, restaurant.budget_band.value.title())
    pct = match_percentage(rec.rank, total)

    tags_html = "".join(
        f'<span class="tt-tag">{html.escape(c)}</span>' for c in restaurant.cuisines[:6]
    )
    if len(restaurant.cuisines) > 6:
        tags_html += f'<span class="tt-tag">+{len(restaurant.cuisines) - 6}</span>'

    return f"""
    <div class="tt-card">
        <div class="tt-card-top">
            <span class="tt-rank">RANK #{rec.rank}</span>
            <span class="tt-match">{pct}% MATCH</span>
        </div>
        <div class="tt-card-title-row">
            <h3 class="tt-card-title">{name}</h3>
            <span class="tt-heart">♡</span>
        </div>
        <div class="tt-meta-row">
            <span>★ {rating}</span>
            <span>🍴 {html.escape(budget)}</span>
        </div>
        <div class="tt-meta-row">
            <span>📍 {location}</span>
            <span class="tt-cost">{cost}</span>
        </div>
        <div class="tt-tags">{tags_html}</div>
        <div class="tt-ai-box">
            <div class="tt-ai-label">✦ WHY AI PICKED IT</div>
            <p class="tt-ai-text">"{explanation}"</p>
        </div>
    </div>
    """


def render_results(response: RecommendationResponse, streamlit_module: Any) -> None:
    """Render summary, grid of cards, empty/fallback states."""
    st = streamlit_module
    meta = response.meta
    total = len(response.recommendations)

    if meta.get("fallback_used"):
        st.markdown(
            '<div class="tt-alert-fallback">'
            "AI ranking was unavailable — showing top-rated matches from your filters."
            "</div>",
            unsafe_allow_html=True,
        )

    if response.summary:
        st.markdown(
            f'<div class="tt-summary">{html.escape(response.summary)}</div>',
            unsafe_allow_html=True,
        )

    if not response.recommendations:
        st.markdown(
            """
            <div class="tt-empty">
                <h3>No restaurants match</h3>
                <p>Try relaxing your area, cuisine, minimum rating, or budget.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown('<div class="tt-results-header">Your recommendations</div>', unsafe_allow_html=True)

    cols_per_row = 3
    for row_start in range(0, total, cols_per_row):
        row_items = response.recommendations[row_start : row_start + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, rec in zip(cols, row_items, strict=False):
            with col:
                st.markdown(
                    render_recommendation_card_html(rec, total=total),
                    unsafe_allow_html=True,
                )
        # Pad empty columns in last row
        for col in cols[len(row_items) :]:
            with col:
                st.empty()

    with st.expander("Search details"):
        st.write(
            f"**Candidates considered:** {meta.get('candidates_considered', '—')}  \n"
            f"**Sent to AI:** {meta.get('candidates_sent_to_llm', meta.get('candidates_considered', '—'))}  \n"
            f"**Filter time:** {meta.get('filter_latency_ms', '—')} ms  \n"
            f"**AI time:** {meta.get('llm_latency_ms', '—')} ms"
        )
        filters = meta.get("filters_applied")
        if filters:
            st.json(filters)


def render_loading_html() -> str:
    return """
    <div class="tt-loading">
        <div class="tt-loading-spinner"></div>
        <p>Finding and ranking restaurants…</p>
    </div>
    """
