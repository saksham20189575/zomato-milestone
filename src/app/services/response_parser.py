import json
import logging
import re
from typing import Any

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


class ParsedRecommendation(BaseModel):
    restaurant_id: str
    rank: int = Field(..., ge=1)
    explanation: str = ""


class ParsedLLMResponse(BaseModel):
    summary: str | None = None
    recommendations: list[ParsedRecommendation] = Field(default_factory=list)


class ResponseParser:
    """Parse and validate Groq JSON responses."""

    def parse(
        self,
        raw: str,
        allowed_ids: set[str],
        top_k: int,
    ) -> ParsedLLMResponse | None:
        data = self._extract_json(raw)
        if data is None:
            logger.warning("Failed to extract JSON from LLM response")
            return None

        try:
            parsed = ParsedLLMResponse.model_validate(data)
        except ValidationError as e:
            logger.warning("LLM JSON validation failed: %s", e)
            return None

        validated = self._validate_recommendations(parsed, allowed_ids, top_k)
        if not validated.recommendations:
            logger.warning("No valid recommendations after validation")
            return None

        return validated

    def _extract_json(self, raw: str) -> dict[str, Any] | None:
        text = raw.strip()
        if not text:
            return None

        # Direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Markdown code fence
        fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fence_match:
            try:
                return json.loads(fence_match.group(1))
            except json.JSONDecodeError:
                pass

        # First JSON object in text
        brace_match = re.search(r"\{.*\}", text, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    def _validate_recommendations(
        self,
        parsed: ParsedLLMResponse,
        allowed_ids: set[str],
        top_k: int,
    ) -> ParsedLLMResponse:
        seen_ids: set[str] = set()
        valid: list[ParsedRecommendation] = []

        sorted_recs = sorted(parsed.recommendations, key=lambda r: r.rank)
        for rec in sorted_recs:
            if rec.restaurant_id not in allowed_ids:
                logger.warning("Dropping unknown restaurant_id: %s", rec.restaurant_id)
                continue
            if rec.restaurant_id in seen_ids:
                logger.warning("Dropping duplicate restaurant_id: %s", rec.restaurant_id)
                continue
            seen_ids.add(rec.restaurant_id)
            valid.append(rec)
            if len(valid) >= top_k:
                break

        # Renumber ranks contiguously
        for i, rec in enumerate(valid, start=1):
            rec.rank = i

        return ParsedLLMResponse(summary=parsed.summary, recommendations=valid)
