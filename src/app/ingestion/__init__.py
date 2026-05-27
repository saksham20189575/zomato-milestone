"""Data ingestion pipeline (HF load → normalize → parquet).

Import submodules directly, e.g. ``from app.ingestion.pipeline import run_ingestion``.
Avoid eager imports here so Streamlit runtime does not require the ``datasets`` package.
"""
