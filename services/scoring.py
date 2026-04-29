"""Scoring helpers for decision-rule recommendations."""

from __future__ import annotations


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
