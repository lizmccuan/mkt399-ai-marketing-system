"""Simple Streamlit interface for the AI Marketing Workflow System."""

from __future__ import annotations

import json
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from main import run_workflow
from utils.parser import parse_csv_file, parse_uploaded_csv


RUNS_DIR = Path("saved_runs")
RUNS_DIR.mkdir(exist_ok=True)


st.set_page_config(page_title="AI Marketing Workflow System", layout="wide")
st.markdown(
    """
    <style>
    :root {
        --page-bg: #F7F8FC;
        --panel-bg: #FFFFFF;
        --text-main: #162033;
        --text-muted: #667085;
        --border-soft: #E6E8F0;
        --accent-purple: #7C3AED;
        --accent-purple-soft: #F3EDFF;
        --success-green: #22C55E;
        --success-soft: #ECFDF3;
        --warning-soft: #FFF4D6;
        --warning-accent: #F4C95D;
        --info-soft: #EEF4FF;
        --info-accent: #7CB3FF;
        --purple-soft: #F4ECFF;
        --purple-accent: #C084FC;
        --orange-soft: #FFF1E8;
        --orange-accent: #FDBA74;
        --shadow-soft: 0 4px 16px rgba(16, 24, 40, 0.04);
    }
    html, body, [class*="css"]  {
        color: var(--text-main);
    }
    .stApp {
        background: var(--page-bg);
        color: var(--text-main);
    }
    [data-testid="stAppViewContainer"] {
        background: var(--page-bg);
    }
    [data-testid="stAppViewContainer"] > .main {
        background: var(--page-bg);
    }
    .main .block-container {
        padding-top: 2.35rem;
        padding-bottom: 2.2rem;
        max-width: 1400px;
    }
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-main);
    }
    p, label, span {
        color: inherit;
    }
    [data-testid="stHeader"] {
        background: rgba(247, 248, 252, 0.92);
        border-bottom: 1px solid rgba(230, 232, 240, 0.75);
    }
    [data-testid="stSidebar"] {
        background: var(--panel-bg);
        border-right: 1px solid var(--border-soft);
    }
    [data-testid="stSidebar"] > div:first-child {
        background: var(--panel-bg);
    }
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div {
        color: var(--text-main);
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 1.25rem;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label {
        border-radius: 14px;
        padding: 0.5rem 0.7rem;
        margin-bottom: 0.28rem;
        border: 1px solid transparent;
        transition: all 0.2s ease;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
        background: var(--accent-purple-soft);
        color: var(--accent-purple);
        border: 1px solid rgba(124, 58, 237, 0.16);
        box-shadow: inset 0 0 0 1px rgba(124, 58, 237, 0.03);
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) * {
        color: var(--accent-purple);
        font-weight: 600;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: #F9FAFB;
        border-color: var(--border-soft);
    }
    .stButton > button,
    [data-testid="baseButton-secondary"] {
        border-radius: 12px;
        border: 1px solid var(--border-soft);
        background: var(--panel-bg);
        color: var(--text-main);
        font-weight: 600;
        min-height: 2.7rem;
        box-shadow: 0 2px 8px rgba(16, 24, 40, 0.04);
        transition: all 0.18s ease;
    }
    .stButton > button[kind="primary"] {
        background: #8C52FF;
        color: #ffffff;
        border: 1px solid #8C52FF;
        box-shadow: 0 8px 18px rgba(124, 58, 237, 0.18);
    }
    .stButton > button:hover {
        border-color: #D0D5DD;
        background: #F9FAFB;
        color: var(--text-main);
    }
    .stButton > button[kind="primary"]:hover {
        background: #D9C5FF;
        border-color: #D9C5FF;
        color: #ffffff;
    }
    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div {
        background: #FFFFFF;
        color: var(--text-main);
        border: 1px solid var(--border-soft);
        border-radius: 12px;
    }
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: #98A2B3;
    }
    .stMetric {
        background: #FFFFFF;
        border: 1px solid var(--border-soft);
        border-radius: 18px;
        padding: 0.9rem 1rem;
        box-shadow: var(--shadow-soft);
    }
    .stDataFrame, .stTable {
        background: #FFFFFF;
        border-radius: 18px;
    }
    .dashboard-title {
        font-size: 2.3rem;
        font-weight: 800;
        color: #162033;
        margin-bottom: 0.35rem;
        letter-spacing: -0.02em;
        line-height: 1.18;
    }
    .dashboard-subtitle {
        color: #667085;
        margin-bottom: 1.75rem;
        font-size: 1rem;
        line-height: 1.55;
    }
    .panel {
        background: var(--panel-bg);
        border: 1px solid var(--border-soft);
        border-radius: 18px;
        padding: 1.2rem 1.25rem;
        margin-bottom: 1rem;
        box-shadow: var(--shadow-soft);
    }
    .panel-title {
        font-size: 1.04rem;
        font-weight: 700;
        color: #162033;
        margin-bottom: 0.9rem;
        line-height: 1.35;
    }
    .change-card {
        background: var(--panel-bg);
        border: 1px solid var(--border-soft);
        border-radius: 18px;
        padding: 1.2rem 1.25rem;
        margin-bottom: 1rem;
        box-shadow: var(--shadow-soft);
    }
    .mock-block {
        background: #FAFBFF;
        border: 1px dashed #D8DCE8;
        border-radius: 16px;
        padding: 1rem 1.05rem;
        margin-top: 0.5rem;
        color: var(--text-muted);
    }
    .recommendation-card {
        background: var(--panel-bg);
        border: 1px solid var(--border-soft);
        border-radius: 18px;
        padding: 1.15rem 1.2rem;
        margin-bottom: 0.9rem;
        box-shadow: var(--shadow-soft);
    }
    .recommendation-card-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.9rem;
        margin-bottom: 0.9rem;
        flex-wrap: wrap;
    }
    .recommendation-category {
        font-size: 0.92rem;
        font-weight: 700;
        color: #162033;
        letter-spacing: 0.01em;
        line-height: 1.35;
    }
    .recommendation-body {
        color: #667085;
        font-size: 0.95rem;
        line-height: 1.62;
    }
    .priority-high-pill {
        display: inline-block;
        background: #FDECEC;
        color: #B42318;
        border: 1px solid #F7C7C2;
        border-radius: 999px;
        padding: 0.34rem 0.72rem;
        font-size: 0.75rem;
        font-weight: 700;
        white-space: nowrap;
    }
    .priority-medium-pill {
        display: inline-block;
        background: #FFF1E8;
        color: #B54708;
        border: 1px solid #F4D1B0;
        border-radius: 999px;
        padding: 0.34rem 0.72rem;
        font-size: 0.75rem;
        font-weight: 700;
        white-space: nowrap;
    }
    .priority-low-pill {
        display: inline-block;
        background: #F5F6FA;
        color: #667085;
        border: 1px solid #E4E7EC;
        border-radius: 999px;
        padding: 0.34rem 0.72rem;
        font-size: 0.75rem;
        font-weight: 700;
        white-space: nowrap;
    }
    .topic-tag-row {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        margin: 0.5rem 0 0.8rem;
    }
    .topic-tag {
        display: inline-block;
        background: var(--accent-purple-soft);
        color: #5B45C6;
        border: 1px solid #E5DAFF;
        border-radius: 999px;
        padding: 0.3rem 0.68rem;
        font-size: 0.74rem;
        font-weight: 600;
        white-space: nowrap;
    }
    .what-next-card {
        background: var(--panel-bg);
        border: 1px solid var(--border-soft);
        border-radius: 18px;
        padding: 1.15rem 1.2rem;
        margin-bottom: 0.9rem;
        box-shadow: var(--shadow-soft);
    }
    .what-next-title {
        font-size: 1.04rem;
        font-weight: 700;
        color: #162033;
        margin-bottom: 0.58rem;
        line-height: 1.35;
    }
    .what-next-label {
        font-weight: 700;
        color: #162033;
    }
    .ai-rail-panel {
        background: var(--panel-bg);
        border: 1px solid var(--border-soft);
        border-radius: 18px;
        padding: 18px;
        height: fit-content;
        position: sticky;
        top: 20px;
        box-shadow: var(--shadow-soft);
    }
    .ai-rail-title {
        font-size: 1.02rem;
        font-weight: 700;
        color: var(--text-main);
        margin-bottom: 0.8rem;
    }
    .ai-insight-card {
        background: #FFFFFF;
        border: 1px solid var(--border-soft);
        border-radius: 16px;
        padding: 0.9rem 1rem;
        margin-bottom: 0.7rem;
        box-shadow: 0 2px 10px rgba(16, 24, 40, 0.03);
    }
    .ai-insight-title {
        font-size: 0.94rem;
        font-weight: 700;
        margin-bottom: 0.38rem;
        color: var(--text-main);
    }
    .ai-insight-text {
        font-size: 0.88rem;
        line-height: 1.5;
        color: var(--text-muted);
    }
    .ai-insight-warning {
        background: var(--warning-soft);
        border-left: 4px solid var(--warning-accent);
    }
    .ai-insight-info {
        background: var(--info-soft);
        border-left: 4px solid var(--info-accent);
    }
    .ai-insight-success {
        background: var(--purple-soft);
        border-left: 4px solid var(--purple-accent);
    }
    .ai-strategy-button-wrap {
        margin-top: 1rem;
        margin-bottom: 0.85rem;
    }
    .ai-chat-box {
        margin-top: 1rem;
    }
    .ai-chat-response {
        background: var(--panel-bg);
        border: 1px solid var(--border-soft);
        border-radius: 16px;
        padding: 0.95rem 1rem;
        margin-top: 0.75rem;
        color: var(--text-main);
        font-size: 0.9rem;
        line-height: 1.5;
        white-space: pre-wrap;
        box-shadow: 0 2px 10px rgba(16, 24, 40, 0.03);
    }
    .take-action-panel {
        background: #FFFFFF;
        border: 1px solid #E6E8F0;
        border-radius: 18px;
        box-shadow: 0 4px 16px rgba(16, 24, 40, 0.04);
        padding: 1.25rem 1.35rem;
        margin-top: 0.85rem;
        margin-bottom: 1rem;
    }
    .take-action-header {
        display: flex;
        align-items: center;
        gap: 0.7rem;
        margin-bottom: 1rem;
    }
    .take-action-icon {
        width: 34px;
        height: 34px;
        border-radius: 999px;
        background: #F3EDFF;
        color: #7C3AED;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        font-weight: 700;
        flex-shrink: 0;
    }
    .take-action-title {
        font-size: 1.15rem;
        font-weight: 800;
        color: #162033;
        line-height: 1.3;
    }
    .take-action-section {
        margin-top: 1rem;
    }
    .take-action-section-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #162033;
        margin-bottom: 0.45rem;
    }
    .take-action-list {
        color: #475467;
        line-height: 1.7;
        margin: 0;
        padding-left: 1.15rem;
    }
    .take-action-list li {
        margin-bottom: 0.38rem;
        color: #475467 !important;
        line-height: 1.7;
    }
    .take-action-code {
        background: #F8FAFC;
        border: 1px solid #E6E8F0;
        border-radius: 14px;
        padding: 1rem 1rem;
        color: #162033;
        line-height: 1.75;
        white-space: pre-wrap;
        margin-top: 0.35rem;
    }

    /* GLOBAL TEXT FIX */
    body, p, span, div, label {
        color: #111827 !important;
    }
    /* HEADINGS */
    h1, h2, h3, h4, h5, h6 {
        color: #111827 !important;
        font-weight: 600;
    }
    /* STREAMLIT METRICS */
    [data-testid="stMetricValue"] {
        color: #111827 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #6b7280 !important;
    }
    /* TABLE FIX */
    [data-testid="stDataFrame"] {
        background: white !important;
        border-radius: 12px;
        overflow: hidden;
    }
    [data-testid="stDataFrame"] * {
        color: #111827 !important;
    }
    thead tr th {
        background: #f9fafb !important;
        color: #374151 !important;
    }
    tbody tr {
        background: white !important;
    }
    .css-1n76uvr, .css-1d391kg {
        background: white !important;
    }
    input, textarea {
        color: #111827 !important;
    }
    [data-testid="stSidebar"] * {
        color: #111827 !important;
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


def format_ctr_value(value, fallback: str = "Not available") -> str:
    """Format an already-normalized CTR percentage for display."""
    if value is None or value == "":
        return fallback

    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        text_value = str(value).strip()
        return text_value if text_value else fallback

    if pd.isna(numeric_value):
        return fallback

    return f"{numeric_value:.2f}%"


def normalize_ctr_percent(value) -> float | None:
    """Read a CTR percentage value safely for app-side calculations."""
    if value is None or value == "":
        return None

    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return None

    if pd.isna(numeric_value):
        return None

    return numeric_value


def format_ctr_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of a dataframe with CTR column formatted for display."""
    if "ctr" not in dataframe.columns:
        return dataframe

    formatted_dataframe = dataframe.copy()
    formatted_dataframe["ctr"] = formatted_dataframe["ctr"].apply(format_ctr_value)
    return formatted_dataframe


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


def parse_meta_posts_csv(file) -> pd.DataFrame:
    """Read a Meta content export CSV into a cleaned DataFrame."""
    if file is None:
        return pd.DataFrame()

    dataframe = pd.read_csv(file)
    normalized_columns = {str(column).strip().lower(): column for column in dataframe.columns}

    for column_name in ["Views", "Reach", "Likes", "Shares", "Follows", "Comments", "Saves"]:
        source_column = normalized_columns.get(column_name.lower())
        if source_column is not None:
            dataframe[column_name] = pd.to_numeric(dataframe[source_column], errors="coerce").fillna(0)
        else:
            dataframe[column_name] = 0

    description_column = normalized_columns.get("description")
    if description_column is not None:
        dataframe["Description"] = dataframe[description_column].fillna("").astype(str)
    else:
        dataframe["Description"] = ""

    post_type_column = normalized_columns.get("post type")
    if post_type_column is None:
        post_type_column = normalized_columns.get("post_type")
    if post_type_column is not None:
        dataframe["Post type"] = dataframe[post_type_column].fillna("").replace("", "Unknown")
    else:
        dataframe["Post type"] = "Unknown"

    publish_time_column = normalized_columns.get("publish time")
    if publish_time_column is None:
        publish_time_column = normalized_columns.get("publish_time")
    if publish_time_column is not None:
        dataframe["Publish time"] = pd.to_datetime(dataframe[publish_time_column], errors="coerce")

    dataframe["Hook"] = dataframe["Description"].apply(extract_hook_from_caption)
    dataframe["Topic"] = dataframe["Description"].apply(infer_social_topic)
    dataframe["Engagement"] = (
        dataframe["Likes"].fillna(0)
        + dataframe["Comments"].fillna(0)
        + dataframe["Shares"].fillna(0)
        + dataframe["Saves"].fillna(0)
    )
    dataframe["Engagement Rate"] = (
        (dataframe["Engagement"] / dataframe["Reach"].replace(0, pd.NA)) * 100
    ).fillna(0).round(2)

    return dataframe


def extract_hook_from_caption(caption) -> str:
    """Return the first non-empty caption line."""
    if caption is None or (isinstance(caption, float) and pd.isna(caption)):
        return ""

    for line in str(caption).splitlines():
        stripped_line = line.strip()
        if stripped_line:
            return stripped_line
    return ""


def infer_social_topic(caption) -> str:
    """Infer a simple social content topic from caption text."""
    if caption is None or (isinstance(caption, float) and pd.isna(caption)):
        return "general"

    caption_text = str(caption).lower()

    if any(keyword in caption_text for keyword in ["meet one of the providers", "provider", "pa-c", "specialists"]):
        return "provider spotlight"
    if any(keyword in caption_text for keyword in ["testimonial", "results", "before and after", "patient story", "success story"]):
        return "social proof"
    if any(keyword in caption_text for keyword in ["quiz", "book", "schedule", "consultation", "evaluation", "call us"]):
        return "patient conversion"
    if any(keyword in caption_text for keyword in ["botox", "treatment", "fda-approved", "options", "relief is possible"]):
        return "treatment education"
    if any(keyword in caption_text for keyword in ["myth", "fact", "facts", "misconception", "truth"]):
        return "myth / education"
    if any(keyword in caption_text for keyword in ["why", "what causes", "migraines are", "headaches aren’t", "symptoms"]):
        return "symptom awareness"
    if any(keyword in caption_text for keyword in ["opening", "launch", "now open", "new location", "grand opening"]):
        return "announcement / launch"
    if any(keyword in caption_text for keyword in ["expo", "community", "event", "westmont"]):
        return "community / event"
    return "general"


def humanize_social_topic(topic: str) -> str:
    """Convert internal social topic labels into natural user-facing language."""
    topic_map = {
        "provider spotlight": "Provider Spotlight",
        "treatment education": "Treatment Education",
        "myth / education": "Myth / Education",
        "symptom awareness": "Symptom Awareness",
        "patient conversion": "Patient Conversion",
        "announcement / launch": "Announcement / Launch",
        "community / event": "Community / Event",
        "social proof": "Social Proof",
        "general": "General",
    }
    return topic_map.get(str(topic).strip().lower(), str(topic).replace("_", " "))


def describe_social_post_pattern(row: pd.Series) -> str:
    """Describe a strong social post pattern in natural language."""
    hook = str(row.get("Hook", "")).strip()
    post_type = str(row.get("Post type", "Unknown")).strip()
    topic = humanize_social_topic(str(row.get("Topic", "general")).strip())

    post_type_map = {
        "reel": "IG Reel",
        "ig reel": "IG Reel",
        "carousel": "IG Carousel",
        "ig carousel": "IG Carousel",
        "image": "IG Image",
        "ig image": "IG Image",
    }
    post_type_label = post_type_map.get(post_type.lower(), post_type if post_type else "Social posts")

    if hook:
        return f"{post_type_label} posts with hooks like '{hook}' and {topic}"
    return f"{post_type_label} {topic}"


def classify_social_post(row) -> str:
    """Classify social post performance using simple threshold rules."""
    reach = float(row.get("Reach", 0) or 0)
    engagement_rate = float(row.get("Engagement Rate", 0) or 0)
    saves = float(row.get("Saves", 0) or 0)
    follows = float(row.get("Follows", 0) or 0)

    is_high_performing = (reach >= 150 and engagement_rate >= 5) or saves >= 3
    is_conversion_content = follows >= 1

    if is_high_performing and is_conversion_content:
        return "Both"
    if is_high_performing:
        return "High Performing Content"
    if is_conversion_content:
        return "Conversion Content"
    return "Underperforming"


def build_social_insights(meta_posts_data) -> dict[str, object]:
    """Build a simple social insight summary from Meta post performance."""
    empty_payload = {
        "top_performing_content": [],
        "conversion_content": [],
        "best_post_type": "Not available",
        "worst_post_type": "Not available",
        "top_topics": [],
        "weak_topics": [],
        "what_drives_saves": "Not enough Meta content data yet.",
        "what_drives_follows": "Not enough Meta content data yet.",
        "balance_problems": [],
    }

    if meta_posts_data is None or getattr(meta_posts_data, "empty", True):
        return empty_payload

    dataframe = meta_posts_data.copy()
    dataframe["Performance Class"] = dataframe.apply(classify_social_post, axis=1)

    def summarize_group(column_name: str) -> pd.DataFrame:
        grouped = dataframe.groupby(column_name, dropna=False).agg(
            avg_reach=("Reach", "mean"),
            avg_engagement_rate=("Engagement Rate", "mean"),
            total_follows=("Follows", "sum"),
            total_saves=("Saves", "sum"),
        )
        grouped["score"] = (
            grouped["avg_reach"].fillna(0)
            + (grouped["avg_engagement_rate"].fillna(0) * 10)
            + (grouped["total_follows"].fillna(0) * 25)
            + (grouped["total_saves"].fillna(0) * 10)
        )
        return grouped.sort_values("score", ascending=False)

    top_performing_content = dataframe[
        dataframe["Performance Class"].isin(["High Performing Content", "Both"])
    ]
    conversion_content = dataframe[
        dataframe["Performance Class"].isin(["Conversion Content", "Both"])
    ]

    post_type_summary = summarize_group("Post type")
    topic_summary = summarize_group("Topic")
    top_topics = topic_summary.head(3).index.tolist() if not topic_summary.empty else []
    top_topic_set = {str(topic).strip().lower() for topic in top_topics}
    weak_topics: list[str] = []
    if not topic_summary.empty:
        for topic in reversed(topic_summary.index.tolist()):
            normalized_topic = str(topic).strip().lower()
            if normalized_topic in top_topic_set:
                continue
            weak_topics.append(topic)
            if len(weak_topics) == 3:
                break

    balance_problems = []
    if ((dataframe["Reach"] >= 150) & (dataframe["Engagement Rate"] < 3)).any():
        balance_problems.append("High reach with low engagement suggests weak hook or creative payoff.")
    if ((dataframe["Engagement Rate"] >= 5) & (dataframe["Follows"] == 0)).any():
        balance_problems.append("High engagement but low conversion suggests strong content without a clear follow or next-step path.")
    if ((dataframe["Reach"] < 100) & (dataframe["Follows"] >= 1)).any():
        balance_problems.append("Low reach but strong conversion signal suggests promising content that needs more distribution.")
    if ((dataframe["Reach"] >= 150) & (dataframe["Engagement Rate"] >= 5) & (dataframe["Follows"] >= 1)).any():
        balance_problems.append("Best-performing pattern combines strong reach, strong engagement, and at least one follow.")

    top_save_row = (
        dataframe.sort_values(["Saves", "Reach", "Engagement Rate"], ascending=[False, False, False]).iloc[0]
        if not dataframe.empty
        else None
    )
    top_follow_row = (
        dataframe.sort_values(["Follows", "Reach", "Engagement Rate"], ascending=[False, False, False]).iloc[0]
        if not dataframe.empty
        else None
    )

    return {
        "top_performing_content": (
            top_performing_content[
                ["Hook", "Post type", "Topic", "Reach", "Engagement Rate", "Saves", "Follows"]
            ]
            .head(5)
            .fillna("")
            .to_dict(orient="records")
        ),
        "conversion_content": (
            conversion_content[
                ["Hook", "Post type", "Topic", "Reach", "Engagement Rate", "Saves", "Follows"]
            ]
            .head(5)
            .fillna("")
            .to_dict(orient="records")
        ),
        "best_post_type": post_type_summary.index[0] if not post_type_summary.empty else "Not available",
        "worst_post_type": post_type_summary.index[-1] if not post_type_summary.empty else "Not available",
        "top_topics": top_topics,
        "weak_topics": weak_topics,
        "what_drives_saves": (
            f"{describe_social_post_pattern(top_save_row)} are currently driving the most saves."
            if top_save_row is not None
            else "Not enough Meta content data yet."
        ),
        "what_drives_follows": (
            f"{describe_social_post_pattern(top_follow_row)} are currently driving the most follows."
            if top_follow_row is not None
            else "Not enough Meta content data yet."
        ),
        "balance_problems": balance_problems,
    }


def save_uploaded_file(file, destination: Path) -> None:
    """Save an uploaded file to disk when it exists."""
    if file is None:
        return

    with destination.open("wb") as output_file:
        output_file.write(file.getbuffer())


def save_run_files(
    ga4_pages_file,
    ga4_source_file,
    gsc_queries_file,
    semrush_positions_file,
    semrush_pages_file,
    semrush_topics_file,
    meta_posts_file,
) -> str:
    """Save uploaded run files into a timestamped folder and return the run id."""
    run_id = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(exist_ok=True)

    file_map = {
        "ga4_pages.csv": ga4_pages_file,
        "ga4_source.csv": ga4_source_file,
        "gsc_queries.csv": gsc_queries_file,
        "semrush_positions.csv": semrush_positions_file,
        "semrush_pages.csv": semrush_pages_file,
        "semrush_topics.csv": semrush_topics_file,
        "meta_posts.csv": meta_posts_file,
    }

    included_files = []
    for filename, uploaded_file in file_map.items():
        if uploaded_file is not None:
            save_uploaded_file(uploaded_file, run_dir / filename)
            included_files.append(filename)

    metadata = {
        "run_id": run_id,
        "display_label": run_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "included_files": included_files,
    }

    with (run_dir / "metadata.json").open("w", encoding="utf-8") as metadata_file:
        json.dump(metadata, metadata_file, indent=2)

    return run_id


def list_saved_runs() -> list[dict]:
    """Return saved run metadata sorted newest first."""
    saved_runs = []

    if not RUNS_DIR.exists():
        return saved_runs

    for run_dir in RUNS_DIR.iterdir():
        if not run_dir.is_dir():
            continue

        metadata_path = run_dir / "metadata.json"
        if not metadata_path.exists():
            continue

        try:
            with metadata_path.open("r", encoding="utf-8") as metadata_file:
                saved_runs.append(json.load(metadata_file))
        except (json.JSONDecodeError, OSError):
            continue

    return sorted(saved_runs, key=lambda item: item.get("run_id", ""), reverse=True)


def load_saved_run(run_id: str) -> dict | None:
    """Load a saved run from disk, rerun the workflow, and return restored results."""
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        return None

    ga4_pages_path = run_dir / "ga4_pages.csv"
    ga4_source_path = run_dir / "ga4_source.csv"
    gsc_queries_path = run_dir / "gsc_queries.csv"
    semrush_positions_path = run_dir / "semrush_positions.csv"
    semrush_pages_path = run_dir / "semrush_pages.csv"
    semrush_topics_path = run_dir / "semrush_topics.csv"
    meta_posts_path = run_dir / "meta_posts.csv"

    ga4_pages_data = parse_csv_file(str(ga4_pages_path), "GA4_PAGES") if ga4_pages_path.exists() else None
    ga4_source_data = parse_csv_file(str(ga4_source_path), "GA4_SOURCE") if ga4_source_path.exists() else None
    gsc_queries_data = parse_csv_file(str(gsc_queries_path), "GSC_QUERIES") if gsc_queries_path.exists() else None
    semrush_positions_data = parse_semrush_positions_csv(semrush_positions_path) if semrush_positions_path.exists() else None
    semrush_pages_data = parse_semrush_pages_csv(semrush_pages_path) if semrush_pages_path.exists() else None
    semrush_topics_data = parse_semrush_topics_csv(semrush_topics_path) if semrush_topics_path.exists() else None
    meta_posts_data = parse_meta_posts_csv(meta_posts_path) if meta_posts_path.exists() else None

    results = run_workflow(
        ga4_pages_data=ga4_pages_data,
        ga4_source_data=ga4_source_data,
        gsc_queries_data=gsc_queries_data,
        semrush_positions_data=semrush_positions_data,
        semrush_pages_data=semrush_pages_data,
        semrush_topics_data=semrush_topics_data,
    )
    results["meta_posts_data"] = meta_posts_data
    results["social_insights"] = build_social_insights(meta_posts_data)

    ga4_debug_titles = []
    if ga4_pages_data is not None and "page_title" in ga4_pages_data.columns:
        ga4_debug_titles = ga4_pages_data["page_title"].head(5).fillna("").astype(str).tolist()

    return {
        "results": results,
        "ga4_debug_titles": ga4_debug_titles,
        "run_id": run_id,
    }


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
    target_ctr_percent = 5.0

    top_opportunity_query = get_first_value(insight["high_impression_low_click"], "query")
    top_ctr_percent = normalize_ctr_percent(top_opportunity_item.get("ctr")) if top_opportunity_item else None
    top_ctr_gap_value = max(0.0, target_ctr_percent - top_ctr_percent) if top_ctr_percent is not None else None
    top_ctr_gap = format_ctr_value(top_ctr_gap_value)
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
                top_queries_df = format_ctr_dataframe(pd.DataFrame(insight["query_analysis"]))
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



def render_analysis_page(results: dict) -> None:
    """Render the Analysis page (Traffic, Behavior, Queries, Pages)."""
    st.title("Analysis")
    st.caption("Performance data from GA4 + GSC")

    if not results:
        st.info("Run the workflow to view analysis.")
        return

    insight = results["insight"]
    combined = results["data_intake"]["summary"]["combined"]
    data_summary = results["data_intake"]["summary"]

    has_query_data = bool(insight["query_analysis"])
    has_page_data = bool(combined["top_pages"])
    has_source_data = bool(combined["top_traffic_sources"])
    has_behavior_data = (
        data_summary["ga4_pages"]["rows"] > 0 or data_summary["ga4_sources"]["rows"] > 0
    )

    if has_source_data:
        st.subheader("Traffic Distribution")
        top_sources_df = pd.DataFrame(combined["top_traffic_sources"])
        source_chart_df = top_sources_df[["source_medium", "value"]].set_index("source_medium")
        st.bar_chart(source_chart_df)
        st.dataframe(top_sources_df, use_container_width=True, hide_index=True)
        st.divider()

    if has_behavior_data:
        st.subheader("User Behavior")
        col1, col2, col3 = st.columns(3)

        behavior_metrics = {
            "Sessions": data_summary["ga4_pages"]["key_metrics"].get("sessions", "—"),
            "Active Users": data_summary["ga4_pages"]["key_metrics"].get("active_users", "—"),
            "Engagement Rate": data_summary["ga4_pages"]["key_metrics"].get("engagement_rate", "—"),
        }

        with col1:
            st.metric("Sessions", behavior_metrics["Sessions"])
        with col2:
            st.metric("Users", behavior_metrics["Active Users"])
        with col3:
            st.metric("Engagement Rate", behavior_metrics["Engagement Rate"])

        st.divider()

    if has_query_data:
        st.subheader("Top Queries")
        top_queries_df = format_ctr_dataframe(pd.DataFrame(insight["query_analysis"]))
        st.dataframe(
            top_queries_df[["query", "ctr", "impressions", "position"]].head(10),
            use_container_width=True,
            hide_index=True,
        )
        st.divider()

    if has_page_data:
        st.subheader("Top Pages")
        page_rows = []
        best_source = get_first_value(insight["top_sources"], "source_medium")

        for item in combined["top_pages"][:10]:
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


def render_social_analysis_page(results: dict) -> None:
    """Render the Social Analysis page using Meta social insights."""
    st.title("Social Analysis")
    st.caption("Instagram + Facebook performance insights")

    if not results:
        st.info("Upload a Meta content export and run the workflow first on the Data Sources page.")
        return

    social_insights = results.get("social_insights") or {}
    meta_posts_data = results.get("meta_posts_data")

    if not social_insights or meta_posts_data is None or getattr(meta_posts_data, "empty", True):
        st.info("Upload a Meta content export and run the workflow first on the Data Sources page.")
        return

    top_topics = social_insights.get("top_topics", [])
    weak_topics = social_insights.get("weak_topics", [])
    best_post_type = social_insights.get("best_post_type", "Not available")
    worst_post_type = social_insights.get("worst_post_type", "Not available")
    top_topic = humanize_social_topic(top_topics[0]) if top_topics else "Not available"
    weak_topic = humanize_social_topic(weak_topics[0]) if weak_topics else "Not available"

    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric("Best Post Type", best_post_type)
    with metric_cols[1]:
        st.metric("Worst Post Type", worst_post_type)
    with metric_cols[2]:
        st.metric("Top Topic", top_topic)
    with metric_cols[3]:
        st.metric("Weak Topic", weak_topic)

    st.subheader("Top Performing Content")
    top_performing_content = social_insights.get("top_performing_content", [])
    if top_performing_content:
        top_performing_df = pd.DataFrame(top_performing_content)
        visible_columns = [
            column
            for column in ["Hook", "Post type", "Topic", "Reach", "Engagement Rate", "Saves", "Follows"]
            if column in top_performing_df.columns
        ]
        st.dataframe(top_performing_df[visible_columns], use_container_width=True, hide_index=True)
    else:
        st.info("No top performing social content available yet.")

    st.subheader("Conversion Content")
    conversion_content = social_insights.get("conversion_content", [])
    if conversion_content:
        conversion_df = pd.DataFrame(conversion_content)
        visible_columns = [
            column
            for column in ["Hook", "Post type", "Topic", "Reach", "Engagement Rate", "Saves", "Follows"]
            if column in conversion_df.columns
        ]
        st.dataframe(conversion_df[visible_columns], use_container_width=True, hide_index=True)
    else:
        st.info("No conversion-oriented social content available yet.")

    st.subheader("Topic Insights")
    topic_left_col, topic_right_col = st.columns(2)

    with topic_left_col:
        st.markdown("**Top Topics**")
        if top_topics:
            for topic in top_topics:
                st.write(f"- {humanize_social_topic(topic)}")
        else:
            st.write("No top topics available yet.")

    with topic_right_col:
        st.markdown("**Weak Topics**")
        if weak_topics:
            for topic in weak_topics:
                st.write(f"- {humanize_social_topic(topic)}")
        else:
            st.write("No weak topics available yet.")

    st.subheader("What Drives Performance")
    st.write(f"**What Drives Saves:** {social_insights.get('what_drives_saves', 'Not available')}")
    st.write(f"**What Drives Follows:** {social_insights.get('what_drives_follows', 'Not available')}")

    st.subheader("Balance Problems")
    balance_problems = social_insights.get("balance_problems", [])
    if balance_problems:
        for issue in balance_problems:
            st.markdown(
                f"""
                <div class="panel">
                    <strong>Issue:</strong> {issue}
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No balance problems detected yet.")


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


def build_semrush_topic_cards(
    semrush_topics_data: pd.DataFrame,
    strategy_topic_opportunities: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    """Turn SEMrush Topic Opportunities data into AI topic cards."""
    dataframe = semrush_topics_data.copy()
    dataframe.columns = [str(column).strip().lower() for column in dataframe.columns]
    strategy_topic_opportunities = strategy_topic_opportunities or []

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
        topic_value = str(row[topic_column])
        volume_value = int(row[volume_column]) if volume_column and pd.notna(row[volume_column]) else None
        competitor_value = int(row[competitor_column]) if competitor_column and pd.notna(row[competitor_column]) else 0
        strategy_match = next(
            (
                item
                for item in strategy_topic_opportunities
                if str(item.get("topic", "")).strip().lower() == topic_value.strip().lower()
            ),
            {},
        )

        priority = "High" if (volume_value or 0) >= 500 or competitor_value >= 5 else "Medium"
        cards.append(
            {
                "topic": topic_value,
                "volume": str(volume_value) if volume_value is not None else "Not available",
                "intent_type": format_heading(str(strategy_match.get("intent_type", ""))).title()
                if strategy_match.get("intent_type")
                else "",
                "opportunity_type": format_heading(str(strategy_match.get("opportunity_type", ""))).title()
                if strategy_match.get("opportunity_type")
                else "",
                "gap_type": format_heading(str(strategy_match.get("gap_type", ""))).title()
                if strategy_match.get("gap_type")
                else "",
                "why_it_matters": (
                    str(strategy_match.get("why_it_matters", "")).strip()
                    or (
                        "This topic can help the site build AI visibility and close a meaningful content gap."
                        if priority == "High"
                        else "This topic supports future authority building and can strengthen cluster-level coverage."
                    )
                ),
                "recommended_action": (
                    str(strategy_match.get("recommended_action", "")).strip()
                    or str(strategy_match.get("action", "")).strip()
                    or (
                        "Create a dedicated page or in-depth guide supported by related cluster content."
                        if priority == "High"
                        else "Add the topic into an existing cluster or build a focused supporting article."
                    )
                ),
                "priority": str(strategy_match.get("priority", priority)),
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

    queue: list[dict[str, object]] = []

    for item in insight["high_impression_low_click"][:5]:
        impressions = item.get("impressions", 0)
        ctr = item.get("ctr", 0)
        position = item.get("position", 0)
        impact_score = float(impressions or 0) + max(0.0, 20.0 - float(position or 0)) * 25

        queue.append(
            {
                "title": f"Improve CTR for {item['query']}",
                "data_source": "GSC",
                "supporting_data": f"Impressions: {int(impressions)} | CTR: {format_ctr_value(ctr)} | Position: {position}",
                "why_it_matters": "This query already has visibility but is underperforming on clicks, which signals a strong high-intent gap.",
                "recommended_action": "Refresh the title tag, meta description, and on-page answer structure to better match search intent.",
                "priority": "High",
                "impact_score": impact_score,
            }
        )

    for item in insight["conversion_intent_queries"][:3]:
        if any(str(existing["title"]).endswith(item["query"]) for existing in queue):
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
                "supporting_data": f"Impressions: {int(impressions)} | CTR: {format_ctr_value(ctr)} | Position: {position}",
                "why_it_matters": "This conversion-oriented query suggests commercial demand that could turn into appointments with stronger coverage.",
                "recommended_action": "Add targeted copy, FAQs, and internal links so the page better supports decision-stage search intent.",
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
                "why_it_matters": "A page already attracting meaningful traffic is one of the fastest places to improve conversions and content performance.",
                "recommended_action": "Review message clarity, CTA placement, and content depth so existing traffic is more likely to convert.",
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
                "why_it_matters": "This source is already driving visits, so improving the destination experience can lift outcomes without needing a new acquisition channel.",
                "recommended_action": "Audit the landing pages receiving this traffic and align headlines, trust signals, and CTAs with acquisition intent.",
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
                        "supporting_data": f"Position: {int(position)} | Volume: {int(volume) if volume else 'Not available'} | URL: {url_value}",
                        "why_it_matters": (
                            "This keyword is already ranking within reach, which makes it a realistic SEO opportunity with measurable upside."
                            if priority == "High"
                            else "The keyword has moderate ranking visibility and could become stronger with more focused optimization."
                        ),
                        "recommended_action": "Tighten keyword targeting in the title tag, H1, supporting copy, and FAQ content.",
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
                        "why_it_matters": "This page already has search visibility, so improving UX, messaging, or conversion paths can create faster business impact.",
                        "recommended_action": "Review content depth, internal linking, and CTA hierarchy to make the page more competitive and conversion-focused.",
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
                        "why_it_matters": "This topic represents a broader content gap that can strengthen authority, internal linking, and AI-search relevance.",
                        "recommended_action": "Create a focused page or guide, then support it with cluster content and internal links.",
                        "priority": priority,
                        "impact_score": impact_score,
                    }
                )

    priority_rank = {"High": 3, "Medium": 2, "Low": 1}
    sorted_queue = sorted(
        queue,
        key=lambda item: (priority_rank.get(str(item["priority"]), 0), float(item.get("impact_score", 0))),
        reverse=True,
    )

    return [
        {
            "title": str(item["title"]),
            "data_source": str(item["data_source"]),
            "supporting_data": str(item["supporting_data"]),
            "why_it_matters": str(item["why_it_matters"]),
            "recommended_action": str(item["recommended_action"]),
            "priority": str(item["priority"]),
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
        metric_name = item["metric"]
        metric_value = item["value"]
        if str(metric_name).strip().lower() == "ctr":
            metric_value = format_ctr_value(metric_value)
        rows.append(
            {
                "section": "top_queries",
                "label": item["query"],
                "metric": metric_name,
                "value": str(metric_value),
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


def render_data_sources() -> dict[str, object]:
    """Render uploaders and workflow trigger on the Data Sources page."""
    st.title("Data Sources")
    st.write("Upload and manage your marketing data inputs")
    saved_runs = list_saved_runs()

    if st.session_state.get("loaded_run_id"):
        st.caption(f"Current loaded run: {st.session_state['loaded_run_id']}")

    if saved_runs:
        run_labels = {run["run_id"]: run.get("display_label", run["run_id"]) for run in saved_runs}
        selected_saved_run_id = st.selectbox(
            "Load Previous Run",
            options=[run["run_id"] for run in saved_runs],
            format_func=lambda run_id: run_labels.get(run_id, run_id),
        )
        load_saved_run_button = st.button("Load Selected Run")
    else:
        st.info("No saved runs yet.")
        selected_saved_run_id = None
        load_saved_run_button = False

    st.subheader("Upload CSV files")
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

    st.write("Meta Content Export: Instagram / Facebook post-level performance export from Meta Business Suite.")
    meta_posts_file = st.file_uploader("Upload Meta Content Export CSV", type="csv")

    st.subheader("Run the workflow")
    run_button = st.button("Run Workflow")

    return {
        "ga4_pages_file": ga4_pages_file,
        "ga4_source_file": ga4_source_file,
        "gsc_queries_file": gsc_queries_file,
        "semrush_positions_file": semrush_positions_file,
        "semrush_pages_file": semrush_pages_file,
        "semrush_topics_file": semrush_topics_file,
        "meta_posts_file": meta_posts_file,
        "selected_saved_run_id": selected_saved_run_id,
        "load_saved_run_button": load_saved_run_button,
        "run_button": run_button,
    }


def build_social_opportunity_cards(results: dict) -> list[dict[str, str]]:
    """Build social opportunity cards from Meta social insight summaries."""
    social_insights = results.get("social_insights", {})
    top_topics = social_insights.get("top_topics", [])
    weak_topics = social_insights.get("weak_topics", [])
    best_post_type = social_insights.get("best_post_type", "Not available")
    worst_post_type = social_insights.get("worst_post_type", "Not available")
    balance_problems = social_insights.get("balance_problems", [])
    what_drives_saves = social_insights.get("what_drives_saves", "Not available")
    what_drives_follows = social_insights.get("what_drives_follows", "Not available")

    cards = []

    if best_post_type and best_post_type != "Not available":
        cards.append(
            {
                "title": f"Double down on {best_post_type}",
                "area": "Format Opportunity",
                "supporting_data": f"Best Post Type: {best_post_type}",
                "why_it_matters": (
                    "This format is currently producing the strongest results and is the best candidate to scale with repeatable hooks and topics."
                ),
                "recommended_action": (
                    "Create more content in this format using the same topic patterns, strong openings, and high-performing post structure."
                ),
                "priority": "High",
            }
        )

    if worst_post_type and worst_post_type != "Not available":
        cards.append(
            {
                "title": f"Improve or reduce {worst_post_type}",
                "area": "Format Opportunity",
                "supporting_data": f"Worst Post Type: {worst_post_type}",
                "why_it_matters": (
                    "This format is currently the weakest, which suggests it may need stronger hooks, clearer structure, or less overall emphasis."
                ),
                "recommended_action": (
                    "Test stronger hooks and CTAs for this format, or shift effort toward better-performing content types."
                ),
                "priority": "Medium",
            }
        )

    if top_topics:
        cards.append(
            {
                "title": f"Scale content around {top_topics[0]}",
                "area": "Topic Opportunity",
                "supporting_data": f"Top Topic: {top_topics[0]}",
                "why_it_matters": (
                    "This topic is currently resonating most and should be turned into a repeatable content theme across multiple posts."
                ),
                "recommended_action": (
                    "Build a small content series with multiple hook variations, post formats, and follow-up angles around this topic."
                ),
                "priority": "High",
            }
        )

    if weak_topics:
        cards.append(
            {
                "title": f"Fix or replace weak topic: {weak_topics[0]}",
                "area": "Topic Opportunity",
                "supporting_data": f"Weak Topic: {weak_topics[0]}",
                "why_it_matters": (
                    "This topic appears to be underperforming and may not be connecting with the audience in its current angle or format."
                ),
                "recommended_action": (
                    "Test a new hook, a different format, or a stronger CTA for this topic, and reduce emphasis if performance stays weak."
                ),
                "priority": "Medium",
            }
        )

    if what_drives_saves and what_drives_saves != "Not available":
        cards.append(
            {
                "title": "Turn save-worthy content into conversion content",
                "area": "Content Gap",
                "supporting_data": what_drives_saves,
                "why_it_matters": (
                    "Content that earns saves already shows strong audience value, but it needs a clearer next-step path to drive business outcomes."
                ),
                "recommended_action": (
                    "Add stronger CTAs, trust signals, booking prompts, or quiz links so high-value content also pushes users toward action."
                ),
                "priority": "High",
            }
        )

    if what_drives_follows and what_drives_follows != "Not available":
        cards.append(
            {
                "title": "Replicate follow-driving content",
                "area": "Growth Opportunity",
                "supporting_data": what_drives_follows,
                "why_it_matters": (
                    "This content pattern is strongest for audience growth and can be scaled into a repeatable acquisition engine."
                ),
                "recommended_action": (
                    "Create multiple new posts using similar hooks, topics, and structure to expand reach and follower growth."
                ),
                "priority": "High",
            }
        )

    for issue in balance_problems[:4]:
        issue_text = str(issue)
        issue_lower = issue_text.lower()

        if "low conversion" in issue_lower:
            recommended_action = "Add stronger CTAs, clearer next-step guidance, and more direct conversion prompts."
            priority = "High"
        elif "best-performing pattern" in issue_lower:
            recommended_action = "Replicate this pattern and turn it into a reusable post template for future content."
            priority = "High"
        elif "low reach but strong conversion" in issue_lower:
            recommended_action = "Repurpose this content, boost distribution, or turn it into a Reel to increase visibility."
            priority = "Medium"
        else:
            recommended_action = "Improve the hook, opening, and creative payoff so the content better holds attention."
            priority = "Medium"

        cards.append(
            {
                "title": "Balance Problem Detected",
                "area": "Performance Gap",
                "supporting_data": issue_text,
                "why_it_matters": (
                    "This imbalance suggests the content is not yet performing strongly across the full funnel from reach to engagement to conversion."
                ),
                "recommended_action": recommended_action,
                "priority": priority,
            }
        )

    return cards


def build_social_recommendation_cards(results: dict) -> list[dict[str, str]]:
    """Build social recommendation cards from Meta social insight summaries."""
    social_insights = results.get("social_insights", {})
    top_topics = social_insights.get("top_topics", [])
    weak_topics = social_insights.get("weak_topics", [])
    best_post_type = social_insights.get("best_post_type", "Not available")
    worst_post_type = social_insights.get("worst_post_type", "Not available")
    balance_problems = social_insights.get("balance_problems", [])
    what_drives_saves = social_insights.get("what_drives_saves", "Not available")
    what_drives_follows = social_insights.get("what_drives_follows", "Not available")

    cards = []

    if best_post_type and best_post_type != "Not available":
        cards.append(
            {
                "category": "social_format",
                "issue": f"{best_post_type} is the strongest current social format.",
                "recommendation": "Scale this format by creating more posts with similar hooks, structure, and topics.",
                "why_it_matters": "Doubling down on the best-performing format is the fastest way to increase reach, saves, and growth.",
                "priority": "High",
            }
        )

    if worst_post_type and worst_post_type != "Not available":
        cards.append(
            {
                "category": "social_format",
                "issue": f"{worst_post_type} is underperforming compared to other formats.",
                "recommendation": "Test stronger hooks, a clearer CTA, or shift effort toward stronger formats if performance stays low.",
                "why_it_matters": "Improving or reducing weak formats prevents wasted effort and improves content efficiency.",
                "priority": "Medium",
            }
        )

    if top_topics:
        cards.append(
            {
                "category": "social_topic",
                "issue": f"{top_topics[0]} is currently the strongest content topic.",
                "recommendation": "Create a repeatable content series around this topic using multiple formats.",
                "why_it_matters": "Top-performing topics are the easiest opportunities to scale because they already resonate with the audience.",
                "priority": "High",
            }
        )

    if weak_topics:
        cards.append(
            {
                "category": "social_topic",
                "issue": f"{weak_topics[0]} is underperforming.",
                "recommendation": "Test a different hook, stronger patient-focused angle, or reduce emphasis on this topic.",
                "why_it_matters": "Weak topics may be misaligned with audience interest, patient intent, or format fit.",
                "priority": "Medium",
            }
        )

    if what_drives_saves and what_drives_saves != "Not available":
        cards.append(
            {
                "category": "social_conversion",
                "issue": "Some content is generating saves without a strong next step.",
                "recommendation": "Add stronger CTAs, trust signals, quiz prompts, or booking guidance to save-worthy content.",
                "why_it_matters": "Saves signal interest, but without conversion guidance, the content may not move patients toward action.",
                "priority": "High",
            }
        )

    if what_drives_follows and what_drives_follows != "Not available":
        cards.append(
            {
                "category": "social_growth",
                "issue": "Some content is clearly stronger for follower growth.",
                "recommendation": "Replicate the hook/topic structure of follow-driving posts in new variations.",
                "why_it_matters": "Follower-driving content is a strong signal of audience expansion potential.",
                "priority": "High",
            }
        )

    for issue_text in balance_problems[:4]:
        issue_lower = str(issue_text).lower()

        if "low engagement" in issue_lower:
            cards.append(
                {
                    "category": "social_hook",
                    "issue": str(issue_text),
                    "recommendation": "Improve the hook, first frame, and creative payoff so the content earns more interaction.",
                    "why_it_matters": "High reach with low engagement usually means the post is visible but not compelling enough to hold attention.",
                    "priority": "Medium",
                }
            )
        elif "low conversion" in issue_lower:
            cards.append(
                {
                    "category": "social_conversion",
                    "issue": str(issue_text),
                    "recommendation": "Add a stronger CTA and a clearer next step such as booking, quiz, or consultation prompt.",
                    "why_it_matters": "High engagement without conversion means the audience is interested but not being guided forward.",
                    "priority": "High",
                }
            )
        elif "low reach but strong conversion" in issue_lower:
            cards.append(
                {
                    "category": "social_scale",
                    "issue": str(issue_text),
                    "recommendation": "Repurpose the content into a Reel, test a stronger opening, or boost it to increase visibility.",
                    "why_it_matters": "If a post converts well at low reach, the content itself is strong and needs more distribution.",
                    "priority": "High",
                }
            )
        elif "best-performing pattern" in issue_lower:
            cards.append(
                {
                    "category": "social_scale",
                    "issue": str(issue_text),
                    "recommendation": "Treat this as a winning template and build multiple new posts from the same structure.",
                    "why_it_matters": "Best-performing patterns are the clearest signal of what to replicate.",
                    "priority": "High",
                }
            )

    return cards


def build_combined_what_next_cards(results: dict) -> list[dict[str, str]]:
    """Build a concise combined website + social next-step list."""
    strategy = results.get("strategy", {}).get("strategy", {})
    website_cards = []
    social_cards = []

    for item in strategy.get("priority_actions", []):
        website_cards.append(
            {
                "title": str(item.get("title", "Website Priority Action")),
                "action": str(item.get("action", "")),
                "reason": str(item.get("reason", "")),
                "priority": str(item.get("priority", "Medium")),
            }
        )

    social_priority_title_map = {
        "social_conversion": "Improve social conversion path",
        "social_format": "Scale winning social format",
        "social_topic": "Fix underperforming topic",
        "social_scale": "Replicate best-performing content",
        "social_growth": "Replicate best-performing content",
        "social_hook": "Improve social hook performance",
    }

    for item in build_social_recommendation_cards(results):
        if str(item.get("priority", "")).strip().title() != "High":
            continue
        social_cards.append(
            {
                "title": social_priority_title_map.get(str(item.get("category", "")), "Social Priority Action"),
                "action": str(item.get("recommendation", "")),
                "reason": str(item.get("why_it_matters", "")),
                "priority": str(item.get("priority", "High")),
            }
        )

    combined_cards = website_cards + social_cards[:3]
    priority_rank = {"High": 3, "Medium": 2, "Low": 1}
    combined_cards = sorted(
        combined_cards,
        key=lambda item: priority_rank.get(str(item.get("priority", "Low")).title(), 0),
        reverse=True,
    )

    return combined_cards[:6]


def build_chat_context_summary(results: dict) -> str:
    """Create a concise internal summary of the loaded website and social context."""
    if not results:
        return "No marketing data is currently loaded."

    insight = results.get("insight", {})
    strategy = results.get("strategy", {}).get("strategy", {})
    social_insights = results.get("social_insights", {})
    semrush_positions_data = results.get("semrush_positions_data")
    semrush_pages_data = results.get("semrush_pages_data")
    semrush_topics_data = results.get("semrush_topics_data")

    summary_parts = [
        f"Top opportunity query: {get_first_value(insight.get('high_impression_low_click', []), 'query')}.",
        f"Top traffic source: {get_first_value(insight.get('top_sources', []), 'source_medium')}.",
        f"Primary page: {strategy.get('primary_page', 'Not available')}.",
    ]

    patterns = insight.get("patterns", [])
    if patterns:
        summary_parts.append(f"Top website patterns: {' | '.join(patterns[:3])}.")

    if semrush_positions_data is not None and not getattr(semrush_positions_data, "empty", True):
        keyword_cards = build_semrush_opportunity_cards(semrush_positions_data)
        if keyword_cards:
            summary_parts.append(f"Top keyword opportunity: {keyword_cards[0].get('keyword', 'Not available')}.")

    if semrush_pages_data is not None and not getattr(semrush_pages_data, "empty", True):
        page_cards = build_semrush_page_cards(semrush_pages_data)
        if page_cards:
            summary_parts.append(f"Top page opportunity: {page_cards[0].get('page_url', 'Not available')}.")

    if semrush_topics_data is not None and not getattr(semrush_topics_data, "empty", True):
        topic_cards = build_semrush_topic_cards(
            semrush_topics_data,
            strategy.get("topic_opportunities", []),
        )
        if topic_cards:
            summary_parts.append(f"Top topic opportunity: {topic_cards[0].get('topic', 'Not available')}.")

    if social_insights:
        summary_parts.append(f"Best social format: {social_insights.get('best_post_type', 'Not available')}.")
        summary_parts.append(f"Worst social format: {social_insights.get('worst_post_type', 'Not available')}.")
        if social_insights.get("top_topics"):
            summary_parts.append(
                f"Top social topics: {', '.join(humanize_social_topic(topic) for topic in social_insights.get('top_topics', [])[:3])}."
            )
        if social_insights.get("weak_topics"):
            summary_parts.append(
                f"Weak social topics: {', '.join(humanize_social_topic(topic) for topic in social_insights.get('weak_topics', [])[:3])}."
            )
        summary_parts.append(f"What drives saves: {social_insights.get('what_drives_saves', 'Not available')}.")
        summary_parts.append(f"What drives follows: {social_insights.get('what_drives_follows', 'Not available')}.")
        if social_insights.get("balance_problems"):
            summary_parts.append(
                f"Balance problems: {' | '.join(social_insights.get('balance_problems', [])[:3])}."
            )

    priority_actions = strategy.get("priority_actions", [])
    if priority_actions:
        summary_parts.append(
            f"Top website priority actions: {' | '.join(action.get('title', '') for action in priority_actions[:3])}."
        )

    social_recommendations = build_social_recommendation_cards(results)
    if social_recommendations:
        summary_parts.append(
            f"Top social recommendation themes: {' | '.join(format_heading(card.get('category', 'social')).title() for card in social_recommendations[:3])}."
        )

    return " ".join(summary_parts)


def user_asked_for_more_ideas(user_message: str) -> bool:
    """Return True when the user is explicitly asking for multiple ideas or options."""
    message_lower = user_message.lower()
    triggers = [
        "more ideas",
        "more options",
        "3 ideas",
        "3 recommendations",
        "what else",
        "give me more",
        "additional recommendations",
    ]
    return any(trigger in message_lower for trigger in triggers)


def generate_ai_chat_response(user_message: str, results: dict | None) -> str:
    """Generate a structured strategist response using loaded run data."""
    if not results:
        return (
            "INSIGHT\n"
            "No marketing data is loaded yet.\n\n"
            "WHY IT MATTERS\n"
            "Without a loaded run, I cannot tie advice to your actual GA4, GSC, SEMrush, or Meta performance.\n\n"
            "RECOMMENDATION\n"
            "Load a saved run or upload fresh data on the Data Sources page first.\n\n"
            "NEXT ACTION\n"
            "Go to Data Sources, load a previous run or upload your files, then ask your question again."
        )

    message_lower = user_message.lower()
    insight = results.get("insight", {})
    strategy = results.get("strategy", {}).get("strategy", {})
    social_insights = results.get("social_insights", {})
    context_summary = build_chat_context_summary(results)

    top_query = get_first_value(insight.get("high_impression_low_click", []), "query")
    top_source = get_first_value(insight.get("top_sources", []), "source_medium")
    primary_page = strategy.get("primary_page", "Not available")
    priority_actions = strategy.get("priority_actions", [])
    social_best_format = social_insights.get("best_post_type", "Not available")
    social_worst_format = social_insights.get("worst_post_type", "Not available")
    social_top_topic = (
        humanize_social_topic(social_insights.get("top_topics", [])[0])
        if social_insights.get("top_topics")
        else "Not available"
    )
    social_weak_topic = (
        humanize_social_topic(social_insights.get("weak_topics", [])[0])
        if social_insights.get("weak_topics")
        else "Not available"
    )
    social_balance_problems = social_insights.get("balance_problems", [])

    insight_text = ""
    why_text = ""
    recommendation_text = ""
    next_action_text = ""
    additional_ideas: list[str] = []

    if any(term in message_lower for term in ["reel", "reels", "engagement", "post", "social", "instagram", "facebook"]):
        if not social_insights:
            insight_text = "Meta social data is not loaded in the current run."
            why_text = "Without Meta post-level performance, I cannot diagnose what is driving reach, saves, follows, or weak engagement."
            recommendation_text = "Upload a Meta content export so the strategy can connect content format, topic, and conversion behavior."
            next_action_text = "Go to Data Sources, upload the Meta Content Export CSV, and rerun the workflow."
        elif "conversion" in message_lower and "low" in message_lower:
            issue = social_balance_problems[0] if social_balance_problems else "The current social funnel is not converting as strongly as engagement suggests."
            insight_text = issue
            why_text = "Your loaded social data suggests interest exists, but the path from attention to follow, quiz, or booking action is still too weak."
            recommendation_text = "Strengthen conversion prompts on the formats and topics already earning attention, especially by adding clearer next-step guidance, quiz prompts, or booking language."
            next_action_text = "Start with the best-performing format and add one direct CTA variant to the next 3 posts."
            additional_ideas = [
                "Turn save-worthy content into CTA-led variants with a clearer follow or booking prompt.",
                "Use the strongest follow-driving hook again, but change the close so it pushes one clear next step.",
            ]
        elif "engagement" in message_lower and "low" in message_lower:
            issue = next((item for item in social_balance_problems if "low engagement" in item.lower()), "")
            insight_text = issue or f"{social_worst_format} is the weakest current social format."
            why_text = "Low engagement usually means the post is getting seen but the opening, framing, or payoff is not strong enough to hold attention."
            recommendation_text = "Improve the first frame and hook on the weakest format before increasing volume."
            next_action_text = "Rewrite the next 3 low-performing posts so the first line or first frame creates a sharper problem-solution payoff."
            additional_ideas = [
                f"Test the strongest topic, {social_top_topic}, in a more attention-grabbing format.",
                "Repurpose a post that already drove saves into a shorter, stronger opening sequence.",
            ]
        elif any(term in message_lower for term in ["what should i post", "content works best", "what content works best"]):
            insight_text = f"{social_best_format} is the strongest current social format, and {social_top_topic} is the strongest topic theme in the loaded run."
            why_text = "The fastest social growth usually comes from scaling what is already producing saves, follows, or strong engagement, not from inventing a new content direction from scratch."
            recommendation_text = f"Create more {social_best_format} content around {social_top_topic}, using the same style of hook that is already driving saves or follows."
            next_action_text = "Build a 3-post content series this week using your strongest topic and strongest format."
            additional_ideas = [
                "Create one educational variation, one trust-building variation, and one CTA-led variation of the same topic.",
                "Turn the top save-driving pattern into a Reel and a Carousel to test format expansion.",
            ]
        else:
            insight_text = f"Your current social signals point to {social_best_format} as the strongest format and {social_top_topic} as the strongest topic, while {social_weak_topic} is lagging."
            why_text = "That gives a clear performance split between what should be scaled and what should be fixed or reduced."
            recommendation_text = "Scale the strongest format-topic combination first instead of spreading effort evenly across all content types."
            next_action_text = "Use the next content cycle to prioritize one winning format and one winning topic."
            additional_ideas = [
                "Reduce effort on the weakest topic until a stronger hook or format test is ready.",
                "Replicate the strongest follow-driving pattern with a sharper patient-acquisition CTA.",
            ]
    elif any(term in message_lower for term in ["top opportunity", "optimize first", "seo", "website", "query", "page", "traffic"]):
        if not insight:
            insight_text = "Website and SEO data is missing from the current run."
            why_text = "Without GA4, GSC, or SEMrush inputs, I cannot identify the highest-leverage website opportunity."
            recommendation_text = "Load a run with website data so the recommendation can be tied to actual search and traffic performance."
            next_action_text = "Upload GA4, GSC, or SEMrush data and rerun the workflow."
        else:
            top_action = priority_actions[0] if priority_actions else {}
            insight_text = (
                f"The clearest website opportunity is {top_query}, with {primary_page} as the primary page to optimize first."
            )
            why_text = (
                f"The loaded run shows existing visibility around {top_query} and a clear page-level focus, which means you can improve growth faster by concentrating effort instead of spreading it across multiple pages."
            )
            recommendation_text = (
                top_action.get("action")
                or f"Optimize {primary_page} first around {top_query}, tightening page structure, SERP messaging, and conversion guidance."
            )
            next_action_text = (
                f"Start with {primary_page}, then align the title, H1, FAQ content, and CTA flow to the demand showing up in {top_query}."
            )
            additional_ideas = [
                f"Use {top_source} landing-page traffic as a second optimization layer so the page converts better once rankings improve.",
                "Support the primary page with one related topic asset to strengthen internal linking and topical depth.",
            ]
    elif any(term in message_lower for term in ["what should i do", "give me recommendations", "strategy", "mixed", "growth"]):
        website_action = priority_actions[0] if priority_actions else {}
        social_recommendations = build_social_recommendation_cards(results)
        top_social = social_recommendations[0] if social_recommendations else {}

        insight_text = (
            f"Your loaded run shows a split opportunity: website growth is centered on {top_query}, while social momentum is strongest in {social_best_format} content."
        )
        why_text = (
            "That means your next move should not be generic marketing activity. It should be one website action and one content action that both map to the strongest available signals."
        )
        recommendation_text = (
            website_action.get("action")
            or f"Optimize {primary_page} first for {top_query}, then align social content to reinforce the same patient questions and conversion themes."
        )
        next_action_text = (
            top_social.get("recommendation")
            or "Use the strongest website topic as the basis for the next social content series so both channels reinforce the same growth priority."
        )
        additional_ideas = [
            "Turn the primary SEO question into a short-form social series that warms up the same patient audience.",
            "Use social save-driving content as a clue for which FAQs should move higher on the main website page.",
        ]
    else:
        insight_text = context_summary
        why_text = "The loaded run gives enough context to identify one immediate growth move, but your question is broad enough that I need to anchor the response to the strongest currently visible signal."
        recommendation_text = (
            priority_actions[0].get("action")
            if priority_actions
            else "Start with the clearest loaded website or social signal rather than spreading effort across every channel."
        )
        next_action_text = (
            "Ask a more specific question about SEO, social, conversions, content, or optimization priority if you want a tighter strategist answer."
        )
        additional_ideas = [
            "Ask which page to optimize first.",
            "Ask what social content format to scale next.",
        ]

    response = (
        f"INSIGHT\n{insight_text}\n\n"
        f"WHY IT MATTERS\n{why_text}\n\n"
        f"RECOMMENDATION\n{recommendation_text}\n\n"
        f"NEXT ACTION\n{next_action_text}"
    )

    if user_asked_for_more_ideas(user_message):
        extra_lines = [f"- {idea}" for idea in additional_ideas[:2]] or ["- Ask a more specific follow-up and I can give two grounded options."]
        response += "\n\nADDITIONAL IDEAS\n" + "\n".join(extra_lines)

    return response



def render_opportunity_card(title: str, data: dict[str, str]) -> None:
    """Render a website opportunity using the same card style as recommendations."""
    priority = str(data.get("priority", "Medium")).strip().title()
    priority_class_map = {
        "High": "priority-high-pill",
        "Medium": "priority-medium-pill",
        "Low": "priority-low-pill",
    }
    pill_class = priority_class_map.get(priority, "priority-medium-pill")

    body_parts = []

    if data.get("keyword"):
        body_parts.append(f"<strong>Keyword:</strong> {data.get('keyword', '-')}")
    if data.get("position"):
        body_parts.append(f"<strong>Position:</strong> {data.get('position', '-')}")
    if data.get("page_url"):
        body_parts.append(f"<strong>Page:</strong> {data.get('page_url', '-')}")
    if data.get("metric_line"):
        body_parts.append(f"<strong>Metrics:</strong> {data.get('metric_line', '-')}")
    if data.get("topic"):
        body_parts.append(f"<strong>Topic:</strong> {data.get('topic', '-')}")
    if data.get("volume") and data.get("volume") != "Not available":
        body_parts.append(f"<strong>Volume:</strong> {data.get('volume', '-')}")
    if data.get("url") and data.get("url") != "Not available":
        url = str(data.get("url", "#"))
        body_parts.append(f'<strong>URL:</strong> <a href="{url}" target="_blank">{url}</a>')
    if data.get("intent_type") or data.get("opportunity_type") or data.get("gap_type"):
        tag_parts = [part for part in [data.get("intent_type"), data.get("opportunity_type"), data.get("gap_type")] if part]
        body_parts.append(f"<strong>Tags:</strong> {' | '.join(tag_parts)}")
    if data.get("why_it_matters") or data.get("reason"):
        body_parts.append(f"<strong>Why it matters:</strong> {data.get('why_it_matters', data.get('reason', ''))}")
    if data.get("recommended_action") or data.get("action"):
        body_parts.append(f"<strong>Recommended action:</strong> {data.get('recommended_action', data.get('action', ''))}")

    body_html = "<br><br>".join(body_parts) if body_parts else "No opportunity details available."

    st.markdown(
        f"""
        <div class="recommendation-card">
            <div class="recommendation-card-top">
                <div class="recommendation-category">{title}</div>
                <div class="{pill_class}">{priority} Priority</div>
            </div>
            <div class="recommendation-body">
                {body_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_opportunities_page(results: dict) -> None:
    """Render the Opportunities page."""
    st.title("Opportunities")
    st.caption("Combined website + social growth opportunities")

    if not results:
        st.info("Run the workflow first on the Data Sources page.")
        return

    semrush_positions_data = results.get("semrush_positions_data")
    semrush_pages_data = results.get("semrush_pages_data")
    semrush_topics_data = results.get("semrush_topics_data")
    strategy = results["strategy"]["strategy"]
    social_cards = build_social_opportunity_cards(results)

    st.subheader("Website Opportunities")

    if semrush_positions_data is not None and not semrush_positions_data.empty:
        st.markdown("**Keyword Opportunities**")
        opportunity_cards = build_semrush_opportunity_cards(semrush_positions_data)
        if opportunity_cards:
            for card in opportunity_cards:
                render_opportunity_card("SEO Opportunity", card)
        else:
            st.info("No SEMrush keyword opportunities available yet.")
    else:
        st.info("No SEMrush Organic Positions data uploaded yet.")

    if semrush_pages_data is not None and not semrush_pages_data.empty:
        st.markdown("**Page Opportunities**")
        page_cards = build_semrush_page_cards(semrush_pages_data)
        if page_cards:
            for card in page_cards:
                render_opportunity_card("Page Opportunity", card)
        else:
            st.info("No SEMrush page opportunities available yet.")
    else:
        st.info("No SEMrush Pages Report data uploaded yet.")

    if semrush_topics_data is not None and not semrush_topics_data.empty:
        st.markdown("**AI Topic Opportunities**")
        topic_cards = build_semrush_topic_cards(
            semrush_topics_data,
            strategy.get("topic_opportunities", []),
        )
        if topic_cards:
            for card in topic_cards:
                render_opportunity_card("Topic Opportunity", card)
        else:
            st.info("No SEMrush topic opportunities available yet.")
    else:
        st.info("No SEMrush Topic Opportunities data uploaded yet.")

    st.subheader("Social Opportunities")
    if social_cards:
        priority_class_map = {
            "High": "priority-high-pill",
            "Medium": "priority-medium-pill",
            "Low": "priority-low-pill",
        }

        for card in social_cards:
            card_priority = str(card.get("priority", "Medium")).strip().title()
            pill_class = priority_class_map.get(card_priority, "priority-medium-pill")

            st.markdown(
                f"""
                <div class="recommendation-card">
                    <div class="recommendation-card-top">
                        <div class="recommendation-category">{card.get("title", "Social Opportunity")}</div>
                        <div class="{pill_class}">{card_priority} Priority</div>
                    </div>
                    <div class="recommendation-body">
                        <strong>Area:</strong> {card.get("area", "Not available")}<br><br>
                        <strong>Supporting Data:</strong> {card.get("supporting_data", "Not available")}<br><br>
                        <strong>Why it matters:</strong> {card.get("why_it_matters", "")}<br><br>
                        <strong>Recommended action:</strong> {card.get("recommended_action", "")}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No social opportunities available yet. Upload a Meta content export and run the workflow.")


def build_take_action_payload(card: dict, results: dict) -> dict | None:
    """Build a drill-down action payload for supported recommendation types."""
    if not results or not card:
        return None

    category = str(card.get("category", "")).strip().lower()
    issue_text = str(card.get("issue", "")).strip()
    recommendation_text = str(card.get("recommendation", "") or card.get("action", "")).strip()
    combined_text = f"{category} {issue_text} {recommendation_text}".lower()

    website_terms = [
        "seo",
        "keyword",
        "ctr",
        "title",
        "meta",
        "h1",
        "faq",
        "content update",
        "content refresh",
    ]
    social_terms = [
        "social",
        "follow",
        "format",
        "variation",
        "content series",
        "conversion",
        "best-performing",
        "growth",
        "reel",
    ]

    if any(term in combined_text for term in website_terms):
        insight = results.get("insight", {})
        strategy = results.get("strategy", {}).get("strategy", {})
        semrush_positions_data = results.get("semrush_positions_data")
        combined = results.get("data_intake", {}).get("summary", {}).get("combined", {})

        top_query = get_first_value(insight.get("high_impression_low_click", []), "query")
        primary_page = (
            str(strategy.get("primary_page", "")).strip()
            or get_first_value(combined.get("top_pages", []), "page_title")
        )

        keywords: list[str] = []
        if top_query != "Not available":
            keywords.append(top_query)

        if semrush_positions_data is not None and not getattr(semrush_positions_data, "empty", True):
            for item in build_semrush_opportunity_cards(semrush_positions_data)[:5]:
                keyword = str(item.get("keyword", "")).strip()
                if keyword and keyword not in keywords:
                    keywords.append(keyword)

        for item in insight.get("query_analysis", [])[:5]:
            query = str(item.get("query", "")).strip()
            if query and query not in keywords:
                keywords.append(query)

        keywords = keywords[:5]
        focus_keyword = keywords[0] if keywords else "priority keyword"
        page_label = primary_page if primary_page and primary_page != "Not available" else "priority landing page"

        faq_ideas = []
        if keywords:
            faq_ideas = [f"Answer the search intent behind '{keyword}' directly on the page." for keyword in keywords[:3]]
        else:
            faq_ideas = [
                "Add one FAQ that addresses the core patient question behind the target search.",
                "Add one FAQ that handles cost, fit, or treatment expectations.",
                "Add one FAQ that moves the visitor toward booking or contacting the clinic.",
            ]

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
            "faq_ideas": faq_ideas,
        }

    if category.startswith("social_") or any(term in combined_text for term in social_terms):
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
            topic = humanize_social_topic(str(row.get("Topic", "general")).strip())
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
                f"Top topic signal: {', '.join(humanize_social_topic(topic) for topic in top_topics[:2])}."
            )

        base_topic = humanize_social_topic(top_topics[0]) if top_topics else "the strongest current topic"
        format_label = best_post_type if best_post_type and best_post_type != "Not available" else "your best-performing format"
        base_hook = ""
        if top_examples_rows:
            base_hook = str(top_examples_rows[0].get("Hook", "")).strip()

        variations = [
            f"{format_label} variation focused on {base_topic} with a stronger booking-oriented CTA.",
            f"{format_label} variation that reuses the winning structure but tests a shorter first-line hook.",
            f"{format_label} variation that turns the current high-interest topic into a clearer follow-driving post.",
        ]
        if base_hook:
            variations[1] = f"{format_label} variation using a hook inspired by '{base_hook}' with a tighter patient outcome angle."

        return {
            "type": "social",
            "button_label": "View follow-driving posts & generate variations",
            "headline": "Social Take Action",
            "top_examples": top_examples or ["No high-performing examples were available from the current run."],
            "why_they_worked": why_they_worked or ["Not enough social performance context is loaded yet."],
            "variations": variations[:5],
        }

    return None


def render_take_action_block(payload: dict, unique_key: str) -> None:
    """Render a take-action drill-down block beneath a recommendation."""
    st.markdown('<div class="take-action-panel">', unsafe_allow_html=True)
    icon = "↗" if payload.get("type") == "seo" else "✦"
    st.markdown(
        f'''
        <div class="take-action-header">
            <div class="take-action-icon">{icon}</div>
            <div class="take-action-title">{payload.get("headline", "Take Action")}</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    if payload.get("type") == "seo":
        keywords = payload.get("keywords", [])
        if keywords:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Best Keywords</div>', unsafe_allow_html=True)
            keyword_items = "".join(f"<li>{keyword}</li>" for keyword in keywords)
            st.markdown(f'<ul class="take-action-list">{keyword_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        rewrites = payload.get("rewrites", {})
        if rewrites:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Rewrite Examples</div>', unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="take-action-code">
                    <strong>Title Tag:</strong><br>
                    {rewrites.get('title_tag', '')}
                    <br><br>
                    <strong>H1:</strong><br>
                    {rewrites.get('h1', '')}
                    <br><br>
                    <strong>Meta Description:</strong><br>
                    {rewrites.get('meta_description', '')}
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        faq_ideas = payload.get("faq_ideas", [])
        if faq_ideas:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">FAQ Ideas</div>', unsafe_allow_html=True)
            faq_items = "".join(f"<li>{item}</li>" for item in faq_ideas)
            st.markdown(f'<ul class="take-action-list">{faq_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    elif payload.get("type") == "social":
        top_examples = payload.get("top_examples", [])
        if top_examples:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Top Examples</div>', unsafe_allow_html=True)
            example_items = "".join(f"<li>{example}</li>" for example in top_examples)
            st.markdown(f'<ul class="take-action-list">{example_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        why_they_worked = payload.get("why_they_worked", [])
        if why_they_worked:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Why They Worked</div>', unsafe_allow_html=True)
            why_items = "".join(f"<li>{item}</li>" for item in why_they_worked)
            st.markdown(f'<ul class="take-action-list">{why_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        variations = payload.get("variations", [])
        if variations:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">New Variations</div>', unsafe_allow_html=True)
            variation_items = "".join(f"<li>{variation}</li>" for variation in variations)
            st.markdown(f'<ul class="take-action-list">{variation_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No drill-down action plan is available for this recommendation yet.")

    st.markdown("</div>", unsafe_allow_html=True)


def render_recommendation_take_action(card: dict, results: dict, unique_key: str) -> None:
    """Render a Take Action control and drill-down block when supported."""
    payload = build_take_action_payload(card, results)
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


def render_recommendations_page(results: dict) -> None:
    """Render the Recommendations page."""
    st.title("Recommendations")
    st.caption("Combined website + social action plan")

    if not results:
        st.info("Run the workflow first on the Data Sources page.")
        return

    strategy = results["strategy"]["strategy"]
    social_cards = build_social_recommendation_cards(results)
    what_next_cards = build_combined_what_next_cards(results)
    priority_class_map = {
        "High": "priority-high-pill",
        "Medium": "priority-medium-pill",
        "Low": "priority-low-pill",
    }
    priority_cycle = ["High", "Medium", "Low"]
    action_index = 0

    st.subheader("Website Recommendations")
    for category, recommendations in strategy["recommendations"].items():
        for index, recommendation in enumerate(recommendations):
            priority = priority_cycle[action_index % len(priority_cycle)]
            pill_class = priority_class_map[priority]
            recommendation_card = {
                "category": category,
                "issue": "",
                "recommendation": "",
                "why_it_matters": "",
                "priority": priority,
            }

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
                recommendation_card.update(
                    {
                        "issue": issue,
                        "recommendation": rec_text,
                        "why_it_matters": why,
                        "priority": display_priority,
                    }
                )
            else:
                body_html = str(recommendation)
                display_priority = priority
                recommendation_card.update(
                    {
                        "recommendation": str(recommendation),
                        "priority": display_priority,
                    }
                )

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
            render_recommendation_take_action(
                recommendation_card,
                results,
                f"website_{str(category).strip().lower()}_{index}",
            )
            action_index += 1

    st.subheader("Social Recommendations")
    if social_cards:
        for index, card in enumerate(social_cards):
            display_priority = str(card.get("priority", "Medium")).strip().title()
            pill_class = priority_class_map.get(display_priority, "priority-medium-pill")
            body_parts = []
            if card.get("issue"):
                body_parts.append(f"<strong>Issue:</strong> {card['issue']}")
            if card.get("recommendation"):
                body_parts.append(f"<strong>Recommendation:</strong> {card['recommendation']}")
            if card.get("why_it_matters"):
                body_parts.append(f"<strong>Why it matters:</strong> {card['why_it_matters']}")
            body_html = "<br><br>".join(body_parts) if body_parts else "No recommendation details available."

            st.markdown(
                f"""
                <div class="recommendation-card">
                    <div class="recommendation-card-top">
                        <div class="recommendation-category">{format_heading(str(card.get("category", "social")))}</div>
                        <div class="{pill_class}">{display_priority} Priority</div>
                    </div>
                    <div class="recommendation-body">
                        {body_html}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            render_recommendation_take_action(
                card,
                results,
                f"social_{str(card.get('category', 'social')).strip().lower()}_{index}",
            )
    else:
        st.info("No social recommendations available yet. Upload a Meta content export and run the workflow.")

    st.subheader("Priority Action Queue")
    render_priority_action_queue(results, priority_class_map)

    st.markdown("### 🚀 What To Do Next")
    if what_next_cards:
        for action in what_next_cards:
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
        st.info("No next-step recommendations available yet.")

    render_suggested_changes_section(results)


def render_reports_page(results: dict) -> None:
    """Render the Reports page."""
    st.title("Reports")
    st.caption("Export and client-ready report views")

    if not results:
        st.info("Run the workflow first on the Data Sources page.")
        return

    render_client_report(results)
    st.markdown("---")
    render_export_section(results)


def render_ai_chat_page(results: dict | None) -> None:
    """Render the dedicated Chat with AI Agent page."""
    if "ai_chat_messages" not in st.session_state:
        st.session_state["ai_chat_messages"] = [
            {
                "role": "assistant",
                "content": (
                    "I’m your AI Marketing Strategist. Ask about your SEO, website performance, "
                    "social content, opportunities, or recommendations."
                ),
            }
        ]

    st.title("Chat with AI Agent")
    st.caption("Ask your AI Marketing Strategist about your loaded website, SEO, and social data.")
    st.write("Choose a suggested prompt or type your own question.")

    suggested_prompts = [
        "What are my biggest SEO opportunities?",
        "Which queries have high impressions but low CTR?",
        "What pages should I update first?",
        "What content topics could drive more traffic?",
        "What are the biggest issues in my social content?",
        "Summarize the top recommendations from this dataset.",
        "Which queries should I prioritize for quick wins?",
        "Compare website insights vs social insights.",
    ]

    def submit_chat_message(prompt_text: str) -> None:
        prompt = str(prompt_text).strip()
        if not prompt:
            return

        st.session_state["ai_chat_messages"].append({"role": "user", "content": prompt})
        assistant_response = generate_ai_chat_response(prompt, results)
        st.session_state["ai_chat_messages"].append({"role": "assistant", "content": assistant_response})

    prompt_columns = st.columns(2)
    for index, prompt in enumerate(suggested_prompts):
        with prompt_columns[index % 2]:
            if st.button(prompt, key=f"chat_page_prompt_chip_{index}"):
                submit_chat_message(prompt)

    if not results:
        st.info("Load a saved run or upload data first, then ask the AI agent about your marketing performance.")

    for message in st.session_state["ai_chat_messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_prompt = st.chat_input("Ask about your marketing data...")
    if user_prompt:
        submit_chat_message(user_prompt)
        st.rerun()


def build_ai_insight_feed(results: dict | None) -> list[dict[str, str]]:
    """Build a short list of AI insight cards for the shared rail."""
    if not results:
        return [
            {
                "title": "No Data Loaded",
                "message": "Load a saved run or upload data to activate AI insights.",
                "level": "info",
            }
        ]

    cards = []
    insight = results.get("insight", {})
    social_insights = results.get("social_insights", {})
    semrush_positions_data = results.get("semrush_positions_data")
    semrush_pages_data = results.get("semrush_pages_data")

    high_ctr_gap = insight.get("high_impression_low_click", [])
    if high_ctr_gap:
        top_item = high_ctr_gap[0]
        cards.append(
            {
                "title": "Low CTR Detected",
                "message": (
                    f"{top_item.get('query', 'A top query')} is getting visibility but not enough clicks, which suggests a stronger SERP message or page alignment is needed."
                ),
                "level": "warning",
            }
        )

    if semrush_positions_data is not None and not getattr(semrush_positions_data, "empty", True):
        keyword_cards = build_semrush_opportunity_cards(semrush_positions_data)
        if keyword_cards:
            cards.append(
                {
                    "title": "Ranking Opportunity",
                    "message": (
                        f"{keyword_cards[0].get('keyword', 'A tracked keyword')} is within striking distance and can likely move with focused optimization."
                    ),
                    "level": "info",
                }
            )
    elif semrush_pages_data is not None and not getattr(semrush_pages_data, "empty", True):
        page_cards = build_semrush_page_cards(semrush_pages_data)
        if page_cards:
            cards.append(
                {
                    "title": "Ranking Opportunity",
                    "message": (
                        f"{page_cards[0].get('page_url', 'A tracked page')} already has visibility and looks like a strong optimization candidate."
                    ),
                    "level": "info",
                }
            )

    if insight.get("patterns"):
        cards.append(
            {
                "title": "Growth Insight",
                "message": str(insight["patterns"][0]),
                "level": "success",
            }
        )

    best_post_type = social_insights.get("best_post_type", "Not available")
    if best_post_type and best_post_type != "Not available":
        cards.append(
            {
                "title": "Social Format Winner",
                "message": f"{best_post_type} is currently the strongest social format in the loaded run.",
                "level": "success",
            }
        )

    balance_problems = social_insights.get("balance_problems", [])
    if balance_problems:
        cards.append(
            {
                "title": "Content Gap Identified",
                "message": str(balance_problems[0]),
                "level": "warning",
            }
        )
    elif social_insights.get("what_drives_follows") and social_insights.get("what_drives_follows") != "Not available":
        cards.append(
            {
                "title": "Social Performance Signal",
                "message": str(social_insights.get("what_drives_follows", "")),
                "level": "info",
            }
        )
    elif social_insights.get("what_drives_saves") and social_insights.get("what_drives_saves") != "Not available":
        cards.append(
            {
                "title": "Social Performance Signal",
                "message": str(social_insights.get("what_drives_saves", "")),
                "level": "info",
            }
        )

    return cards[:5] if cards else [
        {
            "title": "No Data Loaded",
            "message": "Load a saved run or upload data to activate AI insights.",
            "level": "info",
        }
    ]


def render_ai_right_rail(results: dict | None) -> None:
    """Render the shared AI rail used across app pages."""
    insight_cards = build_ai_insight_feed(results)

    st.markdown('<div class="ai-rail-panel">', unsafe_allow_html=True)
    st.markdown('<div class="ai-rail-title">AI Insights Feed</div>', unsafe_allow_html=True)
    for card in insight_cards:
        level_class = {
            "warning": "ai-insight-warning",
            "success": "ai-insight-success",
            "info": "ai-insight-info",
        }.get(card.get("level", "info"), "ai-insight-info")

        st.markdown(
            f"""
            <div class="ai-insight-card {level_class}">
                <div class="ai-insight-title">{card.get("title", "Insight")}</div>
                <div class="ai-insight-text">{card.get("message", "")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="ai-rail-title">Generate Strategy</div>', unsafe_allow_html=True)
    st.markdown('<div class="ai-strategy-button-wrap">', unsafe_allow_html=True)
    if st.button("Generate Strategy", key="ai_rail_generate_strategy"):
        if results:
            st.session_state["ai_strategy_summary"] = generate_ai_chat_response("What should I optimize first?", results)
        else:
            st.session_state["ai_strategy_summary"] = (
                "INSIGHT\nNo data is loaded yet.\n\nWHY IT MATTERS\nThe strategist summary depends on a loaded run.\n\nRECOMMENDATION\nLoad a saved run or upload data first.\n\nNEXT ACTION\nGo to Data Sources and load or run your marketing data."
            )
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.get("ai_strategy_summary"):
        st.markdown(
            f'<div class="ai-chat-response">{st.session_state["ai_strategy_summary"]}</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="ai-rail-title">Chat with AI Agent</div>', unsafe_allow_html=True)
    st.caption("Choose a suggested prompt or type your own question.")

    suggested_prompts = [
        "What are my biggest SEO opportunities?",
        "Which queries have high impressions but low CTR?",
        "What pages should I update first?",
        "What content topics could drive more traffic?",
        "What are the biggest issues in my social content?",
        "Summarize the top recommendations from this dataset.",
        "Which queries should I prioritize for quick wins?",
        "Compare website insights vs social insights.",
    ]

    prompt_columns = st.columns(2)
    for index, prompt in enumerate(suggested_prompts):
        with prompt_columns[index % 2]:
            if st.button(prompt, key=f"ai_prompt_chip_{index}"):
                st.session_state["ai_sidebar_prompt_input"] = prompt

    st.markdown('<div class="ai-chat-box">', unsafe_allow_html=True)
    sidebar_prompt = st.text_area(
        "Ask about your data",
        key="ai_sidebar_prompt_input",
        height=100,
        label_visibility="visible",
    )
    st.markdown("</div>", unsafe_allow_html=True)
    if st.button("Send", key="ai_sidebar_send_button"):
        st.session_state["ai_sidebar_last_prompt"] = sidebar_prompt
        st.session_state["ai_sidebar_last_response"] = generate_ai_chat_response(sidebar_prompt, results)

    if st.session_state.get("ai_sidebar_last_response"):
        st.markdown(
            f'<div class="ai-chat-response">{st.session_state["ai_sidebar_last_response"]}</div>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def render_dashboard_page(results: dict | None, ga4_debug_titles: list[str], show_debug: bool) -> None:
    """Render the dashboard page inside the shared shell."""
    if results:
        render_standard_view(results, ga4_debug_titles, show_debug)
    else:
        st.title("Marketing Intelligence Dashboard")
        st.caption("Overview of your marketing performance and opportunities")
        st.info("Run the workflow first on the Data Sources page.")


def render_with_ai_rail(page_renderer, results=None, *args) -> None:
    """Render a page inside the shared main-content plus AI-rail shell."""
    main_col, rail_col = st.columns([4.2, 1])

    with main_col:
        page_renderer(*args)

    with rail_col:
        render_ai_right_rail(results)


# Sidebar Navigation
with st.sidebar:
    st.markdown("## AI Marketing")
    st.caption("Workflow System")

    page = st.radio(
        "Navigation",
        [
            "Data Sources",
            "Dashboard",
            "Analysis",
            "Social Analysis",
            "Opportunities",
            "Recommendations",
            "Reports",
            "Chat with AI Agent",
        ],
    )

    show_debug = st.checkbox("Show debug data", value=False)


results = None
ga4_debug_titles: list[str] = []

if page == "Data Sources":
    current_results = st.session_state.get("results")
    uploaded = render_data_sources()

    if uploaded["load_saved_run_button"] and uploaded["selected_saved_run_id"]:
        loaded_run = load_saved_run(uploaded["selected_saved_run_id"])
        if loaded_run is not None:
            st.session_state["results"] = loaded_run["results"]
            st.session_state["ga4_debug_titles"] = loaded_run["ga4_debug_titles"]
            st.session_state["loaded_run_id"] = loaded_run["run_id"]
            current_results = loaded_run["results"]
            st.success(f"Loaded saved run: {loaded_run['run_id']}")
        else:
            st.error("Could not load the selected saved run.")

    if uploaded["run_button"]:
        uploaded_files = [
            uploaded["ga4_pages_file"],
            uploaded["ga4_source_file"],
            uploaded["gsc_queries_file"],
            uploaded["semrush_positions_file"],
            uploaded["semrush_pages_file"],
            uploaded["semrush_topics_file"],
            uploaded["meta_posts_file"],
        ]

        if not has_uploaded_data(uploaded_files):
            st.error("Please upload at least one file before running the workflow.")
            st.stop()

        ga4_pages_data = parse_uploaded_csv(uploaded["ga4_pages_file"], "GA4_PAGES") if uploaded["ga4_pages_file"] else None
        ga4_source_data = parse_uploaded_csv(uploaded["ga4_source_file"], "GA4_SOURCE") if uploaded["ga4_source_file"] else None
        gsc_queries_data = parse_uploaded_csv(uploaded["gsc_queries_file"], "GSC_QUERIES") if uploaded["gsc_queries_file"] else None
        semrush_positions_data = parse_semrush_positions_csv(uploaded["semrush_positions_file"]) if uploaded["semrush_positions_file"] else None
        semrush_pages_data = parse_semrush_pages_csv(uploaded["semrush_pages_file"]) if uploaded["semrush_pages_file"] else None
        semrush_topics_data = parse_semrush_topics_csv(uploaded["semrush_topics_file"]) if uploaded["semrush_topics_file"] else None
        meta_posts_data = parse_meta_posts_csv(uploaded["meta_posts_file"]) if uploaded["meta_posts_file"] else None

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

        results["meta_posts_data"] = meta_posts_data
        results["social_insights"] = build_social_insights(meta_posts_data)
        run_id = save_run_files(
            uploaded["ga4_pages_file"],
            uploaded["ga4_source_file"],
            uploaded["gsc_queries_file"],
            uploaded["semrush_positions_file"],
            uploaded["semrush_pages_file"],
            uploaded["semrush_topics_file"],
            uploaded["meta_posts_file"],
        )

        st.session_state["results"] = results
        st.session_state["ga4_debug_titles"] = ga4_debug_titles
        st.session_state["loaded_run_id"] = run_id
        current_results = results

        st.success("Workflow complete. Results were saved and can now be loaded from Saved Runs.")

elif page == "Dashboard":
    results = st.session_state.get("results")
    ga4_debug_titles = st.session_state.get("ga4_debug_titles", [])
    render_dashboard_page(results, ga4_debug_titles, show_debug)

elif page == "Analysis":
    results = st.session_state.get("results")
    render_analysis_page(results)

elif page == "Social Analysis":
    results = st.session_state.get("results")
    render_social_analysis_page(results)

elif page == "Opportunities":
    results = st.session_state.get("results")
    render_opportunities_page(results)

elif page == "Recommendations":
    results = st.session_state.get("results")
    render_recommendations_page(results)

elif page == "Reports":
    results = st.session_state.get("results")
    render_reports_page(results)

elif page == "Chat with AI Agent":
    results = st.session_state.get("results")
    render_ai_chat_page(results)
