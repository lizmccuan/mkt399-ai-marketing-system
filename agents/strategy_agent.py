"""Strategy Agent."""

from __future__ import annotations

import json
from typing import Any

# Load best practices rules
with open("reference_docs/distilled/best_practices_rules.json") as f:
    BEST_PRACTICES = json.load(f)

# Load agent prompt text (optional but useful for documentation / future upgrades)
with open("reference_docs/distilled/agent_prompt.txt") as f:
    AGENT_PROMPT = f.read()


def run_strategy_agent(insights: dict[str, Any]) -> dict[str, Any]:
    """Turn insight patterns into more specific marketing strategy."""
    primary_query = pick_primary_query(insights)
    primary_page = pick_primary_page(insights, primary_query["query"])
    secondary_query = pick_secondary_query(insights, primary_query["query"])

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

    print(f"[Strategy Agent] Primary non-branded query: {primary_query['query']}")
    print(f"[Strategy Agent] Page selected for refresh: {primary_page}")

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