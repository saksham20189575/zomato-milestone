from pydantic import BaseModel, Field, field_validator

from app.models.restaurant import BudgetBand


class UserPreferences(BaseModel):
    """User search preferences for restaurant recommendations."""

    location: str = Field(..., min_length=1, description="Area or locality, e.g. Indiranagar, Bellandur")
    budget: BudgetBand
    cuisine: str = Field(..., min_length=1, description="Preferred cuisine type")
    min_rating: float = Field(..., ge=0.0, le=5.0)
    additional_preferences: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)

    @field_validator("location", "cuisine", mode="before")
    @classmethod
    def strip_required_strings(cls, v: str) -> str:
        if v is None:
            raise ValueError("Field cannot be null")
        stripped = str(v).strip()
        if not stripped:
            raise ValueError("Field cannot be empty or whitespace only")
        return stripped

    @field_validator("additional_preferences", mode="before")
    @classmethod
    def strip_optional_text(cls, v: str | None) -> str | None:
        if v is None:
            return None
        stripped = str(v).strip()
        return stripped or None


class FilterCriteria(BaseModel):
    """
    Structural filter fields derived from user preferences.
    Free-text additional_preferences is excluded (forwarded to LLM only).
    """

    location: str
    budget: BudgetBand
    cuisine: str
    min_rating: float

    @classmethod
    def from_preferences(cls, preferences: UserPreferences) -> "FilterCriteria":
        return cls(
            location=preferences.location,
            budget=preferences.budget,
            cuisine=preferences.cuisine,
            min_rating=preferences.min_rating,
        )
