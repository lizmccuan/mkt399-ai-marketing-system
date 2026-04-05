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


def format_heading(value: str) -> str:
    """Convert keys like ux_conversion into clean labels."""
    return value.replace("_", " ").upper()


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
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Performance Overview</div>', unsafe_allow_html=True)
        query_chart_df = pd.DataFrame(insight["query_analysis"])
        if not query_chart_df.empty and {"query", "impressions"}.issubset(query_chart_df.columns):
            chart_data = (
                query_chart_df.sort_values("impressions", ascending=False)[["query", "impressions"]]
                .head(5)
                .set_index("query")
            )
            st.bar_chart(chart_data)
        else:
            st.info("No query impression data available yet.")
        st.markdown("</div>", unsafe_allow_html=True)

        row_b_left, row_b_right = st.columns(2)

        with row_b_left:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">Top Queries</div>', unsafe_allow_html=True)
            top_queries_df = pd.DataFrame(insight["query_analysis"])
            if not top_queries_df.empty:
                st.dataframe(
                    top_queries_df[["query", "ctr", "impressions", "position"]].head(5),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No query data available.")
            st.markdown("</div>", unsafe_allow_html=True)

        with row_b_right:
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
            if not top_pages_df.empty:
                st.dataframe(top_pages_df, use_container_width=True, hide_index=True)
            else:
                st.info("No page data available.")
            st.markdown("</div>", unsafe_allow_html=True)

        # Optional SEMrush preview panel shown only when SEMrush data is available.
        if semrush_positions_data is not None and not semrush_positions_data.empty:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">SEMrush Keyword Opportunities</div>', unsafe_allow_html=True)
            preferred_columns = ["keyword", "position", "volume", "url"]
            available_columns = [column for column in preferred_columns if column in semrush_positions_data.columns]

            if available_columns:
                st.dataframe(
                    semrush_positions_data[available_columns].head(10),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.dataframe(
                    semrush_positions_data.head(10),
                    use_container_width=True,
                    hide_index=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

        row_c_left, row_c_right = st.columns(2)

        with row_c_left:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">Traffic Distribution</div>', unsafe_allow_html=True)
            top_sources_df = pd.DataFrame(combined["top_traffic_sources"])
            if not top_sources_df.empty:
                source_chart_df = top_sources_df[["source_medium", "value"]].set_index("source_medium")
                st.bar_chart(source_chart_df)
                st.dataframe(top_sources_df, use_container_width=True, hide_index=True)
            else:
                st.info("No traffic source data available.")
            st.markdown("</div>", unsafe_allow_html=True)

        with row_c_right:
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

        render_suggested_changes_section(results)

    with right_col:
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
st.write("Upload the three source files below, then run the full marketing workflow.")

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

st.subheader("2. Run the workflow")
run_button = st.button("Run Workflow")

if run_button:
    if not all([ga4_pages_file, ga4_source_file, gsc_queries_file]):
        st.error("Please upload all three required CSV files before running the workflow.")
        st.stop()

    ga4_pages_data = parse_uploaded_csv(ga4_pages_file, "GA4_PAGES")
    ga4_source_data = parse_uploaded_csv(ga4_source_file, "GA4_SOURCE")
    gsc_queries_data = parse_uploaded_csv(gsc_queries_file, "GSC_QUERIES")
    semrush_positions_data = parse_semrush_positions_csv(semrush_positions_file) if semrush_positions_file else None

    ga4_debug_titles = []
    if "page_title" in ga4_pages_data.columns:
        ga4_debug_titles = ga4_pages_data["page_title"].head(5).fillna("").astype(str).tolist()

    results = run_workflow(
        ga4_pages_data=ga4_pages_data,
        ga4_source_data=ga4_source_data,
        gsc_queries_data=gsc_queries_data,
        semrush_positions_data=semrush_positions_data,
    )

    st.success("Workflow complete. Results were also saved to logs/workflow_runs.csv.")

    if view_mode == "Client Report Mode":
        render_client_report(results)
        render_export_section(results)
    else:
        render_standard_view(results, ga4_debug_titles, show_debug)
else:
    st.info("Upload your files and click Run Workflow to start.")
