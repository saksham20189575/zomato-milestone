import json
from pathlib import Path

from app.models.restaurant import BudgetBand, Restaurant
from app.services.merger import RecommendationMerger
from app.services.response_parser import ParsedLLMResponse, ParsedRecommendation, ResponseParser

FIXTURES = Path(__file__).parent / "fixtures"


def _restaurant(id: str, name: str, rating: float, votes: int = 0) -> Restaurant:
    return Restaurant(
        id=id,
        name=name,
        location="Bangalore, BTM",
        cuisines=["Italian"],
        rating=rating,
        estimated_cost=800.0,
        budget_band=BudgetBand.MEDIUM,
        metadata={"votes": votes},
    )


class TestRecommendationMerger:
    def test_merge_joins_restaurants(self):
        candidates = [
            _restaurant("abc123", "A", 4.5),
            _restaurant("def456", "B", 4.0),
        ]
        raw = (FIXTURES / "llm_response_valid.json").read_text()
        parsed = ResponseParser().parse(raw, {"abc123", "def456"}, top_k=5)
        assert parsed is not None

        summary, recs = RecommendationMerger().merge(parsed, candidates, top_k=5)
        assert summary is not None
        assert len(recs) == 2
        assert recs[0].restaurant.name == "A"
        assert recs[0].rank == 1
        assert "Italian" in recs[0].explanation or "Bangalore" in recs[0].explanation

    def test_fallback_merge_by_rating(self):
        candidates = [
            _restaurant("low", "Low", 3.5),
            _restaurant("high", "High", 4.9, votes=200),
            _restaurant("mid", "Mid", 4.2, votes=50),
        ]
        summary, recs = RecommendationMerger().fallback_merge(candidates, top_k=2)
        assert "unavailable" in summary.lower()
        assert len(recs) == 2
        assert recs[0].restaurant.name == "High"
        assert recs[1].restaurant.name == "Mid"

    def test_merge_fills_when_llm_returns_fewer(self):
        parsed = ParsedLLMResponse(
            summary="One pick",
            recommendations=[
                ParsedRecommendation(
                    restaurant_id="id1", rank=1, explanation="Best"
                ),
            ],
        )
        candidates = [
            _restaurant("id1", "One", 4.8),
            _restaurant("id2", "Two", 4.5),
        ]
        _, recs = RecommendationMerger().merge(parsed, candidates, top_k=2)
        assert len(recs) == 2
        assert {r.restaurant.id for r in recs} == {"id1", "id2"}
