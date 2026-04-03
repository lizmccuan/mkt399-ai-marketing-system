"""Data Intake Agent."""

from __future__ import annotations

from typing import Any

import pandas as pd

from utils.parser import summarize_dataframe


def run_data_intake(
    ga4_pages_data: pd.DataFrame | None = None,
    ga4_source_data: pd.DataFrame | None = None,
    gsc_queries_data: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Structure the uploaded files into separate summaries plus a combined view."""
    ga4_pages_data = ga4_pages_data if ga4_pages_data is not None else pd.DataFrame()
    ga4_source_data = ga4_source_data if ga4_source_data is not None else pd.DataFrame()
    gsc_queries_data = gsc_queries_data if gsc_queries_data is not None else pd.DataFrame()

    ga4_pages_summary = summarize_dataframe(ga4_pages_data, "GA4 Page Title Report")
    ga4_source_summary = summarize_dataframe(ga4_source_data, "GA4 Session Source / Medium")
    gsc_queries_summary = summarize_dataframe(gsc_queries_data, "GSC Queries")

    top_pages = extract_top_rows(
        ga4_pages_data,
        label_keys=["page_title", "page_title_and_screen_class"],
        metric_keys=["active_users", "sessions", "views"],
        item_label="page_title",
    )
    top_sources = extract_top_rows(
        ga4_source_data,
        label_keys=["session_source_/_medium", "session_source_medium", "source_medium", "session_source", "source"],
        metric_keys=["sessions", "active_users", "new_users"],
        item_label="source_medium",
    )
    top_queries = extract_top_rows(
        gsc_queries_data,
        label_keys=["top_queries", "query", "queries", "search_query"],
        metric_keys=["clicks", "impressions"],
        item_label="query",
    )

    total_rows = len(ga4_pages_data) + len(ga4_source_data) + len(gsc_queries_data)

    print(f"[Data Intake] GA4 page rows: {ga4_pages_summary['rows']}")
    print(f"[Data Intake] GA4 source rows: {ga4_source_summary['rows']}")
    print(f"[Data Intake] GSC query rows: {gsc_queries_summary['rows']}")
    print(f"[Data Intake] Total rows entering workflow: {total_rows}")

    return {
        "agent": "data_intake",
        "summary": {
            "ga4_pages": ga4_pages_summary,
            "ga4_sources": ga4_source_summary,
            "gsc_queries": gsc_queries_summary,
            "ga4": ga4_pages_summary,
            "gsc": gsc_queries_summary,
            "combined": {
                "top_pages": top_pages,
                "top_traffic_sources": top_sources,
                "top_queries": top_queries,
                "total_rows": total_rows,
            },
            "total_rows": total_rows,
        },
        "notes": [
            "GA4 Page Title Report represents page-level behavior data.",
            "GA4 Session Source / Medium represents acquisition source data.",
            "GSC Queries represents search demand data from Google Search Console.",
        ],
    }


def extract_top_rows(
    dataframe: pd.DataFrame,
    label_keys: list[str],
    metric_keys: list[str],
    item_label: str,
) -> list[dict[str, Any]]:
    """Build a small top-items list that downstream agents can use directly."""
    if dataframe.empty:
        return []

    top_items = []

    for _, row in dataframe.head(10).iterrows():
        row_dict = row.fillna("").to_dict()
        label = first_value(row_dict, label_keys)
        metric_key = first_existing_key(row_dict, metric_keys)

        if not label or not metric_key:
            continue

        top_items.append(
            {
                item_label: str(label),
                "metric": metric_key,
                "value": to_number(row_dict.get(metric_key)),
            }
        )

    return sorted(top_items, key=lambda item: item["value"], reverse=True)[:5]


def first_value(record: dict[str, Any], keys: list[str]) -> Any:
    """Return the first non-empty value from a list of possible keys."""
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return value
    return None


def first_existing_key(record: dict[str, Any], keys: list[str]) -> str | None:
    """Return the first key that exists in the record."""
    for key in keys:
        if key in record:
            return key
    return None


def to_number(value: Any) -> float:
    """Convert common CSV values to a sortable number."""
    if value in (None, ""):
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    cleaned = str(value).replace(",", "").replace("%", "").strip()

    try:
        return float(cleaned)
    except ValueError:
        return 0.0
