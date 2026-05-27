import logging
from pathlib import Path

import pandas as pd

from app.config import settings
from app.models.restaurant import BudgetBand, Restaurant

logger = logging.getLogger(__name__)


class DataStoreError(Exception):
    """Raised when restaurant data cannot be loaded."""


class RestaurantRepository:
    """In-memory store of preprocessed restaurants loaded from Parquet."""

    def __init__(self, data_path: Path | None = None) -> None:
        path = data_path or settings.data_path
        self._restaurants: list[Restaurant] = []
        self._by_id: dict[str, Restaurant] = {}
        self._load(path)

    def _load(self, path: Path) -> None:
        if not path.exists():
            raise DataStoreError(
                f"Processed data not found at {path}. "
                "Run ingestion first: python scripts/ingest.py"
            )

        try:
            df = pd.read_parquet(path)
        except Exception as e:
            raise DataStoreError(f"Failed to read restaurant data from {path}: {e}") from e

        if df.empty:
            raise DataStoreError(f"Restaurant data file is empty: {path}")

        restaurants: list[Restaurant] = []
        for record in df.to_dict(orient="records"):
            restaurants.append(_row_to_restaurant(record))

        self._restaurants = restaurants
        self._by_id = {r.id: r for r in restaurants}

        if not self._restaurants:
            raise DataStoreError(f"No valid restaurants loaded from {path}")

        logger.info("Loaded %d restaurants from %s", len(self._restaurants), path)

    def get_all(self) -> list[Restaurant]:
        """Return all restaurants (defensive copy of list reference)."""
        return list(self._restaurants)

    def get_by_ids(self, ids: list[str]) -> list[Restaurant]:
        """Return restaurants for the given ids, preserving input order. Unknown ids are omitted."""
        if not ids:
            return []
        result: list[Restaurant] = []
        for restaurant_id in ids:
            restaurant = self._by_id.get(restaurant_id)
            if restaurant is not None:
                result.append(restaurant)
            else:
                logger.warning("Unknown restaurant id requested: %s", restaurant_id)
        return result

    def get_by_id(self, restaurant_id: str) -> Restaurant | None:
        return self._by_id.get(restaurant_id)

    @property
    def count(self) -> int:
        return len(self._restaurants)

    def get_distinct_localities(self) -> list[str]:
        """
        Sorted unique locality/area names for UI dropdowns (e.g. Indiranagar, Bellandur).
        Uses metadata.locality, falling back to metadata.listed_area when locality is absent.
        """
        seen: set[str] = set()
        localities: list[str] = []
        for restaurant in self._restaurants:
            meta = restaurant.metadata or {}
            for key in ("locality", "listed_area"):
                value = meta.get(key)
                if not value or not isinstance(value, str):
                    continue
                label = value.strip()
                if not label:
                    continue
                normalized = label.casefold()
                if normalized in seen:
                    break
                seen.add(normalized)
                localities.append(label)
                break
        return sorted(localities, key=str.casefold)


def _row_to_restaurant(record: dict) -> Restaurant:
    """Convert a Parquet row dict to a Restaurant model."""
    cuisines = record.get("cuisines", [])
    if cuisines is None:
        cuisines = []
    elif not isinstance(cuisines, list):
        cuisines = list(cuisines)

    metadata = record.get("metadata", {})
    if metadata is None or (isinstance(metadata, float) and pd.isna(metadata)):
        metadata = {}
    elif not isinstance(metadata, dict):
        metadata = dict(metadata)

    budget_raw = record["budget_band"]
    if isinstance(budget_raw, BudgetBand):
        budget_band = budget_raw
    else:
        budget_band = BudgetBand(str(budget_raw).lower())

    return Restaurant(
        id=str(record["id"]),
        name=str(record["name"]),
        location=str(record["location"]),
        cuisines=[str(c) for c in cuisines],
        rating=float(record["rating"]),
        estimated_cost=float(record["estimated_cost"]),
        budget_band=budget_band,
        metadata=metadata,
    )


_repository: RestaurantRepository | None = None


def get_repository(data_path: Path | None = None, *, reload: bool = False) -> RestaurantRepository:
    """
    Return a shared RestaurantRepository instance (load-on-first-use).
    Pass reload=True to force a fresh load from disk.
    """
    global _repository
    if _repository is None or reload:
        _repository = RestaurantRepository(data_path=data_path)
    return _repository


def reset_repository() -> None:
    """Clear cached repository (for tests)."""
    global _repository
    _repository = None
