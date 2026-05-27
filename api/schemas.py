"""API request/response schemas (HTTP layer)."""

from typing import Any, Literal

from pydantic import BaseModel, Field


BudgetApi = Literal["low", "medium", "high"]


class RecommendationRequest(BaseModel):
    location: str = Field(..., min_length=1)
    budget: BudgetApi
    cuisine: str = Field(..., min_length=1)
    min_rating: float = Field(..., ge=0.0, le=5.0)
    additional_preferences: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class RestaurantOut(BaseModel):
    id: str
    name: str
    location: str
    cuisines: list[str]
    rating: float
    estimated_cost: float
    budget_band: str


class RecommendationOut(BaseModel):
    rank: int
    restaurant: RestaurantOut
    explanation: str
    match_percent: int


class RecommendationResponseOut(BaseModel):
    summary: str | None = None
    recommendations: list[RecommendationOut] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class LocationsResponse(BaseModel):
    locations: list[str]
