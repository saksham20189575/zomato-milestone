"""Unit tests for presentation-layer render helpers."""

from unittest.mock import MagicMock

from app.models.recommendation import Recommendation, RecommendationResponse
from app.models.restaurant import BudgetBand, Restaurant
from app.presentation.metrics import match_percentage
from app.ui.render import (
    format_cost,
    format_cuisines,
    render_recommendation_card_html,
    render_results,
    truncate_location,
)


def _sample_restaurant() -> Restaurant:
    return Restaurant(
        id="r1",
        name="Test Bistro",
        location="Bangalore, BTM",
        cuisines=["Italian", "Pizza"],
        rating=4.5,
        estimated_cost=800.0,
        budget_band=BudgetBand.MEDIUM,
    )


def _sample_response(*, fallback: bool = False, with_summary: bool = True) -> RecommendationResponse:
    return RecommendationResponse(
        summary="Great Italian spots in Bangalore." if with_summary else None,
        recommendations=[
            Recommendation(
                restaurant=_sample_restaurant(),
                rank=1,
                explanation="Strong Italian menu and fits your budget.",
            )
        ],
        meta={
            "candidates_considered": 12,
            "candidates_sent_to_llm": 12,
            "fallback_used": fallback,
            "filter_latency_ms": 3.2,
            "llm_latency_ms": 450.0,
            "filters_applied": {"location": "bangalore"},
        },
    )


class TestFormatHelpers:
    def test_format_cost(self):
        assert format_cost(800.0) == "₹800 for two"
        assert format_cost(None) == "N/A"

    def test_format_cuisines_empty(self):
        assert format_cuisines([]) == "N/A"

    def test_format_cuisines_joined(self):
        assert format_cuisines(["Italian", "Pizza"]) == "Italian, Pizza"

    def test_match_percentage(self):
        assert match_percentage(1, 5) == 100
        assert match_percentage(2, 5) == 94
        assert match_percentage(5, 5) == 76

    def test_truncate_location(self):
        assert truncate_location("Short") == "Short"
        long_loc = "Bellandur, Bangalore Karnataka India"
        assert truncate_location(long_loc).endswith("...")


class TestRecommendationCardHtml:
    def test_card_contains_key_fields(self):
        rec = _sample_response().recommendations[0]
        html_out = render_recommendation_card_html(rec, total=5)
        assert "RANK #1" in html_out
        assert "100% MATCH" in html_out
        assert "Test Bistro" in html_out
        assert "WHY AI PICKED IT" in html_out
        assert "₹800 for two" in html_out


def _mock_streamlit() -> MagicMock:
    st = MagicMock()
    st.columns.return_value = (MagicMock(), MagicMock(), MagicMock())
    return st


class TestRenderResults:
    def test_empty_state_message(self):
        st = MagicMock()
        response = RecommendationResponse(recommendations=[], meta={})
        render_results(response, st)
        call_html = st.markdown.call_args_list[0][0][0]
        assert "No restaurants match" in call_html

    def test_fallback_warning(self):
        st = MagicMock()
        render_results(_sample_response(fallback=True), st)
        first_call = st.markdown.call_args_list[0][0][0]
        assert "AI ranking was unavailable" in first_call

    def test_summary_and_cards(self):
        st = _mock_streamlit()
        render_results(_sample_response(), st)
        assert any("tt-summary" in str(c) for c in st.markdown.call_args_list)
        assert st.columns.called
