import json
from pathlib import Path

import pandas as pd
import pytest

from app.data.repository import RestaurantRepository
from app.models.preferences import UserPreferences
from app.models.restaurant import BudgetBand, Restaurant
from app.services.filter_service import FilterService
from app.services.llm_client import LLMConfigError, MockLLMClient
from app.services.recommendation_engine import RecommendationEngine

FIXTURES = Path(__file__).parent / "fixtures"


def _make_repo(tmp_path, restaurants: list[Restaurant]) -> RestaurantRepository:
    records = [
        {
            "id": r.id,
            "name": r.name,
            "location": r.location,
            "cuisines": r.cuisines,
            "rating": r.rating,
            "estimated_cost": r.estimated_cost,
            "budget_band": r.budget_band.value,
            "metadata": r.metadata,
        }
        for r in restaurants
    ]
    path = tmp_path / "test.parquet"
    pd.DataFrame(records).to_parquet(path, index=False)
    return RestaurantRepository(path)


@pytest.fixture
def sample_restaurants() -> list[Restaurant]:
    return [
        Restaurant(
            id="abc123",
            name="Italian Bistro",
            location="Bangalore, BTM",
            cuisines=["Italian"],
            rating=4.5,
            estimated_cost=800.0,
            budget_band=BudgetBand.MEDIUM,
            metadata={"votes": 100},
        ),
        Restaurant(
            id="def456",
            name="Pasta House",
            location="Bangalore, BTM",
            cuisines=["Italian", "Continental"],
            rating=4.2,
            estimated_cost=900.0,
            budget_band=BudgetBand.MEDIUM,
            metadata={"votes": 80},
        ),
        Restaurant(
            id="ghi789",
            name="Chinese Wok",
            location="Bangalore, BTM",
            cuisines=["Chinese"],
            rating=4.6,
            estimated_cost=600.0,
            budget_band=BudgetBand.MEDIUM,
            metadata={"votes": 120},
        ),
    ]


class TestRecommendationEngineMocked:
    def test_end_to_end_with_mock_groq(self, tmp_path, sample_restaurants):
        repo = _make_repo(tmp_path, sample_restaurants)
        mock_response = (FIXTURES / "llm_response_valid.json").read_text()
        engine = RecommendationEngine(llm_client=MockLLMClient(mock_response))

        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetBand.MEDIUM,
            cuisine="Italian",
            min_rating=4.0,
            top_k=2,
        )
        filter_result = FilterService().filter(prefs, repo)
        assert len(filter_result.candidates) == 2

        response = engine.generate(prefs, filter_result)
        assert len(response.recommendations) == 2
        assert response.recommendations[0].restaurant.id == "abc123"
        assert response.meta["fallback_used"] is False
        assert all(
            r.restaurant.id in {"abc123", "def456"} for r in response.recommendations
        )

    def test_fallback_on_invalid_llm_response(self, tmp_path, sample_restaurants):
        repo = _make_repo(tmp_path, sample_restaurants)
        invalid = (FIXTURES / "llm_response_invalid.json").read_text()
        engine = RecommendationEngine(llm_client=MockLLMClient(invalid))

        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetBand.MEDIUM,
            cuisine="Italian",
            min_rating=4.0,
            top_k=2,
        )
        filter_result = FilterService().filter(prefs, repo)
        response = engine.generate(prefs, filter_result)

        assert len(response.recommendations) == 2
        assert response.meta["fallback_used"] is True
        assert all(r.restaurant.id in {"abc123", "def456"} for r in response.recommendations)

    def test_empty_filter_skips_llm(self, tmp_path, sample_restaurants):
        repo = _make_repo(tmp_path, sample_restaurants)
        engine = RecommendationEngine(llm_client=MockLLMClient('{"should": "not be called"}'))

        prefs = UserPreferences(
            location="Mumbai",
            budget=BudgetBand.MEDIUM,
            cuisine="Italian",
            min_rating=4.0,
        )
        filter_result = FilterService().filter(prefs, repo)
        response = engine.generate(prefs, filter_result)

        assert response.recommendations == []
        assert response.meta["llm_used"] is False


class TestGroqClient:
    def test_missing_api_key_raises(self):
        from app.services.llm_client import GroqClient

        with pytest.raises(LLMConfigError, match="API key"):
            GroqClient(api_key="")


@pytest.mark.integration
class TestGroqLive:
    def test_live_groq_completion(self):
        from app.config import settings
        from app.services.llm_client import GroqClient

        if not settings.resolved_llm_api_key:
            pytest.skip("LLM_API_KEY or GROQ_API_KEY not set")

        client = GroqClient()
        messages = [
            {"role": "system", "content": "Respond with JSON only."},
            {
                "role": "user",
                "content": '{"summary": "test", "recommendations": []}',
            },
        ]
        raw = client.complete(messages)
        assert raw and len(raw) > 0
        data = json.loads(raw)
        assert isinstance(data, dict)
        assert len(data) > 0
