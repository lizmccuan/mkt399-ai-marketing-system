"""Strategy Agent."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

# Load best practices rules
with open("reference_docs/distilled/best_practices_rules.json") as f:
    BEST_PRACTICES = json.load(f)

# Load agent prompt text (optional but useful for documentation / future upgrades)
with open("reference_docs/distilled/agent_prompt.txt") as f:
    AGENT_PROMPT = f.read()


def run_strategy_agent(
    insights: dict[str, Any], semrush_positions_data: Any | None = None
) -> dict[str, Any]:
    """Turn insight patterns into more specific marketing strategy."""
    primary_query = pick_primary_query(insights)
    primary_page = pick_primary_page(insights, primary_query["query"])
    secondary_query = pick_secondary_query(insights, primary_query["query"])
    semrush_intelligence = build_semrush_strategy_intelligence(semrush_positions_data)

    # Reference prompt so the system is explicitly grounded in your strategy instructions
    prompt_reference = AGENT_PROMPT

    seo_recommendations = [
        {
            "issue": f"Low CTR and untapped visibility for {primary_query['query']}",
            "recommendation": (
                f"Refresh {primary_page} to target {primary_query['query']} in the title tag, H1, "
                "opening paragraph, meta description, and FAQ section."
            ),
            "why_it_matters": (
                f"The query shows non-branded demand with {int(primary_query['impressions'])} impressions "
                f"and only {primary_query['ctr']}% CTR, which suggests the page is being seen but not compelling enough."
            ),
            "priority": "High",
            "best_practice_category": "seo_keyword_strategy",
        },
        {
            "issue": f"Secondary non-branded opportunity exists for {secondary_query['query']}",
            "recommendation": (
                f"Create a supporting page or dedicated section for {secondary_query['query']} instead of relying only on branded pages."
            ),
            "why_it_matters": (
                "This expands non-branded visibility and helps the site capture additional intent-driven searches."
            ),
            "priority": "Medium",
            "best_practice_category": "seo_keyword_strategy",
        },
    ]

    aeo_geo_recommendations = [
        {
            "issue": f"The page may not be structured clearly enough for AI summaries around {primary_query['query']}",
            "recommendation": (
                f"Add concise answer blocks for {primary_query['query']} with a direct definition, "
                "eligibility details, FAQs, and next-step guidance near the top of the page."
            ),
            "why_it_matters": (
                "Clear question-answer formatting makes content easier for AI overviews, answer engines, and snippet extraction."
            ),
            "priority": "High",
            "best_practice_category": "aeo_geo_ai_search",
        },
        {
            "issue": "Local-intent trust signals may be too weak on key service pages",
            "recommendation": (
                "Expand location references, provider expertise, service-area language, and local proof points on pages tied to local-intent queries."
            ),
            "why_it_matters": (
                "AI search and local search often reward clear relevance, authority, and geographic context."
            ),
            "priority": "Medium",
            "best_practice_category": "aeo_geo_ai_search",
        },
    ]

    ux_conversion_recommendations = [
        {
            "issue": f"{primary_page} may not convert high-intent traffic efficiently",
            "recommendation": (
                f"Update {primary_page} with a stronger appointment CTA, visible insurance/payment details, and a short trust section near the top."
            ),
            "why_it_matters": (
                "Search demand appears conversion-oriented, so the page should reduce friction and help users act quickly."
            ),
            "priority": "High",
            "best_practice_category": "website_ux_conversion",
        },
        {
            "issue": "Users may need to scroll too far to find answers and next steps",
            "recommendation": (
                "Move FAQ and CTA modules higher on the page so users with cost or specialist intent can act sooner."
            ),
            "why_it_matters": (
                "Better page hierarchy improves usability and reduces the chance of losing high-intent visitors."
            ),
            "priority": "Medium",
            "best_practice_category": "website_ux_conversion",
        },
    ]

    content_expansion_recommendations = [
        {
            "issue": f"The site may not have enough depth around {primary_query['query']}",
            "recommendation": (
                f"Publish a focused article or landing page on {primary_query['query']} that answers cost, candidate fit, treatment expectations, and FAQs."
            ),
            "why_it_matters": (
                "This builds topical depth, supports SEO, and increases the site's ability to capture long-tail and informational intent."
            ),
            "priority": "High",
            "best_practice_category": "aeo_geo_ai_search",
        },
        {
            "issue": f"Topical coverage is limited for {secondary_query['query']}",
            "recommendation": (
                f"Add follow-up content for {secondary_query['query']} and related local-intent variants to support cluster-based visibility."
            ),
            "why_it_matters": (
                "Building content clusters improves topical authority and gives search engines and AI systems more relevant material to cite."
            ),
            "priority": "Medium",
            "best_practice_category": "analytics_digital_strategy",
        },
    ]

    priority_actions = [
        {
            "action": f"Prioritize non-branded query: {primary_query['query']}",
            "priority": "High",
        },
        {
            "action": f"Refresh page focus: {primary_page}",
            "priority": "High",
        },
        {
            "action": f"Support with secondary topic: {secondary_query['query']}",
            "priority": "Medium",
        },
    ]

    what_to_do_this_week = [
        f"Refresh {primary_page} title, H1, intro, and FAQ structure for {primary_query['query']}.",
        "Add stronger CTA and trust/payment information above the fold.",
        f"Draft a new supporting content piece for {secondary_query['query']}.",
    ]

    what_to_test_next = [
        "Test a stronger meta title and description to improve CTR.",
        "Test moving FAQ blocks higher on the page.",
        "Test direct-answer formatting for AI/search snippet visibility.",
    ]

    observed_patterns = insights["patterns"]
    executive_summary = build_executive_summary(primary_query, primary_page, semrush_intelligence)
    recommended_actions_summary = build_recommended_actions_summary(
        primary_query, primary_page, secondary_query, semrush_intelligence
    )

    print(f"[Strategy Agent] Primary non-branded query: {primary_query['query']}")
    print(f"[Strategy Agent] Page selected for refresh: {primary_page}")
    print(f"[Strategy Agent] SEMrush quick wins: {len(semrush_intelligence['quick_wins'])}")

    return {
        "agent": "strategy",
        "input_agent": insights["agent"],
        "prompt_reference": prompt_reference,
        "best_practice_categories_used": list(BEST_PRACTICES.keys()),
        "based_on_insights": insights["insights"] + observed_patterns,
        "strategy": {
            "goal": "Increase non-branded organic visibility and convert high-intent search demand into appointments.",
            "primary_query": primary_query,
            "secondary_query": secondary_query,
            "primary_page": primary_page,
            "executive_summary": executive_summary,
            "keyword_opportunities": semrush_intelligence["keyword_opportunities"],
            "intent_clusters": semrush_intelligence["intent_clusters"],
            "aeo_geo_opportunities": semrush_intelligence["aeo_geo_opportunities"],
            "recommended_actions_summary": recommended_actions_summary,
            "recommendations": {
                "seo": seo_recommendations,
                "aeo_geo": aeo_geo_recommendations,
                "ux_conversion": ux_conversion_recommendations,
                "content_expansion": content_expansion_recommendations,
            },
            "priority_actions": priority_actions,
            "what_should_be_done_this_week": what_to_do_this_week,
            "what_should_be_tested_next": what_to_test_next,
        },
        "notes": [
            "The Strategy Agent prioritizes non-branded, high-intent demand over branded terms.",
            "Recommendations are grounded in performance data and mapped to best-practice categories.",
        ],
    }


def build_executive_summary(
    primary_query: dict[str, Any], primary_page: str, semrush_intelligence: dict[str, Any]
) -> list[str]:
    """Create short strategy summary bullets."""
    summary = [
        (
            f"Primary growth focus remains {primary_query['query']}, anchored to {primary_page} and supported by "
            "high-intent non-branded demand."
        )
    ]

    if semrush_intelligence["available"]:
        quick_win = semrush_intelligence["quick_wins"][0] if semrush_intelligence["quick_wins"] else None
        if quick_win:
            summary.append(
                f"SEMrush shows a quick-win keyword in striking distance: {quick_win['keyword']} at position {quick_win['position']}."
            )
        high_opportunity = (
            semrush_intelligence["high_opportunity_keywords"][0]
            if semrush_intelligence["high_opportunity_keywords"]
            else None
        )
        if high_opportunity:
            summary.append(
                f"A higher-effort opportunity exists for {high_opportunity['keyword']} due to strong search volume and lower current visibility."
            )

    return summary


def build_recommended_actions_summary(
    primary_query: dict[str, Any],
    primary_page: str,
    secondary_query: dict[str, Any],
    semrush_intelligence: dict[str, Any],
) -> list[str]:
    """Create a short summary action list that includes SEMrush when present."""
    actions = [
        f"Refresh {primary_page} around {primary_query['query']} first.",
        f"Support the refresh with a secondary content asset for {secondary_query['query']}.",
    ]

    if semrush_intelligence["available"]:
        if semrush_intelligence["quick_wins"]:
            actions.append(
                f"Prioritize quick-win keyword updates for {semrush_intelligence['quick_wins'][0]['keyword']}."
            )
        if semrush_intelligence["aeo_geo_opportunities"]:
            actions.append(
                f"Add answer-focused or comparison-style content for {semrush_intelligence['aeo_geo_opportunities'][0]['keyword']}."
            )

    return actions


def build_semrush_strategy_intelligence(semrush_positions_data: Any | None) -> dict[str, Any]:
    """Summarize SEMrush keyword intelligence without returning raw tables."""
    empty_payload = {
        "available": False,
        "quick_wins": [],
        "high_opportunity_keywords": [],
        "keyword_opportunities": [],
        "intent_clusters": [],
        "aeo_geo_opportunities": [],
    }

    if semrush_positions_data is None or getattr(semrush_positions_data, "empty", True):
        return empty_payload

    dataframe = semrush_positions_data.copy()
    dataframe.columns = [str(column).strip().lower() for column in dataframe.columns]

    if "keyword" not in dataframe.columns:
        return empty_payload

    dataframe["position"] = to_numeric_series(dataframe, "position")
    dataframe["volume"] = to_numeric_series(dataframe, "volume")
    dataframe["url"] = dataframe["url"].astype(str) if "url" in dataframe.columns else ""

    keyword_records = []
    for _, row in dataframe.iterrows():
        keyword = str(row.get("keyword", "")).strip()
        if not keyword:
            continue

        position = float(row.get("position", 0) or 0)
        volume = float(row.get("volume", 0) or 0)
        keyword_lower = keyword.lower()
        intent = infer_keyword_intent(keyword_lower)

        keyword_records.append(
            {
                "keyword": keyword,
                "position": position,
                "volume": volume,
                "url": str(row.get("url", "")),
                "intent": intent,
                "is_quick_win": 4 <= position <= 20,
                "is_high_opportunity": position > 20 and volume >= 100,
                "is_aeo_geo": any(token in keyword_lower for token in ["how", "what", "best", "vs", "near me", "?"]),
            }
        )

    quick_wins = sorted(
        [item for item in keyword_records if item["is_quick_win"]],
        key=lambda item: (item["position"], -item["volume"]),
    )[:5]
    high_opportunity_keywords = sorted(
        [item for item in keyword_records if item["is_high_opportunity"]],
        key=lambda item: (-item["volume"], item["position"]),
    )[:5]
    aeo_geo_opportunities = sorted(
        [item for item in keyword_records if item["is_aeo_geo"]],
        key=lambda item: (-item["volume"], item["position"]),
    )[:5]

    keyword_opportunities = []
    for item in quick_wins[:3]:
        keyword_opportunities.append(
            {
                "keyword": item["keyword"],
                "opportunity_type": "Quick Win",
                "insight": (
                    f"{item['keyword']} is already ranking at position {int(item['position'])}, so on-page updates could improve visibility faster."
                ),
            }
        )
    for item in high_opportunity_keywords[:2]:
        keyword_opportunities.append(
            {
                "keyword": item["keyword"],
                "opportunity_type": "High Opportunity",
                "insight": (
                    f"{item['keyword']} has meaningful volume but sits beyond page-one visibility, making it a candidate for deeper content or landing-page support."
                ),
            }
        )

    intent_clusters = build_intent_clusters(keyword_records)
    aeo_geo_summaries = [
        {
            "keyword": item["keyword"],
            "insight": (
                f"{item['keyword']} is suited to answer-style, comparison, or local discovery content that can support AI overviews and decision-stage search."
            ),
        }
        for item in aeo_geo_opportunities[:3]
    ]

    return {
        "available": True,
        "quick_wins": quick_wins,
        "high_opportunity_keywords": high_opportunity_keywords,
        "keyword_opportunities": keyword_opportunities,
        "intent_clusters": intent_clusters,
        "aeo_geo_opportunities": aeo_geo_summaries,
    }


def build_intent_clusters(keyword_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group SEMrush keywords into simple intent clusters."""
    clusters: dict[str, list[str]] = {}

    for item in keyword_records:
        clusters.setdefault(item["intent"], []).append(item["keyword"])

    cluster_summaries = []
    for intent, keywords in clusters.items():
        cluster_summaries.append(
            {
                "cluster": intent,
                "insight": f"{intent.title()} intent includes keywords such as {', '.join(keywords[:3])}.",
            }
        )

    return cluster_summaries


def infer_keyword_intent(keyword_lower: str) -> str:
    """Classify a keyword into a simple intent bucket."""
    if any(token in keyword_lower for token in ["cost", "price", "book", "appointment", "near me", "specialist"]):
        return "transactional"
    if any(token in keyword_lower for token in ["best", "vs", "compare"]):
        return "commercial"
    if any(token in keyword_lower for token in ["how", "what", "why", "faq"]):
        return "informational"
    return "general"


def to_numeric_series(dataframe: Any, column: str):
    """Safely convert an optional column to numeric."""
    if column not in dataframe.columns:
        return 0
    return pd.to_numeric(
        dataframe[column].astype(str).str.replace(",", "", regex=False),
        errors="coerce",
    ).fillna(0)


def pick_primary_query(insights: dict[str, Any]) -> dict[str, Any]:
    """Pick the strongest non-branded opportunity."""
    candidates = insights["high_impression_low_click"] or insights["conversion_intent_queries"] or insights["non_branded_queries"]

    if candidates:
        return candidates[0]

    return {
        "query": "high-intent service query",
        "impressions": 0.0,
        "ctr": 0.0,
        "position": 0.0,
        "is_local_intent": False,
        "is_conversion_intent": True,
    }


def pick_secondary_query(insights: dict[str, Any], primary_query_text: str) -> dict[str, Any]:
    """Pick a second useful topic different from the primary query."""
    for group_name in ["local_intent_queries", "conversion_intent_queries", "non_branded_queries"]:
        for item in insights[group_name]:
            if item["query"] != primary_query_text:
                return item

    return {
        "query": "local service intent query",
        "impressions": 0.0,
        "ctr": 0.0,
        "position": 0.0,
        "is_local_intent": True,
        "is_conversion_intent": True,
    }


def pick_primary_page(insights: dict[str, Any], primary_query_text: str) -> str:
    """Choose the best GA4 page to update first."""
    primary_query_words = meaningful_words(primary_query_text)

    best_page = None
    best_score = -1

    for page in insights["aligned_pages"]:
        page_title = page["page_title"]
        page_words = meaningful_words(page_title)
        overlap_score = len(page_words.intersection(primary_query_words))
        branded_penalty = 2 if is_branded_page(page_title) else 0
        score = overlap_score - branded_penalty

        if score > best_score:
            best_score = score
            best_page = page_title

    if best_page:
        return best_page

    if insights["top_pages"]:
        non_branded_pages = [item["label"] for item in insights["top_pages"] if not is_branded_page(item["label"])]
        if non_branded_pages:
            return non_branded_pages[0]
        return insights["top_pages"][0]["label"]

    return "primary service page"


def meaningful_words(text: str) -> set[str]:
    """Extract keywords for quick matching between pages and queries."""
    stop_words = {
        "the",
        "and",
        "for",
        "with",
        "page",
        "home",
        "guide",
        "about",
        "what",
        "how",
        "from",
        "your",
    }
    cleaned = "".join(character.lower() if character.isalnum() or character.isspace() else " " for character in text)
    return {word for word in cleaned.split() if len(word) > 2 and word not in stop_words}


def is_branded_page(page_title: str) -> bool:
    """Detect simple branded page titles."""
    page_lower = page_title.lower()
    return "headache lab" in page_lower or "dr. khan" in page_lower or "khan" in page_lower
