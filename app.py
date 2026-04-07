"""Simple Streamlit interface for the AI Marketing Workflow System."""

from __future__ import annotations

import json
from io import BytesIO

import pandas as pd
import streamlit as st

from main import run_workflow
from utils.parser import parse_uploaded_csv


st.set_page_config(page_title="AI Marketing Workflow System", layout="wide")
st.markdown(
    """
    <style>
    .dashboard-title {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    .dashboard-subtitle {
        color: #5b6470;
        margin-bottom: 1.5rem;
    }
    .panel {
        background: #f7f9fc;
        border: 1px solid #e6ebf2;
        border-radius: 14px;
        padding: 1rem 1.1rem;
        margin-bottom: 1rem;
    }
    .panel-title {
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
    }
    .change-card {
        background: #ffffff;
        border: 1px solid #e6ebf2;
        border-radius: 14px;
        padding: 1rem 1.1rem;
        margin-bottom: 1rem;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
    }
    .mock-block {
        background: #f7f9fc;
        border: 1px dashed #cdd6e1;
        border-radius: 10px;
        padding: 0.85rem;
        margin-top: 0.5rem;
    }
    .recommendation-card {
        background: #ffffff;
        border: 1px solid #e6ebf2;
        border-radius: 14px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
    }
    .recommendation-card-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 0.75rem;
        flex-wrap: wrap;
    }
    .recommendation-category {
        font-size: 0.9rem;
        font-weight: 600;
        color: #111827;
        letter-spacing: 0.01em;
    }
    .recommendation-body {
        color: #374151;
        font-size: 0.95rem;
        line-height: 1.55;
    }
    .priority-high-pill {
        display: inline-block;
        background: #fee2e2;
        color: #b91c1c;
        border: 1px solid #fecaca;
        border-radius: 999px;
        padding: 0.3rem 0.65rem;
        font-size: 0.75rem;
        font-weight: 700;
        white-space: nowrap;
    }
    .priority-medium-pill {
        display: inline-block;
        background: #ffedd5;
        color: #c2410c;
        border: 1px solid #fed7aa;
        border-radius: 999px;
        padding: 0.3rem 0.65rem;
        font-size: 0.75rem;
        font-weight: 700;
        white-space: nowrap;
    }
    .priority-low-pill {
        display: inline-block;
        background: #e5e7eb;
        color: #374151;
        border: 1px solid #d1d5db;
        border-radius: 999px;
        padding: 0.3rem 0.65rem;
        font-size: 0.75rem;
        font-weight: 700;
        white-space: nowrap;
    }

    .what-next-card {
        background: #ffffff;
        border: 1px solid #e6ebf2;
        border-radius: 14px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
    }
    .what-next-title {
        font-size: 1rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 0.5rem;
    }
    .what-next-label {
        font-weight: 600;
        color: #111827;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_first_value(items: list[dict], key: str, fallback: str = "Not available") -> str:
    """Return the first item value when it exists."""
    if items:
        return str(items[0].get(key, fallback))
    return fallback


def parse_semrush_positions_csv(file) -> pd.DataFrame:
    """Read an uploaded SEMrush Organic Positions CSV into a DataFrame."""
    if file is None:
        return pd.DataFrame()

    return pd.read_csv(file)


def parse_semrush_pages_csv(file) -> pd.DataFrame:
    """Read an uploaded SEMrush Pages Report CSV into a DataFrame."""
    if file is None:
        return pd.DataFrame()

    return pd.read_csv(file)


def parse_semrush_topics_csv(file) -> pd.DataFrame:
    """Read an uploaded SEMrush Topic Opportunities CSV into a DataFrame."""
    if file is None:
        return pd.DataFrame()

    return pd.read_csv(file)


def format_heading(value: str) -> str:
    """Convert keys like ux_conversion into clean labels."""
    return value.replace("_", " ").upper()


def has_uploaded_data(files: list[object | None]) -> bool:
    """Return True when at least one upload is present."""
    return any(file is not None for file in files)


def build_scorecard(results: dict) -> dict[str, str]:
    """Collect the main scorecard values from workflow results."""
    insight = results["insight"]
    top_opportunity_item = insight["high_impression_low_click"][0] if insight["high_impression_low_click"] else {}

    top_opportunity_query = get_first_value(insight["high_impression_low_click"], "query")
    top_ctr_gap = get_first_value(insight["high_impression_low_click"], "ctr")
    top_traffic_source = get_first_value(insight["top_sources"], "source_medium")
    opportunity_score = str(top_opportunity_item.get("opportunity_score", "Not available"))

    return {
        "Opportunity Score": opportunity_score,
        "Top Opportunity": top_opportunity_query,
        "CTR Gap": top_ctr_gap,
        "Top Traffic Source": top_traffic_source,
    }


def render_scorecard(results: dict) -> None:
    """Show dashboard metrics in a presentation-friendly layout."""
    scorecard = build_scorecard(results)

    row_one = st.columns(4)
    with row_one[0]:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.metric("Opportunity Score", scorecard["Opportunity Score"])
        st.markdown("</div>", unsafe_allow_html=True)
    with row_one[1]:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.metric("Top Opportunity", scorecard["Top Opportunity"])
        st.markdown("</div>", unsafe_allow_html=True)
    with row_one[2]:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.metric("CTR Gap", scorecard["CTR Gap"])
        st.markdown("</div>", unsafe_allow_html=True)
    with row_one[3]:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.metric("Top Traffic Source", scorecard["Top Traffic Source"])
        st.markdown("</div>", unsafe_allow_html=True)


def render_client_report(results: dict) -> None:
    """Show a simplified client-facing report view."""
    insight = results["insight"]
    strategy = results["strategy"]["strategy"]
    evaluation = results["evaluation"]["evaluation"]

    st.subheader("Executive Summary")
    st.write(
        f"The strongest current opportunity is **{get_first_value(insight['high_impression_low_click'], 'query')}**, "
        f"supported by traffic to **{strategy['primary_page']}** and acquisition led by "
        f"**{get_first_value(insight['top_sources'], 'source_medium')}**."
    )

    st.subheader("Key Insights")
    for item in insight["patterns"][:5]:
        st.write(f"- {item}")

    st.subheader("Recommended Actions")

    for category, recommendations in strategy["recommendations"].items():
        visible_recommendations = []

        for recommendation in recommendations:
            if isinstance(recommendation, dict):
                issue = recommendation.get("issue", "").strip()
                rec_text = recommendation.get("recommendation", "").strip()
                why = recommendation.get("why_it_matters", "").strip()
                priority = recommendation.get("priority", "").strip()

                if issue or rec_text or why:
                    visible_recommendations.append(
                        {
                            "issue": issue,
                            "recommendation": rec_text,
                            "why": why,
                            "priority": priority,
                        }
                    )
            elif isinstance(recommendation, str) and recommendation.strip():
                visible_recommendations.append(
                    {
                        "issue": "",
                        "recommendation": recommendation.strip(),
                        "why": "",
                        "priority": "",
                    }
                )

        if not visible_recommendations:
            continue

        st.markdown(f"### {format_heading(category)}")

        for item in visible_recommendations:
            if item["priority"]:
                st.markdown(f"**Priority:** {item['priority']}")
            if item["issue"]:
                st.markdown(f"**Issue:** {item['issue']}")
            if item["recommendation"]:
                st.markdown(f"**Recommendation:** {item['recommendation']}")
            if item["why"]:
                st.markdown(f"**Why it matters:** {item['why']}")
            st.markdown("---")

    st.subheader("Priority Opportunities")
    st.write(f"- Primary query focus: {strategy['primary_query']['query']}")
    st.write(f"- Secondary query focus: {strategy['secondary_query']['query']}")
    st.write(f"- Primary page to refresh: {strategy['primary_page']}")
    st.write(f"- Top traffic source: {get_first_value(insight['top_sources'], 'source_medium')}")

    st.subheader("Suggested Next Steps")
    st.write("- Refresh the primary page with the updated cost, savings, and FAQ content.")
    st.write("- Add internal links to the migraine quiz, treatment page, and booking page.")
    st.write("- Review the draft assets and publish the highest-priority page update first.")
    st.write(f"- Current readiness score: {evaluation['score']}/5")


def render_standard_view(results: dict, ga4_debug_titles: list[str], show_debug: bool) -> None:
    """Show the standard dashboard view using real workflow data."""
    insight = results["insight"]
    combined = results["data_intake"]["summary"]["combined"]
    data_summary = results["data_intake"]["summary"]
    strategy = results["strategy"]["strategy"]
    semrush_positions_data = results.get("semrush_positions_data")
    semrush_pages_data = results.get("semrush_pages_data")
    semrush_topics_data = results.get("semrush_topics_data")
    has_query_data = bool(insight["query_analysis"])
    has_page_data = bool(combined["top_pages"])
    has_source_data = bool(combined["top_traffic_sources"])
    has_behavior_data = (
        data_summary["ga4_pages"]["rows"] > 0 or data_summary["ga4_sources"]["rows"] > 0
    )
    has_insight_patterns = bool(insight["patterns"])

    header_left, header_right = st.columns([4, 1.2])
    with header_left:
        st.markdown('<div class="dashboard-title">Marketing Intelligence Dashboard</div>', unsafe_allow_html=True)
        st.markdown('<div class="dashboard-subtitle">Real-time insights and opportunities</div>', unsafe_allow_html=True)
    with header_right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("**Status**")
        st.write("Workflow complete")
        st.write("Profile placeholder")
        st.markdown("</div>", unsafe_allow_html=True)

    render_scorecard(results)

    left_col, right_col = st.columns([2.2, 1])

    with left_col:
        if has_query_data:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">Performance Overview</div>', unsafe_allow_html=True)
            query_chart_df = pd.DataFrame(insight["query_analysis"])
            if {"query", "impressions"}.issubset(query_chart_df.columns):
                chart_data = (
                    query_chart_df.sort_values("impressions", ascending=False)[["query", "impressions"]]
                    .head(5)
                    .set_index("query")
                )
                st.bar_chart(chart_data)
            st.markdown("</div>", unsafe_allow_html=True)

        row_b_left, row_b_right = st.columns(2)

        with row_b_left:
            if has_query_data:
                st.markdown('<div class="panel">', unsafe_allow_html=True)
                st.markdown('<div class="panel-title">Top Queries</div>', unsafe_allow_html=True)
                top_queries_df = pd.DataFrame(insight["query_analysis"])
                st.dataframe(
                    top_queries_df[["query", "ctr", "impressions", "position"]].head(5),
                    use_container_width=True,
                    hide_index=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)

        with row_b_right:
            if has_page_data:
                st.markdown('<div class="panel">', unsafe_allow_html=True)
                st.markdown('<div class="panel-title">Top Pages</div>', unsafe_allow_html=True)
                page_rows = []
                best_source = get_first_value(insight["top_sources"], "source_medium")
                for item in combined["top_pages"][:5]:
                    page_rows.append(
                        {
                            "page_title": item["page_title"],
                            "metric": item["metric"],
                            "value": item["value"],
                            "traffic_context": best_source,
                        }
                    )
                top_pages_df = pd.DataFrame(page_rows)
                st.dataframe(top_pages_df, use_container_width=True, hide_index=True)
                st.markdown("</div>", unsafe_allow_html=True)

        # Optional SEMrush preview panel shown only when SEMrush data is available.
        if semrush_positions_data is not None and not semrush_positions_data.empty:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">Keyword Opportunities</div>', unsafe_allow_html=True)

            opportunity_cards = build_semrush_opportunity_cards(semrush_positions_data)

            if opportunity_cards:
                for card in opportunity_cards:
                    st.markdown("**" + card["keyword"] + "**")
                    st.write(f"Position: {card['position']}")
                    if card["volume"] != "Not available":
                        st.write(f"Volume: {card['volume']}")
                    if card["url"] != "Not available":
                        st.write(f"URL: {card['url']}")
                    st.write(f"Why it matters: {card['why_it_matters']}")
                    st.write(f"Recommended action: {card['recommended_action']}")
                    st.write(f"Priority: {card['priority']}")
                    st.divider()
            else:
                st.info("No SEMrush keyword opportunities available yet.")
            st.markdown("</div>", unsafe_allow_html=True)

        if semrush_pages_data is not None and not semrush_pages_data.empty:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">Page Opportunities</div>', unsafe_allow_html=True)

            page_cards = build_semrush_page_cards(semrush_pages_data)

            if page_cards:
                for card in page_cards:
                    st.markdown("**" + card["page_url"] + "**")
                    st.write(card["metric_line"])
                    st.write(f"Why it matters: {card['why_it_matters']}")
                    st.write(f"Recommended action: {card['recommended_action']}")
                    st.write(f"Priority: {card['priority']}")
                    st.divider()
            else:
                st.info("No SEMrush page opportunities available yet.")
            st.markdown("</div>", unsafe_allow_html=True)

        if semrush_topics_data is not None and not semrush_topics_data.empty:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">AI Topic Opportunities</div>', unsafe_allow_html=True)

            topic_cards = build_semrush_topic_cards(semrush_topics_data)

            if topic_cards:
                for card in topic_cards:
                    st.markdown("**" + card["topic"] + "**")
                    if card["volume"] != "Not available":
                        st.write(f"Volume: {card['volume']}")
                    st.write(f"Why it matters: {card['why_it_matters']}")
                    st.write(f"Recommended action: {card['recommended_action']}")
                    st.write(f"Priority: {card['priority']}")
                    st.divider()
            else:
                st.info("No SEMrush topic opportunities available yet.")
            st.markdown("</div>", unsafe_allow_html=True)

        row_c_left, row_c_right = st.columns(2)

        with row_c_left:
            if has_source_data:
                st.markdown('<div class="panel">', unsafe_allow_html=True)
                st.markdown('<div class="panel-title">Traffic Distribution</div>', unsafe_allow_html=True)
                top_sources_df = pd.DataFrame(combined["top_traffic_sources"])
                source_chart_df = top_sources_df[["source_medium", "value"]].set_index("source_medium")
                st.bar_chart(source_chart_df)
                st.dataframe(top_sources_df, use_container_width=True, hide_index=True)
                st.markdown("</div>", unsafe_allow_html=True)

        with row_c_right:
            if has_behavior_data:
                st.markdown('<div class="panel">', unsafe_allow_html=True)
                st.markdown('<div class="panel-title">User Behavior Signals</div>', unsafe_allow_html=True)

                behavior_metrics = {
                    "Sessions": data_summary["ga4_pages"]["key_metrics"].get("sessions", "Not available"),
                    "Active Users": data_summary["ga4_pages"]["key_metrics"].get("active_users", "Not available"),
                    "Engagement Rate": data_summary["ga4_pages"]["key_metrics"].get("engagement_rate", "Not available"),
                    "Source Sessions": data_summary["ga4_sources"]["key_metrics"].get("sessions", "Not available"),
                }

                for label, value in behavior_metrics.items():
                    st.metric(label, value)

                st.markdown("</div>", unsafe_allow_html=True)

        if has_insight_patterns:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">Key Insights</div>', unsafe_allow_html=True)
            insight_cols = st.columns(3)
            insight_titles = ["Low CTR Opportunity", "Growth Opportunity", "Traffic Insight"]
            for index, title in enumerate(insight_titles):
                with insight_cols[index]:
                    st.markdown("**" + title + "**")
                    st.write(insight["patterns"][index] if len(insight["patterns"]) > index else "No insight available.")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="panel" id="recommended-actions">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Recommended Actions</div>', unsafe_allow_html=True)

        priority_cycle = ["High", "Medium", "Low"]
        priority_class_map = {
            "High": "priority-high-pill",
            "Medium": "priority-medium-pill",
            "Low": "priority-low-pill",
        }
        action_index = 0

        for category, recommendations in strategy["recommendations"].items():
            for recommendation in recommendations:
                priority = priority_cycle[action_index % len(priority_cycle)]
                pill_class = priority_class_map[priority]

                if isinstance(recommendation, dict):
                    issue = recommendation.get("issue", "").strip()
                    rec_text = recommendation.get("recommendation", "").strip()
                    why = recommendation.get("why_it_matters", "").strip()
                    rec_priority = recommendation.get("priority", "").strip()
                    bp_category = recommendation.get("best_practice_category", "").strip()
                    body_parts = []
                    if issue:
                        body_parts.append(f"<strong>Issue:</strong> {issue}")
                    if rec_text:
                        body_parts.append(f"<strong>Recommendation:</strong> {rec_text}")
                    if why:
                        body_parts.append(f"<strong>Why it matters:</strong> {why}")
                    if bp_category:
                        body_parts.append(f"<strong>Best Practice Category:</strong> {bp_category}")
                    body_html = "<br><br>".join(body_parts) if body_parts else "No recommendation details available."
                    display_priority = rec_priority or priority
                else:
                    body_html = str(recommendation)
                    display_priority = priority

                pill_class = priority_class_map.get(display_priority, pill_class)

                st.markdown(
                    f"""
                    <div class="recommendation-card">
                        <div class="recommendation-card-top">
                            <div class="recommendation-category">{format_heading(category)}</div>
                            <div class="{pill_class}">{display_priority} Priority</div>
                        </div>
                        <div class="recommendation-body">
                            {body_html}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                action_index += 1

        st.markdown("</div>", unsafe_allow_html=True)

        render_priority_action_queue(results, priority_class_map)


        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">🚀 What To Do Next</div>', unsafe_allow_html=True)

        priority_actions = strategy.get("priority_actions", [])
        if priority_actions:
            for action in priority_actions:
                action_priority = str(action.get("priority", "Medium")).strip().title()
                action_pill_class = priority_class_map.get(action_priority, "priority-medium-pill")

                st.markdown(
                    f"""
                    <div class="what-next-card">
                        <div class="recommendation-card-top">
                            <div class="what-next-title">{action.get("title", "Opportunity")}</div>
                            <div class="{action_pill_class}">{action_priority} Priority</div>
                        </div>
                        <div class="recommendation-body">
                            <span class="what-next-label">What to do:</span><br>
                            {action.get("action", "")}
                            <br><br>
                            <span class="what-next-label">Why it matters:</span><br>
                            {action.get("reason", "")}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No prioritized actions available yet. Connect strategy agent output.")

        st.markdown("</div>", unsafe_allow_html=True)

        render_suggested_changes_section(results)

    with right_col:
        if has_insight_patterns:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">AI Insights Feed</div>', unsafe_allow_html=True)
            for index, pattern in enumerate(insight["patterns"][:5], start=1):
                st.markdown(f"**Insight {index}**")
                st.write(pattern)
                st.divider()
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Primary CTA</div>', unsafe_allow_html=True)
        st.write("Use the recommendations below to move from insight to action.")
        st.button("View Recommendations", key="view_recommendations_button")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Export Options</div>', unsafe_allow_html=True)
    render_export_section(results, inside_panel=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if show_debug:
        with st.expander("Workflow Debug Data", expanded=False):
            if ga4_debug_titles:
                st.write("First 5 parsed GA4 page titles:")
                st.write(ga4_debug_titles)
            else:
                st.write("No GA4 page titles were detected.")

            st.subheader("Combined Summary")
            st.json(results["data_intake"]["summary"]["combined"])

            st.subheader("Full Workflow Output")
            st.code(json.dumps(results, indent=2), language="json")


def render_suggested_changes_section(results: dict) -> None:
    """Show the top recommendation changes as presentation-ready visual cards."""
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Suggested Changes with Examples</div>', unsafe_allow_html=True)

    for card in build_suggested_change_cards(results)[:3]:
        st.markdown('<div class="change-card">', unsafe_allow_html=True)
        st.markdown(f"**{card['page_or_asset_name']}**")
        st.write(f"**Issue:** {card['issue']}")
        st.write(f"**Why it matters:** {card['why_it_matters']}")
        st.write(f"**Recommended change:** {card['recommended_change']}")
        st.write(f"**Example headline or CTA:** {card['example_headline_or_cta']}")

        before_col, after_col = st.columns(2)
        with before_col:
            st.markdown("**Before**")
            st.markdown('<div class="mock-block">', unsafe_allow_html=True)
            st.write(card["before_state"])
            st.markdown("</div>", unsafe_allow_html=True)
        with after_col:
            st.markdown("**Suggested Change**")
            st.markdown('<div class="mock-block">', unsafe_allow_html=True)
            st.write(card["example_layout_content_improvement"])
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def build_suggested_change_cards(results: dict) -> list[dict[str, str]]:
    """Create concrete recommendation cards from real workflow outputs."""
    strategy = results["strategy"]["strategy"]
    execution = results["execution"]
    insight = results["insight"]
    primary_page = strategy["primary_page"]
    primary_query = strategy["primary_query"]["query"]
    top_source = get_first_value(insight["top_sources"], "source_medium")
    blog_title = execution.get("blog_content_draft", {}).get("title", f"{primary_query.title()} article")
    faq_heading = execution.get("faq_block", {}).get("heading", f"FAQ for {primary_query}")
    social_goal = execution.get("social_post_draft", {}).get("goal", "Drive action")

    return [
        {
            "page_or_asset_name": primary_page,
            "issue": f"The page does not fully answer {primary_query} with clear local and conversion-focused language.",
            "why_it_matters": (
                "Visitors coming from high-intent search need immediate clarity on cost, savings, and the next step. "
                "If the page stays too generic, click-through and booking intent can stall."
            ),
            "recommended_change": (
                "Rework the hero, FAQ, and CTA flow so the page speaks directly to Evergreen Park and Chicago suburbs patients "
                "who are close to booking."
            ),
            "example_headline_or_cta": f"Botox Cost & Savings in Evergreen Park: Book Your Consultation",
            "before_state": "Hero Section\nGeneric service overview with no clear local value proposition or urgency.",
            "example_layout_content_improvement": (
                "Hero Section\n"
                f"Headline: Botox Cost & Savings in Evergreen Park\n"
                f"CTA Placement: Book a Consultation\n"
                f"Trust Section: Mention local specialist access and top source context from {top_source} traffic."
            ),
        },
        {
            "page_or_asset_name": blog_title,
            "issue": "The content opportunity needs a stronger example of how education turns into conversion.",
            "why_it_matters": (
                "A full draft can capture high-impression searches, but it works best when it also guides readers toward the quiz, "
                "treatment page, and booking page."
            ),
            "recommended_change": (
                "Use the article to answer cost and savings questions, then connect readers to a migraine quiz and the main treatment page."
            ),
            "example_headline_or_cta": "If You’ve Been Delaying Care, Start With the Migraine Quiz",
            "before_state": "Content Flow\nHelpful information exists, but internal paths to action are easy to miss.",
            "example_layout_content_improvement": (
                "Content Improvement\n"
                "Hero Section: Introduce the local problem and reassure readers.\n"
                "Trust Section: Add specialist credibility.\n"
                "CTA Placement: Link to migraine quiz, treatment page, and booking page at midpoint and close."
            ),
        },
        {
            "page_or_asset_name": faq_heading,
            "issue": "FAQ content can do more to reduce hesitation right before a patient decides whether to schedule.",
            "why_it_matters": (
                "FAQ blocks often win quick-answer visibility and help visitors feel confident enough to move forward, especially for cost and savings questions."
            ),
            "recommended_change": (
                "Position the FAQ block directly above the main CTA and add stronger reassurance around savings, fit, and specialist guidance."
            ),
            "example_headline_or_cta": f"Still Unsure? Review the FAQ and Schedule With a Specialist Today",
            "before_state": "FAQ Block\nAnswers may sit lower on the page without a clear action path afterward.",
            "example_layout_content_improvement": (
                "FAQ Block\n"
                "Questions: cost, savings, candidate fit, clinic comparison\n"
                "CTA Placement: Add a booking button directly under the answers\n"
                f"Trust Section: Reinforce {social_goal.lower()} with local reassurance."
            ),
        },
    ]


def build_semrush_opportunity_cards(semrush_positions_data: pd.DataFrame) -> list[dict[str, str]]:
    """Turn SEMrush position data into clean keyword opportunity cards."""
    dataframe = semrush_positions_data.copy()
    dataframe.columns = [str(column).strip().lower() for column in dataframe.columns]

    if "keyword" not in dataframe.columns or "position" not in dataframe.columns:
        return []

    dataframe["position"] = pd.to_numeric(dataframe["position"], errors="coerce")

    if "volume" in dataframe.columns:
        dataframe["volume"] = pd.to_numeric(dataframe["volume"], errors="coerce")
        opportunity_df = dataframe[(dataframe["position"] > 10) & (dataframe["volume"].fillna(0) > 0)]
        opportunity_df = opportunity_df.sort_values(["position", "volume"], ascending=[True, False])
    else:
        opportunity_df = dataframe[dataframe["position"] > 10].sort_values("position", ascending=True)

    cards = []
    for _, row in opportunity_df.head(10).iterrows():
        position_value = int(row["position"]) if pd.notna(row["position"]) else "Not available"
        volume_value = (
            int(row["volume"]) if "volume" in opportunity_df.columns and pd.notna(row.get("volume")) else "Not available"
        )
        url_value = str(row["url"]) if "url" in opportunity_df.columns and pd.notna(row.get("url")) else "Not available"
        priority = "High" if pd.notna(row["position"]) and row["position"] > 20 else "Medium"

        cards.append(
            {
                "keyword": str(row["keyword"]),
                "position": str(position_value),
                "volume": str(volume_value),
                "url": url_value,
                "why_it_matters": (
                    "This keyword is already ranking but still has room to move higher and capture more visibility."
                    if priority == "Medium"
                    else "This keyword has meaningful upside because it is outside the strongest ranking range and may need a bigger content or page update."
                ),
                "recommended_action": (
                    "Tighten on-page targeting, improve internal links, and refresh supporting copy."
                    if priority == "Medium"
                    else "Create or expand a dedicated page or content section to improve relevance and ranking potential."
                ),
                "priority": priority,
            }
        )

    return cards


def build_semrush_page_cards(semrush_pages_data: pd.DataFrame) -> list[dict[str, str]]:
    """Turn SEMrush Pages Report data into page opportunity cards."""
    dataframe = semrush_pages_data.copy()
    dataframe.columns = [str(column).strip().lower() for column in dataframe.columns]

    url_column = first_matching_column(dataframe, ["page", "url", "page url", "page_url"])
    traffic_column = first_matching_column(dataframe, ["traffic", "organic traffic"])
    keywords_column = first_matching_column(dataframe, ["keywords", "organic keywords"])

    if url_column is None:
        return []

    if traffic_column:
        dataframe[traffic_column] = pd.to_numeric(dataframe[traffic_column], errors="coerce").fillna(0)
    if keywords_column:
        dataframe[keywords_column] = pd.to_numeric(dataframe[keywords_column], errors="coerce").fillna(0)

    sort_column = traffic_column or keywords_column
    if sort_column:
        dataframe = dataframe.sort_values(sort_column, ascending=False)

    cards = []
    for _, row in dataframe.head(10).iterrows():
        traffic_value = int(row[traffic_column]) if traffic_column and pd.notna(row[traffic_column]) else None
        keywords_value = int(row[keywords_column]) if keywords_column and pd.notna(row[keywords_column]) else None
        priority = "High" if (traffic_value or 0) >= 100 or (keywords_value or 0) >= 20 else "Medium"

        metric_parts = []
        if traffic_value is not None:
            metric_parts.append(f"Traffic: {traffic_value}")
        if keywords_value is not None:
            metric_parts.append(f"Keywords: {keywords_value}")

        cards.append(
            {
                "page_url": str(row[url_column]),
                "metric_line": " | ".join(metric_parts) if metric_parts else "Metrics not available",
                "why_it_matters": (
                    "This page already has visibility and may represent a strong optimization opportunity if engagement or conversion is not matching demand."
                    if traffic_value and traffic_value > 0
                    else "This page ranks for multiple keywords and could move higher with stronger page targeting and support content."
                ),
                "recommended_action": (
                    "Improve layout, tighten CTA placement, and refresh page messaging to turn current traffic into stronger outcomes."
                    if traffic_value and traffic_value > 0
                    else "Expand topical depth, improve internal links, and strengthen keyword-to-page alignment."
                ),
                "priority": priority,
            }
        )

    return cards


def build_semrush_topic_cards(semrush_topics_data: pd.DataFrame) -> list[dict[str, str]]:
    """Turn SEMrush Topic Opportunities data into AI topic cards."""
    dataframe = semrush_topics_data.copy()
    dataframe.columns = [str(column).strip().lower() for column in dataframe.columns]

    topic_column = first_matching_column(dataframe, ["topic", "keyword", "title"])
    volume_column = first_matching_column(dataframe, ["volume", "search volume"])
    competitor_column = first_matching_column(dataframe, ["competitors", "competitor presence", "competition"])

    if topic_column is None:
        return []

    if volume_column:
        dataframe[volume_column] = pd.to_numeric(dataframe[volume_column], errors="coerce").fillna(0)
    if competitor_column:
        dataframe[competitor_column] = pd.to_numeric(dataframe[competitor_column], errors="coerce").fillna(0)

    sort_column = volume_column or competitor_column
    if sort_column:
        dataframe = dataframe.sort_values(sort_column, ascending=False)

    cards = []
    for _, row in dataframe.head(10).iterrows():
        volume_value = int(row[volume_column]) if volume_column and pd.notna(row[volume_column]) else None
        competitor_value = int(row[competitor_column]) if competitor_column and pd.notna(row[competitor_column]) else 0

        priority = "High" if (volume_value or 0) >= 500 or competitor_value >= 5 else "Medium"
        cards.append(
            {
                "topic": str(row[topic_column]),
                "volume": str(volume_value) if volume_value is not None else "Not available",
                "why_it_matters": (
                    "This topic can help the site build AI visibility and close a meaningful content gap."
                    if priority == "High"
                    else "This topic supports future authority building and can strengthen cluster-level coverage."
                ),
                "recommended_action": (
                    "Create a dedicated page or in-depth guide supported by related cluster content."
                    if priority == "High"
                    else "Add the topic into an existing cluster or build a focused supporting article."
                ),
                "priority": priority,
            }
        )

    return cards


def build_priority_action_queue(results: dict) -> list[dict[str, str]]:
    """Combine all available inputs into one prioritized action list."""
    insight = results["insight"]
    combined = results["data_intake"]["summary"]["combined"]
    semrush_positions_data = results.get("semrush_positions_data")
    semrush_pages_data = results.get("semrush_pages_data")
    semrush_topics_data = results.get("semrush_topics_data")

    queue: list[dict[str, Any]] = []

    for item in insight["high_impression_low_click"][:5]:
        impressions = item.get("impressions", 0)
        ctr = item.get("ctr", 0)
        position = item.get("position", 0)
        impact_score = float(impressions or 0) + max(0.0, 20.0 - float(position or 0)) * 25

        queue.append(
            {
                "title": f"Improve CTR for {item['query']}",
                "data_source": "GSC",
                "supporting_data": f"Impressions: {int(impressions)} | CTR: {ctr}% | Position: {position}",
                "why_it_matters": (
                    "This query already has visibility but is underperforming on clicks, which signals a strong high-intent gap."
                ),
                "recommended_action": (
                    "Refresh the title tag, meta description, and on-page answer structure to better match search intent."
                ),
                "priority": "High",
                "impact_score": impact_score,
            }
        )

    for item in insight["conversion_intent_queries"][:3]:
        if any(existing["title"].endswith(item["query"]) for existing in queue):
            continue

        impressions = item.get("impressions", 0)
        ctr = item.get("ctr", 0)
        position = item.get("position", 0)
        priority = "Medium" if 20 <= float(position or 0) <= 50 else "Low"
        impact_score = float(impressions or 0) + max(0.0, 50.0 - float(position or 0)) * 10

        queue.append(
            {
                "title": f"Expand visibility for {item['query']}",
                "data_source": "GSC",
                "supporting_data": f"Impressions: {int(impressions)} | CTR: {ctr}% | Position: {position}",
                "why_it_matters": (
                    "This conversion-oriented query suggests commercial demand that could turn into appointments with stronger coverage."
                ),
                "recommended_action": (
                    "Add targeted copy, FAQs, and internal links so the page better supports decision-stage search intent."
                ),
                "priority": priority,
                "impact_score": impact_score,
            }
        )

    if combined["top_pages"]:
        top_page = combined["top_pages"][0]
        page_value = float(top_page.get("value", 0) or 0)
        priority = "High" if page_value >= 100 else "Medium" if page_value >= 25 else "Low"
        queue.append(
            {
                "title": f"Optimize high-traffic GA4 page: {top_page['page_title']}",
                "data_source": "GA4",
                "supporting_data": f"{top_page['metric']}: {int(page_value)}",
                "why_it_matters": (
                    "A page already attracting meaningful traffic is one of the fastest places to improve conversions and content performance."
                ),
                "recommended_action": (
                    "Review message clarity, CTA placement, and content depth so existing traffic is more likely to convert."
                ),
                "priority": priority,
                "impact_score": page_value,
            }
        )

    if combined["top_traffic_sources"]:
        top_source = combined["top_traffic_sources"][0]
        source_value = float(top_source.get("value", 0) or 0)
        priority = "Medium" if source_value >= 50 else "Low"
        queue.append(
            {
                "title": f"Strengthen pages fed by {top_source['source_medium']}",
                "data_source": "GA4",
                "supporting_data": f"{top_source['metric']}: {int(source_value)}",
                "why_it_matters": (
                    "This source is already driving visits, so improving the destination experience can lift outcomes without needing a new acquisition channel."
                ),
                "recommended_action": (
                    "Audit the landing pages receiving this traffic and align headlines, trust signals, and CTAs with acquisition intent."
                ),
                "priority": priority,
                "impact_score": source_value,
            }
        )

    if semrush_positions_data is not None and not semrush_positions_data.empty:
        dataframe = semrush_positions_data.copy()
        dataframe.columns = [str(column).strip().lower() for column in dataframe.columns]

        if "keyword" in dataframe.columns and "position" in dataframe.columns:
            dataframe["position"] = pd.to_numeric(dataframe["position"], errors="coerce")
            dataframe["volume"] = pd.to_numeric(dataframe["volume"], errors="coerce") if "volume" in dataframe.columns else 0
            dataframe = dataframe.dropna(subset=["position"])
            dataframe = dataframe[(dataframe["position"] >= 4) & (dataframe["position"] <= 50)]
            dataframe = dataframe.sort_values(["position", "volume"], ascending=[True, False])

            for _, row in dataframe.head(5).iterrows():
                position = float(row["position"])
                volume = float(row["volume"]) if "volume" in dataframe.columns else 0.0
                priority = "High" if 4 <= position <= 20 else "Medium"
                impact_score = (1000 - (position * 20)) + volume
                url_value = str(row["url"]) if "url" in dataframe.columns and pd.notna(row.get("url")) else "Not available"

                queue.append(
                    {
                        "title": f"Improve ranking for {row['keyword']}",
                        "data_source": "Keyword",
                        "supporting_data": (
                            f"Position: {int(position)} | Volume: {int(volume) if volume else 'Not available'} | URL: {url_value}"
                        ),
                        "why_it_matters": (
                            "This keyword is already ranking within reach, which makes it a realistic SEO opportunity with measurable upside."
                            if priority == "High"
                            else "The keyword has moderate ranking visibility and could become stronger with more focused optimization."
                        ),
                        "recommended_action": (
                            "Tighten keyword targeting in the title tag, H1, supporting copy, and FAQ content."
                        ),
                        "priority": priority,
                        "impact_score": impact_score,
                    }
                )

    if semrush_pages_data is not None and not semrush_pages_data.empty:
        dataframe = semrush_pages_data.copy()
        dataframe.columns = [str(column).strip().lower() for column in dataframe.columns]
        url_column = first_matching_column(dataframe, ["page", "url", "page url", "page_url"])
        traffic_column = first_matching_column(dataframe, ["traffic", "organic traffic"])
        keywords_column = first_matching_column(dataframe, ["keywords", "organic keywords"])

        if url_column:
            if traffic_column:
                dataframe[traffic_column] = pd.to_numeric(dataframe[traffic_column], errors="coerce").fillna(0)
            if keywords_column:
                dataframe[keywords_column] = pd.to_numeric(dataframe[keywords_column], errors="coerce").fillna(0)

            sort_column = traffic_column or keywords_column
            if sort_column:
                dataframe = dataframe.sort_values(sort_column, ascending=False)

            for _, row in dataframe.head(3).iterrows():
                traffic = float(row[traffic_column]) if traffic_column else 0.0
                keywords = float(row[keywords_column]) if keywords_column else 0.0
                priority = "High" if traffic >= 100 or keywords >= 20 else "Medium" if traffic >= 25 or keywords >= 5 else "Low"
                impact_score = traffic + (keywords * 10)

                queue.append(
                    {
                        "title": f"Improve performance of {row[url_column]}",
                        "data_source": "Page",
                        "supporting_data": (
                            f"Traffic: {int(traffic) if traffic_column else 'Not available'} | "
                            f"Keywords: {int(keywords) if keywords_column else 'Not available'}"
                        ),
                        "why_it_matters": (
                            "This page already has search visibility, so improving UX, messaging, or conversion paths can create faster business impact."
                        ),
                        "recommended_action": (
                            "Review content depth, internal linking, and CTA hierarchy to make the page more competitive and conversion-focused."
                        ),
                        "priority": priority,
                        "impact_score": impact_score,
                    }
                )

    if semrush_topics_data is not None and not semrush_topics_data.empty:
        dataframe = semrush_topics_data.copy()
        dataframe.columns = [str(column).strip().lower() for column in dataframe.columns]
        topic_column = first_matching_column(dataframe, ["topic", "keyword", "title"])
        volume_column = first_matching_column(dataframe, ["volume", "search volume"])
        competitor_column = first_matching_column(dataframe, ["competitors", "competitor presence", "competition"])

        if topic_column:
            if volume_column:
                dataframe[volume_column] = pd.to_numeric(dataframe[volume_column], errors="coerce").fillna(0)
            if competitor_column:
                dataframe[competitor_column] = pd.to_numeric(dataframe[competitor_column], errors="coerce").fillna(0)

            sort_column = volume_column or competitor_column
            if sort_column:
                dataframe = dataframe.sort_values(sort_column, ascending=False)

            for _, row in dataframe.head(3).iterrows():
                volume = float(row[volume_column]) if volume_column else 0.0
                competitors = float(row[competitor_column]) if competitor_column else 0.0
                priority = "Medium" if volume >= 250 or competitors >= 3 else "Low"
                impact_score = volume + (competitors * 25)

                queue.append(
                    {
                        "title": f"Build content around {row[topic_column]}",
                        "data_source": "Topic",
                        "supporting_data": (
                            f"Volume: {int(volume) if volume_column else 'Not available'} | "
                            f"Competition: {int(competitors) if competitor_column else 'Not available'}"
                        ),
                        "why_it_matters": (
                            "This topic represents a broader content gap that can strengthen authority, internal linking, and AI-search relevance."
                        ),
                        "recommended_action": (
                            "Create a focused page or guide, then support it with cluster content and internal links."
                        ),
                        "priority": priority,
                        "impact_score": impact_score,
                    }
                )

    priority_rank = {"High": 3, "Medium": 2, "Low": 1}
    sorted_queue = sorted(
        queue,
        key=lambda item: (priority_rank.get(item["priority"], 0), float(item.get("impact_score", 0))),
        reverse=True,
    )

    return [
        {
            "title": item["title"],
            "data_source": item["data_source"],
            "supporting_data": item["supporting_data"],
            "why_it_matters": item["why_it_matters"],
            "recommended_action": item["recommended_action"],
            "priority": item["priority"],
        }
        for item in sorted_queue[:12]
    ]


def render_priority_action_queue(results: dict, priority_class_map: dict[str, str]) -> None:
    """Render the unified queue using the existing dashboard card style."""
    queue = build_priority_action_queue(results)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Priority Action Queue</div>', unsafe_allow_html=True)

    if queue:
        for item in queue:
            action_priority = str(item.get("priority", "Medium")).strip().title()
            action_pill_class = priority_class_map.get(action_priority, "priority-medium-pill")

            st.markdown(
                f"""
                <div class="recommendation-card">
                    <div class="recommendation-card-top">
                        <div class="recommendation-category">{item.get("title", "Action")}</div>
                        <div class="{action_pill_class}">{action_priority} Priority</div>
                    </div>
                    <div class="recommendation-body">
                        <strong>Data Source:</strong> {item.get("data_source", "Not available")}<br><br>
                        <strong>Supporting Data:</strong> {item.get("supporting_data", "Not available")}<br><br>
                        <strong>Why it matters:</strong> {item.get("why_it_matters", "")}<br><br>
                        <strong>Recommended action:</strong> {item.get("recommended_action", "")}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No priority actions available yet.")

    st.markdown("</div>", unsafe_allow_html=True)


def first_matching_column(dataframe: pd.DataFrame, candidates: list[str]) -> str | None:
    """Return the first matching column from a list of possible names."""
    normalized_columns = {str(column).strip().lower(): column for column in dataframe.columns}
    for candidate in candidates:
        if candidate in normalized_columns:
            return normalized_columns[candidate]
    return None


def build_export_dataframe(results: dict) -> pd.DataFrame:
    """Build a flat export table for CSV and spreadsheet use."""
    rows: list[dict[str, str]] = []
    combined = results["data_intake"]["summary"]["combined"]
    strategy = results["strategy"]["strategy"]["recommendations"]

    for item in combined["top_pages"]:
        rows.append(
            {
                "section": "top_pages",
                "label": item["page_title"],
                "metric": item["metric"],
                "value": str(item["value"]),
            }
        )

    for item in combined["top_traffic_sources"]:
        rows.append(
            {
                "section": "top_traffic_sources",
                "label": item["source_medium"],
                "metric": item["metric"],
                "value": str(item["value"]),
            }
        )

    for item in combined["top_queries"]:
        rows.append(
            {
                "section": "top_queries",
                "label": item["query"],
                "metric": item["metric"],
                "value": str(item["value"]),
            }
        )

    for category, recommendations in strategy.items():
        for recommendation in recommendations:
            rows.append(
                {
                    "section": "key_recommendations",
                    "label": format_heading(category),
                    "metric": "recommendation",
                    "value": str(recommendation),
                }
            )

    return pd.DataFrame(rows)


def build_pdf_report_bytes(results: dict) -> bytes:
    """Create a simple PDF report without extra dependencies."""
    insight = results["insight"]
    strategy = results["strategy"]["strategy"]

    report_lines = [
        "AI Marketing Workflow Report",
        "",
        "Executive Summary",
        (
            f"Top opportunity: {get_first_value(insight['high_impression_low_click'], 'query')}. "
            f"Primary page: {strategy['primary_page']}. "
            f"Top traffic source: {get_first_value(insight['top_sources'], 'source_medium')}."
        ),
        "",
        "Key Insights",
        *[f"- {item}" for item in insight["patterns"][:5]],
        "",
        "Recommended Actions",
    ]

    for category, recommendations in strategy["recommendations"].items():
        report_lines.append(f"{format_heading(category)}")
        report_lines.extend([f"- {recommendation}" for recommendation in recommendations])

    report_lines.extend(
        [
            "",
            "Priority Opportunities",
            f"- Primary query: {strategy['primary_query']['query']}",
            f"- Secondary query: {strategy['secondary_query']['query']}",
            f"- Primary page: {strategy['primary_page']}",
            f"- Top traffic source: {get_first_value(insight['top_sources'], 'source_medium')}",
        ]
    )

    return simple_pdf_from_lines(report_lines)


def simple_pdf_from_lines(lines: list[str]) -> bytes:
    """Build a very small PDF document from plain text lines."""
    safe_lines = [line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for line in lines]
    content_lines = ["BT", "/F1 12 Tf", "50 780 Td", "14 TL"]

    first = True
    for line in safe_lines:
        if first:
            content_lines.append(f"({line}) Tj")
            first = False
        else:
            content_lines.append("T*")
            content_lines.append(f"({line}) Tj")

    content_lines.append("ET")
    content_stream = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj",
        f"4 0 obj << /Length {len(content_stream)} >> stream\n".encode("latin-1") + content_stream + b"\nendstream endobj",
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",
    ]

    pdf = BytesIO()
    pdf.write(b"%PDF-1.4\n")
    offsets = [0]

    for obj in objects:
        offsets.append(pdf.tell())
        pdf.write(obj)
        pdf.write(b"\n")

    xref_start = pdf.tell()
    pdf.write(f"xref\n0 {len(offsets)}\n".encode("latin-1"))
    pdf.write(b"0000000000 65535 f \n")

    for offset in offsets[1:]:
        pdf.write(f"{offset:010d} 00000 n \n".encode("latin-1"))

    pdf.write(
        (
            f"trailer << /Size {len(offsets)} /Root 1 0 R >>\n"
            f"startxref\n{xref_start}\n%%EOF"
        ).encode("latin-1")
    )

    return pdf.getvalue()


def render_export_section(results: dict, inside_panel: bool = False) -> None:
    """Show export buttons for CSV, PDF, and future Google Sheets use."""
    export_df = build_export_dataframe(results)
    csv_bytes = export_df.to_csv(index=False).encode("utf-8")
    pdf_bytes = build_pdf_report_bytes(results)

    if not inside_panel:
        st.subheader("Export Options")
    export_columns = st.columns(3)

    export_columns[0].download_button(
        "Export CSV",
        data=csv_bytes,
        file_name="marketing_workflow_export.csv",
        mime="text/csv",
    )

    export_columns[1].download_button(
        "Export PDF Report",
        data=pdf_bytes,
        file_name="marketing_workflow_report.pdf",
        mime="application/pdf",
    )

    export_columns[2].download_button(
        "Google Sheets Placeholder",
        data=csv_bytes,
        file_name="google_sheets_ready_export.csv",
        mime="text/csv",
        help="Placeholder for future Google Sheets integration. For now this exports a spreadsheet-friendly CSV.",
    )


st.title("AI Marketing Workflow System")
st.write("Upload one or more source files below, then run the workflow.")

view_mode = st.radio(
    "View Mode",
    options=["Standard Workflow View", "Client Report Mode"],
    horizontal=True,
)

with st.sidebar:
    show_debug = st.checkbox("Show debug data", value=False)

st.subheader("1. Upload CSV files")
st.write("GA4 Page Title Report: page-level behavior such as top pages, sessions, and engagement.")
ga4_pages_file = st.file_uploader("Upload GA4 Page Title Report CSV", type="csv")

st.write("GA4 Session Source / Medium: acquisition data showing where traffic came from.")
ga4_source_file = st.file_uploader("Upload GA4 Session Source / Medium CSV", type="csv")

st.write("GSC Queries: Google Search Console query data showing search demand and clicks.")
gsc_queries_file = st.file_uploader("Upload GSC Queries CSV", type="csv")

st.write("SEMrush Organic Positions: optional organic keyword and ranking export for future use.")
semrush_positions_file = st.file_uploader("Upload SEMrush Organic Positions CSV", type="csv")

st.write("SEMrush Pages Report: optional page-level organic performance export for future use.")
semrush_pages_file = st.file_uploader("Upload SEMrush Pages Report CSV", type="csv")

st.write("SEMrush Topic Opportunities: optional topic-level opportunity export for future use.")
semrush_topics_file = st.file_uploader("Upload SEMrush Topic Opportunities CSV", type="csv")

st.subheader("2. Run the workflow")
run_button = st.button("Run Workflow")

if run_button:
    uploaded_files = [
        ga4_pages_file,
        ga4_source_file,
        gsc_queries_file,
        semrush_positions_file,
        semrush_pages_file,
        semrush_topics_file,
    ]

    if not has_uploaded_data(uploaded_files):
        st.error("Please upload at least one CSV file before running the workflow.")
        st.stop()

    ga4_pages_data = parse_uploaded_csv(ga4_pages_file, "GA4_PAGES") if ga4_pages_file else None
    ga4_source_data = parse_uploaded_csv(ga4_source_file, "GA4_SOURCE") if ga4_source_file else None
    gsc_queries_data = parse_uploaded_csv(gsc_queries_file, "GSC_QUERIES") if gsc_queries_file else None
    semrush_positions_data = parse_semrush_positions_csv(semrush_positions_file) if semrush_positions_file else None
    semrush_pages_data = parse_semrush_pages_csv(semrush_pages_file) if semrush_pages_file else None
    semrush_topics_data = parse_semrush_topics_csv(semrush_topics_file) if semrush_topics_file else None

    ga4_debug_titles = []
    if ga4_pages_data is not None and "page_title" in ga4_pages_data.columns:
        ga4_debug_titles = ga4_pages_data["page_title"].head(5).fillna("").astype(str).tolist()

    results = run_workflow(
        ga4_pages_data=ga4_pages_data,
        ga4_source_data=ga4_source_data,
        gsc_queries_data=gsc_queries_data,
        semrush_positions_data=semrush_positions_data,
        semrush_pages_data=semrush_pages_data,
        semrush_topics_data=semrush_topics_data,
    )

    st.success("Workflow complete. Results were also saved to logs/workflow_runs.csv.")

    if view_mode == "Client Report Mode":
        render_client_report(results)
        render_export_section(results)
    else:
        render_standard_view(results, ga4_debug_titles, show_debug)
else:
    st.info("Upload your files and click Run Workflow to start.")
