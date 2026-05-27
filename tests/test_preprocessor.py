import pandas as pd

from app.ingestion.preprocessor import assign_budget_band, preprocess_dataframe
from app.models.restaurant import BudgetBand


class TestBudgetBand:
    def test_low(self):
        assert assign_budget_band(400) == BudgetBand.LOW

    def test_medium(self):
        assert assign_budget_band(800) == BudgetBand.MEDIUM

    def test_high(self):
        assert assign_budget_band(2000) == BudgetBand.HIGH

    def test_boundary_low_max(self):
        assert assign_budget_band(500) == BudgetBand.LOW

    def test_boundary_medium_max(self):
        assert assign_budget_band(1500) == BudgetBand.MEDIUM


class TestPreprocessor:
    def test_assigns_id_and_dedupes(self):
        df = pd.DataFrame(
            [
                {
                    "name": "Cafe A",
                    "location": "Bangalore, BTM",
                    "cuisines": ["Italian"],
                    "rating": 4.0,
                    "estimated_cost": 600.0,
                    "metadata": {},
                },
                {
                    "name": "Cafe A",
                    "location": "Bangalore, BTM",
                    "cuisines": ["Italian"],
                    "rating": 4.2,
                    "estimated_cost": 600.0,
                    "metadata": {},
                },
            ]
        )
        result = preprocess_dataframe(df)
        assert len(result) == 1
        assert "id" in result.columns
        assert result.iloc[0]["budget_band"] == "medium"
