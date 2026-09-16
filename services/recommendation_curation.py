"""User-facing recommendation curation helpers.

Raw rule matches are diagnostic evidence. This module groups those matches into
distinct strategic actions for the Recommendations experience.
"""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from services.scoring import clamp_score, to_numeric_score_value


MAX_USER_FACING_RECOMMENDATIONS = 20
PREFERRED_USER_FACING_RECOMMENDATIONS = 12

GSC_MEANINGFUL_IMPRESSIONS = 50
GSC_STRONG_IMPRESSIONS = 250
GSC_MAJOR_IMPRESSIONS = 1000

CONFIDENCE_BY_EVIDENCE_TIER = {
    "very_small": 50.0,
    "small": 65.0,
    "meaningful": 80.0,
    "strong": 90.0,
}


ACTION_FAMILY_LABELS = {
    "SEO_CTR": "CTR Opportunity",
    "SEO_RANKING_GROWTH": "Ranking Growth Opportunity",
    "SEO_CONTENT_EXPANSION": "Content Expansion Opportunity",
    "SEO_TRUE_KEYWORD_GAP": "Keyword Gap",
    "LOCAL_SEARCH": "Local Search",
    "UX_CRO": "UX/CRO",
    "ANALYTICS": "Analytics",
    "SOCIAL_CONTENT": "Social Content",
    "SOCIAL_NEXT_STEP": "Social Next Step",
    "OTHER": "Recommendation",
}


PRIORITY_RANK = {"High": 3, "Medium": 2, "Low": 1}


def normalize_text(value: object) -> str:
    """Normalize text for stable comparison without importing Streamlit UI code."""
    text = str(value or "").strip().lower()
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def display_text(value: object) -> str:
    """Normalize user-facing whitespace."""
    return re.sub(r"\s+", " ", str(value or "").strip())


def page_asset_label(item: dict[str, Any]) -> str:
    """Return a concise known page/entity label without inventing a URL."""
    evidence = evidence_for_item(item)
    sample_data = item.get("sample_data") if isinstance(item.get("sample_data"), dict) else {}
    for source, keys in [
        (evidence, ["page_title", "page", "subject", "target"]),
        (sample_data, ["page_title", "page", "subject", "target"]),
        (item, ["subject", "target"]),
    ]:
        if not isinstance(source, dict):
            continue
        for key in keys:
            value = display_text(source.get(key))
            if value:
                return display_text(value.split("|")[0])
    return ""


def category_for_item(item: dict[str, Any]) -> str:
    """Map an item into the client-facing recommendation category."""
    source = normalize_text(item.get("source"))
    source_type = normalize_text(item.get("source_type"))
    action_type = normalize_text(item.get("action_type"))
    category = normalize_text(item.get("category"))
    tab = display_text(item.get("tab"))
    evidence = item.get("evidence") if isinstance(item.get("evidence"), dict) else {}
    content = " ".join(
        normalize_text(item.get(key))
        for key in ["title", "issue", "insight", "recommendation", "opportunity_type"]
    )

    if source in {"gsc", "google search console", "keyword", "semrush"}:
        return "SEO"
    if any(key in evidence for key in ["ctr", "impressions", "position", "clicks"]):
        return "SEO"
    if source_type in {"ga4_sources", "ga4 sources"}:
        return "Analytics"
    if source in {"meta", "facebook", "instagram", "meta social analytics"} or action_type.startswith("social"):
        return "Social"
    if action_type in {"ux conversion", "website ux conversion", "ux cro"} or "cro" in content:
        return "UX/CRO"
    if action_type in {"geo", "local", "local seo"} or category == "local seo":
        return "Local SEO"
    if action_type in {"analytics", "measurement", "tracking"}:
        return "Analytics"
    return tab if tab in {"SEO", "UX/CRO", "Local SEO", "Social", "Analytics"} else "SEO"


def evidence_for_item(item: dict[str, Any]) -> dict[str, Any]:
    """Return the explicit metric evidence on a recommendation-like item."""
    return item.get("evidence") if isinstance(item.get("evidence"), dict) else {}


def metric_value(item: dict[str, Any], key: str) -> float | None:
    """Read a numeric metric from explicit evidence first, then item-level fields."""
    evidence = evidence_for_item(item)
    if key in evidence:
        return to_numeric_score_value(evidence.get(key))
    return to_numeric_score_value(item.get(key))


def gsc_evidence_tier(item: dict[str, Any]) -> str:
    """Classify query evidence by observed sample magnitude."""
    if category_for_item(item) != "SEO":
        return "not_gsc"
    impressions = metric_value(item, "impressions")
    if impressions is None:
        return "limited"
    if impressions < GSC_MEANINGFUL_IMPRESSIONS:
        return "very_small"
    if impressions < GSC_STRONG_IMPRESSIONS:
        return "small"
    if impressions < GSC_MAJOR_IMPRESSIONS:
        return "meaningful"
    return "strong"


def evidence_tier_for_volume(value: float | None) -> str:
    """Classify source-specific evidence volume with the shared internal tiers."""
    if value is None:
        return "limited"
    if value < GSC_MEANINGFUL_IMPRESSIONS:
        return "very_small"
    if value < GSC_STRONG_IMPRESSIONS:
        return "small"
    if value < GSC_MAJOR_IMPRESSIONS:
        return "meaningful"
    return "strong"


def has_conversion_evidence(item: dict[str, Any]) -> bool:
    """Return true only when real conversion/funnel evidence is present."""
    evidence = evidence_for_item(item)
    for key in ["conversions", "conversion_rate", "leads", "bookings", "revenue"]:
        value = evidence.get(key, item.get(key))
        numeric = to_numeric_score_value(value)
        if numeric is not None and numeric > 0:
            return True
    return False


def has_true_keyword_gap_evidence(item: dict[str, Any]) -> bool:
    """Gate keyword/content-gap language behind explicit coverage or gap evidence."""
    source = normalize_text(item.get("source"))
    source_type = normalize_text(item.get("source_type"))
    evidence = evidence_for_item(item)
    content = " ".join(
        normalize_text(item.get(key))
        for key in ["rule_id", "title", "issue", "insight", "recommendation", "supporting_evidence"]
    )
    if source in {"semrush"} or source_type.startswith("semrush"):
        return True
    explicit_keys = [
        "keyword_gap_count",
        "content_gap_count",
        "missing_coverage_count",
        "coverage_gap",
        "competitor_keywords",
    ]
    if any(to_numeric_score_value(evidence.get(key)) for key in explicit_keys):
        return True
    return any(token in content for token in ["semrush", "coverage analysis"])


def has_direct_schema_or_authority_evidence(item: dict[str, Any]) -> bool:
    """Detect direct support for schema, authority, or AI-citation assertions."""
    evidence = evidence_for_item(item)
    sample_data = item.get("sample_data") if isinstance(item.get("sample_data"), dict) else {}
    direct_keys = [
        "schema_errors",
        "schema_present",
        "faq_schema_present",
        "citations",
        "citation_count",
        "ai_citations",
        "authority_score",
        "backlinks",
        "entity_consistency_score",
    ]
    return any(key in evidence or key in sample_data for key in direct_keys)


def social_observation_count(item: dict[str, Any]) -> int:
    """Estimate whether social claims come from one post or a broader sample."""
    evidence = evidence_for_item(item)
    for key in ["posts_analyzed", "post_count", "observations"]:
        value = to_numeric_score_value(evidence.get(key, item.get(key)))
        if value is not None:
            return int(value)
    related = item.get("_related_items") if isinstance(item.get("_related_items"), list) else []
    if category_for_item(item) == "Social":
        return max(1, len(related) + 1)
    return 0


def action_family_for_item(item: dict[str, Any]) -> str:
    """Assign a strategic action family for conservative clustering."""
    category = category_for_item(item)
    source_type = normalize_text(item.get("source_type"))
    content = " ".join(
        normalize_text(item.get(key))
        for key in ["rule_id", "title", "issue", "insight", "recommendation", "action_type", "opportunity_type"]
    )
    evidence = evidence_for_item(item)

    if category == "Social":
        if any(token in content for token in ["cta", "next step", "conversion path", "follow"]):
            return "SOCIAL_NEXT_STEP"
        return "SOCIAL_CONTENT"
    if source_type in {"ga4_sources", "ga4 sources"} or category == "Analytics":
        return "ANALYTICS"
    if category == "UX/CRO":
        return "UX_CRO"
    if category == "Local SEO":
        return "LOCAL_SEARCH"

    if any(token in content for token in ["keyword gap", "content gap", "missing coverage"]):
        return "SEO_TRUE_KEYWORD_GAP" if has_true_keyword_gap_evidence(item) else "SEO_CONTENT_EXPANSION"
    if any(token in content for token in ["ctr", "click through", "click response", "click appeal", "title tag", "meta description", "snippet"]):
        return "SEO_CTR"
    if "position 6 15" in content or "ranking" in content or "rank" in content:
        return "SEO_RANKING_GROWTH"
    if any(key in evidence for key in ["position", "ctr", "impressions", "clicks"]):
        position = metric_value(item, "position")
        ctr = metric_value(item, "ctr")
        if position is not None and position <= 8 and (ctr is None or ctr <= 3):
            return "SEO_CTR"
        if position is not None and position <= 20:
            return "SEO_RANKING_GROWTH"
    return "OTHER"


def normalized_subject(item: dict[str, Any]) -> str:
    """Return a stable subject/entity key for grouping."""
    for key in ["subject", "target", "label"]:
        value = normalize_text(item.get(key))
        if value:
            return value
    title = normalize_text(item.get("title"))
    return " ".join(title.split()[:8])


def normalized_target_page(item: dict[str, Any]) -> str:
    """Return a target-page key when present."""
    evidence = evidence_for_item(item)
    for source in [item, evidence, item.get("sample_data") if isinstance(item.get("sample_data"), dict) else {}]:
        if not isinstance(source, dict):
            continue
        for key in ["url", "page", "page_url", "page_title", "landing_page"]:
            value = normalize_text(source.get(key))
            if value:
                return value
    return ""


def cluster_key_for_item(item: dict[str, Any]) -> tuple[str, str, str, str]:
    """Build a conservative grouping identity."""
    return (
        category_for_item(item),
        normalized_subject(item),
        normalized_target_page(item),
        action_family_for_item(item),
    )


def priority_label(item: dict[str, Any]) -> str:
    """Return normalized priority label."""
    priority = display_text(item.get("priority")).title()
    return priority if priority in PRIORITY_RANK else "Medium"


def priority_rank(item: dict[str, Any]) -> int:
    return PRIORITY_RANK.get(priority_label(item), 2)


def score_value(item: dict[str, Any], key: str) -> float:
    value = to_numeric_score_value(item.get(key))
    if value is None:
        bundle = item.get("priority_bundle") if isinstance(item.get("priority_bundle"), dict) else {}
        value = to_numeric_score_value(bundle.get(key))
    return value or 0.0


def evidence_quality_score(item: dict[str, Any]) -> float:
    """Score evidence quality for representative selection and queue ranking."""
    category = category_for_item(item)
    score = 0.0
    evidence = evidence_for_item(item)
    score += min(len([value for value in evidence.values() if value not in (None, "")]) * 8, 32)

    if category == "SEO":
        impressions = metric_value(item, "impressions") or 0
        position = metric_value(item, "position")
        ctr = metric_value(item, "ctr")
        if impressions >= GSC_MAJOR_IMPRESSIONS:
            score += 42
        elif impressions >= GSC_STRONG_IMPRESSIONS:
            score += 30
        elif impressions >= GSC_MEANINGFUL_IMPRESSIONS:
            score += 18
        elif impressions > 0:
            score += 4
        if position is not None and position <= 10:
            score += 18
        elif position is not None and position <= 20:
            score += 10
        if ctr is not None and ctr <= 3:
            score += 12
        if action_family_for_item(item) == "SEO_CONTENT_EXPANSION" and not has_true_keyword_gap_evidence(item):
            score -= 28
    elif category == "Social":
        observations = social_observation_count(item)
        score += 18 if observations >= 3 else 6
        score += min((metric_value(item, "reach") or 0) / 1000 * 10, 20)
    elif category == "Analytics":
        score += min((metric_value(item, "sessions") or 0) / 250 * 28, 28)
        if metric_value(item, "engagement_rate") is not None:
            score += 10
    else:
        score += min((metric_value(item, "sessions") or 0) / 250 * 35, 35)
        if has_conversion_evidence(item):
            score += 12

    if action_family_for_item(item) in {"SEO_TRUE_KEYWORD_GAP", "SEO_CTR", "UX_CRO", "SOCIAL_CONTENT"}:
        score += 8
    return score


def dampened_priority(item: dict[str, Any]) -> str:
    """Apply conservative presentation priority safeguards."""
    priority = priority_label(item)
    family = action_family_for_item(item)
    category = category_for_item(item)
    content = " ".join(
        normalize_text(item.get(key))
        for key in ["rule_id", "title", "issue", "insight", "recommendation"]
    )

    if category == "SEO" and gsc_evidence_tier(item) in {"very_small", "small", "limited"} and priority == "High":
        return "Medium"
    if category == "Analytics" and priority == "High":
        return "Medium"
    if family == "SEO_CONTENT_EXPANSION" and any(token in content for token in ["keyword gap", "content gap", "missing coverage"]):
        return "Medium" if priority == "High" else priority
    if any(token in content for token in ["schema", "citation", "authority", "entity"]) and not has_direct_schema_or_authority_evidence(item):
        return "Medium" if priority == "High" else priority
    if category in {"UX/CRO", "Social", "Analytics"} and "conversion" in content and not has_conversion_evidence(item):
        return "Medium" if priority == "High" else priority
    return priority


def sanitize_claim_language(item: dict[str, Any]) -> dict[str, Any]:
    """Conservatively rewrite unsupported user-facing claims while retaining evidence."""
    cleaned = deepcopy(item)
    family = action_family_for_item(cleaned)
    category = category_for_item(cleaned)
    title = display_text(cleaned.get("title"))
    recommendation = display_text(cleaned.get("recommendation"))
    why = display_text(cleaned.get("why_it_matters"))
    issue = display_text(cleaned.get("issue"))

    if family == "SEO_CONTENT_EXPANSION" and not has_true_keyword_gap_evidence(cleaned):
        for field_name, value in [
            ("title", title),
            ("recommendation", recommendation),
            ("why_it_matters", why),
            ("issue", issue),
        ]:
            value = re.sub(r"\b(keyword|content)\s+gap\b", "search opportunity", value, flags=re.IGNORECASE)
            value = re.sub(r"\bmissing coverage\b", "additional coverage", value, flags=re.IGNORECASE)
            cleaned[field_name] = value
        if "gap" in normalize_text(title):
            cleaned["title"] = f"{ACTION_FAMILY_LABELS[family]}: {display_text(cleaned.get('subject')) or 'Search Opportunity'}"

    if not has_conversion_evidence(cleaned):
        replacements = {
            r"\bconversion rate\b": "next-step response",
            r"\bconversions\b": "next-step actions",
            r"\bconverts\b": "encourages the next step",
            r"\bconversion\b": "next-step",
            r"\bdrive leads\b": "encourage qualified actions",
            r"\bdrives leads\b": "encourages qualified actions",
            r"\bdrives bookings\b": "encourages appointment interest",
            r"\bgenerates customers\b": "supports audience action",
        }
        for field_name in ["title", "recommendation", "why_it_matters", "issue"]:
            value = display_text(cleaned.get(field_name))
            for pattern, replacement in replacements.items():
                value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)
            cleaned[field_name] = value

    if category == "Social" and social_observation_count(cleaned) < 3:
        cautious_replacements = {
            r"\bwinning\b": "promising",
            r"\bbest-performing\b": "strong in the available sample",
            r"\bproven\b": "promising",
            r"\bscale\b": "test",
            r"\breplicate\b": "test a similar",
        }
        for field_name in ["title", "recommendation", "why_it_matters", "issue"]:
            value = display_text(cleaned.get(field_name))
            for pattern, replacement in cautious_replacements.items():
                value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)
            cleaned[field_name] = value

    cleaned["_original_priority"] = priority_label(cleaned)
    cleaned["priority"] = dampened_priority(cleaned)
    cleaned["_action_family"] = family
    cleaned["_evidence_tier"] = gsc_evidence_tier(cleaned)
    subject = display_text(cleaned.get("subject"))
    source_type = normalize_text(cleaned.get("source_type"))
    if family == "SEO_CTR" and subject:
        cleaned["title"] = f'Improve click-through for "{subject}"'
    elif family == "SEO_RANKING_GROWTH" and subject:
        cleaned["title"] = f'Improve ranking growth for "{subject}"'
    elif family == "SEO_CONTENT_EXPANSION" and subject and "schema" not in normalize_text(title):
        cleaned["title"] = f'Expand search coverage for "{subject}"'
    elif family == "ANALYTICS" and source_type in {"ga4_sources", "ga4 sources"} and subject:
        cleaned["title"] = f"Review engagement quality from {subject} traffic"
        cleaned["recommendation"] = (
            f"Compare campaign intent, audience, offer, landing experience, and on-site engagement for {subject} traffic."
        )
        cleaned["why_it_matters"] = (
            "When a traffic source brings sessions but engagement is weak, review whether the acquisition path and on-site experience align with visitor expectations."
        )
    elif family == "UX_CRO" and source_type in {"ga4_pages", "ga4 pages"}:
        asset_label = page_asset_label(cleaned)
        if asset_label and any(token in normalize_text(title) for token in ["weak page", "page refresh", "low engagement"]):
            cleaned["title"] = f"Review the {asset_label} page experience"
    return cleaned


def representative_sort_key(item: dict[str, Any]) -> tuple[float, float, float, float, int, int, str]:
    """Rank representatives inside a cluster."""
    direct_rule_bonus = 0
    content = " ".join(normalize_text(item.get(key)) for key in ["rule_id", "title"])
    if action_family_for_item(item) == "SEO_CTR" and any(
        token in content for token in ["ctr", "click", "high impressions", "high position", "position 6 15"]
    ):
        direct_rule_bonus = 20
    return (
        direct_rule_bonus,
        evidence_quality_score(item),
        score_value(item, "business_impact_score"),
        score_value(item, "opportunity_score"),
        score_value(item, "confidence_score"),
        priority_rank(item),
        len(display_text(item.get("recommendation"))),
        normalize_text(item.get("title")),
    )


def queue_sort_key(item: dict[str, Any]) -> tuple[float, int, float, float, float, str]:
    """Rank curated recommendations for the user-facing queue."""
    high_priority_bonus = 14 if priority_label(item) == "High" else 0
    return (
        evidence_quality_score(item) + high_priority_bonus,
        priority_rank(item),
        score_value(item, "business_impact_score"),
        score_value(item, "opportunity_score"),
        score_value(item, "confidence_score"),
        normalize_text(item.get("title")),
    )


def diversify_curated_queue(
    ranked: list[dict[str, Any]],
    *,
    preferred_items: int,
    max_items: int,
) -> list[dict[str, Any]]:
    """Keep the queue compact while preserving distinct channel actions."""
    selected: list[dict[str, Any]] = ranked[:preferred_items]
    selected_ids = {id(item) for item in selected}
    represented_categories = {category_for_item(item) for item in selected}

    for category in ["UX/CRO", "Social", "Local SEO", "Analytics"]:
        if category in represented_categories:
            continue
        candidate = next((item for item in ranked if id(item) not in selected_ids and category_for_item(item) == category), None)
        if candidate is None:
            continue
        selected.append(candidate)
        selected_ids.add(id(candidate))
        represented_categories.add(category)
        if len(selected) >= max_items:
            return selected
    return selected


def merge_related_items(representative: dict[str, Any], related_items: list[dict[str, Any]]) -> dict[str, Any]:
    """Attach related diagnostics to the displayed representative."""
    item = deepcopy(representative)
    existing_related = item.get("_related_items") if isinstance(item.get("_related_items"), list) else []
    related_by_id: dict[str, dict[str, Any]] = {}
    for related in existing_related + related_items:
        related_id = display_text(related.get("recommendation_id")) or "|".join(str(value) for value in cluster_key_for_item(related))
        if related_id != display_text(item.get("recommendation_id")):
            related_by_id[related_id] = related
    item["_related_items"] = list(related_by_id.values())
    item["_cluster_size"] = len(item["_related_items"]) + 1
    item["_cluster_key"] = cluster_key_for_item(item)
    return item


def query_tokens(value: object) -> list[str]:
    """Return deterministic search-query tokens for conservative intent checks."""
    text = normalize_text(value)
    joined_patterns = {
        "botoxsavingsprogram": "botox savings program",
        "botoxsavings": "botox savings",
    }
    for joined, spaced in joined_patterns.items():
        text = text.replace(joined, spaced)
    tokens = text.split()
    return [
        token
        for token in tokens
        if token
        and token
        not in {
            "the",
            "a",
            "an",
            "near",
            "me",
            "in",
            "il",
            "illinois",
            "chicago",
            "evergreen",
            "park",
            "westmont",
            "abbvie",
            "program",
            "official",
        }
    ]


def search_intent_key_for_query(value: object) -> str:
    """Build a conservative intent key for related query variants."""
    raw = normalize_text(value)
    tokens = query_tokens(raw)
    token_set = set(tokens)
    if {"botox", "savings"}.issubset(token_set):
        return "botox savings program"
    if {"migraine", "quiz"}.issubset(token_set):
        return "migraine quiz"
    if {"botox", "blepharospasm"}.issubset(token_set):
        return "botox blepharospasm"
    if "legit" in raw and {"headache", "clinic"}.issubset(token_set):
        return "headache clinic trust"
    if {"headache", "clinic"}.issubset(token_set):
        return "headache clinic"
    if {"headache", "labs"}.issubset(token_set):
        return "headache labs"
    return " ".join(tokens[:6])


def is_search_item(item: dict[str, Any]) -> bool:
    """Return true for query-level SEO recommendations that can be intent-clustered."""
    if category_for_item(item) != "SEO":
        return False
    if normalize_text(item.get("source")) not in {"gsc", "google search console", "keyword"}:
        return False
    return bool(normalized_subject(item))


def intent_consolidation_family(item: dict[str, Any]) -> str:
    """Collapse compatible search action families into one marketing decision."""
    family = str(item.get("_action_family") or action_family_for_item(item))
    if family in {"SEO_CTR", "SEO_RANKING_GROWTH"}:
        return "SEO_SEARCH_PERFORMANCE"
    return family


def intent_cluster_key_for_item(item: dict[str, Any]) -> tuple[str, str, str, str] | None:
    """Return a second-pass search-intent cluster key when safe."""
    if not is_search_item(item):
        return None
    target_page = normalized_target_page(item)
    family = intent_consolidation_family(item)
    if family not in {"SEO_SEARCH_PERFORMANCE", "SEO_TRUE_KEYWORD_GAP"}:
        return None
    return (
        "SEO",
        normalize_text(item.get("source")),
        target_page,
        search_intent_key_for_query(item.get("subject")),
        family,
    )


def supporting_query_rows(item: dict[str, Any]) -> list[dict[str, Any]]:
    """Preserve each query's explicit metrics separately."""
    rows: dict[str, dict[str, Any]] = {}
    candidates = [item] + (item.get("_related_items") if isinstance(item.get("_related_items"), list) else [])
    for candidate in candidates:
        subject = display_text(candidate.get("subject"))
        if not subject:
            continue
        evidence = evidence_for_item(candidate)
        rows[subject] = {
            "query": subject,
            "impressions": evidence.get("impressions"),
            "clicks": evidence.get("clicks"),
            "ctr": evidence.get("ctr"),
            "position": evidence.get("position"),
            "rule_id": candidate.get("rule_id"),
        }
    return sorted(
        rows.values(),
        key=lambda row: (
            to_numeric_score_value(row.get("impressions")) or 0,
            -(to_numeric_score_value(row.get("position")) or 999),
        ),
        reverse=True,
    )


def unique_supporting_query_metrics(item: dict[str, Any]) -> list[dict[str, Any]]:
    """Return one metric row per query so duplicate rules cannot inflate confidence."""
    source_rows = item.get("_supporting_queries") if isinstance(item.get("_supporting_queries"), list) else []
    if not source_rows:
        source_rows = supporting_query_rows(item)

    rows: dict[str, dict[str, Any]] = {}
    for row in source_rows:
        if not isinstance(row, dict):
            continue
        query = display_text(row.get("query"))
        if not query:
            continue
        existing = rows.get(query, {})
        current_impressions = to_numeric_score_value(row.get("impressions")) or 0.0
        existing_impressions = to_numeric_score_value(existing.get("impressions")) or -1.0
        if current_impressions >= existing_impressions:
            rows[query] = row
    return list(rows.values())


def metric_presence_bonus(metrics: dict[str, Any], required_keys: list[str]) -> float:
    """Award a small confidence lift when the claim's core metrics are present."""
    if not required_keys:
        return 0.0
    present = sum(metrics.get(key) is not None for key in required_keys)
    return round((present / len(required_keys)) * 5.0, 2)


def materially_inferred_claim(item: dict[str, Any]) -> bool:
    """Detect surviving recommendations that still depend on inferential wording."""
    content = " ".join(
        normalize_text(item.get(key))
        for key in ["title", "issue", "insight", "recommendation", "why_it_matters"]
    )
    if any(token in content for token in ["ai citation", "citation", "authority", "entity", "schema"]) and not has_direct_schema_or_authority_evidence(item):
        return True
    if action_family_for_item(item) == "SEO_CONTENT_EXPANSION" and not has_true_keyword_gap_evidence(item):
        return True
    inferred_phrases = [
        "may indicate",
        "likely",
        "inferred",
        "assume",
        "potentially",
        "could indicate",
        "appears to indicate",
    ]
    return any(phrase in content for phrase in inferred_phrases)


def calculate_display_confidence(item: dict[str, Any]) -> float:
    """Calibrate displayed confidence to evidence strength and sufficiency."""
    category = category_for_item(item)
    source_type = normalize_text(item.get("source_type"))
    evidence = evidence_for_item(item)

    if category == "SEO":
        query_rows = unique_supporting_query_metrics(item)
        if query_rows:
            total_impressions = sum(to_numeric_score_value(row.get("impressions")) or 0.0 for row in query_rows)
            tier = evidence_tier_for_volume(total_impressions)
            merged_metrics = {
                "impressions": total_impressions,
                "clicks": sum(to_numeric_score_value(row.get("clicks")) or 0.0 for row in query_rows),
                "ctr": next((row.get("ctr") for row in query_rows if row.get("ctr") is not None), None),
                "position": next((row.get("position") for row in query_rows if row.get("position") is not None), None),
            }
        else:
            tier = gsc_evidence_tier(item)
            merged_metrics = evidence
        base = CONFIDENCE_BY_EVIDENCE_TIER.get(tier, 45.0)
        confidence = base + metric_presence_bonus(merged_metrics, ["impressions", "clicks", "ctr", "position"])
    elif source_type in {"ga4_pages", "ga4 sources", "ga4_sources"} or category in {"UX/CRO", "Analytics"}:
        sessions = metric_value(item, "sessions")
        tier = evidence_tier_for_volume(sessions)
        base = CONFIDENCE_BY_EVIDENCE_TIER.get(tier, 45.0)
        confidence = base + metric_presence_bonus(evidence, ["sessions", "active_users", "engagement_rate"])
    elif category == "Social":
        observations = social_observation_count(item)
        tier = evidence_tier_for_volume(float(observations) * GSC_MEANINGFUL_IMPRESSIONS if observations else None)
        base = CONFIDENCE_BY_EVIDENCE_TIER.get(tier, 45.0)
        confidence = base + metric_presence_bonus(evidence, ["reach", "engagement_rate", "saves"])
    else:
        populated_metrics = len([value for value in evidence.values() if value not in (None, "")])
        confidence = 50.0 + min(populated_metrics * 5.0, 20.0)

    if materially_inferred_claim(item):
        confidence -= 12.0
    return round(clamp_score(confidence, 40.0, 95.0), 2)


def apply_display_confidence_calibration(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Annotate final user-facing items with calibrated display confidence."""
    calibrated: list[dict[str, Any]] = []
    for item in items:
        copy = deepcopy(item)
        copy["_raw_confidence_score"] = copy.get("confidence_score")
        copy["confidence_score"] = calculate_display_confidence(copy)
        calibrated.append(copy)
    return calibrated


def has_search_performance_opportunity(item: dict[str, Any]) -> bool:
    """Confirm query evidence supports click/ranking action."""
    rows = supporting_query_rows(item) if item.get("_supporting_queries") else []
    if not rows:
        evidence = evidence_for_item(item)
        rows = [
            {
                "impressions": evidence.get("impressions"),
                "clicks": evidence.get("clicks"),
                "ctr": evidence.get("ctr"),
                "position": evidence.get("position"),
            }
        ]
    for row in rows:
        impressions = to_numeric_score_value(row.get("impressions")) or 0
        ctr = to_numeric_score_value(row.get("ctr"))
        position = to_numeric_score_value(row.get("position"))
        if impressions < GSC_MEANINGFUL_IMPRESSIONS:
            continue
        if ctr is not None and ctr <= 3:
            return True
        if position is not None and 6 <= position <= 15:
            return True
    return False


def consolidate_search_intent_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge clearly related query variants into one strategic search decision."""
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    passthrough: list[dict[str, Any]] = []
    for item in items:
        key = intent_cluster_key_for_item(item)
        if key is None:
            passthrough.append(item)
        else:
            grouped.setdefault(key, []).append(item)

    consolidated: list[dict[str, Any]] = []
    for key, intent_items in grouped.items():
        sorted_items = sorted(intent_items, key=representative_sort_key, reverse=True)
        representative = merge_related_items(sorted_items[0], sorted_items[1:])
        intent_label = key[3].title()
        family = key[4]
        supporting_rows = supporting_query_rows(representative)
        representative["_search_intent"] = intent_label
        representative["_supporting_queries"] = supporting_rows
        representative["_intent_cluster_size"] = len(supporting_rows)
        if family == "SEO_SEARCH_PERFORMANCE":
            representative["_action_family"] = "SEO_SEARCH_PERFORMANCE"
            representative["title"] = f"Improve search performance for {intent_label} queries"
            representative["recommendation"] = (
                f"Review the result currently earning visibility for {intent_label} intent, then improve title/meta click appeal, "
                "align visible copy to the query variants, and strengthen relevance signals without assuming a specific landing page."
            )
        consolidated.append(representative)

    return passthrough + consolidated


def has_unsupported_authority_claim(item: dict[str, Any]) -> bool:
    """Return true when authority/schema/AI-citation language is the core unsupported claim."""
    content = " ".join(
        normalize_text(item.get(key))
        for key in ["rule_id", "title", "issue", "insight", "recommendation", "why_it_matters"]
    )
    return any(token in content for token in ["ai citation", "citation", "authority", "entity", "schema"]) and not has_direct_schema_or_authority_evidence(item)


def has_actionable_text(item: dict[str, Any]) -> bool:
    """Check whether the item tells a marketer what to inspect or change."""
    text = normalize_text(item.get("recommendation"))
    if not text:
        return False
    generic = {"improve seo", "expand content", "improve engagement", "optimize experience"}
    return text not in generic and len(text.split()) >= 5


def is_quality_eligible(item: dict[str, Any]) -> bool:
    """Gate user-facing recommendations before ranking/diversification."""
    category = category_for_item(item)
    evidence = evidence_for_item(item)
    subject = normalized_subject(item) or normalize_text(item.get("_search_intent"))
    if not subject:
        return False
    if not evidence and not item.get("_supporting_queries"):
        return False
    if not has_actionable_text(item):
        return False
    if has_unsupported_authority_claim(item):
        return False
    if category == "Social":
        if social_observation_count(item) < 3:
            return False
        if evidence_quality_score(item) < 35:
            return False
    if category == "SEO":
        tier = gsc_evidence_tier(item)
        family = str(item.get("_action_family") or action_family_for_item(item))
        if family == "SEO_CONTENT_EXPANSION" and not has_true_keyword_gap_evidence(item):
            return False
        if family == "SEO_SEARCH_PERFORMANCE" and not has_search_performance_opportunity(item):
            return False
        if tier in {"very_small", "limited"}:
            return False
    if category == "Analytics":
        if normalize_text(item.get("source_type")) not in {"ga4_sources", "ga4 sources"}:
            return False
        if evidence_quality_score(item) < 35:
            return False
    return evidence_quality_score(item) >= 40


def cluster_recommendation_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group raw recommendation-like items into distinct action clusters."""
    clusters: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        cleaned = sanitize_claim_language(item)
        clusters.setdefault(cluster_key_for_item(cleaned), []).append(cleaned)

    representatives: list[dict[str, Any]] = []
    for cluster_items in clusters.values():
        sorted_cluster = sorted(cluster_items, key=representative_sort_key, reverse=True)
        representative = sorted_cluster[0]
        representatives.append(merge_related_items(representative, sorted_cluster[1:]))
    return representatives


def build_intent_level_recommendation_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return Phase 2 intent-level recommendation decisions."""
    return consolidate_search_intent_items(cluster_recommendation_items(items))


def curate_recommendation_queue(
    items: list[dict[str, Any]],
    *,
    max_items: int = MAX_USER_FACING_RECOMMENDATIONS,
) -> list[dict[str, Any]]:
    """Return the user-facing recommendation queue from raw workspace items."""
    representatives = build_intent_level_recommendation_items(items)
    eligible = [item for item in representatives if is_quality_eligible(item)]
    ranked = sorted(eligible, key=queue_sort_key, reverse=True)
    selected = diversify_curated_queue(
        ranked,
        preferred_items=min(len(ranked), PREFERRED_USER_FACING_RECOMMENDATIONS, max_items),
        max_items=max_items,
    )
    return apply_display_confidence_calibration(selected)


def recommendation_curation_summary(raw_items: list[dict[str, Any]], curated_items: list[dict[str, Any]]) -> dict[str, Any]:
    """Build lightweight diagnostics for validation and tests."""
    def category_counts(items: list[dict[str, Any]]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in items:
            category = category_for_item(item)
            counts[category] = counts.get(category, 0) + 1
        return counts

    small_high_priority = 0
    for item in curated_items:
        if priority_label(item) == "High" and gsc_evidence_tier(item) in {"very_small", "limited"}:
            small_high_priority += 1

    return {
        "pre_curation_count": len(raw_items),
        "post_curation_count": len(cluster_recommendation_items(raw_items)),
        "displayed_count": len(curated_items),
        "category_distribution": category_counts(curated_items),
        "high_priority_count": sum(priority_label(item) == "High" for item in curated_items),
        "small_sample_high_priority_count": small_high_priority,
        "related_items_collapsed": sum(len(item.get("_related_items", [])) for item in curated_items if isinstance(item.get("_related_items"), list)),
    }
