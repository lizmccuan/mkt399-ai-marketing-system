"""Insight Agent."""

from __future__ import annotations

from typing import Any


BRAND_TERMS = [
    "the headache lab",
    "headache lab",
    "dr. khan",
    "khan",
]

LOCAL_TERMS = [
    "near me",
    "chicago",
    "evergreen park",
    "orland park",
    "oak lawn",
    "illinois",
    "il",
]

CONVERSION_TERMS = [
    "cost",
    "price",
    "pricing",
    "book",
    "appointment",
    "consultation",
    "treatment",
    "doctor",
    "specialist",
    "clinic",
]


def run_insight_agent(data: dict[str, Any]) -> dict[str, Any]:
    """Analyze structured data and produce more decision-useful insights."""
    ga4_pages_summary = data["summary"]["ga4_pages"]
    ga4_sources_summary = data["summary"]["ga4_sources"]
    gsc_queries_summary = data["summary"]["gsc_queries"]
    combined_summary = data["summary"]["combined"]

    top_pages = [
        {"label": item["page_title"], "metric": item["metric"], "value": item["value"]}
        for item in combined_summary["top_pages"]
    ]
    top_sources = combined_summary["top_traffic_sources"]
    query_analysis = analyze_queries(gsc_queries_summary["sample_records"])
    branded_queries = [item for item in query_analysis if item["is_branded"]]
    non_branded_queries = [item for item in query_analysis if not item["is_branded"]]
    high_impression_low_click = [item for item in non_branded_queries if item["is_high_impression_low_click"]][:5]
    local_intent_queries = [item for item in non_branded_queries if item["is_local_intent"]][:5]
    conversion_intent_queries = [item for item in non_branded_queries if item["is_conversion_intent"]][:5]
    aligned_pages = align_pages_to_queries(top_pages, non_branded_queries)

    insights = []
    patterns = []

    if ga4_pages_summary["rows"] > 0:
        insights.append(
            f"GA4 page data contains {ga4_pages_summary['rows']} rows and {len(ga4_pages_summary['columns'])} columns."
        )
    else:
        insights.append("GA4 data is missing, so page-performance analysis is limited.")

    if ga4_sources_summary["rows"] > 0:
        insights.append(
            f"GA4 source/medium data contains {ga4_sources_summary['rows']} rows and {len(ga4_sources_summary['columns'])} columns."
        )
    else:
        insights.append("GA4 source/medium data is missing, so acquisition analysis is limited.")

    if gsc_queries_summary["rows"] > 0:
        insights.append(
            f"GSC query data contains {gsc_queries_summary['rows']} rows and {len(gsc_queries_summary['columns'])} columns."
        )
    else:
        insights.append("GSC data is missing, so search-query analysis is limited.")

    if branded_queries:
        patterns.append(f"Branded demand is present, but it should not drive the main growth strategy: {format_labels(branded_queries)}.")

    if non_branded_queries:
        patterns.append(f"Top non-branded opportunities are: {format_labels(non_branded_queries)}.")

    if top_sources:
        patterns.append(
            "Top traffic sources in the uploaded GA4 source/medium report are: "
            f"{', '.join(item['source_medium'] for item in top_sources[:3])}."
        )

    if high_impression_low_click:
        patterns.append(
            f"High-impression, low-click gaps suggest weak SERP performance for: {format_labels(high_impression_low_click)}."
        )

    if local_intent_queries:
        patterns.append(f"Local-intent demand is visible in queries like: {format_labels(local_intent_queries)}.")

    if conversion_intent_queries:
        patterns.append(f"Conversion-intent demand is visible in queries like: {format_labels(conversion_intent_queries)}.")

    if aligned_pages:
        patterns.append(
            "GA4 pages that best align with non-branded search demand are: "
            f"{', '.join(item['page_title'] for item in aligned_pages[:3])}."
        )
    elif top_pages:
        patterns.append("Top GA4 pages do not clearly align with the sampled non-branded queries yet.")

    print(f"[Insight Agent] Top GA4 pages found: {len(top_pages)}")
    print(f"[Insight Agent] Non-branded queries found: {len(non_branded_queries)}")
    print(f"[Insight Agent] High-impression/low-click opportunities: {len(high_impression_low_click)}")

    return {
        "agent": "insight",
        "input_agent": data["agent"],
        "insights": insights,
        "patterns": patterns,
        "top_pages": top_pages,
        "top_sources": top_sources,
        "query_analysis": query_analysis,
        "branded_queries": branded_queries,
        "non_branded_queries": non_branded_queries,
        "high_impression_low_click": high_impression_low_click,
        "local_intent_queries": local_intent_queries,
        "conversion_intent_queries": conversion_intent_queries,
        "aligned_pages": aligned_pages,
        "notes": [
            "A2A happens here: the Insight Agent uses the structured output from Data Intake.",
        ],
    }


def analyze_queries(sample_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Classify GSC queries into more useful decision buckets."""
    analyzed_queries = []

    for record in sample_records:
        query = first_value(record, ["top_queries", "query", "queries", "search_query"])
        if not query:
            continue

        query_text = str(query)
        query_lower = query_text.lower()
        clicks = to_number(record.get("clicks"))
        impressions = to_number(record.get("impressions"))
        ctr = normalize_ctr_percent(record.get("ctr"), clicks, impressions)
        position = to_number(record.get("position"))

        analyzed_queries.append(
            {
                "query": query_text,
                "clicks": clicks,
                "impressions": impressions,
                "ctr": ctr,
                "position": position,
                "is_branded": contains_any(query_lower, BRAND_TERMS),
                "is_local_intent": contains_any(query_lower, LOCAL_TERMS),
                "is_conversion_intent": contains_any(query_lower, CONVERSION_TERMS),
                "is_high_impression_low_click": impressions >= 100 and ctr <= 5,
                "opportunity_score": build_opportunity_score(
                    impressions=impressions,
                    ctr=ctr,
                    position=position,
                    is_branded=contains_any(query_lower, BRAND_TERMS),
                    is_local_intent=contains_any(query_lower, LOCAL_TERMS),
                    is_conversion_intent=contains_any(query_lower, CONVERSION_TERMS),
                ),
            }
        )

    return sorted(analyzed_queries, key=lambda item: item["opportunity_score"], reverse=True)


def normalize_ctr_percent(raw_ctr: Any, clicks: float, impressions: float) -> float:
    """Normalize CTR into percentage units for all downstream logic."""
    if impressions > 0 and clicks >= 0:
        return round((clicks / impressions) * 100, 2)

    ctr = to_number(raw_ctr)
    return ctr


def build_opportunity_score(
    impressions: float,
    ctr: float,
    position: float,
    is_branded: bool,
    is_local_intent: bool,
    is_conversion_intent: bool,
) -> float:
    """Score queries with extra weight on non-branded, high-intent opportunities."""
    score = impressions / 100

    if ctr <= 5:
        score += 2

    if 3 <= position <= 20:
        score += 2

    if is_local_intent:
        score += 2

    if is_conversion_intent:
        score += 3

    if is_branded:
        score -= 4

    return round(score, 2)


def align_pages_to_queries(top_pages: list[dict[str, Any]], non_branded_queries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Find top pages whose titles overlap with non-branded query terms."""
    aligned = []

    for page in top_pages:
        page_title = page["label"]
        page_words = meaningful_words(page_title)
        best_matches = []

        for query in non_branded_queries:
            query_words = meaningful_words(query["query"])
            overlap = sorted(page_words.intersection(query_words))

            if overlap:
                best_matches.append(
                    {
                        "query": query["query"],
                        "overlap_terms": overlap,
                        "opportunity_score": query["opportunity_score"],
                    }
                )

        if best_matches:
            aligned.append(
                {
                    "page_title": page_title,
                    "page_metric": page["metric"],
                    "page_value": page["value"],
                    "matched_queries": sorted(best_matches, key=lambda item: item["opportunity_score"], reverse=True)[:3],
                }
            )

    return aligned


def get_top_items(sample_records: list[dict[str, Any]], label_keys: list[str], metric_keys: list[str]) -> list[dict[str, Any]]:
    """Pick top rows from sample data using the first matching metric column."""
    top_items = []

    for record in sample_records:
        label = first_value(record, label_keys)
        metric_key = first_existing_key(record, metric_keys)

        if not label or not metric_key:
            continue

        metric_value = to_number(record.get(metric_key))
        top_items.append({"label": str(label), "metric": metric_key, "value": metric_value})

    return sorted(top_items, key=lambda item: item["value"], reverse=True)[:5]


def format_labels(items: list[dict[str, Any]]) -> str:
    """Create a short comma-separated label summary."""
    labels = []

    for item in items[:3]:
        label = item.get("query") or item.get("label") or ""
        if label:
            labels.append(label)

    return ", ".join(labels)


def meaningful_words(text: str) -> set[str]:
    """Extract simple keywords for quick overlap matching."""
    stop_words = {
        "the",
        "and",
        "for",
        "with",
        "near",
        "page",
        "guide",
        "about",
        "what",
        "how",
        "your",
        "from",
        "treatment",
    }
    cleaned = "".join(character.lower() if character.isalnum() or character.isspace() else " " for character in text)
    words = {word for word in cleaned.split() if len(word) > 2 and word not in stop_words}
    return words


def contains_any(text: str, terms: list[str]) -> bool:
    """Check whether any term appears in the text."""
    return any(term in text for term in terms)


def first_value(record: dict[str, Any], keys: list[str]) -> Any:
    """Return the first non-empty value from a list of possible keys."""
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return value
    return None


def first_existing_key(record: dict[str, Any], keys: list[str]) -> str | None:
    """Return the first key that exists in the record."""
    for key in keys:
        if key in record:
            return key
    return None


def to_number(value: Any) -> float:
    """Convert common CSV values to a sortable number."""
    if value in (None, ""):
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    cleaned = str(value).replace(",", "").replace("%", "").strip()

    try:
        return float(cleaned)
    except ValueError:
        return 0.0
