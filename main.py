"""Main workflow runner for the AI Marketing Workflow System."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from agents.data_intake import run_data_intake
from agents.evaluation_agent import run_evaluation_agent
from agents.execution_agent import run_execution_agent
from agents.insight_agent import run_insight_agent
from agents.strategy_agent import run_strategy_agent
from utils.parser import parse_csv_file


LOG_FILE = Path("logs/workflow_runs.csv")
LOG_HEADERS = [
    "run_id",
    "timestamp",
    "ga4_rows",
    "gsc_rows",
    "insight_count",
    "strategy_goal",
    "execution_count",
    "evaluation_score",
]


def ensure_log_file() -> None:
    """Create the workflow log file with headers if it does not exist yet."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    # If the file already exists, keep it only when the header matches the new MVP format.
    if LOG_FILE.exists() and LOG_FILE.stat().st_size > 0:
        with LOG_FILE.open("r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            existing_headers = next(reader, [])

        if existing_headers == LOG_HEADERS:
            return

    with LOG_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=LOG_HEADERS)
        writer.writeheader()


def log_workflow_run(results: dict[str, Any]) -> None:
    """Save a workflow run summary to logs/workflow_runs.csv."""
    ensure_log_file()

    intake = results["data_intake"]["summary"]
    strategy = results["strategy"]["strategy"]
    evaluation = results["evaluation"]["evaluation"]

    row = {
        "run_id": results["run_id"],
        "timestamp": results["timestamp"],
        "ga4_rows": intake["ga4"]["rows"],
        "gsc_rows": intake["gsc"]["rows"],
        "insight_count": len(results["insight"]["insights"]),
        "strategy_goal": strategy["goal"],
        "execution_count": len(results["execution"]["execution_plan"]),
        "evaluation_score": evaluation["score"],
    }

    with LOG_FILE.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=LOG_HEADERS)
        writer.writerow(row)


def run_workflow(ga4_data: pd.DataFrame | None = None, gsc_data: pd.DataFrame | None = None) -> dict[str, Any]:
    """Run the full agent workflow in order and return all outputs."""
    print("Starting AI Marketing Workflow...\n")

    # Step 1: structure the uploaded marketing data.
    data = run_data_intake(ga4_data=ga4_data, gsc_data=gsc_data)
    print("Data Intake Complete\n")

    # Step 2: generate simple findings from the structured data.
    insights = run_insight_agent(data)
    print("Insight Agent Complete\n")

    # Step 3: turn the findings into a starter strategy.
    strategy = run_strategy_agent(insights)
    print("Strategy Agent Complete\n")

    # Step 4: turn the strategy into sample marketing deliverables.
    execution = run_execution_agent(strategy)
    print("Execution Agent Complete\n")

    # Step 5: score and summarize the workflow output.
    evaluation = run_evaluation_agent(execution)
    print("Evaluation Agent Complete\n")

    results = {
        "run_id": datetime.now().strftime("run_%Y%m%d_%H%M%S"),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "data_intake": data,
        "insight": insights,
        "strategy": strategy,
        "execution": execution,
        "evaluation": evaluation,
    }

    log_workflow_run(results)

    print("\nFINAL OUTPUT:")
    print(json.dumps(results["evaluation"], indent=2))

    return results


if __name__ == "__main__":
    default_ga4 = Path("data/ga4.csv")
    default_gsc = Path("data/gsc.csv")

    # If local sample files exist, the CLI runner will use them automatically.
    ga4_data = parse_csv_file(str(default_ga4), "GA4") if default_ga4.exists() else pd.DataFrame()
    gsc_data = parse_csv_file(str(default_gsc), "GSC") if default_gsc.exists() else pd.DataFrame()

    run_workflow(ga4_data=ga4_data, gsc_data=gsc_data)
