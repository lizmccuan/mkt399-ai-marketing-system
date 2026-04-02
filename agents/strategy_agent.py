"""Strategy Agent."""

from __future__ import annotations

from typing import Any

from utils.parser import load_prompt


def run_strategy_agent(insights: dict[str, Any]) -> dict[str, Any]:
    """Turn insights into a simple marketing strategy."""
    prompt_text = load_prompt("strategy.txt")

    recommendations = [
        "Prioritize search queries that suggest high intent and low current engagement.",
        "Refresh underperforming landing pages with clearer calls to action and FAQ content.",
        "Test one content update and one conversion improvement before scaling further changes.",
    ]

    return {
        "agent": "strategy",
        "prompt_used": prompt_text,
        "input_agent": insights["agent"],
        "based_on_insights": insights["insights"],
        "strategy": {
            "goal": "Improve organic visibility and convert more existing traffic.",
            "recommendations": recommendations,
        },
        "notes": [
            "The Strategy Agent receives Insight Agent output and turns it into action steps.",
        ],
    }
