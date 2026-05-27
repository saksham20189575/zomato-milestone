"""Form metadata loaded from the restaurant repository (API + UI)."""

from __future__ import annotations

from pathlib import Path

from app.data.repository import RestaurantRepository, get_repository


def get_location_options(
    repository: RestaurantRepository | None = None,
    *,
    data_path: Path | None = None,
) -> list[str]:
    """Neighbourhood/area names for the location dropdown (e.g. Indiranagar, Bellandur)."""
    repo = repository or get_repository(data_path)
    return repo.get_distinct_localities()
