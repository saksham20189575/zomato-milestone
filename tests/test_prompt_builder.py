import json

import pytest

from app.models.preferences import UserPreferences
from app.models.restaurant import BudgetBand, Restaurant
from app.services.prompt_builder import PromptBuilder


def _restaurant(id: str, name: str = "Test") -> Restaurant:
    return Restaurant(
        id=id,
        name=name,
        location="Bangalore, BTM",
        cuisines=["Italian"],
        rating=4.5,
        estimated_cost=800.0,
        budget_band=BudgetBand.MEDIUM,
    )


class TestPromptBuilder:
    def test_build_returns_system_and_user_messages(self):
        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetBand.MEDIUM,
            cuisine="Italian",
            min_rating=4.0,
            additional_preferences="family-friendly",
            top_k=2,
        )
        candidates = [_restaurant("abc123"), _restaurant("def456")]
        messages = PromptBuilder().build(prefs, candidates)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "Bangalore" in messages[1]["content"]
        assert "family-friendly" in messages[1]["content"]
        assert "abc123" in messages[1]["content"]
        assert "def456" in messages[1]["content"]
        assert "top 2" in messages[1]["content"].lower()

    def test_candidates_included_as_json(self):
        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetBand.MEDIUM,
            cuisine="Italian",
            min_rating=4.0,
        )
        messages = PromptBuilder().build(prefs, [_restaurant("id1")])
        assert '"restaurant_id": "id1"' in messages[1]["content"]

    def test_zero_candidates_raises(self):
        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetBand.MEDIUM,
            cuisine="Italian",
            min_rating=4.0,
        )
        with pytest.raises(ValueError, match="zero candidates"):
            PromptBuilder().build(prefs, [])

    def test_allowed_ids_listed(self):
        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetBand.MEDIUM,
            cuisine="Italian",
            min_rating=4.0,
            top_k=1,
        )
        messages = PromptBuilder().build(prefs, [_restaurant("x1"), _restaurant("x2")])
        allowed = json.loads(
            messages[1]["content"].split("Allowed restaurant_id values: ")[1].strip()
        )
        assert allowed == ["x1", "x2"]
