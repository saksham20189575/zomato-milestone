import hashlib
import logging

import pandas as pd

from app.config import settings
from app.models.restaurant import BudgetBand

logger = logging.getLogger(__name__)


def assign_budget_band(cost: float) -> BudgetBand:
    if cost <= settings.budget_low_max:
        return BudgetBand.LOW
    if cost <= settings.budget_medium_max:
        return BudgetBand.MEDIUM
    return BudgetBand.HIGH


def _stable_id(name: str, location: str) -> str:
    key = f"{name.strip().lower()}|{location.strip().lower()}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Assign stable IDs, budget bands, and deduplicate on (name, location).
    """
    if df.empty:
        return df

    df = df.copy()
    df["id"] = df.apply(lambda r: _stable_id(r["name"], r["location"]), axis=1)
    df["budget_band"] = df["estimated_cost"].apply(
        lambda c: assign_budget_band(float(c)).value
    )

    before_dedup = len(df)
    df = df.drop_duplicates(subset=["name", "location"], keep="first")
    dropped_dupes = before_dedup - len(df)

    if dropped_dupes:
        logger.info("Dropped %d duplicate (name, location) rows", dropped_dupes)

    # Stable column order for Parquet
    columns = [
        "id",
        "name",
        "location",
        "cuisines",
        "rating",
        "estimated_cost",
        "budget_band",
        "metadata",
    ]
    return df[columns].reset_index(drop=True)


def to_restaurant_records(df: pd.DataFrame) -> list[dict]:
    """Convert DataFrame rows to dicts suitable for Restaurant model validation."""
    return df.to_dict(orient="records")
