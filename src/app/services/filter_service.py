import logging

from pydantic import BaseModel, Field

from app.config import settings
from app.data.repository import RestaurantRepository
from app.models.preferences import FilterCriteria, UserPreferences
from app.models.restaurant import Restaurant

logger = logging.getLogger(__name__)


class FilterResult(BaseModel):
    """Result of deterministic filtering before LLM ranking."""

    candidates: list[Restaurant] = Field(default_factory=list)
    total_before_cap: int = 0
    applied_filters: dict[str, str | float] = Field(default_factory=dict)


class FilterService:
    """Apply structural filters and cap candidates for the LLM."""

    def filter(
        self,
        preferences: UserPreferences,
        repository: RestaurantRepository,
    ) -> FilterResult:
        criteria = FilterCriteria.from_preferences(preferences)
        all_restaurants = repository.get_all()

        matched = [r for r in all_restaurants if self._matches_criteria(r, criteria)]
        total_before_cap = len(matched)

        sorted_matches = self._sort_candidates(matched)
        capped = sorted_matches[: settings.max_candidates]

        applied = {
            "location": criteria.location,
            "budget": criteria.budget.value,
            "cuisine": criteria.cuisine,
            "min_rating": criteria.min_rating,
            "max_candidates": settings.max_candidates,
        }

        logger.info(
            "Filter: %d matches before cap, %d candidates (from %d total)",
            total_before_cap,
            len(capped),
            len(all_restaurants),
        )

        return FilterResult(
            candidates=capped,
            total_before_cap=total_before_cap,
            applied_filters=applied,
        )

    def _matches_criteria(self, restaurant: Restaurant, criteria: FilterCriteria) -> bool:
        if not self._matches_location(restaurant, criteria.location):
            return False
        if restaurant.budget_band != criteria.budget:
            return False
        if not self._matches_cuisine(restaurant, criteria.cuisine):
            return False
        if restaurant.rating < criteria.min_rating:
            return False
        return True

    @staticmethod
    def _matches_location(restaurant: Restaurant, location: str) -> bool:
        return location.lower() in restaurant.location.lower()

    @staticmethod
    def _matches_cuisine(restaurant: Restaurant, cuisine: str) -> bool:
        cuisine_lower = cuisine.lower()
        for item in restaurant.cuisines:
            if cuisine_lower in item.lower():
                return True
        return False

    @staticmethod
    def _sort_candidates(restaurants: list[Restaurant]) -> list[Restaurant]:
        def sort_key(r: Restaurant) -> tuple[float, int, str]:
            votes = r.metadata.get("votes", 0) if r.metadata else 0
            try:
                votes_int = int(votes)
            except (TypeError, ValueError):
                votes_int = 0
            return (-r.rating, -votes_int, r.name.lower())

        return sorted(restaurants, key=sort_key)
