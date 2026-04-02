"""Evaluation Agent."""

from __future__ import annotations

from typing import Any

from utils.parser import load_prompt


def run_evaluation_agent(execution: dict[str, Any]) -> dict[str, Any]:
    """Review the execution output and return a simple score."""
    prompt_text = load_prompt("evaluation.txt")
    execution_count = len(execution["execution_plan"])

    score = min(10, 6 + execution_count)

    return {
        "agent": "evaluation",
        "prompt_used": prompt_text,
        "input_agent": execution["agent"],
        "evaluation": {
            "score": score,
            "summary": "The workflow produced usable placeholder outputs that are ready for human review.",
            "strengths": [
                "All agents ran in sequence without manual handoff.",
                "The system captured simple marketing recommendations and execution items.",
            ],
            "next_steps": [
                "Replace placeholder logic with real scoring rules or API-based LLM calls.",
                "Expand parsing to detect specific GA4 and GSC metrics automatically.",
            ],
        },
        "notes": [
            "The Evaluation Agent checks the output from Execution and closes the workflow loop.",
        ],
    }
