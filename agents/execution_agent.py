"""Execution Agent."""

from __future__ import annotations

from typing import Any

from utils.parser import load_prompt


def run_execution_agent(strategy: dict[str, Any]) -> dict[str, Any]:
    """Convert strategy recommendations into example deliverables."""
    prompt_text = load_prompt("execution.txt")

    recommendations = strategy["strategy"]["recommendations"]

    execution_items = [
        {
            "asset_type": "SEO content brief",
            "title": "High-intent landing page refresh",
            "description": "Create or revise a landing page that targets a high-intent search theme.",
        },
        {
            "asset_type": "FAQ block",
            "title": "Answer common search questions",
            "description": "Add FAQ content to support search visibility and improve clarity for users.",
        },
        {
            "asset_type": "CTA test",
            "title": "Conversion improvement test",
            "description": "Test a clearer call to action on a page with existing traffic.",
        },
    ]

    return {
        "agent": "execution",
        "prompt_used": prompt_text,
        "input_agent": strategy["agent"],
        "execution_plan": execution_items,
        "source_recommendations": recommendations,
        "notes": [
            "The Execution Agent turns strategy into deliverables a marketer could use next.",
        ],
    }
