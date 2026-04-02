"""Data Intake Agent."""

from __future__ import annotations

from typing import Any

import pandas as pd

from utils.parser import load_prompt, summarize_dataframe


def run_data_intake(ga4_data: pd.DataFrame | None = None, gsc_data: pd.DataFrame | None = None) -> dict[str, Any]:
    """Structure the raw GA4 and GSC data for the rest of the workflow."""
    ga4_data = ga4_data if ga4_data is not None else pd.DataFrame()
    gsc_data = gsc_data if gsc_data is not None else pd.DataFrame()

    prompt_text = load_prompt("data_intake.txt")

    combined_rows = len(ga4_data) + len(gsc_data)

    return {
        "agent": "data_intake",
        "prompt_used": prompt_text,
        "summary": {
            "ga4": summarize_dataframe(ga4_data, "GA4"),
            "gsc": summarize_dataframe(gsc_data, "GSC"),
            "total_rows": combined_rows,
        },
        "notes": [
            "M2M happens here: machine-generated CSV exports enter the workflow.",
            "The data was cleaned, labeled, and summarized for downstream agents.",
        ],
    }
