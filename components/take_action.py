"""Take Action payload and rendering helpers."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st


def build_take_action_payload(
    card: dict,
    results: dict,
    *,
    get_first_value_fn: Callable[[list[dict], str, str], str],
    build_semrush_opportunity_cards_fn: Callable,
    humanize_social_topic_fn: Callable[[str], str],
) -> dict | None:
    """Build a drill-down action payload for supported recommendation types."""
    if not results or not card:
        return None

    category = str(card.get("category", "")).strip().lower()

    insight = results.get("insight", {})
    strategy = results.get("strategy", {}).get("strategy", {})
    combined = results.get("data_intake", {}).get("summary", {}).get("combined", {})
    semrush_positions_data = results.get("semrush_positions_data")
    top_query = get_first_value_fn(insight.get("high_impression_low_click", []), "query")
    primary_page = (
        str(strategy.get("primary_page", "")).strip()
        or get_first_value_fn(combined.get("top_pages", []), "page_title")
    )
    page_label = primary_page if primary_page and primary_page != "Not available" else "priority landing page"

    if category in {"seo", "seo_keyword_strategy"}:
        keywords: list[str] = []
        if top_query != "Not available":
            keywords.append(top_query)

        if semrush_positions_data is not None and not getattr(semrush_positions_data, "empty", True):
            for item in build_semrush_opportunity_cards_fn(semrush_positions_data)[:5]:
                keyword = str(item.get("keyword", "")).strip()
                if keyword and keyword not in keywords:
                    keywords.append(keyword)

        for item in insight.get("query_analysis", [])[:5]:
            query = str(item.get("query", "")).strip()
            if query and query not in keywords:
                keywords.append(query)

        keywords = keywords[:5]
        focus_keyword = keywords[0] if keywords else "priority keyword"

        return {
            "type": "seo",
            "button_label": "View keyword opportunities & rewrite examples",
            "headline": "SEO Take Action",
            "keywords": keywords or ["No strong keyword set available from the current run."],
            "rewrites": {
                "title_tag": f"{focus_keyword.title()} | {page_label}",
                "h1": f"{focus_keyword.title()}: What Patients Should Know",
                "meta_description": (
                    f"Explore {focus_keyword} on {page_label}. Get clear answers, stronger on-page guidance, and the next step for patients ready to take action."
                ),
            },
            "meta_description_suggestions": [
                f"Clarify the value of {focus_keyword} and include a patient-oriented next step in the meta description.",
                "Use more decision-stage language so the snippet feels more actionable in search results.",
                "Test one version focused on expertise and one focused on symptom or treatment intent.",
            ],
            "keyword_variations": [f"{focus_keyword} near me", f"{focus_keyword} cost", f"best {focus_keyword}"],
            "internal_links": [
                f"Add an internal link from related educational pages to {page_label} using {focus_keyword} language.",
                "Link supporting FAQ or blog content back to the primary page with intent-matched anchor text.",
                "Add one conversion-oriented internal link near the middle of the page and one near the CTA section.",
            ],
        }

    if category in {"aeo", "aeo_geo", "aeo_geo_ai_search"}:
        related_queries = [
            str(item.get("query", "")).strip()
            for item in insight.get("query_analysis", [])[:5]
            if str(item.get("query", "")).strip()
        ]
        answer_focus = top_query if top_query != "Not available" else (related_queries[0] if related_queries else "the priority query")
        faq_suggestions = [f"Add a direct answer block for '{query}' near the top of {page_label}." for query in related_queries[:3]]
        if not faq_suggestions:
            faq_suggestions = [
                f"Add a direct answer block for {answer_focus} near the top of {page_label}.",
                "Add a comparison-style FAQ that addresses the most likely follow-up question.",
                "Add a concise decision-stage FAQ that supports AI answer extraction.",
            ]

        return {
            "type": "aeo",
            "button_label": "View answer block & FAQ suggestions",
            "headline": "AEO Take Action",
            "faq_ideas": faq_suggestions,
            "heading_ideas": [
                f"What should patients know about {answer_focus}?",
                f"Who is a good candidate for {answer_focus}?",
                f"When should someone seek help for {answer_focus}?",
            ],
            "answer_blocks": [
                f"Lead {page_label} with a concise answer block for {answer_focus}.",
                "Use a short definition, a one-sentence explanation, and a quick next-step answer under the main heading.",
                "Break long answers into digestible blocks so AI systems can lift the most relevant section cleanly.",
            ],
            "paragraph_rewrites": [
                f"{answer_focus.title()} can be explained in one direct sentence first, followed by one short supporting paragraph and a practical next step.",
                "Start each key section with the plain-language answer before adding detail, nuance, or proof.",
                "Use one example or patient-facing scenario after the direct answer so the content stays helpful without becoming dense.",
            ],
            "structure_examples": [
                "Use a question heading followed by a 2-3 sentence direct answer.",
                "Follow the answer with a short bullet list and one supporting fact or comparison.",
                f"Place the answer block high on {page_label} so both users and AI systems can find it quickly.",
            ],
            "schema_recommendations": [
                "Add FAQ schema to the page section that contains the strongest answer-driven questions.",
                "Use Article, Service, or LocalBusiness schema where the page purpose clearly supports it.",
                "Use concise comparison or definition language that is easier for featured snippets and AI summaries to quote.",
            ],
            "snippet_formatting": [
                "Use a direct 40-60 word answer immediately under the question heading.",
                "Follow the answer with bullets or a numbered list for scannability.",
                "Use one consistent heading structure so the page is easier to parse for featured snippets and AI Overviews.",
            ],
            "ai_overview_optimizations": [
                "Answer the main patient question plainly before moving into longer supporting detail.",
                "Use comparison language, definitions, and eligibility-style answers that AI Overviews often summarize.",
                "Make provider, treatment, and location entities explicit so the page is easier for AI systems to cite.",
            ],
        }

    if category == "geo":
        geo_focus = top_query if top_query != "Not available" else "priority local search terms"
        return {
            "type": "geo",
            "button_label": "View local search & GBP improvements",
            "headline": "GEO Take Action",
            "local_keyword_targets": [
                f"{geo_focus} near me",
                f"{geo_focus} in evergreen park",
                f"{geo_focus} specialist chicago",
            ],
            "entity_consistency_checklist": [
                "Use the same brand, provider, organization, and location language across the website, GBP, and directories.",
                "Keep treatment/service descriptions consistent so AI systems can connect the same entity across sources.",
                "Align business category, service list, and local descriptors across every profile that mentions the brand.",
            ],
            "city_service_page_opportunities": [
                "Build or refresh city + service pages that connect treatment intent with location-specific demand.",
                f"Expand {page_label} with clearer service-area language and location-specific patient concerns.",
                "Add unique local FAQs so city/service pages are not thin variations of each other.",
            ],
            "gbp_improvements": [
                "Refresh Google Business Profile services, business description, and treatment-specific categories.",
                "Add recent photos, service highlights, and posts that reinforce the primary local treatment focus.",
                "Keep appointment, call, and website actions aligned with the main landing-page CTA.",
            ],
            "local_trust_signals": [
                "Surface provider credentials, local proof, and service-area reassurance near conversion points.",
                "Add neighborhood, city, or nearby-location references where they support real patient intent.",
                "Strengthen on-page review snippets or testimonial placement for local decision-stage visitors.",
            ],
            "citation_review_recommendations": [
                "Audit core local citations for NAP consistency and treatment/service accuracy.",
                "Request fresh review language that mentions both service quality and location relevance when appropriate.",
                "Make sure review and citation signals reinforce the same primary service themes as the page.",
            ],
            "quotable_insight_suggestions": [
                "Add one or two short expert statements that explain a treatment or symptom clearly enough to quote externally.",
                "Use provider insights that sound authoritative, specific, and easy for AI systems or journalists to reuse.",
                "Turn complex treatment explanations into one-sentence plain-language insights that can travel beyond the page.",
            ],
            "external_trust_signal_opportunities": [
                "Strengthen review volume and review specificity on trusted third-party platforms.",
                "Look for PR, podcast, YouTube, or community/forum opportunities that reinforce expertise and brand mention frequency.",
                "Support citation readiness with trustworthy off-site mentions that use consistent entity language.",
            ],
        }

    if category in {"ux_conversion", "website_ux_conversion"}:
        return {
            "type": "ux_conversion",
            "button_label": "View CTA & landing page improvements",
            "headline": "UX Conversion Take Action",
            "conversion_suggestions": [
                f"Rewrite the primary CTA on {page_label} so the next step is visible without heavy scrolling.",
                "Bring trust signals closer to the CTA, including provider reassurance, outcomes, or patient confidence signals.",
                "Reduce decision friction by tightening headline-to-CTA message alignment.",
            ],
            "checklist": [
                "Primary CTA above the fold",
                "Supporting CTA after the main answer section",
                "Trust block near the booking or contact action",
                "Clear form, quiz, or consultation next step",
            ],
            "cta_rewrites": [
                "Book Your Migraine Evaluation",
                "See If This Treatment Is Right For You",
                "Start With a Quick Patient Next Step",
            ],
            "landing_page_clarity": [
                "Make the main page promise clearer in the first screen so users know exactly what problem the page solves.",
                "Use one primary next step and remove messaging that competes with the main conversion action.",
                "Clarify what happens after the CTA so users feel less uncertainty before taking action.",
            ],
            "page_structure_fixes": [
                "Move the main value proposition higher on the page before dense explanation sections.",
                "Group FAQs, trust, and CTA sections so the user can move from question to action more easily.",
                "Tighten long paragraphs into shorter blocks with clearer section hierarchy.",
            ],
            "friction_reduction": [
                "Reduce the number of decisions required before a visitor can take the next step.",
                "Clarify whether the CTA leads to booking, consultation, quiz, or contact so the action feels lower risk.",
                "Remove repeated or competing calls to action that can dilute intent.",
            ],
            "trust_improvements": [
                "Bring provider trust, treatment credibility, and patient reassurance closer to the first CTA.",
                "Use concise proof points before the action area so the conversion decision feels safer.",
                "Make care-path clarity more visible for users who are not ready to book immediately.",
            ],
            "ux_recommendations": [
                "Shorten or reorganize dense sections before the first conversion action.",
                "Use visual hierarchy so benefits, trust, and next steps are easier to scan.",
                "Keep mobile CTA placement and form friction under review for the primary landing page.",
            ],
        }

    if category == "content_expansion":
        topic_opportunities = strategy.get("topic_opportunities", [])
        topic_names = [str(item.get("topic", "")).strip() for item in topic_opportunities if str(item.get("topic", "")).strip()]
        if not topic_names:
            topic_names = [
                str(item.get("query", "")).strip()
                for item in insight.get("query_analysis", [])[:5]
                if str(item.get("query", "")).strip()
            ]
        topic_focus = topic_names[0] if topic_names else "the primary topic opportunity"

        return {
            "type": "content_expansion",
            "button_label": "View supporting content ideas",
            "headline": "Content Expansion Take Action",
            "supporting_content_ideas": [f"Create a supporting article focused on {topic}." for topic in topic_names[:3]]
            or [f"Create a supporting article focused on {topic_focus}."],
            "new_page_recommendations": [
                f"Build a focused landing page or guide for {topic_focus}.",
                "Add a blog or resource piece that addresses the next most relevant related query.",
                f"Use {page_label} as the hub page and connect new content back to it with internal links.",
            ],
            "topic_cluster_suggestions": [
                "Choose one hub page and 2-3 supporting articles around the same patient intent theme.",
                "Link informational content to the conversion page so traffic can move deeper into the funnel.",
                "Reuse strong FAQs across the cluster so the site builds clearer topical authority.",
            ],
        }

    if category == "social" or category.startswith("social_"):
        social_insights = results.get("social_insights", {})
        top_examples_rows = social_insights.get("top_performing_content", []) or []
        conversion_rows = social_insights.get("conversion_content", []) or []
        best_post_type = str(social_insights.get("best_post_type", "Not available")).strip()
        top_topics = social_insights.get("top_topics", []) or []
        what_drives_follows = str(social_insights.get("what_drives_follows", "Not available")).strip()
        what_drives_saves = str(social_insights.get("what_drives_saves", "Not available")).strip()

        top_examples = []
        seen_examples = set()
        for row in top_examples_rows[:3] + conversion_rows[:3]:
            hook = str(row.get("Hook", "")).strip()
            post_type = str(row.get("Post type", "Unknown")).strip()
            topic = humanize_social_topic_fn(str(row.get("Topic", "general")).strip())
            example_key = (hook, post_type, topic)
            if example_key in seen_examples:
                continue
            seen_examples.add(example_key)
            example_text = f"{post_type} | {topic}"
            if hook:
                example_text = f"{post_type} | {topic} | Hook: {hook}"
            top_examples.append(example_text)
            if len(top_examples) == 3:
                break

        why_they_worked = []
        if what_drives_follows and what_drives_follows != "Not available":
            why_they_worked.append(what_drives_follows)
        if what_drives_saves and what_drives_saves != "Not available":
            why_they_worked.append(what_drives_saves)
        if best_post_type and best_post_type != "Not available":
            why_they_worked.append(f"{best_post_type} is the strongest current format in this run.")
        if top_topics:
            why_they_worked.append(
                f"Top topic signal: {', '.join(humanize_social_topic_fn(topic) for topic in top_topics[:2])}."
            )

        base_topic = humanize_social_topic_fn(top_topics[0]) if top_topics else "the strongest current topic"
        format_label = best_post_type if best_post_type and best_post_type != "Not available" else "your best-performing format"
        base_hook = str(top_examples_rows[0].get("Hook", "")).strip() if top_examples_rows else ""

        variations = [
            f"{format_label} variation focused on {base_topic} with a stronger booking-oriented CTA.",
            f"{format_label} variation that reuses the winning structure but tests a shorter first-line hook.",
            f"{format_label} variation that turns the current high-interest topic into a clearer follow-driving post.",
        ]
        if base_hook:
            variations[1] = f"{format_label} variation using a hook inspired by '{base_hook}' with a tighter patient outcome angle."

        return {
            "type": "social",
            "button_label": "View top-performing posts & content variations",
            "headline": "Social Take Action",
            "top_examples": top_examples or ["No high-performing examples were available from the current run."],
            "why_they_worked": why_they_worked or ["Not enough social performance context is loaded yet."],
            "hook_ideas": [
                "Lead with the patient problem in the first line instead of the brand or service name.",
                "Turn a common objection into the opening hook so the post feels immediately relevant.",
                "Use a short symptom-based or outcome-based first line that is easier to stop on in-feed.",
            ],
            "engagement_improvements": [
                "Use clearer tension in the first line so the audience has a reason to keep reading or watching.",
                "Shorten the path from hook to value so the post rewards attention faster.",
                "End with one focused prompt instead of multiple competing asks.",
            ],
            "retention_strategy": [
                "Front-load the strongest value point in the first second or first line.",
                "Use a tighter narrative arc so the audience has a reason to stay through the middle of the post.",
                "Break educational posts into cleaner beats or slides so the payoff builds instead of flattening out.",
            ],
            "format_recommendations": [
                f"Use {format_label} more aggressively when the goal is to repeat the strongest current format signal.",
                "Turn one winning concept into Reel, carousel, and static variants before moving to new topics.",
                "Match the format to the job: education for saves, authority for trust, and sharper CTA for conversion.",
            ],
            "post_angles": [
                f"Create a patient-facing version of {base_topic} that speaks to the pain point more directly.",
                "Turn a myth, question, or objection into a content angle that feels more discussion-worthy.",
                "Take one topic and create beginner, comparison, and next-step versions so the message fits multiple funnel stages.",
            ],
            "captions": [
                "Use shorter opening lines with one clear emotional or practical tension point.",
                "Add one trust-building sentence before the CTA so the post feels more complete.",
                "Close with a single next step instead of stacking multiple asks in the caption.",
            ],
            "hook_cta_examples": [
                "Hook: Still dealing with symptoms and not sure what to do next? | CTA: Start with a quick evaluation.",
                "Hook: What most patients misunderstand about treatment options. | CTA: See if this is the right next step.",
                "Hook: This is why some posts get saved but do not convert. | CTA: Use one clear next action.",
            ],
            "repurposing": [
                "Turn the strongest Reel idea into a carousel and one short image-post version.",
                "Break one high-performing topic into a mini-series instead of a one-off post.",
                "Use the same core idea for awareness, trust, and conversion versions.",
            ],
            "variations": variations,
        }

    return {
        "type": "general",
        "button_label": "View strategic next steps",
        "headline": "Strategic Take Action",
        "next_steps": [
            "Prioritize the highest-confidence recommendation first and turn it into a concrete experiment.",
            "Match one metric, one page or asset, and one next step so execution stays focused.",
            "Review performance after implementation and decide whether to scale, refine, or replace the tactic.",
        ],
    }


def _render_list_section(title: str, items: list[str]) -> None:
    if not items:
        return
    list_items = "".join(f"<li>{item}</li>" for item in items)
    st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
    st.markdown(f'<div class="take-action-section-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<ul class="take-action-list">{list_items}</ul>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_take_action_block(payload: dict, unique_key: str) -> None:
    """Render the take-action drill-down UI block."""
    if not payload:
        return

    icon_map = {
        "seo": "↗",
        "aeo": "?",
        "geo": "◎",
        "ux_conversion": "UX",
        "content_expansion": "+",
        "social": "✦",
        "general": "→",
    }
    icon = icon_map.get(payload.get("type"), "→")

    st.markdown('<div class="take-action-panel">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="take-action-header">
            <div class="take-action-icon">{icon}</div>
            <div class="take-action-title">{payload.get('headline', 'Take Action')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if payload.get("type") == "seo":
        _render_list_section("Best Keywords", payload.get("keywords", []))

        rewrites = payload.get("rewrites", {})
        if rewrites:
            rewrite_text = (
                f"<strong>Title Tag:</strong><br>{rewrites.get('title_tag', '')}"
                f"<br><br><strong>H1:</strong><br>{rewrites.get('h1', '')}"
                f"<br><br><strong>Meta Description:</strong><br>{rewrites.get('meta_description', '')}"
            )
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Rewrite Examples</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="take-action-code">{rewrite_text}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        _render_list_section("FAQ Ideas", payload.get("faq_ideas", []))
        _render_list_section("Suggested Keyword Variations", payload.get("keyword_variations", []))
        _render_list_section("Meta Description Suggestions", payload.get("meta_description_suggestions", []))
        _render_list_section("Internal Linking Ideas", payload.get("internal_links", []))
    elif payload.get("type") == "aeo":
        _render_list_section("FAQ Ideas", payload.get("faq_ideas", []))
        _render_list_section("Answer Block Suggestions", payload.get("answer_blocks", []))
        _render_list_section("Question-Based Heading Ideas", payload.get("heading_ideas", []))
        _render_list_section("Answer-First Paragraph Rewrites", payload.get("paragraph_rewrites", []))
        _render_list_section("Schema / Citation Recommendations", payload.get("schema_recommendations", []))
        _render_list_section("Featured Snippet Formatting", payload.get("snippet_formatting", []))
        _render_list_section("AI Overview Optimization", payload.get("ai_overview_optimizations", []))
    elif payload.get("type") == "geo":
        _render_list_section("Entity Consistency Checklist", payload.get("entity_consistency_checklist", []))
        _render_list_section("Local Keyword Targets", payload.get("local_keyword_targets", []))
        _render_list_section("City / Service Page Opportunities", payload.get("city_service_page_opportunities", []))
        _render_list_section("Google Business Profile Improvements", payload.get("gbp_improvements", []))
        _render_list_section("Local Trust Signals", payload.get("local_trust_signals", []))
        _render_list_section("Citation / Review Recommendations", payload.get("citation_review_recommendations", []))
        _render_list_section("Quotable Insight Suggestions", payload.get("quotable_insight_suggestions", []))
        _render_list_section("External Trust Signal Opportunities", payload.get("external_trust_signal_opportunities", []))
    elif payload.get("type") == "ux_conversion":
        _render_list_section("CTA Rewrites", payload.get("cta_rewrites", []))
        _render_list_section("Landing Page Clarity", payload.get("landing_page_clarity", []))
        _render_list_section("CTA / Trust / Conversion Suggestions", payload.get("conversion_suggestions", []))
        _render_list_section("Page Structure Fixes", payload.get("page_structure_fixes", []))
        _render_list_section("Friction Reduction", payload.get("friction_reduction", []))
        _render_list_section("Trust Improvements", payload.get("trust_improvements", []))
        _render_list_section("Landing Page Improvement Checklist", payload.get("checklist", []))
        _render_list_section("UX Recommendations", payload.get("ux_recommendations", []))
    elif payload.get("type") == "content_expansion":
        _render_list_section("Supporting Content Ideas", payload.get("supporting_content_ideas", []))
        _render_list_section("New Page / Blog Recommendations", payload.get("new_page_recommendations", []))
        _render_list_section("Topic Cluster Expansion Suggestions", payload.get("topic_cluster_suggestions", []))
    elif payload.get("type") == "social":
        _render_list_section("Hook Ideas", payload.get("hook_ideas", []))
        _render_list_section("Engagement Improvements", payload.get("engagement_improvements", []))
        _render_list_section("Retention Strategy", payload.get("retention_strategy", []))
        _render_list_section("Format Recommendations", payload.get("format_recommendations", []))
        _render_list_section("Post Angles", payload.get("post_angles", []))
        _render_list_section("Caption Ideas", payload.get("captions", []))
        _render_list_section("Top Examples", payload.get("top_examples", []))
        _render_list_section("Why They Worked", payload.get("why_they_worked", []))
        _render_list_section("Hook / CTA Examples", payload.get("hook_cta_examples", []))
        _render_list_section("New Variations", payload.get("variations", []))
        _render_list_section("Repurposing Ideas", payload.get("repurposing", []))
    elif payload.get("type") == "general":
        _render_list_section("Strategic Next Steps", payload.get("next_steps", []))
    else:
        st.info("No drill-down action plan is available for this recommendation yet.")

    st.markdown("</div>", unsafe_allow_html=True)


def render_recommendation_take_action(
    card: dict,
    results: dict,
    unique_key: str,
    *,
    get_first_value_fn: Callable[[list[dict], str, str], str],
    build_semrush_opportunity_cards_fn: Callable,
    humanize_social_topic_fn: Callable[[str], str],
) -> None:
    """Render a Take Action control and drill-down block when supported."""
    payload = build_take_action_payload(
        card,
        results,
        get_first_value_fn=get_first_value_fn,
        build_semrush_opportunity_cards_fn=build_semrush_opportunity_cards_fn,
        humanize_social_topic_fn=humanize_social_topic_fn,
    )
    if not payload:
        return

    open_key = f"take_action_open_{unique_key}"
    button_key = f"take_action_button_{unique_key}"
    is_open = st.session_state.get(open_key, False)
    button_label = "Hide Take Action" if is_open else payload.get("button_label", "Take Action")

    if st.button(button_label, key=button_key, type="primary"):
        st.session_state[open_key] = not is_open

    if st.session_state.get(open_key, False):
        render_take_action_block(payload, unique_key)
