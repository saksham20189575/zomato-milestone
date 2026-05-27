from typing import Any

from pydantic import BaseModel, Field

from app.models.restaurant import Restaurant


class Recommendation(BaseModel):
    """A single ranked restaurant recommendation with LLM explanation."""

    restaurant: Restaurant
    rank: int = Field(..., ge=1)
    explanation: str


class RecommendationResponse(BaseModel):
    """Full recommendation response returned by the orchestrator."""

    summary: str | None = None
    recommendations: list[Recommendation] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)
