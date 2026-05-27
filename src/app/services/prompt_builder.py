import json
import logging

from app.config import settings
from app.models.preferences import UserPreferences
from app.models.restaurant import Restaurant

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful restaurant recommendation advisor for Zomato-style dining in India.

RULES:
1. You may ONLY recommend restaurants from the CANDIDATES list below.
2. Do NOT invent restaurant names or IDs not in the list.
3. Rank exactly the requested number of restaurants (or fewer if not enough candidates).
4. Each explanation must reference the user's location, budget, cuisine, and minimum rating.
5. If additional_preferences are provided, address them in explanations.
6. Respond with valid JSON only, matching the required schema."""


class PromptBuilder:
    """Build Groq chat messages from user preferences and filtered candidates."""

    def build(
        self,
        preferences: UserPreferences,
        candidates: list[Restaurant],
    ) -> list[dict[str, str]]:
        if not candidates:
            raise ValueError("Cannot build prompt with zero candidates")

        user_block = self._format_preferences(preferences)
        candidate_block = self._format_candidates(candidates)
        top_k = min(preferences.top_k, len(candidates))

        user_message = f"""USER PREFERENCES:
{user_block}

CANDIDATES ({len(candidates)} restaurants):
{candidate_block}

TASK:
Rank the top {top_k} restaurants from CANDIDATES that best match the user preferences.
Return JSON with this exact schema:
{{
  "summary": "One paragraph overview of your picks for this user",
  "recommendations": [
    {{
      "restaurant_id": "<id from candidates>",
      "rank": 1,
      "explanation": "Why this restaurant fits (mention location, budget, cuisine, rating, and additional preferences if any)"
    }}
  ]
}}

Allowed restaurant_id values: {json.dumps([c.id for c in candidates])}"""

        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

    def _format_preferences(self, preferences: UserPreferences) -> str:
        lines = [
            f"- location: {preferences.location}",
            f"- budget: {preferences.budget.value}",
            f"- cuisine: {preferences.cuisine}",
            f"- min_rating: {preferences.min_rating}",
        ]
        if preferences.additional_preferences:
            text = preferences.additional_preferences
            max_len = settings.additional_preferences_max_length
            if len(text) > max_len:
                text = text[: max_len - 3] + "..."
                logger.warning("Truncated additional_preferences to %d chars", max_len)
            lines.append(f"- additional_preferences: {text}")
        return "\n".join(lines)

    @staticmethod
    def _format_candidates(candidates: list[Restaurant]) -> str:
        payload = [
            {
                "restaurant_id": r.id,
                "name": r.name,
                "location": r.location,
                "cuisines": r.cuisines,
                "rating": r.rating,
                "estimated_cost": r.estimated_cost,
                "budget_band": r.budget_band.value,
            }
            for r in candidates
        ]
        return json.dumps(payload, indent=2)
