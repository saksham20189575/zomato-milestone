import logging

from app.models.recommendation import Recommendation
from app.models.restaurant import Restaurant
from app.services.response_parser import ParsedLLMResponse

logger = logging.getLogger(__name__)

GENERIC_EXPLANATION = (
    "This restaurant matches your filters based on its rating, cuisine, location, and budget."
)


class RecommendationMerger:
    """Join parsed LLM output with Restaurant records."""

    def merge(
        self,
        parsed: ParsedLLMResponse,
        candidates: list[Restaurant],
        top_k: int,
    ) -> tuple[str | None, list[Recommendation]]:
        by_id = {r.id: r for r in candidates}
        recommendations: list[Recommendation] = []

        for item in parsed.recommendations:
            restaurant = by_id.get(item.restaurant_id)
            if restaurant is None:
                logger.warning("Merge skipped unknown id: %s", item.restaurant_id)
                continue
            explanation = item.explanation.strip() or GENERIC_EXPLANATION
            recommendations.append(
                Recommendation(
                    restaurant=restaurant,
                    rank=item.rank,
                    explanation=explanation,
                )
            )

        if len(recommendations) < top_k:
            recommendations = self._fill_from_candidates(
                recommendations, candidates, top_k
            )

        return parsed.summary, recommendations[:top_k]

    def fallback_merge(
        self,
        candidates: list[Restaurant],
        top_k: int,
    ) -> tuple[str | None, list[Recommendation]]:
        """Rating-based top-K when LLM parse or API fails."""
        sorted_candidates = sorted(
            candidates,
            key=lambda r: (
                -r.rating,
                -(int(r.metadata.get("votes", 0)) if r.metadata else 0),
                r.name.lower(),
            ),
        )
        recommendations = [
            Recommendation(
                restaurant=r,
                rank=i,
                explanation=GENERIC_EXPLANATION,
            )
            for i, r in enumerate(sorted_candidates[:top_k], start=1)
        ]
        summary = (
            f"Showing top {len(recommendations)} restaurants by rating "
            "(AI ranking unavailable)."
        )
        return summary, recommendations

    def _fill_from_candidates(
        self,
        existing: list[Recommendation],
        candidates: list[Restaurant],
        top_k: int,
    ) -> list[Recommendation]:
        used_ids = {r.restaurant.id for r in existing}
        remaining = [c for c in candidates if c.id not in used_ids]
        sorted_remaining = sorted(remaining, key=lambda r: -r.rating)

        result = list(existing)
        next_rank = len(result) + 1
        for restaurant in sorted_remaining:
            if len(result) >= top_k:
                break
            result.append(
                Recommendation(
                    restaurant=restaurant,
                    rank=next_rank,
                    explanation=GENERIC_EXPLANATION,
                )
            )
            next_rank += 1
        return result
