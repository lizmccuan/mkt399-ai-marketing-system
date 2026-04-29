"""Decision-rule loading and evaluation helpers."""

from __future__ import annotations

import json
from pathlib import Path

from services.scoring import calculate_rule_scores, to_numeric_score_value


def load_decision_rules(distilled_dir: Path) -> dict:
    """Load distilled decision rules from disk."""
    path = distilled_dir / "decision_rules.json"
    if not path.exists():
        return {"version": "1.0", "rules": []}

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def rule_matches(rule: dict, sample_data: dict) -> bool:
    """Evaluate whether one rule matches the current sample data."""
    conditions = rule.get("conditions", {}).get("all", [])
    for condition in conditions:
        field = condition["field"]
        operator = condition["operator"]
        value = condition["value"]

        if field not in sample_data:
            return False

        data_value = sample_data[field]
        if data_value is None:
            return False

        if operator == ">=" and not (data_value >= value):
            return False
        if operator == "<=" and not (data_value <= value):
            return False
        if operator == "==" and not (data_value == value):
            return False
        if operator == ">" and not (data_value > value):
            return False
        if operator == "<" and not (data_value < value):
            return False

    return True


def evaluate_decision_rules(decision_rules: list[dict], sample_data: dict) -> tuple[list[dict], list[dict]]:
    """Return triggered rules and generated recommendations for a run."""
    triggered_rules = [rule for rule in decision_rules if rule_matches(rule, sample_data)]

    generated_recommendations = []
    for rule in triggered_rules:
        score_bundle = calculate_rule_scores(rule, sample_data)
        generated_recommendations.append(
            {
                "title": rule.get("title"),
                "insight": rule.get("insight"),
                "why_it_matters": rule.get("why_it_matters"),
                "recommendation": rule.get("recommendation"),
                "priority": rule.get("priority"),
                "action_type": rule.get("action_type"),
                "confidence_score": score_bundle.get("confidence_score"),
                "opportunity_score": score_bundle.get("opportunity_score"),
                "business_impact_score": score_bundle.get("business_impact_score"),
            }
        )

    generated_recommendations = sorted(
        generated_recommendations,
        key=lambda item: (
            to_numeric_score_value(item.get("opportunity_score")) or 0,
            to_numeric_score_value(item.get("business_impact_score")) or 0,
            to_numeric_score_value(item.get("confidence_score")) or 0,
        ),
        reverse=True,
    )

    return triggered_rules, generated_recommendations
