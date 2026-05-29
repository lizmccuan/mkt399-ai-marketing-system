"""Decision-rule loading and evaluation helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

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


def evaluate_workflow_rule_matches(
    decision_rules: list[dict],
    data: dict,
    insights: dict,
    *,
    semrush_positions_data=None,
    semrush_pages_data=None,
    semrush_topics_data=None,
    meta_posts_data=None,
) -> dict:
    """Evaluate decision rules across workflow-ready structured marketing datasets."""
    matches_by_section = {
        "gsc_queries": [],
        "ga4_pages": [],
        "ga4_sources": [],
        "semrush_positions": [],
        "semrush_pages": [],
        "semrush_topics": [],
        "social": [],
    }

    for label, payload in _build_gsc_query_payloads(data, insights):
        matches_by_section["gsc_queries"].extend(_evaluate_payload(decision_rules, label, payload, "gsc_queries"))

    for label, payload in _build_ga4_page_payloads(data):
        matches_by_section["ga4_pages"].extend(_evaluate_payload(decision_rules, label, payload, "ga4_pages"))

    for label, payload in _build_ga4_source_payloads(data):
        matches_by_section["ga4_sources"].extend(_evaluate_payload(decision_rules, label, payload, "ga4_sources"))

    for label, payload in _build_semrush_position_payloads(semrush_positions_data):
        matches_by_section["semrush_positions"].extend(
            _evaluate_payload(decision_rules, label, payload, "semrush_positions")
        )

    for label, payload in _build_semrush_page_payloads(semrush_pages_data):
        matches_by_section["semrush_pages"].extend(_evaluate_payload(decision_rules, label, payload, "semrush_pages"))

    for label, payload in _build_semrush_topic_payloads(semrush_topics_data):
        matches_by_section["semrush_topics"].extend(_evaluate_payload(decision_rules, label, payload, "semrush_topics"))

    for label, payload in _build_social_payloads(meta_posts_data):
        matches_by_section["social"].extend(_evaluate_payload(decision_rules, label, payload, "social"))

    all_matches = []
    for section_name, section_matches in matches_by_section.items():
        for match in section_matches:
            match["section"] = section_name
            all_matches.append(match)

    all_matches = sorted(
        all_matches,
        key=lambda item: (
            to_numeric_score_value(item.get("opportunity_score")) or 0,
            to_numeric_score_value(item.get("business_impact_score")) or 0,
            to_numeric_score_value(item.get("confidence_score")) or 0,
        ),
        reverse=True,
    )

    return {
        "sections": matches_by_section,
        "all_matches": all_matches,
        "match_count": len(all_matches),
    }


def _evaluate_payload(decision_rules: list[dict], label: str, sample_data: dict, source_type: str) -> list[dict]:
    """Evaluate one normalized payload against the rule set."""
    triggered_rules, generated_recommendations = evaluate_decision_rules(decision_rules, sample_data)
    matches = []

    for rule, recommendation in zip(triggered_rules, generated_recommendations):
        matches.append(
            {
                "source_type": source_type,
                "label": label,
                "rule_id": rule.get("id"),
                "category": rule.get("category"),
                "title": recommendation.get("title"),
                "insight": recommendation.get("insight"),
                "why_it_matters": recommendation.get("why_it_matters"),
                "recommendation": recommendation.get("recommendation"),
                "priority": recommendation.get("priority"),
                "action_type": recommendation.get("action_type"),
                "confidence_score": recommendation.get("confidence_score"),
                "opportunity_score": recommendation.get("opportunity_score"),
                "business_impact_score": recommendation.get("business_impact_score"),
                "sample_data": sample_data,
            }
        )

    return matches


def _first_available(record: dict, keys: list[str]):
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return value
    return None


def _build_gsc_query_payloads(data: dict, insights: dict) -> list[tuple[str, dict]]:
    payloads = []
    query_analysis = insights.get("query_analysis", []) or []
    non_branded_queries = insights.get("non_branded_queries", []) or []
    non_branded_impressions = sum(to_numeric_score_value(item.get("impressions")) or 0 for item in non_branded_queries)
    non_branded_ctr_values = [
        to_numeric_score_value(item.get("ctr"))
        for item in non_branded_queries
        if to_numeric_score_value(item.get("ctr")) is not None
    ]
    non_branded_ctr = (
        round(sum(non_branded_ctr_values) / len(non_branded_ctr_values), 2)
        if non_branded_ctr_values
        else None
    )
    keyword_gap_count = len(insights.get("high_impression_low_click", []) or [])
    topic_opportunity_count = len(insights.get("aligned_pages", []) or [])

    for item in query_analysis:
        query = str(item.get("query", "")).strip()
        if not query:
            continue
        payloads.append(
            (
                query,
                {
                    "impressions": to_numeric_score_value(item.get("impressions")),
                    "ctr": to_numeric_score_value(item.get("ctr")),
                    "position": to_numeric_score_value(item.get("position")),
                    "non_branded_impressions": non_branded_impressions or None,
                    "non_branded_ctr": non_branded_ctr,
                    "keyword_gap_count": keyword_gap_count or None,
                    "topic_opportunity_count": topic_opportunity_count or None,
                },
            )
        )

    return payloads


def _build_ga4_page_payloads(data: dict) -> list[tuple[str, dict]]:
    payloads = []
    sample_records = data.get("summary", {}).get("ga4_pages", {}).get("sample_records", []) or []

    for record in sample_records:
        label = _first_available(record, ["page_title", "page_title_and_screen_class"])
        if not label:
            continue
        payloads.append(
            (
                str(label),
                {
                    "sessions": to_numeric_score_value(record.get("sessions")),
                    "active_users": to_numeric_score_value(record.get("active_users")),
                    "engagement_rate": to_numeric_score_value(record.get("engagement_rate")),
                    "conversions": to_numeric_score_value(record.get("conversions")) or 0,
                },
            )
        )

    return payloads


def _build_ga4_source_payloads(data: dict) -> list[tuple[str, dict]]:
    payloads = []
    sample_records = data.get("summary", {}).get("ga4_sources", {}).get("sample_records", []) or []
    session_values = [to_numeric_score_value(record.get("sessions")) or 0 for record in sample_records]
    total_sessions = sum(session_values)

    for record, session_value in zip(sample_records, session_values):
        label = _first_available(
            record,
            ["session_source_/_medium", "session_source_medium", "source_medium", "session_source", "source"],
        )
        if not label:
            continue
        top_source_share = (session_value / total_sessions) if total_sessions > 0 else None
        payloads.append(
            (
                str(label),
                {
                    "sessions": session_value or None,
                    "active_users": to_numeric_score_value(record.get("active_users")),
                    "engagement_rate": to_numeric_score_value(record.get("engagement_rate")),
                    "conversions": to_numeric_score_value(record.get("conversions")) or 0,
                    "top_source_share": top_source_share,
                },
            )
        )

    return payloads


def _build_semrush_position_payloads(dataframe) -> list[tuple[str, dict]]:
    if dataframe is None or getattr(dataframe, "empty", True):
        return []

    payloads = []
    for _, row in dataframe.head(50).iterrows():
        label = str(row.get("keyword", "")).strip()
        if not label:
            continue
        payloads.append(
            (
                label,
                {
                    "impressions": to_numeric_score_value(row.get("volume")),
                    "position": to_numeric_score_value(row.get("position")),
                    "keyword_gap_count": to_numeric_score_value(row.get("keyword_gap_count")),
                },
            )
        )

    return payloads


def _build_semrush_page_payloads(dataframe) -> list[tuple[str, dict]]:
    if dataframe is None or getattr(dataframe, "empty", True):
        return []

    payloads = []
    for _, row in dataframe.head(25).iterrows():
        label = str(_first_available(row.to_dict(), ["page", "page_url", "url", "page_title"]) or "").strip()
        if not label:
            continue
        payloads.append(
            (
                label,
                {
                    "sessions": to_numeric_score_value(row.get("traffic")) or to_numeric_score_value(row.get("value")),
                    "engagement_rate": to_numeric_score_value(row.get("engagement_rate")),
                    "conversions": to_numeric_score_value(row.get("conversions")) or 0,
                },
            )
        )

    return payloads


def _build_semrush_topic_payloads(dataframe) -> list[tuple[str, dict]]:
    if dataframe is None or getattr(dataframe, "empty", True):
        return []

    payloads = []
    topic_opportunity_count = min(len(dataframe.index), 25)
    for _, row in dataframe.head(25).iterrows():
        label = str(_first_available(row.to_dict(), ["topic", "keyword", "page"]) or "").strip()
        if not label:
            continue
        payloads.append(
            (
                label,
                {
                    "impressions": to_numeric_score_value(row.get("volume")),
                    "position": to_numeric_score_value(row.get("position")),
                    "topic_opportunity_count": topic_opportunity_count,
                },
            )
        )

    return payloads


def _build_social_payloads(dataframe) -> list[tuple[str, dict]]:
    if dataframe is None or getattr(dataframe, "empty", True):
        return []

    payloads = []
    social_df = dataframe.copy()
    social_df.columns = [str(column).strip().lower().replace(" ", "_") for column in social_df.columns]

    for column in ["reach", "engagement_rate", "follows", "saves"]:
        if column in social_df.columns:
            social_df[column] = pd.to_numeric(social_df[column], errors="coerce")

    for _, row in social_df.head(25).iterrows():
        label = str(_first_available(row.to_dict(), ["hook", "caption", "post_type", "topic"]) or "").strip()
        if not label:
            label = "Social content"
        payloads.append(
            (
                label,
                {
                    "reach": to_numeric_score_value(row.get("reach")),
                    "engagement_rate": to_numeric_score_value(row.get("engagement_rate")),
                    "conversions": to_numeric_score_value(row.get("follows")) or 0,
                },
            )
        )

    return payloads
