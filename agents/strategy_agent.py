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
    insights: dict[str, Any],
    semrush_positions_data: Any | None = None,
    semrush_pages_data: Any | None = None,
    semrush_topics_data: Any | None = None,
    rule_matches: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Turn insight patterns into more specific marketing strategy."""
    actionable_query = select_top_actionable_query(insights, rule_matches)
    primary_query = actionable_query or pick_primary_query(insights)
    top_opportunity = (
        build_top_opportunity_conclusion(actionable_query, rule_matches)
        if actionable_query
        else build_no_actionable_top_opportunity(insights)
    )
    primary_page = pick_primary_page(insights, primary_query["query"])
    secondary_query = pick_secondary_query(insights, primary_query["query"])
    semrush_intelligence = build_semrush_strategy_intelligence(
        semrush_positions_data=semrush_positions_data,
        semrush_pages_data=semrush_pages_data,
        semrush_topics_data=semrush_topics_data,
    )

    # Reference prompt so the system is explicitly grounded in your strategy instructions
    prompt_reference = AGENT_PROMPT

    seo_recommendations = [
        {
            "issue": top_opportunity["diagnosis"],
            "recommendation": top_opportunity["recommended_next_step"],
            "why_it_matters": top_opportunity["why_it_matters"],
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

    priority_actions = build_priority_actions(
        primary_query=primary_query,
        primary_page=primary_page,
        secondary_query=secondary_query,
        semrush_intelligence=semrush_intelligence,
        top_opportunity=top_opportunity,
    )

    what_to_do_this_week = [
        top_opportunity["recommended_next_step"],
        "Add stronger CTA and trust/payment information above the fold.",
        f"Draft a new supporting content piece for {secondary_query['query']}.",
    ]

    if semrush_intelligence["priority_page"]:
        what_to_do_this_week.append(
            f"Review the SEMrush page opportunity for {semrush_intelligence['priority_page']['page']} and tighten conversion paths."
        )
    if semrush_intelligence["priority_topic"]:
        what_to_do_this_week.append(
            f"Brief a new content asset around {semrush_intelligence['priority_topic']['topic']}."
        )

    what_to_test_next = build_top_opportunity_tests(top_opportunity)

    observed_patterns = insights["patterns"]
    executive_summary = build_executive_summary(primary_query, primary_page, semrush_intelligence)
    recommended_actions_summary = build_recommended_actions_summary(
        primary_query, primary_page, secondary_query, semrush_intelligence
    )
    rule_grounded_priorities = build_rule_grounded_priorities(rule_matches)
    priority_reasoning_summary = build_priority_reasoning_summary(rule_grounded_priorities)
    priority_actions = merge_rule_grounded_priority_actions(priority_actions, rule_grounded_priorities)
    recommended_actions_summary = merge_rule_grounded_action_summaries(
        recommended_actions_summary,
        rule_grounded_priorities,
    )
    what_to_do_this_week = merge_rule_grounded_weekly_actions(
        what_to_do_this_week,
        rule_grounded_priorities,
    )

    print(f"[Strategy Agent] Primary non-branded query: {primary_query['query']}")
    print(f"[Strategy Agent] Page selected for refresh: {primary_page}")
    print(f"[Strategy Agent] SEMrush quick wins: {len(semrush_intelligence['quick_wins'])}")
    print(f"[Strategy Agent] Rule-grounded priorities: {len(rule_grounded_priorities)}")

    return {
        "agent": "strategy",
        "input_agent": insights["agent"],
        "prompt_reference": prompt_reference,
        "best_practice_categories_used": list(BEST_PRACTICES.keys()),
        "based_on_insights": insights["insights"] + observed_patterns,
        "rule_match_count": int((rule_matches or {}).get("match_count", 0)) if isinstance(rule_matches, dict) else 0,
        "strategy": {
            "goal": "Increase non-branded organic visibility and convert high-intent search demand into appointments.",
            "primary_query": primary_query,
            "secondary_query": secondary_query,
            "primary_page": primary_page,
            "top_opportunity": top_opportunity,
            "executive_summary": executive_summary,
            "keyword_opportunities": semrush_intelligence["keyword_opportunities"],
            "page_opportunities": semrush_intelligence["page_opportunities"],
            "topic_opportunities": semrush_intelligence["topic_opportunities"],
            "intent_clusters": semrush_intelligence["intent_clusters"],
            "aeo_geo_opportunities": semrush_intelligence["aeo_geo_opportunities"],
            "priority_page_opportunity": semrush_intelligence["priority_page"],
            "next_best_content_topic": semrush_intelligence["priority_topic"],
            "recommended_actions_summary": recommended_actions_summary,
            "rule_grounded_priorities": rule_grounded_priorities,
            "priority_reasoning_summary": priority_reasoning_summary,
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
            "Rule matches are accepted as optional input and exposed as strategy metadata.",
        ],
    }


def build_top_opportunity_conclusion(
    query: dict[str, Any],
    rule_matches: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Turn the selected query's factual pattern into a business-ready conclusion."""
    subject = str(query.get("subject") or query.get("query") or "Current search opportunity").strip()
    evidence = query.get("evidence") if isinstance(query.get("evidence"), dict) else {}
    evidence = {
        key: value
        for key, value in {
            "impressions": evidence.get("impressions", query.get("impressions")),
            "clicks": evidence.get("clicks", query.get("clicks")),
            "ctr": evidence.get("ctr", query.get("ctr")),
            "position": evidence.get("position", query.get("position")),
        }.items()
        if value is not None
    }
    pattern = str(query.get("pattern") or "search_performance_signal")
    position = strategy_number(evidence.get("position"))

    conclusion = {
        "opportunity_type": pattern,
        "subject": subject,
        "subject_type": str(query.get("subject_type") or "query"),
        "source": str(query.get("source") or "Google Search Console"),
        "evidence": evidence,
        "diagnosis": "Search performance opportunity",
        "business_summary": "This result has measurable Google search performance that is worth reviewing.",
        "why_it_matters": "The available search data indicates a potential way to improve how this topic contributes to website traffic.",
        "recommended_next_step": "Review the page and search intent alignment before choosing an optimization action.",
        "business_impact": "A focused improvement could help the result contribute more qualified website traffic.",
        "opportunity_score": query.get("opportunity_score"),
    }

    if pattern == "strong_ctr_mid_ranking" and position is not None:
        conclusion.update(
            {
                "opportunity_type": "ranking_growth",
                "diagnosis": "Ranking growth opportunity",
                "business_summary": (
                    f'"{subject}" earns strong clicks when it appears in Google, but it ranks around position {format_position(position)}.'
                ),
                "why_it_matters": (
                    "Because searchers already respond well when they see this result, improving its ranking could expose it to more people already searching for this topic."
                ),
                "recommended_next_step": (
                    "Strengthen the page content, internal links, and search relevance so it can compete for a higher Google position."
                ),
                "business_impact": "A higher ranking could create more qualified website traffic without relying on a change in click-through rate.",
            }
        )
    elif pattern in {"high_impressions_low_ctr", "low_ctr_search_result"}:
        conclusion.update(
            {
                "opportunity_type": "search_result_messaging",
                "diagnosis": "Search-result click-through opportunity",
                "business_summary": (
                    f'"{subject}" is appearing in Google searches, but relatively few searchers are clicking it.'
                ),
                "why_it_matters": (
                    "The topic is already being shown to searchers, so clearer search-result messaging could help more of those appearances turn into visits."
                ),
                "recommended_next_step": (
                    "Improve the title tag, meta description, and search-intent alignment to make the result more compelling in Google."
                ),
                "business_impact": "Better click-through performance could help this topic generate more visits from its existing Google search appearances.",
            }
        )
    elif pattern == "top_ranking_low_ctr":
        conclusion.update(
            {
                "opportunity_type": "serp_messaging",
                "diagnosis": "Search-result messaging opportunity",
                "business_summary": (
                    f'"{subject}" already ranks near the top of Google, but its search-result message is not earning many clicks.'
                ),
                "why_it_matters": (
                    "Strong rankings create frequent opportunities to be chosen, so a weak click-through rate may leave qualified visits on the table."
                ),
                "recommended_next_step": (
                    "Test a clearer title tag and meta description that better reflect the searcher's likely question and next step."
                ),
                "business_impact": "Improving search-result messaging could help the existing high ranking generate more website visits.",
            }
        )
    elif pattern == "strong_search_performer":
        conclusion.update(
            {
                "opportunity_type": "strong_performer",
                "diagnosis": "Strong search performer",
                "business_summary": f'"{subject}" is already ranking near the top of Google and attracting clicks when it appears.',
                "why_it_matters": "This is a proven search asset that can inform what works well across related pages and topics.",
                "recommended_next_step": "Protect the page's relevance and use its content structure as a reference for related topics.",
                "business_impact": "Maintaining this performance helps preserve a reliable source of organic website traffic.",
            }
        )
    elif pattern == "limited_search_evidence":
        conclusion.update(
            {
                "opportunity_type": "limited_evidence",
                "diagnosis": "Limited search evidence",
                "business_summary": f'"{subject}" has limited Google search appearance data in the current run.',
                "why_it_matters": "There is not enough search evidence yet to treat this as a major optimization priority.",
                "recommended_next_step": "Monitor this topic alongside higher-evidence search opportunities before investing in a dedicated update.",
                "business_impact": "Additional data will make it easier to judge whether this topic merits a larger investment.",
            }
        )
    elif pattern == "mid_ranking_growth_opportunity" and position is not None:
        conclusion.update(
            {
                "opportunity_type": "ranking_growth",
                "diagnosis": "Ranking growth opportunity",
                "business_summary": f'"{subject}" ranks around position {format_position(position)} in Google.',
                "why_it_matters": "A higher Google position could make the result visible to more people searching for this topic.",
                "recommended_next_step": "Review content depth, internal links, and search-intent alignment to identify ranking improvements.",
                "business_impact": "A stronger ranking may increase the topic's opportunity to contribute website traffic.",
            }
        )

    matching_rule = find_matching_query_rule(rule_matches, subject)
    if matching_rule:
        conclusion["rule_id"] = matching_rule.get("rule_id")
        conclusion["priority"] = matching_rule.get("priority")
        conclusion["confidence"] = (
            (matching_rule.get("priority_bundle") or {}).get("confidence_score")
            or matching_rule.get("confidence_score")
        )

    return conclusion


ACTIONABLE_SEARCH_PATTERNS = {
    "high_impressions_low_ctr",
    "low_ctr_search_result",
    "top_ranking_low_ctr",
    "strong_ctr_mid_ranking",
    "mid_ranking_growth_opportunity",
}


def select_top_actionable_query(
    insights: dict[str, Any],
    rule_matches: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Choose the strongest actionable search opportunity without replacing scoring."""
    candidates = (
        insights.get("full_query_analysis")
        or insights.get("query_analysis")
        or insights.get("non_branded_queries")
        or []
    )
    actionable_candidates = [
        candidate
        for candidate in candidates
        if str(candidate.get("pattern") or "") in ACTIONABLE_SEARCH_PATTERNS
    ]
    if not actionable_candidates:
        return None

    return max(
        actionable_candidates,
        key=lambda candidate: actionable_query_priority_key(candidate, rule_matches),
    )


def actionable_query_priority_key(
    query: dict[str, Any],
    rule_matches: dict[str, Any] | None = None,
) -> tuple[float, float, float, float]:
    """Use the existing rule and opportunity signals to order actionable candidates."""
    subject = str(query.get("subject") or query.get("query") or "")
    matching_rule = find_matching_query_rule(rule_matches, subject) or {}
    priority_bundle = matching_rule.get("priority_bundle") or {}

    return (
        strategy_number(priority_bundle.get("priority_score")) or 0.0,
        strategy_number(matching_rule.get("business_impact_score")) or 0.0,
        strategy_number(matching_rule.get("confidence_score")) or 0.0,
        strategy_number(query.get("opportunity_score")) or 0.0,
    )


def build_no_actionable_top_opportunity(insights: dict[str, Any]) -> dict[str, Any]:
    """Provide an honest, non-optimization conclusion when no action is supported."""
    candidates = (
        insights.get("full_query_analysis")
        or insights.get("query_analysis")
        or insights.get("non_branded_queries")
        or []
    )
    strong_performer = next(
        (
            candidate
            for candidate in candidates
            if str(candidate.get("pattern") or "") == "strong_search_performer"
        ),
        None,
    )

    if strong_performer:
        subject = str(strong_performer.get("subject") or strong_performer.get("query") or "Current search result")
        evidence = strong_performer.get("evidence") if isinstance(strong_performer.get("evidence"), dict) else {}
        return {
            "opportunity_type": "no_actionable_search_issue",
            "subject": "No major search optimization issue detected",
            "subject_type": "query",
            "source": "Google Search Console",
            "evidence": evidence,
            "diagnosis": "No major search optimization issue detected",
            "business_summary": f'"{subject}" is a strong current search performer based on the available evidence.',
            "why_it_matters": "The available search data does not identify a higher-priority search optimization issue in this run.",
            "recommended_next_step": "Protect this result's current relevance and monitor it alongside future search opportunities.",
            "business_impact": "Maintaining strong search performance helps preserve an existing source of organic website traffic.",
            "opportunity_score": strong_performer.get("opportunity_score"),
        }

    return {
        "opportunity_type": "no_actionable_search_issue",
        "subject": "No major search optimization issue detected",
        "subject_type": "query",
        "source": "Google Search Console",
        "evidence": {},
        "diagnosis": "No major search optimization issue detected",
        "business_summary": "The available search data does not identify a clear, high-evidence optimization priority.",
        "why_it_matters": "More complete search data is needed before presenting a major search optimization recommendation.",
        "recommended_next_step": "Monitor future search performance and review opportunities when sufficient evidence is available.",
        "business_impact": "Additional evidence will make it easier to prioritize a focused search improvement.",
        "opportunity_score": None,
    }


def build_top_opportunity_tests(top_opportunity: dict[str, Any]) -> list[str]:
    """Keep strategy testing suggestions aligned to the diagnosed opportunity."""
    opportunity_type = top_opportunity.get("opportunity_type")
    if opportunity_type in {"search_result_messaging", "serp_messaging"}:
        return [
            "Test a clearer title tag and meta description against the current search-result message.",
            "Test question-led FAQ content that matches the searcher's intent.",
            "Review whether the page opening answers the same need promised in Google.",
        ]
    if opportunity_type == "ranking_growth":
        return [
            "Test stronger topical coverage and clearer answer sections on the page.",
            "Add relevant internal links from related high-authority pages.",
            "Review the page against the search intent behind the query before expanding content.",
        ]
    return [
        "Review the page's relevance to the search topic before making changes.",
        "Compare the content structure with related pages that already perform well.",
        "Collect additional search data before prioritizing a larger update.",
    ]


def find_matching_query_rule(rule_matches: dict[str, Any] | None, subject: str) -> dict[str, Any] | None:
    """Return the strongest rule match for the selected GSC query when one exists."""
    if not isinstance(rule_matches, dict) or not subject:
        return None

    subject_key = normalize_strategy_text(subject)
    for match in rule_matches.get("all_matches", []) or []:
        if (
            str(match.get("source_type", "")) == "gsc_queries"
            and normalize_strategy_text(match.get("label", "")) == subject_key
        ):
            return match
    return None


def strategy_number(value: Any) -> float | None:
    """Read an optional structured metric without substituting a synthetic zero."""
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def format_position(value: float) -> str:
    """Format an average Google position for plain-language strategy text."""
    return str(int(value)) if float(value).is_integer() else f"{value:.1f}"


def build_rule_grounded_priorities(rule_matches: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Convert workflow-level rule matches into a small strategy-friendly priority list."""
    if not rule_matches or not isinstance(rule_matches, dict):
        return []

    priorities = []
    for match in (rule_matches.get("all_matches") or [])[:5]:
        priority_item: dict[str, Any] = {
            "rule_id": str(match.get("rule_id", "")),
            "subject": str(match.get("subject") or match.get("label") or ""),
            "subject_type": str(match.get("subject_type", "")),
            "source": str(match.get("source", "")),
            "evidence": match.get("evidence") if isinstance(match.get("evidence"), dict) else {},
            "issue": str(match.get("insight", "")),
            "why_it_matters": str(match.get("why_it_matters", "")),
            "recommendation": str(match.get("recommendation", "")),
            "priority": str(match.get("priority", "")),
            "action_type": str(match.get("action_type", "")),
        }

        priority_bundle = match.get("priority_bundle")
        if isinstance(priority_bundle, dict):
            priority_item.update(
                {
                    "priority_score": priority_bundle.get("priority_score"),
                    "impact_score": priority_bundle.get("impact_score"),
                    "effort_score": priority_bundle.get("effort_score"),
                    "urgency_score": priority_bundle.get("urgency_score"),
                    "confidence_score": priority_bundle.get("confidence_score"),
                    "priority_rationale": priority_bundle.get("rationale"),
                }
            )

        priorities.append(priority_item)

    return priorities


def build_priority_reasoning_summary(rule_grounded_priorities: list[dict[str, Any]]) -> str:
    """Explain how rule-driven priorities are ranked when a normalized bundle is available."""
    if not rule_grounded_priorities:
        return ""

    has_priority_bundle = any(item.get("priority_score") is not None for item in rule_grounded_priorities)
    if not has_priority_bundle:
        return ""

    return (
        "Rule-grounded priorities are ranked using a normalized priority bundle that weighs "
        "impact, effort, urgency, and confidence before falling back to existing strategy signals."
    )


def merge_rule_grounded_priority_actions(
    existing_actions: list[dict[str, str]],
    rule_grounded_priorities: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Blend the strongest rule-grounded priorities into strategy actions without removing existing logic."""
    merged_actions = list(existing_actions)
    existing_keys = {
        normalize_strategy_text(
            f"{action.get('issue', '')} {action.get('recommendation', '')} {action.get('action', '')}"
        )
        for action in existing_actions
    }

    for rule_item in select_top_rule_grounded_priorities(rule_grounded_priorities):
        dedupe_key = normalize_strategy_text(
            f"{rule_item.get('issue', '')} {rule_item.get('recommendation', '')}"
        )
        if not dedupe_key or dedupe_key in existing_keys:
            continue

        merged_actions.insert(
            len(merged_actions[:0]),
            {
                "title": f"Rule Priority: {format_action_type_label(rule_item.get('action_type', 'strategy'))}",
                "action": rule_item.get("recommendation", ""),
                "reason": rule_item.get("why_it_matters", ""),
                "priority": rule_item.get("priority", "Medium"),
                "issue": rule_item.get("issue", ""),
                "why_it_matters": rule_item.get("why_it_matters", ""),
                "recommendation": rule_item.get("recommendation", ""),
                "action_type": rule_item.get("action_type", ""),
                "rule_id": rule_item.get("rule_id", ""),
            },
        )
        existing_keys.add(dedupe_key)

    return merged_actions[:8]


def merge_rule_grounded_action_summaries(
    existing_summaries: list[str],
    rule_grounded_priorities: list[dict[str, str]],
) -> list[str]:
    """Add concise rule-grounded actions into the strategy summary list."""
    merged_summaries = list(existing_summaries)
    existing_keys = {normalize_strategy_text(item) for item in existing_summaries}

    for rule_item in select_top_rule_grounded_priorities(rule_grounded_priorities):
        summary_text = (
            f"{format_action_type_label(rule_item.get('action_type', 'strategy'))}: "
            f"{rule_item.get('recommendation', '')}"
        ).strip()
        dedupe_key = normalize_strategy_text(summary_text)
        if not dedupe_key or dedupe_key in existing_keys:
            continue
        merged_summaries.append(summary_text)
        existing_keys.add(dedupe_key)

    return merged_summaries


def merge_rule_grounded_weekly_actions(
    existing_actions: list[str],
    rule_grounded_priorities: list[dict[str, str]],
) -> list[str]:
    """Add the strongest rule-grounded actions into the weekly execution list."""
    merged_actions = list(existing_actions)
    existing_keys = {normalize_strategy_text(item) for item in existing_actions}

    for rule_item in select_top_rule_grounded_priorities(rule_grounded_priorities):
        weekly_text = str(rule_item.get("recommendation", "")).strip()
        dedupe_key = normalize_strategy_text(weekly_text)
        if not dedupe_key or dedupe_key in existing_keys:
            continue
        merged_actions.append(weekly_text)
        existing_keys.add(dedupe_key)

    return merged_actions


def select_top_rule_grounded_priorities(rule_grounded_priorities: list[dict[str, str]]) -> list[dict[str, str]]:
    """Select up to three highest-priority rule-grounded items while preserving original order within priority."""
    priority_rank = {"high": 3, "medium": 2, "low": 1}
    ranked_items = sorted(
        enumerate(rule_grounded_priorities),
        key=lambda item: (priority_rank.get(str(item[1].get("priority", "")).strip().lower(), 0), -item[0]),
        reverse=True,
    )
    return [item for _, item in ranked_items[:3]]


def normalize_strategy_text(value: str) -> str:
    """Normalize strategy text for lightweight deduplication."""
    return " ".join(str(value).strip().lower().split())


def format_action_type_label(action_type: str) -> str:
    """Convert an action type into a cleaner short label."""
    return str(action_type).replace("_", " ").strip().title() or "Strategy"


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
        if semrush_intelligence["priority_page"]:
            summary.append(
                f"SEMrush page data also points to {semrush_intelligence['priority_page']['page']} as a strong optimization candidate."
            )
        if semrush_intelligence["priority_topic"]:
            summary.append(
                f"Topic intelligence suggests expanding coverage around {semrush_intelligence['priority_topic']['topic']} next."
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
        if semrush_intelligence["priority_page"]:
            actions.append(
                f"Optimize {semrush_intelligence['priority_page']['page']} as a page-level SEMrush opportunity."
            )
        if semrush_intelligence["priority_topic"]:
            actions.append(
                f"Create a content brief for {semrush_intelligence['priority_topic']['topic']}."
            )
        if semrush_intelligence["aeo_geo_opportunities"]:
            actions.append(
                f"Add answer-focused or comparison-style content for {semrush_intelligence['aeo_geo_opportunities'][0]['keyword']}."
            )

    return actions


def build_priority_actions(
    primary_query: dict[str, Any],
    primary_page: str,
    secondary_query: dict[str, Any],
    semrush_intelligence: dict[str, Any],
    top_opportunity: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    """Create prioritized actions, using SEMrush quick wins when available."""
    quick_wins = semrush_intelligence.get("quick_wins", [])

    if quick_wins:
        grouped_keywords = group_keywords_into_priority_actions(quick_wins)
        if grouped_keywords:
            return grouped_keywords

    return [
        {
            "title": (top_opportunity or {}).get("diagnosis", "Refresh primary query page"),
            "action": (top_opportunity or {}).get(
                "recommended_next_step",
                f"Optimize {primary_page} for {primary_query['query']} by improving the page's search relevance and content coverage.",
            ),
            "reason": (top_opportunity or {}).get(
                "why_it_matters",
                "The strongest non-branded opportunity is already visible in search data, so improving page relevance could support more qualified website traffic.",
            ),
            "priority": "High",
        },
        {
            "title": "Build supporting query coverage",
            "action": (
                f"Create or expand supporting content for {secondary_query['query']} so it reinforces the primary page and captures adjacent intent."
            ),
            "reason": (
                "A second non-branded topic can expand topical authority and give the strategy a cleaner content cluster."
            ),
            "priority": "Medium",
        },
        {
            "title": "Improve conversion path on core page",
            "action": (
                f"Strengthen CTA placement, trust signals, and answer-first sections on {primary_page} so high-intent visitors can act faster."
            ),
            "reason": (
                "Better page structure helps convert existing demand instead of relying only on traffic growth."
            ),
            "priority": "Medium",
        },
    ]


def group_keywords_into_priority_actions(quick_wins: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Group related SEMrush quick-win keywords into action-oriented strategy items."""
    grouped_actions: dict[str, dict[str, Any]] = {}

    for item in quick_wins:
        keyword = str(item.get("keyword", "")).strip()
        if not keyword:
            continue

        group_key, title_label, recommended_page = classify_keyword_group(keyword, str(item.get("url", "")).strip())
        priority_score = score_priority_action(item, group_key)

        group = grouped_actions.setdefault(
            group_key,
            {
                "title_label": title_label,
                "recommended_page": recommended_page or "the relevant service page",
                "keywords": [],
                "best_position": 999.0,
                "total_volume": 0.0,
                "best_score": -1.0,
            },
        )

        group["keywords"].append(keyword)
        group["best_position"] = min(group["best_position"], float(item.get("position", 0) or 0))
        group["total_volume"] += float(item.get("volume", 0) or 0)
        group["best_score"] = max(group["best_score"], priority_score)

        if recommended_page:
            group["recommended_page"] = recommended_page

    sorted_groups = sorted(grouped_actions.values(), key=lambda group: group["best_score"], reverse=True)

    actions = []
    for group in sorted_groups[:5]:
        page_reference = group["recommended_page"]
        top_keywords = ", ".join(group["keywords"][:3])
        position_text = int(group["best_position"]) if group["best_position"] != 999.0 else "top-20"

        actions.append(
            {
                "title": f"Improve ranking for {group['title_label']} keywords",
                "action": (
                    f"Optimize {page_reference} by updating the title tag, H1, supporting copy, and FAQ/schema coverage for keywords such as {top_keywords}."
                ),
                "reason": (
                    f"These keywords are already ranking between positions 4 and 20, with the strongest opportunity around position {position_text}. "
                    "That existing visibility suggests a realistic chance to move into stronger top-of-page positions with focused on-page improvements."
                ),
                "priority": priority_from_score(group["best_score"]),
            }
        )

    return actions


def classify_keyword_group(keyword: str, url: str) -> tuple[str, str, str]:
    """Map related SEMrush keywords into a reusable business-relevant group."""
    keyword_lower = keyword.lower()

    if any(token in keyword_lower for token in ["saving", "savings", "afford", "coupon", "discount"]):
        return "botox_savings", "Botox Savings", url or "the Botox Savings page"
    if any(token in keyword_lower for token in ["cost", "price", "pricing"]):
        return "botox_cost", "Botox Cost", url or "the Botox cost page"
    if "botox" in keyword_lower and any(token in keyword_lower for token in ["migraine", "migraines"]):
        return "botox_migraine", "Botox for Migraine", url or "the Botox for Migraine page"
    if any(token in keyword_lower for token in ["migraine", "migraines"]):
        return "migraine_treatment", "Migraine Treatment", url or "the migraine treatment page"
    if any(token in keyword_lower for token in ["treatment", "treatments", "therapy", "specialist", "doctor"]):
        return "treatment_services", "Treatment Services", url or "the treatment page"
    return "general_service", keyword.title(), url or "the relevant service page"


def score_priority_action(item: dict[str, Any], group_key: str) -> float:
    """Score grouped quick-win actions using relevance, ranking range, and volume."""
    relevance_score_map = {
        "botox_savings": 5,
        "botox_cost": 5,
        "botox_migraine": 5,
        "migraine_treatment": 4,
        "treatment_services": 4,
        "general_service": 2,
    }
    position = float(item.get("position", 0) or 0)
    volume = float(item.get("volume", 0) or 0)

    relevance_score = relevance_score_map.get(group_key, 2)

    if 4 <= position <= 10:
        ranking_score = 5
    elif 11 <= position <= 15:
        ranking_score = 4
    elif 16 <= position <= 20:
        ranking_score = 3
    else:
        ranking_score = 1

    if volume >= 1000:
        volume_score = 3
    elif volume >= 250:
        volume_score = 2
    elif volume > 0:
        volume_score = 1
    else:
        volume_score = 0

    return float(relevance_score + ranking_score + volume_score)


def priority_from_score(score: float) -> str:
    """Convert numeric action score into High/Medium/Low priority."""
    if score >= 11:
        return "High"
    if score >= 7:
        return "Medium"
    return "Low"


def build_semrush_strategy_intelligence(
    semrush_positions_data: Any | None,
    semrush_pages_data: Any | None = None,
    semrush_topics_data: Any | None = None,
) -> dict[str, Any]:
    """Summarize SEMrush keyword, page, and topic intelligence without returning raw tables."""
    empty_payload = {
        "available": False,
        "quick_wins": [],
        "high_opportunity_keywords": [],
        "keyword_opportunities": [],
        "page_opportunities": [],
        "topic_opportunities": [],
        "intent_clusters": [],
        "aeo_geo_opportunities": [],
        "priority_page": None,
        "priority_topic": None,
    }

    has_positions = semrush_positions_data is not None and not getattr(semrush_positions_data, "empty", True)
    has_pages = semrush_pages_data is not None and not getattr(semrush_pages_data, "empty", True)
    has_topics = semrush_topics_data is not None and not getattr(semrush_topics_data, "empty", True)

    if not any([has_positions, has_pages, has_topics]):
        return empty_payload

    payload = dict(empty_payload)

    if has_positions:
        dataframe = semrush_positions_data.copy()
        dataframe.columns = [str(column).strip().lower() for column in dataframe.columns]

        if "keyword" in dataframe.columns:
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

            payload.update(
                {
                    "quick_wins": quick_wins,
                    "high_opportunity_keywords": high_opportunity_keywords,
                    "keyword_opportunities": keyword_opportunities,
                    "intent_clusters": build_intent_clusters(keyword_records),
                    "aeo_geo_opportunities": [
                        {
                            "keyword": item["keyword"],
                            "insight": (
                                f"{item['keyword']} is suited to answer-style, comparison, or local discovery content that can support AI overviews and decision-stage search."
                            ),
                        }
                        for item in aeo_geo_opportunities[:3]
                    ],
                }
            )

    if has_pages:
        payload["page_opportunities"] = build_page_opportunities(semrush_pages_data)
        if payload["page_opportunities"]:
            payload["priority_page"] = payload["page_opportunities"][0]

    if has_topics:
        payload["topic_opportunities"] = build_topic_opportunities(semrush_topics_data)
        if payload["topic_opportunities"]:
            payload["priority_topic"] = payload["topic_opportunities"][0]

    payload["available"] = any(
        [
            payload["quick_wins"],
            payload["high_opportunity_keywords"],
            payload["page_opportunities"],
            payload["topic_opportunities"],
        ]
    )

    return payload


def build_page_opportunities(semrush_pages_data: Any) -> list[dict[str, Any]]:
    """Create concise page-level SEMrush opportunities for strategy use."""
    dataframe = semrush_pages_data.copy()
    dataframe.columns = [str(column).strip().lower() for column in dataframe.columns]

    url_column = first_matching_column(dataframe, ["page", "url", "page url", "page_url"])
    traffic_column = first_matching_column(dataframe, ["traffic", "organic traffic"])
    keywords_column = first_matching_column(dataframe, ["keywords", "organic keywords"])

    if url_column is None:
        return []

    if traffic_column:
        dataframe[traffic_column] = to_numeric_series(dataframe, traffic_column)
    if keywords_column:
        dataframe[keywords_column] = to_numeric_series(dataframe, keywords_column)

    sort_column = traffic_column or keywords_column
    if sort_column:
        dataframe = dataframe.sort_values(sort_column, ascending=False)

    opportunities = []
    for _, row in dataframe.head(5).iterrows():
        page = str(row.get(url_column, "")).strip()
        if not page:
            continue

        traffic = int(row.get(traffic_column, 0) or 0) if traffic_column else 0
        keywords = int(row.get(keywords_column, 0) or 0) if keywords_column else 0
        priority = "High" if traffic >= 100 or keywords >= 20 else "Medium"

        opportunities.append(
            {
                "page": page,
                "traffic": traffic,
                "keywords": keywords,
                "priority": priority,
                "insight": (
                    f"{page} already attracts measurable organic visibility and is a good candidate for message, UX, and CTA improvements."
                ),
            }
        )

    return opportunities


def build_topic_opportunities(semrush_topics_data: Any) -> list[dict[str, Any]]:
    """Create framework-based topic opportunities for strategy use."""
    dataframe = semrush_topics_data.copy()
    dataframe.columns = [str(column).strip().lower() for column in dataframe.columns]

    topic_column = first_matching_column(dataframe, ["topic", "keyword", "title"])
    volume_column = first_matching_column(dataframe, ["volume", "search volume"])
    competitor_column = first_matching_column(dataframe, ["competitors", "competitor presence", "competition"])

    if topic_column is None:
        return []

    if volume_column:
        dataframe[volume_column] = to_numeric_series(dataframe, volume_column)
    if competitor_column:
        dataframe[competitor_column] = to_numeric_series(dataframe, competitor_column)

    sort_column = volume_column or competitor_column
    if sort_column:
        dataframe = dataframe.sort_values(sort_column, ascending=False)

    opportunities = []
    for _, row in dataframe.head(5).iterrows():
        topic = str(row.get(topic_column, "")).strip()
        if not topic:
            continue

        volume = int(row.get(volume_column, 0) or 0) if volume_column else 0
        competitors = int(row.get(competitor_column, 0) or 0) if competitor_column else 0
        intent_type = infer_topic_intent_type(topic)
        opportunity_type = infer_topic_opportunity_type(topic, intent_type)
        gap_type = infer_topic_gap_type(topic, opportunity_type, competitors, volume)
        framework_recommendation = build_topic_framework_recommendation(
            topic=topic,
            intent_type=intent_type,
            opportunity_type=opportunity_type,
            gap_type=gap_type,
            volume=volume,
            competitors=competitors,
        )

        opportunities.append(
            {
                "topic": topic,
                "volume": volume,
                "competitors": competitors,
                "intent_type": intent_type,
                "opportunity_type": opportunity_type,
                "gap_type": gap_type,
                "issue": framework_recommendation["issue"],
                "action": framework_recommendation["action"],
                "why_it_matters": framework_recommendation["why_it_matters"],
                "priority": framework_recommendation["priority"],
                "recommended_action": framework_recommendation["action"],
                "insight": framework_recommendation["issue"],
            }
        )

    return opportunities


def infer_topic_intent_type(topic: str) -> str:
    """Classify topic intent using simple framework-friendly rules."""
    topic_lower = topic.lower()

    if any(token in topic_lower for token in ["near me", "chicago", "evergreen park", "oak lawn", "orland park", "local"]):
        return "local"
    if any(token in topic_lower for token in ["vs", "versus", "compare", "best", "review", "reviews", "top"]):
        return "comparison"
    if any(token in topic_lower for token in ["cost", "price", "book", "appointment", "clinic", "doctor", "specialist", "treatment"]):
        return "transactional"
    return "informational"


def infer_topic_opportunity_type(topic: str, intent_type: str) -> str:
    """Map topic themes to AI Strategy Framework opportunity types."""
    topic_lower = topic.lower()

    if any(token in topic_lower for token in ["reddit", "forum", "quora", "community", "discussion"]):
        return "community"
    if intent_type == "local":
        return "local"
    if intent_type == "comparison" or any(token in topic_lower for token in ["best", "vs", "compare", "reviews"]):
        return "mention"
    return "citation"


def infer_topic_gap_type(topic: str, opportunity_type: str, competitors: int, volume: int) -> str:
    """Infer the most likely content gap for the topic."""
    topic_lower = topic.lower()

    if competitors >= 5 or any(token in topic_lower for token in ["best", "reviews", "top", "specialist"]):
        return "lack of authority"
    if opportunity_type == "community":
        return "missing content"
    if opportunity_type == "mention":
        return "weak content"
    if opportunity_type == "local":
        return "poor structure" if volume >= 250 else "weak content"
    if any(token in topic_lower for token in ["how", "what", "why", "cost", "faq"]):
        return "poor structure"
    return "missing content"


def build_topic_framework_recommendation(
    topic: str,
    intent_type: str,
    opportunity_type: str,
    gap_type: str,
    volume: int,
    competitors: int,
) -> dict[str, str]:
    """Build topic recommendations using AI Strategy Framework rules."""
    priority = score_topic_framework_priority(intent_type, opportunity_type, volume, competitors)

    if opportunity_type == "citation":
        issue = (
            f"{topic} is more likely to win citations with structured factual content, but the current gap suggests {gap_type}."
        )
        action = (
            f"Create or rework a page for {topic} with direct definitions, fact-led subheads, FAQ schema, comparison tables where relevant, and clearly sourced answers."
        )
        why_it_matters = (
            "Citation-style opportunities are stronger when the content is easy for search engines and AI systems to extract, summarize, and trust."
        )
    elif opportunity_type == "mention":
        issue = (
            f"{topic} is a mention-driven comparison opportunity, but weak brand inclusion and {gap_type} are limiting visibility."
        )
        action = (
            f"Build comparison-ready content for {topic} that positions the brand in shortlist-style evaluations, adds differentiators, and reinforces entity signals across supporting pages."
        )
        why_it_matters = (
            "Comparison and best-of queries often reward brands that are clearly included, differentiated, and supported by strong entity and review signals."
        )
    elif opportunity_type == "community":
        issue = (
            f"{topic} is surfacing as a community-led discovery topic, but the current gap indicates {gap_type} in forum and discussion coverage."
        )
        action = (
            f"Develop a Reddit/forums strategy for {topic} by identifying recurring questions, publishing answer-led supporting content, and creating assets that can be cited naturally in community discussions."
        )
        why_it_matters = (
            "Community-led search journeys often shape discovery before brand visits, so owning the supporting answers improves visibility earlier in the decision process."
        )
    else:
        issue = (
            f"{topic} has local discovery potential, but {gap_type} is weakening local relevance and authority."
        )
        action = (
            f"Strengthen local pages for {topic} with location-specific headings, provider proof, review snippets, service-area language, and clearer entity/trust signals."
        )
        why_it_matters = (
            "Local AI and search results rely on strong geographic relevance plus authority markers such as reviews, expertise, and entity consistency."
        )

    if gap_type == "lack of authority":
        action += " Support the page with trust signals, expert bios, review proof, authoritative mentions, and backlinkable assets."
        why_it_matters += " Stronger authority signals help the brand compete when other sites already dominate the topic."

    return {
        "issue": issue,
        "action": action,
        "why_it_matters": why_it_matters,
        "priority": priority,
    }


def score_topic_framework_priority(intent_type: str, opportunity_type: str, volume: int, competitors: int) -> str:
    """Assign priority to topic opportunities using framework-friendly weights."""
    score = 0

    if volume >= 500:
        score += 3
    elif volume >= 250:
        score += 2
    elif volume > 0:
        score += 1

    if competitors >= 5:
        score += 3
    elif competitors >= 3:
        score += 2
    elif competitors > 0:
        score += 1

    if intent_type in {"transactional", "local"}:
        score += 2
    elif intent_type == "comparison":
        score += 1

    if opportunity_type in {"mention", "local"}:
        score += 2
    elif opportunity_type in {"citation", "community"}:
        score += 1

    if score >= 8:
        return "High"
    if score >= 5:
        return "Medium"
    return "Low"


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


def first_matching_column(dataframe: Any, candidates: list[str]) -> str | None:
    """Return the first matching normalized column name."""
    normalized_columns = {str(column).strip().lower(): column for column in dataframe.columns}
    for candidate in candidates:
        if candidate in normalized_columns:
            return normalized_columns[candidate]
    return None


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
