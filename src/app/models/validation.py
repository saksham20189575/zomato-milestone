"""Validation helpers for user preference input."""

from app.models.preferences import UserPreferences
from app.models.restaurant import BudgetBand


def validate_budget(value: str) -> BudgetBand:
    """Parse and validate budget string."""
    normalized = value.strip().lower()
    try:
        return BudgetBand(normalized)
    except ValueError:
        valid = ", ".join(b.value for b in BudgetBand)
        raise ValueError(f"Budget must be one of: {valid}") from None


def validate_min_rating(value: float) -> float:
    """Validate min_rating is within [0, 5]."""
    if value < 0 or value > 5:
        raise ValueError("min_rating must be between 0 and 5")
    return value


def validate_preferences_dict(data: dict) -> UserPreferences:
    """
    Build UserPreferences from a raw dict (e.g. API body or form).
    Raises ValueError with user-friendly messages on failure.
    """
    try:
        return UserPreferences.model_validate(data)
    except Exception as e:
        raise ValueError(str(e)) from e
