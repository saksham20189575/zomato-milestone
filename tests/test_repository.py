from pathlib import Path

import pandas as pd
import pytest

from app.data.repository import DataStoreError, RestaurantRepository, get_repository, reset_repository
from app.models.restaurant import BudgetBand, Restaurant


@pytest.fixture(autouse=True)
def clear_repository_cache():
    reset_repository()
    yield
    reset_repository()


@pytest.fixture
def sample_parquet(tmp_path: Path) -> Path:
    path = tmp_path / "restaurants.parquet"
    df = pd.DataFrame(
        [
            {
                "id": "abc123",
                "name": "Test Bistro",
                "location": "Bangalore, BTM",
                "cuisines": ["Italian", "Continental"],
                "rating": 4.5,
                "estimated_cost": 800.0,
                "budget_band": "medium",
                "metadata": {"city": "Bangalore", "locality": "BTM", "votes": 100},
            },
            {
                "id": "def456",
                "name": "Spice House",
                "location": "Bangalore, Koramangala",
                "cuisines": ["North Indian"],
                "rating": 4.0,
                "estimated_cost": 400.0,
                "budget_band": "low",
                "metadata": {"city": "Bangalore", "locality": "Indiranagar", "votes": 50},
            },
            {
                "id": "ghi789",
                "name": "Lake View",
                "location": "Bangalore, Bellandur",
                "cuisines": ["Chinese"],
                "rating": 4.2,
                "estimated_cost": 600.0,
                "budget_band": "medium",
                "metadata": {"listed_area": "Bellandur"},
            },
        ]
    )
    df.to_parquet(path, index=False)
    return path


class TestRestaurantRepository:
    def test_loads_restaurants(self, sample_parquet: Path):
        repo = RestaurantRepository(sample_parquet)
        assert repo.count == 3
        all_restaurants = repo.get_all()
        assert len(all_restaurants) == 3
        assert all(isinstance(r, Restaurant) for r in all_restaurants)
        assert all_restaurants[0].budget_band == BudgetBand.MEDIUM

    def test_get_by_ids_preserves_order(self, sample_parquet: Path):
        repo = RestaurantRepository(sample_parquet)
        result = repo.get_by_ids(["def456", "abc123", "unknown"])
        assert len(result) == 2
        assert result[0].id == "def456"
        assert result[1].id == "abc123"

    def test_get_by_ids_empty_list(self, sample_parquet: Path):
        repo = RestaurantRepository(sample_parquet)
        assert repo.get_by_ids([]) == []

    def test_get_by_id(self, sample_parquet: Path):
        repo = RestaurantRepository(sample_parquet)
        r = repo.get_by_id("abc123")
        assert r is not None
        assert r.name == "Test Bistro"
        assert repo.get_by_id("missing") is None

    def test_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(DataStoreError, match="Run ingestion first"):
            RestaurantRepository(tmp_path / "nonexistent.parquet")

    def test_empty_file_raises(self, tmp_path: Path):
        path = tmp_path / "empty.parquet"
        pd.DataFrame().to_parquet(path)
        with pytest.raises(DataStoreError, match="empty"):
            RestaurantRepository(path)

    def test_get_repository_singleton(self, sample_parquet: Path):
        repo1 = get_repository(sample_parquet)
        repo2 = get_repository()
        assert repo1 is repo2
        assert repo1.count == 3

    def test_get_distinct_localities_sorted(self, sample_parquet: Path):
        repo = RestaurantRepository(sample_parquet)
        assert repo.get_distinct_localities() == ["Bellandur", "BTM", "Indiranagar"]


@pytest.mark.integration
class TestRepositoryIntegration:
    def test_loads_processed_dataset(self):
        data_path = Path(__file__).resolve().parents[1] / "data/processed/restaurants.parquet"
        if not data_path.exists():
            pytest.skip("Processed data not found. Run: python scripts/ingest.py")

        repo = RestaurantRepository(data_path)
        assert repo.count > 1000
        sample = repo.get_all()[:1][0]
        assert sample.name
        assert sample.location
        assert len(sample.cuisines) >= 1
        assert 0 <= sample.rating <= 5
        assert sample.estimated_cost > 0
        assert sample.budget_band in BudgetBand
