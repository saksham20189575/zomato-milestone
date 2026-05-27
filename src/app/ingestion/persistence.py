import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def write_parquet(df: pd.DataFrame, output_path: Path) -> None:
    """Write DataFrame to Parquet atomically (temp file then rename)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_suffix(".parquet.tmp")
    df.to_parquet(temp_path, index=False)
    temp_path.replace(output_path)
    logger.info("Wrote %d records to %s", len(df), output_path)


def read_parquet(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)
