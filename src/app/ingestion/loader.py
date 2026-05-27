import logging

import pandas as pd
from datasets import load_dataset

logger = logging.getLogger(__name__)

DATASET_ID = "ManikaSaini/zomato-restaurant-recommendation"


def load_raw_dataframe() -> pd.DataFrame:
    """Fetch the Zomato dataset from Hugging Face and return as a DataFrame."""
    logger.info("Loading dataset from Hugging Face: %s", DATASET_ID)
    dataset = load_dataset(DATASET_ID, split="train")
    df = dataset.to_pandas()
    logger.info("Loaded %d raw rows with columns: %s", len(df), list(df.columns))
    return df
