#!/usr/bin/env python3
"""Debug CLI: print filtered candidates for a preference set (no LLM)."""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app.data.repository import DataStoreError, get_repository
from app.models.preferences import UserPreferences
from app.models.restaurant import BudgetBand
from app.services.filter_service import FilterService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Filter restaurants without LLM")
    parser.add_argument("--location", default="Bangalore", help="Location substring")
    parser.add_argument(
        "--budget",
        default="medium",
        choices=["low", "medium", "high"],
        help="Budget band",
    )
    parser.add_argument("--cuisine", default="Italian", help="Cuisine substring")
    parser.add_argument("--min-rating", type=float, default=4.0, help="Minimum rating")
    parser.add_argument(
        "--additional",
        default=None,
        help="Additional preferences (not used for filtering)",
    )
    parser.add_argument("--limit", type=int, default=10, help="Rows to print")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        repo = get_repository()
    except DataStoreError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    preferences = UserPreferences(
        location=args.location,
        budget=BudgetBand(args.budget),
        cuisine=args.cuisine,
        min_rating=args.min_rating,
        additional_preferences=args.additional,
    )

    result = FilterService().filter(preferences, repo)

    print(f"\nApplied filters: {result.applied_filters}")
    print(f"Matches before cap: {result.total_before_cap}")
    print(f"Candidates returned: {len(result.candidates)}\n")

    if not result.candidates:
        print("No matches. Try relaxing location, cuisine, budget, or min_rating.")
        return

    print(f"{'Name':<35} {'Location':<30} {'Rating':>6} {'Cost':>8} {'Cuisines'}")
    print("-" * 100)
    for r in result.candidates[: args.limit]:
        cuisines = ", ".join(r.cuisines[:3])
        print(
            f"{r.name[:34]:<35} {r.location[:29]:<30} {r.rating:>6.1f} "
            f"{r.estimated_cost:>8.0f} {cuisines}"
        )

    if len(result.candidates) > args.limit:
        print(f"\n... and {len(result.candidates) - args.limit} more")


if __name__ == "__main__":
    main()
