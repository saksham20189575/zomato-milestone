"""FastAPI endpoint tests."""

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.data.repository import reset_repository
from app.models.restaurant import BudgetBand, Restaurant
from app.services.orchestrator import reset_orchestrator


@pytest.fixture(autouse=True)
def clear_caches():
    reset_repository()
    reset_orchestrator()
    yield
    reset_repository()
    reset_orchestrator()


@pytest.fixture
def api_client(tmp_path):
    restaurants = [
        Restaurant(
            id="abc123",
            name="Italian Bistro",
            location="Bangalore, Bellandur",
            cuisines=["Italian"],
            rating=4.5,
            estimated_cost=800.0,
            budget_band=BudgetBand.MEDIUM,
            metadata={"locality": "Bellandur"},
        ),
    ]
    path = tmp_path / "test.parquet"
    pd.DataFrame(
        [
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
    ).to_parquet(path, index=False)

    import os

    os.environ["DATA_PATH"] = str(path)

    from app.config import settings

    settings.data_path = path

    from api.main import app

    return TestClient(app)


def test_health(api_client):
    res = api_client.get("/api/v1/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert "llm_configured" in body


def test_root(api_client):
    res = api_client.get("/")
    assert res.status_code == 200
    assert res.json()["health"] == "/api/v1/health"


def test_locations(api_client):
    res = api_client.get("/api/v1/metadata/locations")
    assert res.status_code == 200
    assert "Bellandur" in res.json()["locations"]


def test_recommendations_validation(api_client):
    res = api_client.post(
        "/api/v1/recommendations",
        json={
            "location": "",
            "budget": "medium",
            "cuisine": "Italian",
            "min_rating": 4.0,
            "top_k": 5,
        },
    )
    assert res.status_code == 422
