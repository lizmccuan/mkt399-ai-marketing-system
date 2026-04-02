"""Insight Agent."""

from __future__ import annotations

from typing import Any

from utils.parser import load_prompt


def run_insight_agent(data: dict[str, Any]) -> dict[str, Any]:
    """Analyze structured data and produce simple insights."""
    prompt_text = load_prompt("insight.txt")
    ga4_summary = data["summary"]["ga4"]
    gsc_summary = data["summary"]["gsc"]

    insights = []

    if ga4_summary["rows"] == 0:
        insights.append("GA4 data is missing, so traffic analysis is limited.")
    else:
        insights.append(f"GA4 upload includes {ga4_summary['rows']} rows of analytics data.")

    if gsc_summary["rows"] == 0:
        insights.append("GSC data is missing, so search opportunity analysis is limited.")
    else:
        insights.append(f"GSC upload includes {gsc_summary['rows']} rows of search performance data.")

    if ga4_summary["rows"] > 0 and gsc_summary["rows"] > 0:
        insights.append("Both data sources are available, so cross-channel analysis can be simulated.")

    insights.append("Placeholder insight: focus on pages and queries with visibility but weaker engagement.")

    return {
        "agent": "insight",
        "prompt_used": prompt_text,
        "input_agent": data["agent"],
        "insights": insights,
        "notes": [
            "A2A happens here: the Insight Agent uses the structured output from Data Intake.",
        ],
    }
