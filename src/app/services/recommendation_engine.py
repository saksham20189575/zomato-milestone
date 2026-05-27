import logging

from app.models.preferences import UserPreferences
from app.models.recommendation import RecommendationResponse
from app.models.restaurant import Restaurant
from app.services.filter_service import FilterResult
from app.services.llm_client import LLMClient, LLMError, get_llm_client
from app.services.merger import RecommendationMerger
from app.services.prompt_builder import PromptBuilder
from app.services.response_parser import ResponseParser

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Phase 4 pipeline: prompt -> Groq -> parse -> merge.
    Used by orchestrator (Phase 5) and integration tests.
    """

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        prompt_builder: PromptBuilder | None = None,
        response_parser: ResponseParser | None = None,
        merger: RecommendationMerger | None = None,
    ) -> None:
        self._llm = llm_client or get_llm_client()
        self._prompt_builder = prompt_builder or PromptBuilder()
        self._parser = response_parser or ResponseParser()
        self._merger = merger or RecommendationMerger()

    def generate(
        self,
        preferences: UserPreferences,
        filter_result: FilterResult,
    ) -> RecommendationResponse:
        candidates = filter_result.candidates
        if not candidates:
            return RecommendationResponse(
                summary=None,
                recommendations=[],
                meta={
                    "candidates_considered": 0,
                    "filters_applied": filter_result.applied_filters,
                    "llm_used": False,
                    "fallback_used": False,
                },
            )

        allowed_ids = {r.id for r in candidates}
        top_k = min(preferences.top_k, len(candidates))
        fallback_used = False
        llm_used = True
        parse_success: bool | None = None

        try:
            messages = self._prompt_builder.build(preferences, candidates)
            raw = self._llm.complete(messages)
            parsed = self._parser.parse(raw, allowed_ids, top_k)

            if parsed is not None:
                parse_success = True
                summary, recommendations = self._merger.merge(parsed, candidates, top_k)
                logger.info("LLM parse succeeded: %d recommendations", len(recommendations))
            else:
                parse_success = False
                fallback_used = True
                logger.warning("LLM parse failed; using rating fallback")
                summary, recommendations = self._merger.fallback_merge(candidates, top_k)
        except LLMError as e:
            logger.error("LLM failed, using fallback: %s", e)
            parse_success = False
            fallback_used = True
            llm_used = True
            summary, recommendations = self._merger.fallback_merge(candidates, top_k)

        return RecommendationResponse(
            summary=summary,
            recommendations=recommendations,
            meta={
                "candidates_considered": filter_result.total_before_cap,
                "filters_applied": filter_result.applied_filters,
                "llm_used": llm_used,
                "parse_success": parse_success,
                "fallback_used": fallback_used,
            },
        )
