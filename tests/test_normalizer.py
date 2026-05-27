import pandas as pd
import pytest

from app.ingestion.normalizer import (
    normalize_dataframe,
    normalize_row,
    validate_raw_columns,
    _parse_cost,
    _parse_rating,
    _parse_cuisines,
)


class TestParsers:
    def test_parse_rating_valid(self):
        assert _parse_rating("4.1/5") == 4.1
        assert _parse_rating("4.1 /5") == 4.1

    def test_parse_rating_new_returns_none(self):
        assert _parse_rating("NEW") is None

    def test_parse_rating_null(self):
        assert _parse_rating(None) is None
        assert _parse_rating(float("nan")) is None

    def test_parse_cost_valid(self):
        assert _parse_cost("800") == 800.0
        assert _parse_cost("300-400") == 300.0

    def test_parse_cost_invalid(self):
        assert _parse_cost(None) is None
        assert _parse_cost("-") is None

    def test_parse_cuisines(self):
        assert _parse_cuisines("North Indian, Chinese") == [
            "North Indian",
            "Chinese",
        ]
        assert _parse_cuisines(None) == []


class TestNormalizeRow:
    def test_valid_row(self, sample_raw_row):
        result = normalize_row(pd.Series(sample_raw_row))
        assert result is not None
        assert result["name"] == "Jalsa"
        assert "Bangalore" in result["location"]
        assert result["rating"] == 4.1
        assert result["estimated_cost"] == 800.0
        assert "North Indian" in result["cuisines"]

    def test_empty_name_dropped(self, sample_raw_row):
        row = sample_raw_row.copy()
        row["name"] = "   "
        assert normalize_row(pd.Series(row)) is None

    def test_new_rating_dropped(self, sample_raw_row):
        row = sample_raw_row.copy()
        row["rate"] = "NEW"
        assert normalize_row(pd.Series(row)) is None

    def test_missing_cost_dropped(self, sample_raw_row):
        row = sample_raw_row.copy()
        row["approx_cost(for two people)"] = None
        assert normalize_row(pd.Series(row)) is None

    def test_bengaluru_normalized_to_bangalore(self, sample_raw_row):
        row = sample_raw_row.copy()
        row["address"] = "Some Street, Bengaluru"
        result = normalize_row(pd.Series(row))
        assert result is not None
        assert result["metadata"]["city"] == "Bangalore"


class TestNormalizeDataframe:
    def test_schema_validation_fails_on_missing_columns(self):
        df = pd.DataFrame([{"name": "Test"}])
        with pytest.raises(ValueError, match="schema mismatch"):
            validate_raw_columns(df)

    def test_normalize_dataframe(self, sample_raw_df):
        result = normalize_dataframe(sample_raw_df)
        assert len(result) == 1
        assert result.iloc[0]["name"] == "Jalsa"
