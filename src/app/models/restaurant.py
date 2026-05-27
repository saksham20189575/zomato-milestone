from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class BudgetBand(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Restaurant(BaseModel):
    """Canonical restaurant record after ingestion."""

    id: str
    name: str
    location: str
    cuisines: list[str]
    rating: float
    estimated_cost: float
    budget_band: BudgetBand
    metadata: dict[str, Any] = Field(default_factory=dict)
