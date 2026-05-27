"""
Root Streamlit entry for Streamlit Community Cloud.

Set main file path to `streamlit_app.py` or `src/app/main.py` (both work).
"""

from __future__ import annotations

from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).parent / "src/app/main.py"), run_name="__main__")
