"""Strategy Agent."""

from __future__ import annotations

from typing import Any


def run_strategy_agent(insights: dict[str, Any]) -> dict[str, Any]:
    """Turn insight patterns into more specific marketing strategy."""
    primary_query = pick_primary_query(insights)
    primary_page = pick_primary_page(insights, primary_query["query"])
    secondary_query = pick_secondary_query(insights, primary_query["query"])

    seo_recommendations = [
        (
            f"Refresh {primary_page} to target {primary_query['query']} with the phrase in the title, "
            f"H1, opening paragraph, and FAQ section because it shows non-branded demand with "
            f"{int(primary_query['impressions'])} impressions and {primary_query['ctr']}% CTR."
        ),
        (
            f"Create a supporting page or section for {secondary_query['query']} to capture a second non-branded opportunity "
            "instead of expanding branded pages."
        ),
    ]

    aeo_geo_recommendations = [
        (
            f"Add concise answer blocks for {primary_query['query']} so the page can serve AI overviews and answer engines "
            "with a direct definition, eligibility details, and next-step guidance."
        ),
        (
            "Expand local proof points such as location references, provider expertise, and service-area language on pages "
            "connected to local-intent queries."
        ),
    ]

    ux_conversion_recommendations = [
        (
            f"Update {primary_page} with a stronger appointment CTA, visible insurance/payment details, and a short trust section "
            "because the search demand appears conversion-oriented."
        ),
        (
            "Place FAQ and CTA modules higher on the page so users with cost or specialist intent can act without scrolling deep."
        ),
    ]

    content_expansion_recommendations = [
        (
            f"Publish a focused article on {primary_query['query']} that answers cost, candidate fit, and treatment expectations."
        ),
        (
            f"Add follow-up content for {secondary_query['query']} and related local-intent variants to build topical depth."
        ),
    ]

    priority_actions = [
        f"Prioritize non-branded query: {primary_query['query']}",
        f"Use page focus: {primary_page}",
        f"Support with secondary topic: {secondary_query['query']}",
    ]

    observed_patterns = insights["patterns"]

    print(f"[Strategy Agent] Primary non-branded query: {primary_query['query']}")
    print(f"[Strategy Agent] Page selected for refresh: {primary_page}")

    return {
        "agent": "strategy",
        "input_agent": insights["agent"],
        "based_on_insights": insights["insights"] + observed_patterns,
        "strategy": {
            "goal": "Increase non-branded organic visibility and convert high-intent search demand into appointments.",
            "primary_query": primary_query,
            "secondary_query": secondary_query,
            "primary_page": primary_page,
            "recommendations": {
                "seo": seo_recommendations,
                "aeo_geo": aeo_geo_recommendations,
                "ux_conversion": ux_conversion_recommendations,
                "content_expansion": content_expansion_recommendations,
            },
            "priority_actions": priority_actions,
        },
        "notes": [
            "The Strategy Agent prioritizes non-branded, high-intent demand over branded terms.",
        ],
    }


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
