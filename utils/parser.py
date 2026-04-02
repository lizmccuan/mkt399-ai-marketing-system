"""Parser utilities for handling GA4 and GSC CSV data."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd


def load_prompt(prompt_name: str) -> str:
    """Load prompt text from the prompts folder."""
    prompt_path = Path("prompts") / prompt_name

    if not prompt_path.exists():
        return f"Prompt file not found: {prompt_name}"

    return prompt_path.read_text(encoding="utf-8").strip()


def parse_uploaded_csv(file_obj: Any, source_name: str) -> pd.DataFrame:
    """Convert an uploaded Streamlit file into a pandas DataFrame."""
    if file_obj is None:
        return pd.DataFrame()

    text_data = file_obj.getvalue().decode("utf-8")
    dataframe = pd.read_csv(StringIO(text_data))
    return clean_marketing_dataframe(dataframe, source_name)


def parse_csv_file(file_path: str, source_name: str) -> pd.DataFrame:
    """Load a CSV file from disk and return a cleaned DataFrame."""
    dataframe = pd.read_csv(file_path)
    return clean_marketing_dataframe(dataframe, source_name)


def clean_marketing_dataframe(dataframe: pd.DataFrame, source_name: str) -> pd.DataFrame:
    """Apply a few beginner-friendly cleanup steps to marketing data."""
    cleaned = dataframe.copy()

    # Standardize column names so later steps are easier to write.
    cleaned.columns = [str(column).strip().lower().replace(" ", "_") for column in cleaned.columns]

    # Remove fully empty rows that sometimes appear in exported CSV files.
    cleaned = cleaned.dropna(how="all")

    # Add a source column so the workflow can tell GA4 and GSC apart later.
    cleaned["data_source"] = source_name

    return cleaned


def summarize_dataframe(dataframe: pd.DataFrame, label: str) -> dict[str, Any]:
    """Build a compact summary of a DataFrame for the agents."""
    if dataframe.empty:
        return {
            "label": label,
            "rows": 0,
            "columns": [],
            "sample_records": [],
        }

    return {
        "label": label,
        "rows": int(len(dataframe)),
        "columns": list(dataframe.columns),
        "sample_records": dataframe.head(5).fillna("").to_dict(orient="records"),
    }
