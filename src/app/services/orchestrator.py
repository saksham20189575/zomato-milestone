import logging
import time
import uuid

from app.data.repository import RestaurantRepository, get_repository
from app.models.preferences import UserPreferences
from app.models.recommendation import RecommendationResponse
from app.services.filter_service import FilterService
from app.services.recommendation_engine import RecommendationEngine

logger = logging.getLogger(__name__)


class RecommendRestaurantsUseCase:
    """
    Single entry point for the recommendation use case.
    UI and API layers should call execute() only.
    """

    def __init__(
        self,
        repository: RestaurantRepository | None = None,
        filter_service: FilterService | None = None,
        engine: RecommendationEngine | None = None,
    ) -> None:
        self._repository = repository or get_repository()
        self._filter_service = filter_service or FilterService()
        self._engine = engine or RecommendationEngine()

    @property
    def repository(self) -> RestaurantRepository:
        return self._repository

    def execute(self, preferences: UserPreferences) -> RecommendationResponse:
        request_id = str(uuid.uuid4())[:8]
        logger.info(
            "[%s] Recommendation request: location=%s, budget=%s, cuisine=%s, min_rating=%s, top_k=%s",
            request_id,
            preferences.location,
            preferences.budget.value,
            preferences.cuisine,
            preferences.min_rating,
            preferences.top_k,
        )

        filter_start = time.perf_counter()
        filter_result = self._filter_service.filter(preferences, self._repository)
        filter_ms = (time.perf_counter() - filter_start) * 1000

        logger.info(
            "[%s] Filter complete in %.1fms: %d matches before cap, %d candidates",
            request_id,
            filter_ms,
            filter_result.total_before_cap,
            len(filter_result.candidates),
        )

        if not filter_result.candidates:
            logger.info("[%s] No candidates; skipping LLM", request_id)
            return RecommendationResponse(
                summary=None,
                recommendations=[],
                meta={
                    "request_id": request_id,
                    "candidates_considered": 0,
                    "candidates_sent_to_llm": 0,
                    "filters_applied": filter_result.applied_filters,
                    "filter_latency_ms": round(filter_ms, 1),
                    "llm_used": False,
                    "llm_latency_ms": 0,
                    "parse_success": None,
                    "fallback_used": False,
                },
            )

        llm_start = time.perf_counter()
        response = self._engine.generate(preferences, filter_result)
        llm_ms = (time.perf_counter() - llm_start) * 1000

        response.meta.update(
            {
                "request_id": request_id,
                "candidates_sent_to_llm": len(filter_result.candidates),
                "filter_latency_ms": round(filter_ms, 1),
                "llm_latency_ms": round(llm_ms, 1),
            }
        )

        logger.info(
            "[%s] Complete in %.1fms (LLM): fallback=%s, parse_success=%s, recommendations=%d",
            request_id,
            llm_ms,
            response.meta.get("fallback_used"),
            response.meta.get("parse_success"),
            len(response.recommendations),
        )

        return response


_orchestrator: RecommendRestaurantsUseCase | None = None


def get_orchestrator(
    repository: RestaurantRepository | None = None,
    *,
    reload: bool = False,
) -> RecommendRestaurantsUseCase:
    """Return a shared orchestrator instance."""
    global _orchestrator
    if _orchestrator is None or reload:
        _orchestrator = RecommendRestaurantsUseCase(repository=repository)
    return _orchestrator


def reset_orchestrator() -> None:
    """Clear cached orchestrator (for tests)."""
    global _orchestrator
    _orchestrator = None
