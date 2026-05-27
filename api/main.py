"""
FastAPI backend for TasteTrail AI.

Run from project root:
    PYTHONPATH=src uvicorn api.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

# Resolve `app` package from src/
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from api.schemas import (
    LocationsResponse,
    RecommendationOut,
    RecommendationRequest,
    RecommendationResponseOut,
    RestaurantOut,
)
from app.data.repository import DataStoreError, get_repository
from app.models.preferences import UserPreferences
from app.models.recommendation import RecommendationResponse
from app.models.restaurant import BudgetBand
from app.services.orchestrator import get_orchestrator
from app.ui.form_options import get_location_options
from app.ui.render import match_percentage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BUDGET_API_TO_BAND = {
    "low": BudgetBand.LOW,
    "medium": BudgetBand.MEDIUM,
    "high": BudgetBand.HIGH,
}

@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        get_orchestrator()
        logger.info("Orchestrator and repository ready")
    except DataStoreError as e:
        logger.warning("Startup: data not loaded — %s", e)
    yield


app = FastAPI(
    title="TasteTrail AI API",
    version="1.0.0",
    description="Restaurant recommendations powered by Zomato data and Groq LLM",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    try:
        repo = get_repository()
        return {"status": "ok", "restaurants_loaded": str(repo.count)}
    except DataStoreError:
        return {"status": "degraded", "restaurants_loaded": "0"}


@app.get("/api/v1/metadata/locations", response_model=LocationsResponse)
def list_locations() -> LocationsResponse:
    try:
        locations = get_location_options()
    except DataStoreError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    if not locations:
        raise HTTPException(status_code=503, detail="No locality metadata in dataset")
    return LocationsResponse(locations=locations)


def _to_api_response(response: RecommendationResponse) -> RecommendationResponseOut:
    total = len(response.recommendations)
    items: list[RecommendationOut] = []
    for rec in response.recommendations:
        r = rec.restaurant
        items.append(
            RecommendationOut(
                rank=rec.rank,
                restaurant=RestaurantOut(
                    id=r.id,
                    name=r.name,
                    location=r.location,
                    cuisines=r.cuisines,
                    rating=r.rating,
                    estimated_cost=r.estimated_cost,
                    budget_band=r.budget_band.value,
                ),
                explanation=rec.explanation,
                match_percent=match_percentage(rec.rank, total),
            )
        )
    return RecommendationResponseOut(
        summary=response.summary,
        recommendations=items,
        meta=response.meta,
    )


@app.post("/api/v1/recommendations", response_model=RecommendationResponseOut)
def create_recommendations(body: RecommendationRequest) -> RecommendationResponseOut:
    try:
        prefs = UserPreferences(
            location=body.location.strip(),
            budget=BUDGET_API_TO_BAND[body.budget],
            cuisine=body.cuisine.strip(),
            min_rating=body.min_rating,
            additional_preferences=body.additional_preferences,
            top_k=body.top_k,
        )
    except (ValidationError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    try:
        use_case = get_orchestrator()
        result = use_case.execute(prefs)
    except DataStoreError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        logger.exception("Recommendation failed")
        raise HTTPException(status_code=502, detail="Recommendation service failed") from e

    return _to_api_response(result)
