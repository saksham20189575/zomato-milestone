import pytest

from app.data.repository import RestaurantRepository
from app.models.preferences import UserPreferences
from app.models.restaurant import BudgetBand, Restaurant
from app.services.filter_service import FilterService


def _restaurant(
    id: str,
    name: str,
    location: str,
    cuisines: list[str],
    rating: float,
    budget_band: BudgetBand,
    votes: int = 0,
) -> Restaurant:
    return Restaurant(
        id=id,
        name=name,
        location=location,
        cuisines=cuisines,
        rating=rating,
        estimated_cost=800.0,
        budget_band=budget_band,
        metadata={"votes": votes},
    )


@pytest.fixture
def sample_restaurants() -> list[Restaurant]:
    return [
        _restaurant(
            "1", "Italian Place", "Bangalore, BTM", ["Italian", "Continental"], 4.5, BudgetBand.MEDIUM, 100
        ),
        _restaurant(
            "2", "Budget Chinese", "Bangalore, BTM", ["Chinese"], 4.0, BudgetBand.LOW, 50
        ),
        _restaurant(
            "3", "High End Italian", "Bangalore, Koramangala", ["Italian"], 4.8, BudgetBand.HIGH, 200
        ),
        _restaurant(
            "4", "Delhi Diner", "Delhi, Connaught Place", ["Italian"], 4.2, BudgetBand.MEDIUM, 80
        ),
        _restaurant(
            "5", "Low Rated Italian", "Bangalore, HSR", ["Italian"], 3.0, BudgetBand.MEDIUM, 30
        ),
        _restaurant(
            "6", "Medium Non-Italian", "Bangalore, BTM", ["North Indian"], 4.6, BudgetBand.MEDIUM, 90
        ),
    ]


@pytest.fixture
def mock_repository(sample_restaurants, monkeypatch, tmp_path):
    """Repository backed by a minimal in-memory parquet file."""
    import pandas as pd

    from app.data import repository as repo_module

    records = []
    for r in sample_restaurants:
        records.append(
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
        )
    path = tmp_path / "test.parquet"
    pd.DataFrame(records).to_parquet(path, index=False)
    repo_module.reset_repository()
    return RestaurantRepository(path)


@pytest.fixture
def filter_service():
    return FilterService()


class TestFilterService:
    def test_location_filter(self, filter_service, mock_repository):
        prefs = UserPreferences(
            location="Delhi",
            budget=BudgetBand.MEDIUM,
            cuisine="Italian",
            min_rating=0,
        )
        result = filter_service.filter(prefs, mock_repository)
        assert all("Delhi" in r.location for r in result.candidates)
        assert len(result.candidates) == 1
        assert result.candidates[0].name == "Delhi Diner"

    def test_budget_filter(self, filter_service, mock_repository):
        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetBand.LOW,
            cuisine="Chinese",
            min_rating=0,
        )
        result = filter_service.filter(prefs, mock_repository)
        assert len(result.candidates) == 1
        assert result.candidates[0].budget_band == BudgetBand.LOW

    def test_cuisine_filter_case_insensitive(self, filter_service, mock_repository):
        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetBand.MEDIUM,
            cuisine="italian",
            min_rating=0,
        )
        result = filter_service.filter(prefs, mock_repository)
        names = {r.name for r in result.candidates}
        assert "Italian Place" in names
        assert "Medium Non-Italian" not in names

    def test_min_rating_filter(self, filter_service, mock_repository):
        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetBand.MEDIUM,
            cuisine="Italian",
            min_rating=4.0,
        )
        result = filter_service.filter(prefs, mock_repository)
        assert all(r.rating >= 4.0 for r in result.candidates)
        assert not any(r.name == "Low Rated Italian" for r in result.candidates)

    def test_combined_filters(self, filter_service, mock_repository):
        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetBand.MEDIUM,
            cuisine="Italian",
            min_rating=4.0,
        )
        result = filter_service.filter(prefs, mock_repository)
        assert len(result.candidates) == 1
        assert result.candidates[0].name == "Italian Place"

    def test_empty_result_no_error(self, filter_service, mock_repository):
        prefs = UserPreferences(
            location="Mumbai",
            budget=BudgetBand.MEDIUM,
            cuisine="Italian",
            min_rating=4.0,
        )
        result = filter_service.filter(prefs, mock_repository)
        assert result.candidates == []
        assert result.total_before_cap == 0

    def test_sort_by_rating_then_votes(self, filter_service, mock_repository):
        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetBand.MEDIUM,
            cuisine="Italian",
            min_rating=0,
        )
        result = filter_service.filter(prefs, mock_repository)
        assert len(result.candidates) == 2
        assert result.candidates[0].name == "Italian Place"  # 4.5, 100 votes
        assert result.candidates[1].name == "Low Rated Italian"

    def test_cap_enforced(self, filter_service, mock_repository, monkeypatch):
        monkeypatch.setattr("app.services.filter_service.settings.max_candidates", 1)
        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetBand.MEDIUM,
            cuisine="Italian",
            min_rating=0,
        )
        result = filter_service.filter(prefs, mock_repository)
        assert result.total_before_cap == 2
        assert len(result.candidates) == 1

    def test_applied_filters_metadata(self, filter_service, mock_repository):
        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetBand.MEDIUM,
            cuisine="Italian",
            min_rating=4.0,
            additional_preferences="family-friendly",
        )
        result = filter_service.filter(prefs, mock_repository)
        assert result.applied_filters["location"] == "Bangalore"
        assert result.applied_filters["budget"] == "medium"
        assert result.applied_filters["cuisine"] == "Italian"
        assert result.applied_filters["min_rating"] == 4.0
        assert "additional_preferences" not in result.applied_filters


@pytest.mark.integration
class TestFilterServiceIntegration:
    def test_bangalore_medium_italian(self):
        from pathlib import Path

        from app.data.repository import RestaurantRepository

        data_path = Path(__file__).resolve().parents[1] / "data/processed/restaurants.parquet"
        if not data_path.exists():
            pytest.skip("Processed data not found. Run: python scripts/ingest.py")

        repo = RestaurantRepository(data_path)
        service = FilterService()
        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetBand.MEDIUM,
            cuisine="Italian",
            min_rating=4.0,
        )
        result = service.filter(prefs, repo)
        assert result.total_before_cap > 0
        assert len(result.candidates) > 0
        assert len(result.candidates) <= 30
        for r in result.candidates:
            assert "bangalore" in r.location.lower()
            assert r.budget_band == BudgetBand.MEDIUM
            assert r.rating >= 4.0
            assert any("italian" in c.lower() for c in r.cuisines)

    def test_impossible_combo_returns_empty(self):
        from pathlib import Path

        from app.data.repository import RestaurantRepository

        data_path = Path(__file__).resolve().parents[1] / "data/processed/restaurants.parquet"
        if not data_path.exists():
            pytest.skip("Processed data not found. Run: python scripts/ingest.py")

        repo = RestaurantRepository(data_path)
        service = FilterService()
        prefs = UserPreferences(
            location="Mumbai",
            budget=BudgetBand.HIGH,
            cuisine="Italian",
            min_rating=4.9,
        )
        result = service.filter(prefs, repo)
        assert result.candidates == []
        assert result.total_before_cap == 0
