"""
Map raw Hugging Face columns to canonical field names.

Raw schema (ManikaSaini/zomato-restaurant-recommendation):
  - name                          -> name
  - location                      -> locality (neighborhood)
  - listed_in(city)               -> listed_area
  - address                       -> address (city extracted in preprocessor)
  - cuisines                      -> cuisines_raw
  - rate                          -> rate_raw
  - approx_cost(for two people)   -> cost_raw
  - votes                         -> votes
  - rest_type, online_order, etc. -> metadata fields
"""

import re
from typing import Any

import pandas as pd

# Hugging Face column names (exact)
COL_NAME = "name"
COL_LOCALITY = "location"
COL_LISTED_CITY = "listed_in(city)"
COL_ADDRESS = "address"
COL_CUISINES = "cuisines"
COL_RATE = "rate"
COL_COST = "approx_cost(for two people)"
COL_VOTES = "votes"
COL_REST_TYPE = "rest_type"
COL_ONLINE_ORDER = "online_order"
COL_BOOK_TABLE = "book_table"
COL_URL = "url"

REQUIRED_RAW_COLUMNS = {
    COL_NAME,
    COL_ADDRESS,
    COL_CUISINES,
    COL_RATE,
    COL_COST,
}

_CITY_ALIASES = {
    "bengaluru": "Bangalore",
    "bangalore": "Bangalore",
    "banglore": "Bangalore",
    "bengalore": "Bangalore",
    "delhi": "Delhi",
    "new delhi": "Delhi",
    "mumbai": "Mumbai",
    "bombay": "Mumbai",
    "hyderabad": "Hyderabad",
    "chennai": "Chennai",
    "kolkata": "Kolkata",
    "calcutta": "Kolkata",
    "pune": "Pune",
}


def _parse_rating(raw: Any) -> float | None:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    text = str(raw).strip().upper()
    if not text or text == "NEW" or text == "NAN":
        return None
    match = re.search(r"(\d+\.?\d*)", text)
    if not match:
        return None
    value = float(match.group(1))
    if value < 0 or value > 5:
        return None
    return value


def _parse_cost(raw: Any) -> float | None:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    text = str(raw).strip().lower().replace(",", "")
    if not text or text in ("-", "nan"):
        return None
    # Handle ranges like "300-400" -> use lower bound
    range_match = re.match(r"(\d+)\s*-\s*(\d+)", text)
    if range_match:
        return float(range_match.group(1))
    digits = re.search(r"(\d+)", text)
    if not digits:
        return None
    value = float(digits.group(1))
    return value if value > 0 else None


def _parse_cuisines(raw: Any) -> list[str]:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return []
    parts = [p.strip() for p in str(raw).split(",")]
    return [p for p in parts if p]


def _extract_city(address: str) -> str:
    if not address or (isinstance(address, float) and pd.isna(address)):
        return "Unknown"
    segments = [s.strip() for s in str(address).split(",") if s.strip()]
    if not segments:
        return "Unknown"
    last = segments[-1]
    key = last.lower()
    if key in _CITY_ALIASES:
        return _CITY_ALIASES[key]
    # If last segment looks like a locality within Bangalore area, check earlier segments
    for segment in reversed(segments):
        seg_key = segment.lower()
        if seg_key in _CITY_ALIASES:
            return _CITY_ALIASES[seg_key]
    return last.title()


def _build_location(city: str, locality: str | None, listed_area: str | None) -> str:
    """Build searchable location: 'Bangalore, Banashankari'."""
    parts: list[str] = []
    if city and city != "Unknown":
        parts.append(city)
    for extra in (locality, listed_area):
        if extra and not (isinstance(extra, float) and pd.isna(extra)):
            extra_str = str(extra).strip()
            if extra_str and extra_str not in parts:
                parts.append(extra_str)
    return ", ".join(parts) if parts else "Unknown"


def normalize_row(row: pd.Series) -> dict[str, Any] | None:
    """Normalize a single raw row. Returns None if row should be dropped."""
    name = str(row.get(COL_NAME, "")).strip()
    if not name:
        return None

    rating = _parse_rating(row.get(COL_RATE))
    if rating is None:
        return None

    cost = _parse_cost(row.get(COL_COST))
    if cost is None:
        return None

    cuisines = _parse_cuisines(row.get(COL_CUISINES))
    if not cuisines:
        return None

    address = row.get(COL_ADDRESS, "")
    city = _extract_city(address)
    locality = row.get(COL_LOCALITY)
    listed_area = row.get(COL_LISTED_CITY)
    location = _build_location(city, locality, listed_area)

    votes = row.get(COL_VOTES)
    try:
        votes_int = int(votes) if votes is not None and not pd.isna(votes) else 0
    except (TypeError, ValueError):
        votes_int = 0

    return {
        "name": name,
        "location": location,
        "cuisines": cuisines,
        "rating": rating,
        "estimated_cost": cost,
        "metadata": {
            "address": str(address) if address is not None else "",
            "locality": str(locality) if locality is not None and not pd.isna(locality) else "",
            "listed_area": str(listed_area) if listed_area is not None and not pd.isna(listed_area) else "",
            "city": city,
            "votes": votes_int,
            "rest_type": str(row.get(COL_REST_TYPE, "") or ""),
            "online_order": str(row.get(COL_ONLINE_ORDER, "") or ""),
            "book_table": str(row.get(COL_BOOK_TABLE, "") or ""),
            "url": str(row.get(COL_URL, "") or ""),
        },
    }


def validate_raw_columns(df: pd.DataFrame) -> None:
    """Fail fast if expected Hugging Face columns are missing."""
    missing = REQUIRED_RAW_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"Dataset schema mismatch. Missing columns: {missing}. "
            f"Found: {list(df.columns)}"
        )


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize all rows; drops invalid records."""
    validate_raw_columns(df)
    records: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        normalized = normalize_row(row)
        if normalized is not None:
            records.append(normalized)
    return pd.DataFrame(records)
