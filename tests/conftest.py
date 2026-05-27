import pandas as pd
import pytest


@pytest.fixture
def sample_raw_row() -> dict:
    return {
        "name": "Jalsa",
        "location": "Banashankari",
        "listed_in(city)": "Banashankari",
        "address": "942, 21st Main Road, 2nd Stage, Banashankari, Bangalore",
        "cuisines": "North Indian, Mughlai, Chinese",
        "rate": "4.1/5",
        "approx_cost(for two people)": "800",
        "votes": 775,
        "rest_type": "Casual Dining",
        "online_order": "Yes",
        "book_table": "Yes",
        "url": "https://www.zomato.com/bangalore/jalsa",
    }


@pytest.fixture
def sample_raw_df(sample_raw_row) -> pd.DataFrame:
    return pd.DataFrame([sample_raw_row])
