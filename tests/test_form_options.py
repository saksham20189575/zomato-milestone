from pathlib import Path

import pandas as pd

from app.data.repository import RestaurantRepository
from app.data.form_options import get_location_options


def test_get_location_options_from_repository(tmp_path: Path):
    path = tmp_path / "restaurants.parquet"
    pd.DataFrame(
        [
            {
                "id": "1",
                "name": "A",
                "location": "Bangalore, BTM",
                "cuisines": ["Italian"],
                "rating": 4.0,
                "estimated_cost": 500.0,
                "budget_band": "low",
                "metadata": {"locality": "BTM"},
            },
            {
                "id": "2",
                "name": "B",
                "location": "Bangalore, Indiranagar",
                "cuisines": ["Chinese"],
                "rating": 4.5,
                "estimated_cost": 800.0,
                "budget_band": "medium",
                "metadata": {"locality": "Indiranagar"},
            },
        ]
    ).to_parquet(path, index=False)

    repo = RestaurantRepository(path)
    assert get_location_options(repo) == ["BTM", "Indiranagar"]
