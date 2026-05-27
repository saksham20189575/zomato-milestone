import pytest
from pydantic import ValidationError

from app.models.preferences import FilterCriteria, UserPreferences
from app.models.restaurant import BudgetBand
from app.models.validation import validate_budget, validate_min_rating


class TestUserPreferences:
    def test_valid_preferences(self):
        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetBand.MEDIUM,
            cuisine="Italian",
            min_rating=4.0,
            additional_preferences="family-friendly",
            top_k=5,
        )
        assert prefs.location == "Bangalore"
        assert prefs.top_k == 5

    def test_strips_whitespace(self):
        prefs = UserPreferences(
            location="  Bangalore  ",
            budget="medium",
            cuisine=" Italian ",
            min_rating=3.5,
        )
        assert prefs.location == "Bangalore"
        assert prefs.cuisine == "Italian"

    def test_empty_location_rejected(self):
        with pytest.raises(ValidationError):
            UserPreferences(
                location="   ",
                budget=BudgetBand.LOW,
                cuisine="Chinese",
                min_rating=3.0,
            )

    def test_min_rating_out_of_range(self):
        with pytest.raises(ValidationError):
            UserPreferences(
                location="Bangalore",
                budget=BudgetBand.LOW,
                cuisine="Chinese",
                min_rating=5.5,
            )

    def test_top_k_bounds(self):
        with pytest.raises(ValidationError):
            UserPreferences(
                location="Bangalore",
                budget=BudgetBand.LOW,
                cuisine="Chinese",
                min_rating=3.0,
                top_k=0,
            )


class TestFilterCriteria:
    def test_from_preferences_excludes_additional(self):
        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetBand.MEDIUM,
            cuisine="Italian",
            min_rating=4.0,
            additional_preferences="quick service",
        )
        criteria = FilterCriteria.from_preferences(prefs)
        assert criteria.location == "Bangalore"
        assert criteria.cuisine == "Italian"
        assert not hasattr(criteria, "additional_preferences")


class TestValidationHelpers:
    def test_validate_budget(self):
        assert validate_budget("medium") == BudgetBand.MEDIUM

    def test_validate_budget_invalid(self):
        with pytest.raises(ValueError, match="Budget must be"):
            validate_budget("luxury")

    def test_validate_min_rating(self):
        assert validate_min_rating(4.5) == 4.5

    def test_validate_min_rating_invalid(self):
        with pytest.raises(ValueError):
            validate_min_rating(6.0)
