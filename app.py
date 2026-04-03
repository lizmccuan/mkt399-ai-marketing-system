"""Simple Streamlit interface for the AI Marketing Workflow System."""

from __future__ import annotations

import json
from io import BytesIO

import pandas as pd
import streamlit as st

from main import run_workflow
from utils.parser import parse_uploaded_csv


st.set_page_config(page_title="AI Marketing Workflow System", layout="wide")


def get_first_value(items: list[dict], key: str, fallback: str = "Not available") -> str:
    """Return the first item value when it exists."""
    if items:
        return str(items[0].get(key, fallback))
    return fallback


def build_scorecard(results: dict) -> dict[str, str]:
    """Collect the main scorecard values from workflow results."""
    insight = results["insight"]

    top_opportunity_query = get_first_value(insight["high_impression_low_click"], "query")
    top_ctr_gap = get_first_value(insight["high_impression_low_click"], "query")
    top_traffic_source = get_first_value(insight["top_sources"], "source_medium")
    top_performing_page = get_first_value(insight["top_pages"], "label")
    top_non_branded_query = get_first_value(insight["non_branded_queries"], "query")
    top_branded_query = get_first_value(insight["branded_queries"], "query")

    return {
        "Top Opportunity Query": top_opportunity_query,
        "Top CTR Gap": top_ctr_gap,
        "Top Traffic Source": top_traffic_source,
        "Top Performing Page": top_performing_page,
        "Top Non-Branded Query": top_non_branded_query,
        "Top Branded Query": top_branded_query,
    }


def render_scorecard(results: dict) -> None:
    """Show dashboard metrics in a presentation-friendly layout."""
    scorecard = build_scorecard(results)

    st.subheader("Scorecard")
    row_one = st.columns(3)
    row_one[0].metric("Top Opportunity Query", scorecard["Top Opportunity Query"])
    row_one[1].metric("Top CTR Gap", scorecard["Top CTR Gap"])
    row_one[2].metric("Top Traffic Source", scorecard["Top Traffic Source"])

    row_two = st.columns(3)
    row_two[0].metric("Top Performing Page", scorecard["Top Performing Page"])
    row_two[1].metric("Top Non-Branded Query", scorecard["Top Non-Branded Query"])
    row_two[2].metric("Top Branded Query", scorecard["Top Branded Query"])


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
    for item in results["insight"]["patterns"][:5]:
        st.write(f"- {item}")

    st.subheader("Recommended Actions")
    for category, recommendations in strategy["recommendations"].items():
        st.write(f"**{format_heading(category)}**")
        for recommendation in recommendations:
            st.write(f"- {recommendation}")

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


def render_standard_view(results: dict, ga4_debug_titles: list[str]) -> None:
    """Show the existing workflow detail view."""
    st.subheader("GA4 Debug")
    if ga4_debug_titles:
        st.write("First 5 parsed GA4 page titles:")
        st.write(ga4_debug_titles)
    else:
        st.write("No GA4 page titles were detected.")

    st.subheader("Combined Summary")
    st.json(results["data_intake"]["summary"]["combined"])

    st.subheader("Data Intake")
    st.json(results["data_intake"])

    st.subheader("Insight")
    st.json(results["insight"])

    st.subheader("Strategy")
    st.json(results["strategy"])

    st.subheader("Execution")
    st.json(results["execution"])

    st.subheader("Evaluation")
    st.json(results["evaluation"])

    st.subheader("Full Workflow Output")
    st.code(json.dumps(results, indent=2), language="json")


def format_heading(value: str) -> str:
    """Convert keys like ux_conversion into clean labels."""
    return value.replace("_", " ").upper()


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
                    "value": recommendation,
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


def render_export_section(results: dict) -> None:
    """Show export buttons for CSV, PDF, and future Google Sheets use."""
    export_df = build_export_dataframe(results)
    csv_bytes = export_df.to_csv(index=False).encode("utf-8")
    pdf_bytes = build_pdf_report_bytes(results)

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

st.subheader("1. Upload CSV files")
st.write("GA4 Page Title Report: page-level behavior such as top pages, sessions, and engagement.")
ga4_pages_file = st.file_uploader("Upload GA4 Page Title Report CSV", type="csv")

st.write("GA4 Session Source / Medium: acquisition data showing where traffic came from.")
ga4_source_file = st.file_uploader("Upload GA4 Session Source / Medium CSV", type="csv")

st.write("GSC Queries: Google Search Console query data showing search demand and clicks.")
gsc_queries_file = st.file_uploader("Upload GSC Queries CSV", type="csv")

st.subheader("2. Run the workflow")
run_button = st.button("Run Workflow")

if run_button:
    if not all([ga4_pages_file, ga4_source_file, gsc_queries_file]):
        st.error("Please upload all three required CSV files before running the workflow.")
        st.stop()

    # Each uploaded file is parsed separately so the workflow can keep page, source, and query data distinct.
    ga4_pages_data = parse_uploaded_csv(ga4_pages_file, "GA4_PAGES")
    ga4_source_data = parse_uploaded_csv(ga4_source_file, "GA4_SOURCE")
    gsc_queries_data = parse_uploaded_csv(gsc_queries_file, "GSC_QUERIES")

    ga4_debug_titles = []
    if "page_title" in ga4_pages_data.columns:
        ga4_debug_titles = ga4_pages_data["page_title"].head(5).fillna("").astype(str).tolist()

    results = run_workflow(
        ga4_pages_data=ga4_pages_data,
        ga4_source_data=ga4_source_data,
        gsc_queries_data=gsc_queries_data,
    )

    st.success("Workflow complete. Results were also saved to logs/workflow_runs.csv.")
    render_scorecard(results)
    render_export_section(results)

    if view_mode == "Client Report Mode":
        render_client_report(results)
    else:
        render_standard_view(results, ga4_debug_titles)
else:
    st.info("Upload your files and click Run Workflow to start.")
