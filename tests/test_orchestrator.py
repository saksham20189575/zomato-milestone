import json
from pathlib import Path

import pandas as pd
import pytest

from app.data.repository import RestaurantRepository
from app.models.preferences import UserPreferences
from app.models.restaurant import BudgetBand, Restaurant
from app.services.llm_client import MockLLMClient
from app.services.orchestrator import RecommendRestaurantsUseCase, reset_orchestrator
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


@pytest.fixture(autouse=True)
def clear_orchestrator():
    reset_orchestrator()
    yield
    reset_orchestrator()


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
            cuisines=["Italian"],
            rating=4.2,
            estimated_cost=900.0,
            budget_band=BudgetBand.MEDIUM,
            metadata={"votes": 80},
        ),
    ]


class TestRecommendRestaurantsUseCase:
    def test_execute_single_entry_point(self, tmp_path, sample_restaurants):
        repo = _make_repo(tmp_path, sample_restaurants)
        mock_response = (FIXTURES / "llm_response_valid.json").read_text()
        engine = RecommendationEngine(llm_client=MockLLMClient(mock_response))
        use_case = RecommendRestaurantsUseCase(repository=repo, engine=engine)

        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetBand.MEDIUM,
            cuisine="Italian",
            min_rating=4.0,
            top_k=2,
        )
        response = use_case.execute(prefs)

        assert len(response.recommendations) == 2
        assert response.meta["candidates_considered"] == 2
        assert response.meta["candidates_sent_to_llm"] == 2
        assert response.meta["llm_used"] is True
        assert response.meta["parse_success"] is True
        assert response.meta["fallback_used"] is False
        assert "filters_applied" in response.meta
        assert response.meta["llm_latency_ms"] >= 0

    def test_empty_candidates_skips_llm(self, tmp_path, sample_restaurants):
        repo = _make_repo(tmp_path, sample_restaurants)
        engine = RecommendationEngine(llm_client=MockLLMClient("should not be called"))
        use_case = RecommendRestaurantsUseCase(repository=repo, engine=engine)

        prefs = UserPreferences(
            location="Mumbai",
            budget=BudgetBand.MEDIUM,
            cuisine="Italian",
            min_rating=4.0,
        )
        response = use_case.execute(prefs)

        assert response.recommendations == []
        assert response.meta["candidates_considered"] == 0
        assert response.meta["llm_used"] is False
        assert response.meta["parse_success"] is None

    def test_fallback_on_parse_failure(self, tmp_path, sample_restaurants):
        repo = _make_repo(tmp_path, sample_restaurants)
        invalid = (FIXTURES / "llm_response_invalid.json").read_text()
        engine = RecommendationEngine(llm_client=MockLLMClient(invalid))
        use_case = RecommendRestaurantsUseCase(repository=repo, engine=engine)

        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetBand.MEDIUM,
            cuisine="Italian",
            min_rating=4.0,
            top_k=2,
        )
        response = use_case.execute(prefs)

        assert len(response.recommendations) == 2
        assert response.meta["fallback_used"] is True
        assert response.meta["parse_success"] is False

    def test_all_recommendations_from_candidate_set(self, tmp_path, sample_restaurants):
        repo = _make_repo(tmp_path, sample_restaurants)
        mock_response = (FIXTURES / "llm_response_valid.json").read_text()
        use_case = RecommendRestaurantsUseCase(
            repository=repo,
            engine=RecommendationEngine(llm_client=MockLLMClient(mock_response)),
        )
        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetBand.MEDIUM,
            cuisine="Italian",
            min_rating=4.0,
            top_k=2,
        )
        response = use_case.execute(prefs)
        allowed = {"abc123", "def456"}
        assert all(r.restaurant.id in allowed for r in response.recommendations)


@pytest.mark.integration
class TestOrchestratorLive:
    def test_execute_with_live_groq(self):
        from app.config import settings

        if not settings.resolved_llm_api_key:
            pytest.skip("LLM_API_KEY or GROQ_API_KEY not set")

        data_path = Path(__file__).resolve().parents[1] / "data/processed/restaurants.parquet"
        if not data_path.exists():
            pytest.skip("Processed data not found. Run: python scripts/ingest.py")

        use_case = RecommendRestaurantsUseCase(repository=RestaurantRepository(data_path))
        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetBand.MEDIUM,
            cuisine="Italian",
            min_rating=4.0,
            top_k=2,
        )
        response = use_case.execute(prefs)

        assert response.meta["llm_used"] is True
        assert len(response.recommendations) <= 2
        assert response.meta["candidates_considered"] > 0
