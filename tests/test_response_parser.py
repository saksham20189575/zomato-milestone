import json
from pathlib import Path

import pytest

from app.services.response_parser import ResponseParser

FIXTURES = Path(__file__).parent / "fixtures"


class TestResponseParser:
    def test_parse_valid_json(self):
        raw = (FIXTURES / "llm_response_valid.json").read_text()
        result = ResponseParser().parse(raw, {"abc123", "def456"}, top_k=5)
        assert result is not None
        assert result.summary is not None
        assert len(result.recommendations) == 2
        assert result.recommendations[0].restaurant_id == "abc123"
        assert result.recommendations[0].rank == 1

    def test_parse_markdown_fenced_json(self):
        inner = json.dumps(
            {
                "summary": "Ok",
                "recommendations": [
                    {"restaurant_id": "id1", "rank": 1, "explanation": "Good fit"}
                ],
            }
        )
        raw = f"```json\n{inner}\n```"
        result = ResponseParser().parse(raw, {"id1"}, top_k=3)
        assert result is not None
        assert len(result.recommendations) == 1

    def test_parse_invalid_returns_none(self):
        raw = (FIXTURES / "llm_response_invalid.json").read_text()
        result = ResponseParser().parse(raw, {"abc123"}, top_k=5)
        assert result is None

    def test_drops_unknown_ids(self):
        raw = json.dumps(
            {
                "summary": "Test",
                "recommendations": [
                    {"restaurant_id": "known", "rank": 1, "explanation": "yes"},
                    {"restaurant_id": "unknown", "rank": 2, "explanation": "no"},
                ],
            }
        )
        result = ResponseParser().parse(raw, {"known"}, top_k=5)
        assert result is not None
        assert len(result.recommendations) == 1
        assert result.recommendations[0].restaurant_id == "known"

    def test_respects_top_k(self):
        raw = json.dumps(
            {
                "summary": "Test",
                "recommendations": [
                    {"restaurant_id": f"id{i}", "rank": i, "explanation": "x"}
                    for i in range(1, 6)
                ],
            }
        )
        allowed = {f"id{i}" for i in range(1, 6)}
        result = ResponseParser().parse(raw, allowed, top_k=2)
        assert result is not None
        assert len(result.recommendations) == 2

    def test_empty_recommendations_returns_none(self):
        raw = json.dumps({"summary": "None", "recommendations": []})
        result = ResponseParser().parse(raw, {"id1"}, top_k=3)
        assert result is None
