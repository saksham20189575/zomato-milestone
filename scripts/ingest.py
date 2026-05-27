#!/usr/bin/env python3
"""CLI entry point for data ingestion (Phase 1)."""

import logging
import sys
from pathlib import Path

# Add src to path for `python scripts/ingest.py`
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app.ingestion.pipeline import run_ingestion

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main() -> None:
    df = run_ingestion()
    print(f"\nIngestion successful: {len(df)} restaurants written.")
    print("\nSample records:")
    print(
        df[["name", "location", "cuisines", "rating", "estimated_cost", "budget_band"]]
        .head(3)
        .to_string()
    )


if __name__ == "__main__":
    main()
