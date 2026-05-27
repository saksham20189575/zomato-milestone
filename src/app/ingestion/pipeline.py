import logging
from collections import Counter
from pathlib import Path

import pandas as pd

from app.config import settings
from app.ingestion.loader import load_raw_dataframe
from app.ingestion.normalizer import normalize_dataframe
from app.ingestion.persistence import write_parquet
from app.ingestion.preprocessor import preprocess_dataframe
from app.models.restaurant import Restaurant

logger = logging.getLogger(__name__)


def run_ingestion(output_path: Path | None = None) -> pd.DataFrame:
    """
    Full ingestion pipeline: load -> normalize -> preprocess -> persist.

    Returns the processed DataFrame.
    """
    output = output_path or settings.data_path

    raw_df = load_raw_dataframe()
    raw_count = len(raw_df)

    normalized_df = normalize_dataframe(raw_df)
    normalized_count = len(normalized_df)
    dropped_invalid = raw_count - normalized_count

    processed_df = preprocess_dataframe(normalized_df)
    final_count = len(processed_df)

    write_parquet(processed_df, output)

    # Validate a sample with Pydantic
    sample = processed_df.head(5)
    for _, row in sample.iterrows():
        Restaurant.model_validate(row.to_dict())

    city_counts = Counter(
        (row.get("metadata") or {}).get("city", "Unknown")
        for row in processed_df.to_dict(orient="records")
    )
    top_cities = city_counts.most_common(10)

    logger.info(
        "Ingestion complete: raw=%d, dropped_invalid=%d, after_dedup=%d, output=%s",
        raw_count,
        dropped_invalid,
        final_count,
        output,
    )
    logger.info("Top cities: %s", top_cities)

    return processed_df
