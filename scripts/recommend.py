#!/usr/bin/env python3
"""CLI: run full recommendation pipeline via orchestrator."""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app.data.repository import DataStoreError
from app.models.preferences import UserPreferences
from app.models.restaurant import BudgetBand
from app.services.orchestrator import RecommendRestaurantsUseCase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Get restaurant recommendations")
    parser.add_argument("--location", default="Bangalore")
    parser.add_argument("--budget", default="medium", choices=["low", "medium", "high"])
    parser.add_argument("--cuisine", default="Italian")
    parser.add_argument("--min-rating", type=float, default=4.0)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--additional", default=None)
    args = parser.parse_args()

    try:
        use_case = RecommendRestaurantsUseCase()
    except DataStoreError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    prefs = UserPreferences(
        location=args.location,
        budget=BudgetBand(args.budget),
        cuisine=args.cuisine,
        min_rating=args.min_rating,
        top_k=args.top_k,
        additional_preferences=args.additional,
    )

    response = use_case.execute(prefs)
    meta = response.meta

    print(f"\nCandidates considered: {meta.get('candidates_considered')}")
    print(f"Sent to LLM: {meta.get('candidates_sent_to_llm', 0)}")
    print(f"LLM latency: {meta.get('llm_latency_ms', 0)} ms")
    print(f"Fallback used: {meta.get('fallback_used')}\n")

    if response.summary:
        print(f"Summary: {response.summary}\n")

    if not response.recommendations:
        print("No recommendations found.")
        return

    for rec in response.recommendations:
        r = rec.restaurant
        print(f"#{rec.rank} {r.name}")
        print(f"   {r.location} | {r.rating} | ₹{r.estimated_cost:.0f} for two")
        print(f"   {', '.join(r.cuisines)}")
        print(f"   {rec.explanation}\n")


if __name__ == "__main__":
    main()
