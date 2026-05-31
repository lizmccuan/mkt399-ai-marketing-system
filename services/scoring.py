"""Scoring helpers for decision-rule recommendations."""

from __future__ import annotations

from typing import Any


PRIORITY_LEVEL_SCORES = {
    "critical": 96.0,
    "high": 84.0,
    "medium": 62.0,
    "low": 38.0,
}

IMPACT_LEVEL_SCORES = {
    "high": 88.0,
    "medium": 64.0,
    "low": 36.0,
}

EFFORT_LEVEL_SCORES = {
    "low": 86.0,
    "medium": 60.0,
    "high": 34.0,
}

URGENCY_LEVEL_SCORES = {
    "critical": 96.0,
    "high": 82.0,
    "medium": 58.0,
    "low": 34.0,
}


def to_numeric_score_value(value) -> float | None:
    """Convert score inputs into floats when possible."""
    if value is None:
        return None
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return None
    text = text.replace(",", "")
    if text.endswith("%"):
        text = text[:-1].strip()

    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def clamp_score(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    """Clamp a score into a 0-100 range."""
    return max(minimum, min(maximum, value))


def normalize_rule_ctr_value(value) -> float | None:
    """Normalize CTR into decimal form for rule scoring."""
    numeric_value = to_numeric_score_value(value)
    if numeric_value is None:
        return None
    return numeric_value / 100 if numeric_value > 1 else numeric_value


def calculate_rule_scores(rule: dict, sample_data: dict) -> dict[str, float]:
    """Score a triggered rule using strategic upside signals."""
    impressions = to_numeric_score_value(sample_data.get("impressions")) or 0
    ctr_decimal = normalize_rule_ctr_value(sample_data.get("ctr"))
    position = to_numeric_score_value(sample_data.get("position"))
    engagement_rate = to_numeric_score_value(sample_data.get("engagement_rate"))
    sessions = to_numeric_score_value(sample_data.get("sessions")) or 0
    conversions = to_numeric_score_value(sample_data.get("conversions")) or 0

    target_ctr_decimal = 0.05
    ctr_gap = max(0.0, target_ctr_decimal - ctr_decimal) if ctr_decimal is not None else 0.0

    impressions_score = clamp_score((impressions / 2000) * 100)
    ctr_gap_score = clamp_score((ctr_gap / target_ctr_decimal) * 100) if ctr_gap else 0.0
    if position is None:
        ranking_score = 35.0
    elif position <= 3:
        ranking_score = 95.0
    elif position <= 8:
        ranking_score = 82.0
    elif position <= 15:
        ranking_score = 72.0
    elif position <= 25:
        ranking_score = 55.0
    else:
        ranking_score = 35.0

    if engagement_rate is None:
        engagement_opportunity_score = 40.0
    else:
        engagement_opportunity_score = clamp_score(((0.65 - engagement_rate) / 0.65) * 100)

    session_score = clamp_score((sessions / 250) * 100)
    if sessions > 0:
        conversion_efficiency = conversions / sessions
        conversion_opportunity_score = clamp_score(((0.05 - conversion_efficiency) / 0.05) * 100)
    else:
        conversion_opportunity_score = 25.0

    available_inputs = [
        sample_data.get("impressions"),
        sample_data.get("ctr"),
        sample_data.get("position"),
        sample_data.get("engagement_rate"),
        sample_data.get("sessions"),
        sample_data.get("conversions"),
    ]
    data_completeness_score = (sum(value is not None for value in available_inputs) / len(available_inputs)) * 100
    matched_conditions = len(rule.get("conditions", {}).get("all", []))
    confidence_score = round(
        clamp_score((data_completeness_score * 0.65) + (min(matched_conditions, 3) / 3 * 35)),
        2,
    )

    opportunity_score = round(
        clamp_score(
            (impressions_score * 0.24)
            + (ctr_gap_score * 0.22)
            + (ranking_score * 0.18)
            + (engagement_opportunity_score * 0.14)
            + (session_score * 0.12)
            + (conversion_opportunity_score * 0.10)
        ),
        2,
    )

    business_impact_score = round(
        clamp_score(
            (impressions_score * 0.22)
            + (session_score * 0.26)
            + (conversion_opportunity_score * 0.22)
            + (engagement_opportunity_score * 0.12)
            + (ranking_score * 0.10)
            + (ctr_gap_score * 0.08)
        ),
        2,
    )

    return {
        "confidence_score": confidence_score,
        "opportunity_score": opportunity_score,
        "business_impact_score": business_impact_score,
    }


def _normalize_level(value: Any) -> str | None:
    """Normalize categorical priority inputs into lowercase tokens."""
    if value is None:
        return None

    text = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    return text or None


def _format_level_label(value: str | None, fallback: str) -> str:
    """Format a normalized level token for display."""
    if not value:
        return fallback
    return value.replace("_", " ").title()


def _score_from_level(value: str | None, score_map: dict[str, float], fallback: float) -> float:
    """Convert a normalized categorical label into a score."""
    if not value:
        return fallback
    return score_map.get(value, fallback)


def _extract_prioritization_rule(
    rule_match: dict,
    prioritization_rules: dict | list[dict] | None = None,
) -> dict | None:
    """Find a loose prioritization-framework match for a rule recommendation."""
    if isinstance(prioritization_rules, dict):
        candidate_rules = prioritization_rules.get("rules", []) or []
    elif isinstance(prioritization_rules, list):
        candidate_rules = prioritization_rules
    else:
        candidate_rules = []

    if not candidate_rules:
        return None

    category = _normalize_level(rule_match.get("category"))
    action_type = _normalize_level(rule_match.get("action_type"))
    priority = _normalize_level(rule_match.get("priority"))
    impact = _normalize_level(rule_match.get("impact"))
    effort = _normalize_level(rule_match.get("effort"))

    exact_candidates = []
    general_candidates = []
    for candidate_rule in candidate_rules:
        candidate_category = _normalize_level(candidate_rule.get("category"))
        candidate_priority = _normalize_level(candidate_rule.get("priority_level"))
        candidate_impact = _normalize_level(candidate_rule.get("impact"))
        candidate_effort = _normalize_level(candidate_rule.get("effort"))

        if candidate_category and candidate_category == category:
            exact_candidates.append(candidate_rule)
            continue
        if candidate_category and candidate_category == action_type:
            exact_candidates.append(candidate_rule)
            continue

        if priority and impact and effort:
            if candidate_priority == priority and candidate_impact == impact and candidate_effort == effort:
                general_candidates.append(candidate_rule)
                continue

        if candidate_category == "general_prioritization":
            general_candidates.append(candidate_rule)

    return exact_candidates[0] if exact_candidates else (general_candidates[0] if general_candidates else None)


def build_priority_bundle(
    rule_match: dict,
    prioritization_rules: dict | list[dict] | None = None,
) -> dict[str, Any]:
    """Build a normalized priority bundle for a rule-driven recommendation."""
    matched_prioritization_rule = _extract_prioritization_rule(rule_match, prioritization_rules)

    normalized_priority = _normalize_level(rule_match.get("priority"))
    normalized_impact = _normalize_level(rule_match.get("impact"))
    normalized_effort = _normalize_level(rule_match.get("effort"))
    normalized_category = _normalize_level(rule_match.get("category"))
    normalized_action_type = _normalize_level(rule_match.get("action_type"))

    fallback_priority = _normalize_level(matched_prioritization_rule.get("priority_level")) if matched_prioritization_rule else None
    fallback_impact = _normalize_level(matched_prioritization_rule.get("impact")) if matched_prioritization_rule else None
    fallback_effort = _normalize_level(matched_prioritization_rule.get("effort")) if matched_prioritization_rule else None
    normalized_urgency = (
        _normalize_level(matched_prioritization_rule.get("urgency")) if matched_prioritization_rule else None
    )

    priority_level = normalized_priority or fallback_priority or "medium"
    impact_level = normalized_impact or fallback_impact or "medium"
    effort_level = normalized_effort or fallback_effort or "medium"
    urgency_level = normalized_urgency or ("high" if priority_level in {"high", "critical"} else "medium")

    opportunity_score = to_numeric_score_value(rule_match.get("opportunity_score"))
    business_impact_score = to_numeric_score_value(rule_match.get("business_impact_score"))
    confidence_score = to_numeric_score_value(rule_match.get("confidence_score"))

    priority_level_score = _score_from_level(priority_level, PRIORITY_LEVEL_SCORES, 62.0)
    impact_score = business_impact_score
    if impact_score is None:
        impact_score = _score_from_level(impact_level, IMPACT_LEVEL_SCORES, 64.0)
        if opportunity_score is not None:
            impact_score = round((impact_score * 0.55) + (opportunity_score * 0.45), 2)
    else:
        impact_score = round(impact_score, 2)

    effort_score = round(_score_from_level(effort_level, EFFORT_LEVEL_SCORES, 60.0), 2)
    urgency_score = round(_score_from_level(urgency_level, URGENCY_LEVEL_SCORES, 58.0), 2)
    confidence_score = round(confidence_score if confidence_score is not None else 55.0, 2)

    priority_score = round(
        clamp_score(
            (impact_score * 0.36)
            + (urgency_score * 0.24)
            + (confidence_score * 0.22)
            + (effort_score * 0.10)
            + (priority_level_score * 0.08)
        ),
        2,
    )

    rationale_parts = [
        f"Priority normalized from {_format_level_label(priority_level, 'Medium')}.",
        f"Impact assessed as {_format_level_label(impact_level, 'Medium')}.",
        f"Effort assessed as {_format_level_label(effort_level, 'Medium')}.",
        f"Urgency assessed as {_format_level_label(urgency_level, 'Medium')}.",
    ]

    if matched_prioritization_rule:
        rationale_parts.append(
            f"Aligned with prioritization rule '{matched_prioritization_rule.get('id', 'matched_rule')}'."
        )
    elif normalized_category or normalized_action_type:
        source_label = _format_level_label(normalized_category or normalized_action_type, "general")
        rationale_parts.append(f"Used default prioritization guidance for {source_label}.")
    else:
        rationale_parts.append("Used safe default prioritization guidance.")

    return {
        "priority_score": priority_score,
        "priority_level": _format_level_label(priority_level, "Medium"),
        "impact_score": impact_score,
        "effort_score": effort_score,
        "urgency_score": urgency_score,
        "confidence_score": confidence_score,
        "rationale": " ".join(rationale_parts),
    }
