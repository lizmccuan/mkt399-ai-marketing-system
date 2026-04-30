"""Simple Streamlit interface for the AI Marketing Workflow System."""

from __future__ import annotations

import json
import re
import textwrap
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from components.take_action import render_recommendation_take_action as render_recommendation_take_action_component
from main import run_workflow
from services.rule_engine import evaluate_decision_rules, load_decision_rules as load_decision_rules_service
from utils.parser import parse_csv_file, parse_uploaded_csv


BASE_DIR = Path(__file__).resolve().parent
DISTILLED_DIR = BASE_DIR / "reference_docs" / "distilled"
RUNS_DIR = Path("saved_runs")
RUNS_DIR.mkdir(exist_ok=True)


def load_decision_rules() -> dict:
    path = DISTILLED_DIR / "decision_rules.json"
    if not path.exists():
        return {"version": "1.0", "rules": []}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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
        --border-strong: #D8DEEA;
        --accent-purple: #7C3AED;
        --accent-purple-soft: #F3EDFF;
        --accent-purple-border: #E4D7FF;
        --panel-shadow: 0 10px 30px rgba(16, 24, 40, 0.06);
        --panel-shadow-soft: 0 4px 16px rgba(16, 24, 40, 0.04);
        --panel-shadow-hover: 0 16px 40px rgba(16, 24, 40, 0.09);
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
    body {
        font-feature-settings: "ss01" on, "cv01" on;
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
        padding-top: 2.8rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-main);
    }
    h1 {
        font-size: 2.35rem !important;
        line-height: 1.08 !important;
        letter-spacing: -0.03em;
        font-weight: 800 !important;
        margin-bottom: 0.4rem !important;
    }
    h2 {
        font-size: 1.55rem !important;
        line-height: 1.15 !important;
        letter-spacing: -0.02em;
        font-weight: 750 !important;
        margin-top: 0.15rem !important;
    }
    h3 {
        font-size: 1.2rem !important;
        line-height: 1.25 !important;
        font-weight: 700 !important;
    }
    p, label, span {
        color: inherit;
    }
    [data-testid="stHeader"] {
        background: rgba(247, 248, 252, 0.92);
        border-bottom: 1px solid rgba(230, 232, 240, 0.75);
        height: 0 !important;
        min-height: 0 !important;
    }
    [data-testid="stSidebar"] {
        background: var(--panel-bg);
        border-right: 1px solid var(--border-soft);
        box-shadow: 10px 0 30px rgba(16, 24, 40, 0.03);
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
        padding-top: 1.4rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label {
        border-radius: 16px;
        padding: 0.72rem 0.8rem;
        margin-bottom: 0.38rem;
        border: 1px solid #EFF2F7;
        transition: all 0.2s ease;
        background: #FCFCFD;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
        background: var(--accent-purple-soft);
        color: var(--accent-purple);
        border: 1px solid rgba(124, 58, 237, 0.22);
        box-shadow: inset 0 0 0 1px rgba(124, 58, 237, 0.03), 0 6px 16px rgba(124, 58, 237, 0.08);
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) * {
        color: var(--accent-purple);
        font-weight: 600;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: #FFFFFF;
        border-color: var(--border-strong);
        box-shadow: 0 4px 14px rgba(16, 24, 40, 0.04);
    }
    .stButton > button,
    [data-testid="baseButton-secondary"] {
        border-radius: 14px;
        border: 1px solid var(--border-soft);
        background: var(--panel-bg);
        color: var(--text-main);
        font-weight: 650;
        min-height: 2.85rem;
        padding: 0.55rem 1rem;
        box-shadow: 0 3px 10px rgba(16, 24, 40, 0.04);
        transition: all 0.18s ease;
    }
    .stButton > button[kind="primary"] {
        background: #8C52FF;
        color: #ffffff;
        border: 1px solid #8C52FF;
        box-shadow: 0 10px 24px rgba(124, 58, 237, 0.18);
    }
    .stButton > button:hover {
        border-color: #D0D5DD;
        background: #F9FAFB;
        color: var(--text-main);
        transform: translateY(-1px);
        box-shadow: 0 10px 22px rgba(16, 24, 40, 0.06);
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
        border-radius: 22px;
        padding: 1.1rem 1.15rem;
        box-shadow: var(--panel-shadow);
        min-height: 132px;
        position: relative;
        overflow: hidden;
    }
    .stMetric::before {
        content: "";
        position: absolute;
        inset: 0 auto auto 0;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, rgba(124, 58, 237, 0.95), rgba(192, 132, 252, 0.45));
    }
    .stDataFrame, .stTable {
        background: #FFFFFF;
        border-radius: 18px;
        border: 1px solid var(--border-soft);
        box-shadow: var(--panel-shadow-soft);
    }
    .dashboard-title {
        font-size: 2.55rem;
        font-weight: 800;
        color: #162033;
        margin-bottom: 0.45rem;
        letter-spacing: -0.035em;
        line-height: 1.08;
    }
    .dashboard-subtitle {
        color: #667085;
        margin-bottom: 2rem;
        font-size: 1.01rem;
        line-height: 1.65;
        max-width: 760px;
    }
    .panel {
        background: var(--panel-bg);
        border: 1px solid var(--border-soft);
        border-radius: 22px;
        padding: 1.35rem 1.45rem;
        margin-bottom: 1.2rem;
        box-shadow: var(--panel-shadow);
    }
    .panel-title {
        font-size: 1.08rem;
        font-weight: 750;
        color: #162033;
        margin-bottom: 1rem;
        line-height: 1.35;
        letter-spacing: -0.01em;
    }
    .panel:empty,
    .change-card:empty,
    .mock-block:empty,
    .recommendation-card:empty,
    .what-next-card:empty,
    .ai-rail-panel:empty,
    .take-action-panel:empty,
    .chat-message-wrap:empty,
    .chat-message-card:empty,
    .ai-chat-response:empty {
        display: none !important;
        padding: 0 !important;
        margin: 0 !important;
        border: 0 !important;
        min-height: 0 !important;
        height: 0 !important;
        box-shadow: none !important;
        overflow: hidden !important;
    }
    .change-card {
        background: var(--panel-bg);
        border: 1px solid var(--border-soft);
        border-radius: 20px;
        padding: 1.25rem 1.3rem;
        margin-bottom: 1.05rem;
        box-shadow: var(--panel-shadow);
    }
    .change-card-title {
        font-size: 1.02rem;
        font-weight: 760;
        color: #162033;
        margin-bottom: 0.85rem;
        letter-spacing: -0.01em;
    }
    .change-card-body {
        color: #52607A;
        font-size: 0.95rem;
        line-height: 1.7;
    }
    .change-card-body strong {
        color: #162033;
    }
    .change-comparison-heading {
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: #667085;
        margin-bottom: 0.45rem;
    }
    .mock-block {
        background: #FBFCFE;
        border: 1px solid #E7EBF3;
        border-radius: 18px;
        padding: 1rem 1.05rem;
        margin-top: 0.65rem;
        color: var(--text-muted);
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.55);
    }
    .recommendation-card {
        background: var(--panel-bg);
        border: 1px solid var(--border-soft);
        border-radius: 22px;
        padding: 1.3rem 1.35rem;
        margin-bottom: 1rem;
        box-shadow: var(--panel-shadow);
    }
    .recommendation-card-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.9rem;
        margin-bottom: 1rem;
        flex-wrap: wrap;
    }
    .recommendation-category {
        font-size: 0.98rem;
        font-weight: 750;
        color: #162033;
        letter-spacing: -0.01em;
        line-height: 1.35;
    }
    .recommendation-body {
        color: #52607A;
        font-size: 0.96rem;
        line-height: 1.7;
    }
    .recommendation-body strong {
        color: #162033;
    }
    .priority-high-pill {
        display: inline-block;
        background: linear-gradient(180deg, #FFF1F2 0%, #FFE4E8 100%);
        color: #B42318;
        border: 1px solid #F5B7C0;
        border-radius: 999px;
        padding: 0.36rem 0.78rem;
        font-size: 0.75rem;
        font-weight: 700;
        white-space: nowrap;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.65);
    }
    .priority-medium-pill {
        display: inline-block;
        background: linear-gradient(180deg, #FFF7ED 0%, #FFEEDC 100%);
        color: #B54708;
        border: 1px solid #F6CFA7;
        border-radius: 999px;
        padding: 0.36rem 0.78rem;
        font-size: 0.75rem;
        font-weight: 700;
        white-space: nowrap;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.65);
    }
    .priority-low-pill {
        display: inline-block;
        background: linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 100%);
        color: #475467;
        border: 1px solid #E4E7EC;
        border-radius: 999px;
        padding: 0.36rem 0.78rem;
        font-size: 0.75rem;
        font-weight: 700;
        white-space: nowrap;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.65);
    }
    .topic-tag-row {
        display: flex;
        gap: 0.55rem;
        flex-wrap: wrap;
        margin: 0.55rem 0 0.9rem;
    }
    .topic-tag {
        display: inline-block;
        background: var(--accent-purple-soft);
        color: #5B45C6;
        border: 1px solid var(--accent-purple-border);
        border-radius: 999px;
        padding: 0.34rem 0.72rem;
        font-size: 0.76rem;
        font-weight: 650;
        white-space: nowrap;
    }
    .what-next-card {
        background: var(--panel-bg);
        border: 1px solid var(--border-soft);
        border-radius: 22px;
        padding: 1.25rem 1.3rem;
        margin-bottom: 1rem;
        box-shadow: var(--panel-shadow);
    }
    .what-next-title {
        font-size: 1.08rem;
        font-weight: 750;
        color: #162033;
        margin-bottom: 0.62rem;
        line-height: 1.35;
    }
    .what-next-label {
        font-weight: 750;
        color: #162033;
    }
    .stPlotlyChart {
        background: #FFFFFF;
        border: 1px solid var(--border-soft);
        border-radius: 20px;
        padding: 0.55rem 0.65rem 0.2rem;
        box-shadow: var(--panel-shadow-soft);
        margin-bottom: 0.55rem;
    }
    .stPlotlyChart > div {
        border-radius: 16px;
    }
    .dashboard-card-marker {
        display: none !important;
    }
    [data-testid="stVerticalBlock"]:has(.dashboard-card-marker) {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 18px;
        padding: 22px;
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
        height: 100%;
    }
    .dashboard-card-helper {
        color: var(--text-muted);
        font-size: 0.92rem;
        line-height: 1.55;
        margin-top: -0.2rem;
        margin-bottom: 0.8rem;
    }
    .dashboard-section-divider {
        height: 1px;
        background: #E5E7EB;
        margin: 0.35rem 0 1.2rem;
        border-radius: 999px;
    }
    .insight-divider {
        height: 1px;
        background: #E9EDF5;
        margin: 0.85rem 0;
        border-radius: 999px;
    }
    [data-testid="column"] > [data-testid="stVerticalBlock"] {
        gap: 1rem;
    }
    [data-testid="stMetric"] + [data-testid="stMetric"] {
        margin-top: 0.15rem;
    }
    [data-testid="stVerticalBlock"] > [data-testid="element-container"]:has(.dashboard-title) {
        margin-bottom: 0.2rem;
    }
    [data-testid="stVerticalBlock"] > [data-testid="element-container"]:has(.dashboard-subtitle) {
        margin-bottom: 0.9rem;
    }
    .ai-rail-panel {
        background: var(--panel-bg);
        border: 1px solid var(--border-soft);
        border-radius: 22px;
        padding: 18px;
        height: fit-content;
        position: sticky;
        top: 20px;
        box-shadow: var(--panel-shadow);
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
        border-radius: 18px;
        padding: 0.95rem 1rem;
        margin-bottom: 0.78rem;
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
        border-radius: 22px;
        box-shadow: var(--panel-shadow);
        padding: 1.28rem 1.4rem;
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
    .chat-message-wrap {
        margin: 0.65rem 0 1rem;
    }
    .chat-message-card {
        border-radius: 20px;
        padding: 1.08rem 1.15rem;
        box-shadow: var(--panel-shadow-soft);
        line-height: 1.65;
        max-width: 880px;
    }
    .chat-message-user {
        background: #F8FAFC;
        border: 1px solid #DCE3EE;
    }
    .chat-message-assistant {
        background: #FFFFFF;
        border: 1px solid #E6E8F0;
    }
    .chat-message-label {
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: #667085;
        margin-bottom: 0.5rem;
    }
    .chat-message-body {
        color: #162033;
        font-size: 0.95rem;
        line-height: 1.7;
    }
    .chat-response-section {
        margin-bottom: 0.95rem;
    }
    .chat-response-section:last-child {
        margin-bottom: 0;
    }
    .chat-response-title {
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: #667085;
        margin-bottom: 0.32rem;
    }
    .chat-response-text {
        color: #162033;
        line-height: 1.72;
    }
    .chat-response-text ul {
        margin: 0.2rem 0 0;
        padding-left: 1.15rem;
    }
    .chat-response-text li {
        margin-bottom: 0.36rem;
        color: #162033;
    }
    .chat-response-next {
        background: #F3EDFF;
        border: 1px solid #E5DAFF;
        border-radius: 14px;
        padding: 0.9rem 1rem;
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
        font-size: 1.48rem !important;
        line-height: 1.18 !important;
        white-space: normal !important;
        overflow-wrap: anywhere !important;
        word-break: break-word !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em !important;
    }
    [data-testid="stMetricLabel"] {
        color: #6b7280 !important;
        font-size: 0.82rem !important;
        line-height: 1.35 !important;
        white-space: normal !important;
        text-transform: uppercase;
        letter-spacing: 0.05em !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricValue"] > div,
    [data-testid="stMetricLabel"] > div {
        width: 100%;
        white-space: normal !important;
        overflow-wrap: anywhere !important;
        word-break: break-word !important;
    }
    /* TABLE FIX */
    [data-testid="stDataFrame"] {
        background: white !important;
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid var(--border-soft);
        box-shadow: var(--panel-shadow-soft);
    }
    [data-testid="stDataFrame"] * {
        color: #111827 !important;
    }
    thead tr th {
        background: #F8FAFC !important;
        color: #374151 !important;
        font-weight: 700 !important;
        border-bottom: 1px solid #E9EDF5 !important;
    }
    tbody tr {
        background: white !important;
    }
    tbody tr:nth-child(even) {
        background: #FCFCFD !important;
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


def make_json_safe(obj):
    import pandas as pd
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")
    if isinstance(obj, pd.Series):
        return obj.to_dict()
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_safe(v) for v in obj]
    return obj


def clamp_score(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    """Clamp a score into a 0-100 range."""
    return max(minimum, min(maximum, value))


def normalize_rule_ctr_value(value) -> float | None:
    """Normalize CTR into decimal form for rule scoring."""
    numeric_value = to_comparison_number(value)
    if numeric_value is None:
        return None
    return numeric_value / 100 if numeric_value > 1 else numeric_value


def calculate_rule_scores(rule: dict, sample_data: dict) -> dict[str, float]:
    """Score a triggered rule using strategic upside signals."""
    impressions = to_comparison_number(sample_data.get("impressions")) or 0
    ctr_decimal = normalize_rule_ctr_value(sample_data.get("ctr"))
    position = to_comparison_number(sample_data.get("position"))
    engagement_rate = to_comparison_number(sample_data.get("engagement_rate"))
    sessions = to_comparison_number(sample_data.get("sessions")) or 0
    conversions = to_comparison_number(sample_data.get("conversions")) or 0

    target_ctr_decimal = 0.05
    ctr_gap = max(0.0, target_ctr_decimal - ctr_decimal) if ctr_decimal is not None else 0.0

    impressions_score = clamp_score((impressions / 2000) * 100)
    ctr_gap_score = clamp_score((ctr_gap / target_ctr_decimal) * 100) if ctr_gap else 0.0
    if position is None:
        ranking_score = 35.0
    elif position <= 3:
        ranking_score = 95.0
    elif position <= 8:
        ranking_score = 82.0
    elif position <= 15:
        ranking_score = 72.0
    elif position <= 25:
        ranking_score = 55.0
    else:
        ranking_score = 35.0

    if engagement_rate is None:
        engagement_opportunity_score = 40.0
    else:
        engagement_opportunity_score = clamp_score(((0.65 - engagement_rate) / 0.65) * 100)

    session_score = clamp_score((sessions / 250) * 100)
    if sessions > 0:
        conversion_efficiency = conversions / sessions
        conversion_opportunity_score = clamp_score(((0.05 - conversion_efficiency) / 0.05) * 100)
    else:
        conversion_opportunity_score = 25.0

    available_inputs = [
        sample_data.get("impressions"),
        sample_data.get("ctr"),
        sample_data.get("position"),
        sample_data.get("engagement_rate"),
        sample_data.get("sessions"),
        sample_data.get("conversions"),
    ]
    data_completeness_score = (sum(value is not None for value in available_inputs) / len(available_inputs)) * 100
    matched_conditions = len(rule.get("conditions", {}).get("all", []))
    confidence_score = round(
        clamp_score((data_completeness_score * 0.65) + (min(matched_conditions, 3) / 3 * 35)),
        2,
    )

    opportunity_score = round(
        clamp_score(
            (impressions_score * 0.24)
            + (ctr_gap_score * 0.22)
            + (ranking_score * 0.18)
            + (engagement_opportunity_score * 0.14)
            + (session_score * 0.12)
            + (conversion_opportunity_score * 0.10)
        ),
        2,
    )

    business_impact_score = round(
        clamp_score(
            (impressions_score * 0.22)
            + (session_score * 0.26)
            + (conversion_opportunity_score * 0.22)
            + (ranking_score * 0.12)
            + (ctr_gap_score * 0.10)
            + (engagement_opportunity_score * 0.08)
        ),
        2,
    )

    return {
        "confidence_score": confidence_score,
        "opportunity_score": opportunity_score,
        "business_impact_score": business_impact_score,
    }


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


def normalize_ga4_page_title_dataframe(df: pd.DataFrame | None) -> pd.DataFrame | None:
    """Normalize GA4 Page Title columns needed for display."""
    if df is None:
        return None

    df = df.copy()
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    required_metric_defaults = {
        "sessions": None,
        "active_users": None,
        "engagement_rate": None,
        "conversions": 0,
    }
    backfilled_metrics: list[str] = []

    for column_name, default_value in required_metric_defaults.items():
        if column_name not in df.columns:
            df[column_name] = default_value
            backfilled_metrics.append(column_name)

    for numeric_column in required_metric_defaults:
        if numeric_column in df.columns:
            df[numeric_column] = pd.to_numeric(df[numeric_column], errors="coerce")

    df.attrs["backfilled_ga4_metrics"] = backfilled_metrics

    return df


def infer_saved_run_version(metadata: dict | None) -> str:
    """Infer a saved run version when explicit metadata is unavailable."""
    metadata = metadata or {}
    run_version = str(metadata.get("run_version", "")).strip()
    if run_version:
        return run_version

    if metadata.get("file_date_ranges") or metadata.get("date_range_label"):
        return "v2"
    if metadata.get("included_files"):
        return "v1"
    return "legacy"


def backfill_ga4_key_metrics(results: dict, ga4_pages_data: pd.DataFrame | None) -> None:
    """Backfill missing GA4 key metrics for older saved runs."""
    data_summary = results.setdefault("data_intake", {}).setdefault("summary", {})
    ga4_pages_summary = data_summary.setdefault("ga4_pages", {})
    key_metrics = ga4_pages_summary.setdefault("key_metrics", {})

    defaults = {
        "sessions": None,
        "active_users": None,
        "engagement_rate": None,
        "conversions": 0,
    }
    for metric_name, default_value in defaults.items():
        key_metrics.setdefault(metric_name, default_value)

    if ga4_pages_data is None or getattr(ga4_pages_data, "empty", True):
        return

    backfilled_metrics = set(ga4_pages_data.attrs.get("backfilled_ga4_metrics", []))

    if key_metrics.get("sessions") in [None, "", "Not available"] and "sessions" not in backfilled_metrics:
        key_metrics["sessions"] = to_comparison_number(ga4_pages_data["sessions"].fillna(0).sum())

    if key_metrics.get("active_users") in [None, "", "Not available"] and "active_users" not in backfilled_metrics:
        key_metrics["active_users"] = to_comparison_number(ga4_pages_data["active_users"].fillna(0).sum())

    if key_metrics.get("engagement_rate") in [None, "", "Not available"] and "engagement_rate" not in backfilled_metrics:
        engagement_rate = ga4_pages_data["engagement_rate"].dropna().mean()
        key_metrics["engagement_rate"] = None if pd.isna(engagement_rate) else engagement_rate

    if key_metrics.get("conversions") in [None, "", "Not available"] and "conversions" not in backfilled_metrics:
        key_metrics["conversions"] = to_comparison_number(ga4_pages_data["conversions"].fillna(0).sum()) or 0


def format_ga4_engagement_rate_kpi(value) -> str:
    """Format the GA4 engagement rate KPI as a percent."""
    numeric_value = to_comparison_number(value)
    if numeric_value is None:
        return "—"

    return f"{round(numeric_value * 100, 2)}%"


def calculate_analysis_engagement_rate_kpi() -> str:
    """Calculate Analysis-page engagement rate from GA4 Page Title rows."""
    ga4_pages_df = load_saved_ga4_pages_dataframe(st.session_state.get("loaded_run_id", ""))

    if ga4_pages_df.empty or "engagement_rate" not in ga4_pages_df.columns:
        return "Not available (requires GA4 Page Title data)"

    ga4_pages_df = ga4_pages_df.copy()
    ga4_pages_df.columns = [col.strip().lower().replace(" ", "_") for col in ga4_pages_df.columns]
    ga4_pages_df["engagement_rate"] = pd.to_numeric(ga4_pages_df["engagement_rate"], errors="coerce")
    engagement_rate = ga4_pages_df["engagement_rate"].dropna().mean()

    if pd.isna(engagement_rate):
        return "Not available (requires GA4 Page Title data)"

    return f"{round(engagement_rate * 100, 2)}%"


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


def format_saved_run_date_range(start_date: datetime, end_date: datetime) -> str:
    """Format a readable saved-run date range label."""
    if start_date.date() == end_date.date():
        return start_date.strftime("%b %d")

    if start_date.year == end_date.year and start_date.month == end_date.month:
        return f"{start_date.strftime('%b')} {start_date.day}\u2013{end_date.day}"

    if start_date.year == end_date.year:
        return f"{start_date.strftime('%b')} {start_date.day}\u2013{end_date.strftime('%b')} {end_date.day}"

    return (
        f"{start_date.strftime('%b')} {start_date.day}, {start_date.year}"
        f"\u2013{end_date.strftime('%b')} {end_date.day}, {end_date.year}"
    )


def parse_saved_run_date_token(token: str, fallback_year: int | None = None) -> datetime | None:
    """Parse a date token from uploaded file header text."""
    cleaned = str(token).strip().replace(".", "")
    if not cleaned:
        return None

    for date_format in ["%b %d, %Y", "%B %d, %Y", "%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d"]:
        try:
            return datetime.strptime(cleaned, date_format)
        except ValueError:
            continue

    if fallback_year is not None:
        for date_format in ["%b %d", "%B %d", "%m/%d"]:
            try:
                parsed = datetime.strptime(cleaned, date_format)
                return parsed.replace(year=fallback_year)
            except ValueError:
                continue

    return None


def extract_uploaded_file_date_range(file) -> dict[str, str] | None:
    """Extract a best-effort date range from the uploaded file header."""
    if file is None:
        return None

    text_data = file.getvalue().decode("utf-8-sig", errors="ignore")
    header_lines = [line.strip() for line in text_data.splitlines()[:15] if line.strip()]
    if not header_lines:
        return None

    shared_month_pattern = re.compile(
        r"(?P<month>Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|"
        r"Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+"
        r"(?P<day1>\d{1,2})\s*(?:-|–|to)\s*(?P<day2>\d{1,2})(?:,\s*(?P<year>\d{4}))?",
        re.IGNORECASE,
    )
    multi_month_pattern = re.compile(
        r"(?P<month1>Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|"
        r"Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+"
        r"(?P<day1>\d{1,2})(?:,\s*(?P<year1>\d{4}))?\s*(?:-|–|to)\s*"
        r"(?P<month2>Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|"
        r"Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+"
        r"(?P<day2>\d{1,2})(?:,\s*(?P<year2>\d{4}))?",
        re.IGNORECASE,
    )
    single_date_pattern = re.compile(
        r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|"
        r"Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:,\s*\d{4})?"
        r"|\d{1,2}/\d{1,2}/\d{2,4}"
        r"|\d{4}-\d{2}-\d{2}",
        re.IGNORECASE,
    )

    fallback_year = datetime.now().year

    for line in header_lines:
        multi_month_match = multi_month_pattern.search(line)
        if multi_month_match:
            year1 = int(multi_month_match.group("year1") or multi_month_match.group("year2") or fallback_year)
            year2 = int(multi_month_match.group("year2") or multi_month_match.group("year1") or fallback_year)
            start_date = parse_saved_run_date_token(
                f"{multi_month_match.group('month1')} {multi_month_match.group('day1')}",
                fallback_year=year1,
            )
            end_date = parse_saved_run_date_token(
                f"{multi_month_match.group('month2')} {multi_month_match.group('day2')}",
                fallback_year=year2,
            )
            if start_date and end_date:
                return {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "label": format_saved_run_date_range(start_date, end_date),
                }

        shared_month_match = shared_month_pattern.search(line)
        if shared_month_match:
            range_year = int(shared_month_match.group("year") or fallback_year)
            start_date = parse_saved_run_date_token(
                f"{shared_month_match.group('month')} {shared_month_match.group('day1')}",
                fallback_year=range_year,
            )
            end_date = parse_saved_run_date_token(
                f"{shared_month_match.group('month')} {shared_month_match.group('day2')}",
                fallback_year=range_year,
            )
            if start_date and end_date:
                return {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "label": format_saved_run_date_range(start_date, end_date),
                }

    parsed_dates: list[datetime] = []
    for line in header_lines:
        for match in single_date_pattern.finditer(line):
            parsed_date = parse_saved_run_date_token(match.group(0), fallback_year=fallback_year)
            if parsed_date:
                parsed_dates.append(parsed_date)

    if parsed_dates:
        start_date = min(parsed_dates)
        end_date = max(parsed_dates)
        return {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "label": format_saved_run_date_range(start_date, end_date),
        }

    return None


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
    file_date_ranges: dict[str, dict[str, str]] = {}
    collected_start_dates: list[datetime] = []
    collected_end_dates: list[datetime] = []

    for filename, uploaded_file in file_map.items():
        if uploaded_file is not None:
            save_uploaded_file(uploaded_file, run_dir / filename)
            included_files.append(filename)

            date_range = extract_uploaded_file_date_range(uploaded_file)
            if date_range:
                file_date_ranges[filename] = date_range
                try:
                    collected_start_dates.append(datetime.strptime(date_range["start_date"], "%Y-%m-%d"))
                    collected_end_dates.append(datetime.strptime(date_range["end_date"], "%Y-%m-%d"))
                except ValueError:
                    continue

    overall_date_range_label = ""
    if collected_start_dates and collected_end_dates:
        overall_date_range_label = format_saved_run_date_range(
            min(collected_start_dates),
            max(collected_end_dates),
        )

    metadata = {
        "run_id": run_id,
        "run_version": "v2",
        "display_label": run_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "included_files": included_files,
        "date_range_label": overall_date_range_label,
        "file_date_ranges": file_date_ranges,
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
                metadata = json.load(metadata_file)
                metadata["run_version"] = infer_saved_run_version(metadata)
                saved_runs.append(metadata)
        except (json.JSONDecodeError, OSError):
            continue

    return sorted(saved_runs, key=lambda item: item.get("run_id", ""), reverse=True)


def get_saved_run_metadata(run_id: str) -> dict | None:
    """Return saved run metadata for a given run id when available."""
    if not run_id:
        return None

    metadata_path = RUNS_DIR / run_id / "metadata.json"
    if not metadata_path.exists():
        return None

    try:
        with metadata_path.open("r", encoding="utf-8") as metadata_file:
            metadata = json.load(metadata_file)
            metadata["run_version"] = infer_saved_run_version(metadata)
            return metadata
    except (json.JSONDecodeError, OSError):
        return None


def build_saved_run_date_label(run_id: str) -> str:
    """Build the clearest available date label for a saved run."""
    metadata = get_saved_run_metadata(run_id) or {}

    for key in ["date_range_label", "report_date_label", "display_label"]:
        value = str(metadata.get(key, "")).strip()
        if value:
            return value

    created_at = str(metadata.get("created_at", "")).strip()
    if created_at:
        try:
            created_at_dt = datetime.fromisoformat(created_at)
            return created_at_dt.strftime("%b %d, %Y")
        except ValueError:
            pass

    run_id_value = str(metadata.get("run_id", run_id)).strip()
    if run_id_value:
        try:
            run_dt = datetime.strptime(run_id_value, "%Y-%m-%d_%H%M%S")
            return run_dt.strftime("%b %d, %Y")
        except ValueError:
            return run_id_value

    return "Not available"


def load_saved_run(run_id: str) -> dict | None:
    """Load a saved run from disk, rerun the workflow, and return restored results."""
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        return None

    metadata = get_saved_run_metadata(run_id) or {"run_id": run_id, "run_version": "legacy"}
    run_version = infer_saved_run_version(metadata)

    ga4_pages_path = run_dir / "ga4_pages.csv"
    ga4_source_path = run_dir / "ga4_source.csv"
    gsc_queries_path = run_dir / "gsc_queries.csv"
    semrush_positions_path = run_dir / "semrush_positions.csv"
    semrush_pages_path = run_dir / "semrush_pages.csv"
    semrush_topics_path = run_dir / "semrush_topics.csv"
    meta_posts_path = run_dir / "meta_posts.csv"

    ga4_pages_data = normalize_ga4_page_title_dataframe(
        parse_csv_file(str(ga4_pages_path), "GA4_PAGES")
    ) if ga4_pages_path.exists() else None
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
    backfill_ga4_key_metrics(results, ga4_pages_data)
    results["meta_posts_data"] = meta_posts_data
    results["social_insights"] = build_social_insights(meta_posts_data)
    results["saved_run_metadata"] = metadata
    results["run_version"] = run_version

    ga4_debug_titles = []
    if ga4_pages_data is not None and "page_title" in ga4_pages_data.columns:
        ga4_debug_titles = ga4_pages_data["page_title"].head(5).fillna("").astype(str).tolist()

    return {
        "results": results,
        "ga4_debug_titles": ga4_debug_titles,
        "run_id": run_id,
        "run_version": run_version,
    }


def load_saved_ga4_pages_dataframe(run_id: str) -> pd.DataFrame:
    """Load the saved GA4 Page Title CSV for a run when available."""
    if not run_id:
        return pd.DataFrame()

    ga4_pages_path = RUNS_DIR / run_id / "ga4_pages.csv"
    if not ga4_pages_path.exists():
        return pd.DataFrame()

    try:
        return normalize_ga4_page_title_dataframe(parse_csv_file(str(ga4_pages_path), "GA4_PAGES"))
    except Exception:
        return pd.DataFrame()


def normalize_percent_metric(value) -> float | None:
    """Normalize a percent-like metric into percentage units for comparison."""
    numeric_value = to_comparison_number(value)
    if numeric_value is None:
        return None

    return numeric_value * 100 if numeric_value <= 1 else numeric_value


def to_comparison_number(value) -> float | None:
    """Convert a stored metric value into a comparison-safe float."""
    if value is None or value == "":
        return None

    try:
        numeric_value = float(str(value).replace(",", "").replace("%", "").strip())
    except (TypeError, ValueError):
        return None

    if pd.isna(numeric_value):
        return None

    return numeric_value


def format_comparison_value(value, value_type: str = "number") -> str:
    """Format comparison values for tables without changing underlying logic."""
    numeric_value = to_comparison_number(value)
    if numeric_value is None:
        return "Not available"

    if value_type == "percent":
        return f"{numeric_value:.2f}%"

    if float(numeric_value).is_integer():
        return f"{int(numeric_value):,}"

    return f"{numeric_value:,.2f}"


def format_percent_change(value) -> str:
    """Format a percentage delta for display."""
    numeric_value = to_comparison_number(value)
    if numeric_value is None:
        return "Not available"
    return f"{numeric_value:.2f}%"


def build_run_metric_snapshot(results: dict | None, run_id: str | None = None) -> dict[str, list[dict[str, object]]]:
    """Extract comparable GA4, GSC, and social metrics from a saved run."""
    if not results:
        return {"ga4": [], "gsc": [], "social": [], "semrush": [], "availability": {}, "run_version": "legacy"}

    data_summary = results.get("data_intake", {}).get("summary", {})
    insight = results.get("insight", {})
    meta_posts_data = results.get("meta_posts_data")
    semrush_positions_data = results.get("semrush_positions_data")
    semrush_pages_data = results.get("semrush_pages_data")
    semrush_topics_data = results.get("semrush_topics_data")
    ga4_pages_data = load_saved_ga4_pages_dataframe(run_id or "")
    backfilled_ga4_metrics = set(ga4_pages_data.attrs.get("backfilled_ga4_metrics", [])) if not ga4_pages_data.empty else set()
    run_metadata = get_saved_run_metadata(run_id or "") if run_id else {}
    run_version = infer_saved_run_version(run_metadata or results.get("saved_run_metadata"))

    ga4_pages_available = not ga4_pages_data.empty if not ga4_pages_data.empty else data_summary.get("ga4_pages", {}).get("rows", 0) > 0
    ga4_sources_available = data_summary.get("ga4_sources", {}).get("rows", 0) > 0
    gsc_available = data_summary.get("gsc_queries", {}).get("rows", 0) > 0
    social_available = meta_posts_data is not None and not getattr(meta_posts_data, "empty", True)
    semrush_positions_available = semrush_positions_data is not None and not getattr(semrush_positions_data, "empty", True)
    semrush_pages_available = semrush_pages_data is not None and not getattr(semrush_pages_data, "empty", True)
    semrush_topics_available = semrush_topics_data is not None and not getattr(semrush_topics_data, "empty", True)

    ga4_page_metrics = data_summary.get("ga4_pages", {}).get("key_metrics", {})
    ga4_sessions = (
        to_comparison_number(ga4_pages_data["sessions"].fillna(0).sum())
        if ga4_pages_available and "sessions" in ga4_pages_data.columns and "sessions" not in backfilled_ga4_metrics
        else to_comparison_number(ga4_page_metrics.get("sessions"))
    )
    ga4_active_users = (
        to_comparison_number(ga4_pages_data["active_users"].fillna(0).sum())
        if ga4_pages_available and "active_users" in ga4_pages_data.columns and "active_users" not in backfilled_ga4_metrics
        else to_comparison_number(ga4_page_metrics.get("active_users"))
    )
    ga4_engagement_rate = (
        normalize_percent_metric(ga4_pages_data["engagement_rate"].fillna(0).mean())
        if ga4_pages_available and "engagement_rate" in ga4_pages_data.columns and "engagement_rate" not in backfilled_ga4_metrics
        else normalize_percent_metric(ga4_page_metrics.get("engagement_rate"))
    )
    ga4_metrics = [
        {"label": "Sessions", "value": ga4_sessions, "type": "number"},
        {"label": "Active Users", "value": ga4_active_users, "type": "number"},
        {
            "label": "Engagement Rate",
            "value": ga4_engagement_rate,
            "type": "percent",
        },
    ]

    query_analysis = insight.get("query_analysis", []) or []
    total_clicks = sum(to_comparison_number(item.get("clicks")) or 0 for item in query_analysis)
    total_impressions = sum(to_comparison_number(item.get("impressions")) or 0 for item in query_analysis)
    average_position = (
        sum(to_comparison_number(item.get("position")) or 0 for item in query_analysis) / len(query_analysis)
        if query_analysis
        else None
    )
    sample_ctr = (total_clicks / total_impressions * 100) if total_impressions else None
    gsc_metrics = [
        {"label": "Tracked GSC Clicks", "value": total_clicks if query_analysis else None, "type": "number"},
        {"label": "Tracked GSC Impressions", "value": total_impressions if query_analysis else None, "type": "number"},
        {"label": "Tracked CTR", "value": sample_ctr, "type": "percent"},
        {"label": "Average Position", "value": average_position, "type": "number"},
    ]

    social_metrics: list[dict[str, object]] = []
    if social_available:
        social_metrics = [
            {
                "label": "Total Reach",
                "value": to_comparison_number(meta_posts_data.get("Reach", pd.Series(dtype=float)).fillna(0).sum()),
                "type": "number",
            },
            {
                "label": "Total Engagement",
                "value": to_comparison_number(meta_posts_data.get("Engagement", pd.Series(dtype=float)).fillna(0).sum()),
                "type": "number",
            },
            {
                "label": "Average Engagement Rate",
                "value": to_comparison_number(meta_posts_data.get("Engagement Rate", pd.Series(dtype=float)).fillna(0).mean()),
                "type": "percent",
            },
            {
                "label": "Total Follows",
                "value": to_comparison_number(meta_posts_data.get("Follows", pd.Series(dtype=float)).fillna(0).sum()),
                "type": "number",
            },
        ]

    semrush_metrics: list[dict[str, object]] = []
    if semrush_positions_available or semrush_pages_available or semrush_topics_available:
        semrush_metrics = [
            {
                "label": "Tracked Keywords",
                "value": len(semrush_positions_data) if semrush_positions_available else None,
                "type": "number",
            },
            {
                "label": "Tracked Pages",
                "value": len(semrush_pages_data) if semrush_pages_available else None,
                "type": "number",
            },
            {
                "label": "Tracked Topics",
                "value": len(semrush_topics_data) if semrush_topics_available else None,
                "type": "number",
            },
        ]

    return {
        "ga4": ga4_metrics,
        "gsc": gsc_metrics,
        "social": social_metrics,
        "semrush": semrush_metrics,
        "run_version": run_version,
        "availability": {
            "ga4_pages": ga4_pages_available,
            "ga4_sources": ga4_sources_available,
            "gsc": gsc_available,
            "social": social_available,
            "semrush_positions": semrush_positions_available,
            "semrush_pages": semrush_pages_available,
            "semrush_topics": semrush_topics_available,
            "ga4_pages_columns": list(ga4_pages_data.columns),
            "ga4_pages_rows": int(len(ga4_pages_data)),
            "ga4_key_metric_keys": list(ga4_page_metrics.keys()),
            "ga4_backfilled_metrics": sorted(backfilled_ga4_metrics),
        },
    }


def compare_saved_runs(current_run_id: str, comparison_run_id: str) -> dict | None:
    """Load two saved runs and compare their major metrics."""
    current_run = load_saved_run(current_run_id)
    comparison_run = load_saved_run(comparison_run_id)

    if current_run is None or comparison_run is None:
        return None

    current_snapshot = build_run_metric_snapshot(current_run["results"], current_run_id)
    comparison_snapshot = build_run_metric_snapshot(comparison_run["results"], comparison_run_id)
    comparison_results: dict[str, object] = {
        "current_run_id": current_run_id,
        "comparison_run_id": comparison_run_id,
        "current_run_version": current_snapshot.get("run_version", "legacy"),
        "comparison_run_version": comparison_snapshot.get("run_version", "legacy"),
        "current_run_date_label": build_saved_run_date_label(current_run_id),
        "comparison_run_date_label": build_saved_run_date_label(comparison_run_id),
        "comparison_date_label": (
            f"{build_saved_run_date_label(current_run_id)} vs {build_saved_run_date_label(comparison_run_id)}"
        ),
        "legacy_warning": (
            current_snapshot.get("run_version") == "legacy"
            or comparison_snapshot.get("run_version") == "legacy"
        ),
        "ga4": [],
        "gsc": [],
        "social": [],
        "semrush": [],
        "section_messages": {},
        "debug": {},
    }

    current_availability = current_snapshot.get("availability", {})
    comparison_availability = comparison_snapshot.get("availability", {})
    section_messages: dict[str, str] = {}

    if not (current_availability.get("ga4_pages") and comparison_availability.get("ga4_pages")):
        section_messages["ga4"] = "Requires GA4 Page Title report in both runs."
    elif not (current_availability.get("ga4_sources") and comparison_availability.get("ga4_sources")):
        section_messages["ga4"] = "Traffic-source comparisons require GA4 Source / Medium in both runs."

    if not (current_availability.get("gsc") and comparison_availability.get("gsc")):
        section_messages["gsc"] = "Requires GSC Queries in both runs."

    if not (current_availability.get("social") and comparison_availability.get("social")):
        section_messages["social"] = "Requires Meta/social export in both runs."

    if not (
        (current_availability.get("semrush_positions") or current_availability.get("semrush_pages") or current_availability.get("semrush_topics"))
        and (
            comparison_availability.get("semrush_positions")
            or comparison_availability.get("semrush_pages")
            or comparison_availability.get("semrush_topics")
        )
    ):
        section_messages["semrush"] = "Requires SEMrush opportunity data in both runs."

    comparison_results["section_messages"] = section_messages
    comparison_results["debug"] = {
        "current_run": {
            "run_id": current_run_id,
            "result_keys": sorted(current_run["results"].keys()),
            "ga4_pages_available": current_availability.get("ga4_pages"),
            "ga4_pages_rows": current_availability.get("ga4_pages_rows"),
            "ga4_pages_columns": current_availability.get("ga4_pages_columns"),
            "ga4_key_metric_keys": current_availability.get("ga4_key_metric_keys"),
            "ga4_backfilled_metrics": current_availability.get("ga4_backfilled_metrics"),
            "run_version": current_snapshot.get("run_version"),
            "ga4_snapshot": current_snapshot.get("ga4", []),
        },
        "comparison_run": {
            "run_id": comparison_run_id,
            "result_keys": sorted(comparison_run["results"].keys()),
            "ga4_pages_available": comparison_availability.get("ga4_pages"),
            "ga4_pages_rows": comparison_availability.get("ga4_pages_rows"),
            "ga4_pages_columns": comparison_availability.get("ga4_pages_columns"),
            "ga4_key_metric_keys": comparison_availability.get("ga4_key_metric_keys"),
            "ga4_backfilled_metrics": comparison_availability.get("ga4_backfilled_metrics"),
            "run_version": comparison_snapshot.get("run_version"),
            "ga4_snapshot": comparison_snapshot.get("ga4", []),
        },
    }

    for section_key in ["ga4", "gsc", "social", "semrush"]:
        current_metrics = {item["label"]: item for item in current_snapshot.get(section_key, [])}
        previous_metrics = {item["label"]: item for item in comparison_snapshot.get(section_key, [])}
        section_rows = []

        for label in list(current_metrics.keys()):
            current_metric = current_metrics.get(label, {})
            previous_metric = previous_metrics.get(label, {})
            current_value = to_comparison_number(current_metric.get("value"))
            previous_value = to_comparison_number(previous_metric.get("value"))

            absolute_change = (
                current_value - previous_value
                if current_value is not None and previous_value is not None
                else None
            )
            percent_change = (
                (absolute_change / previous_value) * 100
                if absolute_change is not None and previous_value not in (None, 0)
                else None
            )

            section_rows.append(
                {
                    "metric": label,
                    "value_type": current_metric.get("type", previous_metric.get("type", "number")),
                    "current_value": current_value,
                    "previous_value": previous_value,
                    "absolute_change": absolute_change,
                    "percent_change": percent_change,
                }
            )

        comparison_results[section_key] = section_rows

    return comparison_results


def render_comparison_summary(results: dict | None, sections: list[str]) -> None:
    """Render saved-run comparison tables when comparison data exists."""
    comparison_results = st.session_state.get("comparison_results")
    comparison_mode = bool(st.session_state.get("comparison_mode"))
    if not results or not comparison_results or not comparison_mode:
        return

    section_titles = {
        "ga4": "GA4 Comparison",
        "gsc": "GSC Comparison",
        "social": "Social Comparison",
        "semrush": "SEMrush Comparison",
    }
    section_messages = comparison_results.get("section_messages", {})
    has_content = any(comparison_results.get(section) or section_messages.get(section) for section in sections)
    if not has_content:
        return

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Saved Run Comparison</div>', unsafe_allow_html=True)
    st.caption(
        f"Current Run: {comparison_results.get('current_run_id', 'Not available')} | "
        f"Comparison Run: {comparison_results.get('comparison_run_id', 'Not available')}"
    )
    st.caption(comparison_results.get("comparison_date_label", "Not available"))
    if comparison_results.get("legacy_warning"):
        st.warning("This saved run was generated using an older data schema. Some metrics may be unavailable.")

    for section in sections:
        rows = comparison_results.get(section, [])
        section_message = str(section_messages.get(section, "")).strip()

        st.markdown(f"**{section_titles.get(section, section.title())}**")

        if not rows:
            if section_message:
                st.info(section_message)
            else:
                st.info("Comparison data is not available for this section yet.")
            continue

        display_rows = []
        for row in rows:
            value_type = str(row.get("value_type", "number"))
            display_rows.append(
                {
                    "Metric": row.get("metric", "Metric"),
                    "Current Value": format_comparison_value(row.get("current_value"), value_type),
                    "Previous Value": format_comparison_value(row.get("previous_value"), value_type),
                    "Absolute Change": format_comparison_value(row.get("absolute_change"), value_type),
                    "% Change": format_percent_change(row.get("percent_change")),
                }
            )

        if section_message:
            st.caption(section_message)
        st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)

    debug_payload = comparison_results.get("debug")
    if debug_payload:
        with st.expander("Comparison Debug", expanded=False):
            st.json(debug_payload)

    st.markdown("</div>", unsafe_allow_html=True)


def format_heading(value: str) -> str:
    """Convert keys like ux_conversion into clean labels."""
    return value.replace("_", " ").upper()


def has_uploaded_data(files: list[object | None]) -> bool:
    """Return True when at least one upload is present."""
    return any(file is not None for file in files)


def build_scorecard(results: dict) -> dict[str, str]:
    """Collect the main scorecard values from workflow results."""
    insight = results.get("insight", {})
    high_impression_low_click = insight.get("high_impression_low_click", []) or []
    query_analysis = insight.get("query_analysis", []) or []
    top_sources = insight.get("top_sources", []) or []
    target_ctr_percent = 5.0

    top_opportunity_item = (
        high_impression_low_click[0]
        if high_impression_low_click
        else max(
            query_analysis,
            key=lambda item: to_comparison_number(item.get("opportunity_score")) or 0,
            default={},
        )
    )

    if top_opportunity_item.get("query"):
        top_opportunity_query = str(top_opportunity_item.get("query"))
    elif query_analysis:
        top_opportunity_query = "No standout GSC query opportunity found"
    else:
        top_opportunity_query = "Requires GSC Queries data"

    opportunity_score_value = to_comparison_number(top_opportunity_item.get("opportunity_score"))
    if opportunity_score_value is not None:
        opportunity_score = str(int(opportunity_score_value) if float(opportunity_score_value).is_integer() else round(opportunity_score_value, 2))
    elif query_analysis:
        opportunity_score = "Requires GSC opportunity scoring"
    else:
        opportunity_score = "Requires GSC Queries data"

    top_ctr_percent = normalize_ctr_percent(top_opportunity_item.get("ctr")) if top_opportunity_item else None
    top_ctr_gap_value = max(0.0, target_ctr_percent - top_ctr_percent) if top_ctr_percent is not None else None
    if top_ctr_gap_value is not None:
        top_ctr_gap = format_ctr_value(top_ctr_gap_value)
    elif query_analysis:
        top_ctr_gap = "No CTR gap found in loaded GSC data"
    else:
        top_ctr_gap = "Requires GSC Queries data"

    if top_sources:
        top_traffic_source = get_first_value(top_sources, "source_medium")
    else:
        top_traffic_source = "Requires GA4 Source / Medium"

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


def collect_report_recommendations(strategy_recommendations: dict) -> dict[str, list[dict[str, str]]]:
    """Normalize recommendation content for client-facing report output."""
    formatted: dict[str, list[dict[str, str]]] = {}

    for category, recommendations in strategy_recommendations.items():
        items: list[dict[str, str]] = []
        for recommendation in recommendations:
            if isinstance(recommendation, dict):
                issue = str(recommendation.get("issue", "")).strip()
                rec_text = str(recommendation.get("recommendation", "")).strip()
                why = str(recommendation.get("why_it_matters", "")).strip()
                priority = str(recommendation.get("priority", "")).strip()

                if issue or rec_text or why:
                    items.append(
                        {
                            "issue": issue,
                            "recommendation": rec_text,
                            "why": why,
                            "priority": priority,
                        }
                    )
            elif isinstance(recommendation, str) and recommendation.strip():
                items.append(
                    {
                        "issue": "",
                        "recommendation": recommendation.strip(),
                        "why": "",
                        "priority": "",
                    }
                )

        if items:
            formatted[str(category)] = items

    return formatted


def render_client_report(results: dict) -> None:
    """Show a simplified client-facing report view."""
    insight = results["insight"]
    strategy = results["strategy"]["strategy"]
    evaluation = results["evaluation"]["evaluation"]
    formatted_recommendations = collect_report_recommendations(strategy["recommendations"])

    st.subheader("Executive Summary")
    summary_parts = [
        f"The strongest current opportunity is {get_first_value(insight['high_impression_low_click'], 'query')}.",
        f"The page with the clearest strategic importance is {strategy['primary_page']}.",
        f"The leading traffic source in the uploaded data is {get_first_value(insight['top_sources'], 'source_medium')}.",
        f"The current readiness score is {evaluation['score']}/5.",
    ]
    st.write(" ".join(summary_parts))

    st.subheader("Key Insights")
    for item in insight["patterns"][:5]:
        st.write(f"- {item}")

    st.subheader("Recommended Actions")
    for category, items in formatted_recommendations.items():
        st.markdown(f"### {format_heading(category)}")
        for item in items:
            if item["priority"]:
                st.markdown(f"**Priority:** {item['priority']}")
            if item["issue"]:
                st.markdown(f"**Issue:** {item['issue']}")
            if item["recommendation"]:
                st.markdown(f"**Recommendation:** {item['recommendation']}")
            if item["why"]:
                st.markdown(f"**Why it matters:** {item['why']}")
            st.markdown("")

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

    st.markdown('<div class="dashboard-title">Marketing Intelligence Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="dashboard-subtitle">Real-time insights and opportunities</div>', unsafe_allow_html=True)

    render_comparison_summary(results, ["ga4", "gsc", "social", "semrush"])
    render_scorecard(results)
    st.markdown('<div class="dashboard-section-divider"></div>', unsafe_allow_html=True)

    left_col, right_col = st.columns([2.35, 1], vertical_alignment="top")

    with left_col:
        if has_query_data:
            overview_card = st.container()
            with overview_card:
                st.markdown('<div class="dashboard-card-marker dashboard-chart-card-marker"></div>', unsafe_allow_html=True)
                st.markdown('<div class="panel-title">Performance Overview</div>', unsafe_allow_html=True)
                st.markdown(
                    '<div class="dashboard-card-helper">Top search queries by impression volume from the loaded run.</div>',
                    unsafe_allow_html=True,
                )
                query_chart_df = pd.DataFrame(insight["query_analysis"])
                if {"query", "impressions"}.issubset(query_chart_df.columns):
                    chart_data = (
                        query_chart_df.sort_values("impressions", ascending=False)[["query", "impressions"]]
                        .head(5)
                        .copy()
                    )
                    performance_fig = px.bar(
                        chart_data,
                        x="query",
                        y="impressions",
                        color_discrete_sequence=["#8C52FF"],
                    )
                    performance_fig.update_layout(
                        showlegend=False,
                        plot_bgcolor="#FFFFFF",
                        paper_bgcolor="#FFFFFF",
                        margin=dict(l=12, r=12, t=8, b=8),
                        font=dict(color="#162033"),
                        xaxis_title="",
                        yaxis_title="",
                    )
                    performance_fig.update_traces(
                        marker_line_color="#7C3AED",
                        marker_line_width=0,
                        hovertemplate="<b>%{x}</b><br>Impressions: %{y}<extra></extra>",
                    )
                    performance_fig.update_xaxes(tickfont=dict(color="#111111"))
                    performance_fig.update_yaxes(tickfont=dict(color="#111111"))
                    st.plotly_chart(performance_fig, use_container_width=True)

        row_b_left, row_b_right = st.columns(2)

        with row_b_left:
            if has_query_data:
                queries_card = st.container()
                with queries_card:
                    st.markdown('<div class="dashboard-card-marker"></div>', unsafe_allow_html=True)
                    st.markdown('<div class="panel-title">Top Queries</div>', unsafe_allow_html=True)
                    st.markdown(
                        '<div class="dashboard-card-helper">Highest-visibility queries from the loaded GSC data.</div>',
                        unsafe_allow_html=True,
                    )
                    top_queries_df = format_ctr_dataframe(pd.DataFrame(insight["query_analysis"]))
                    st.dataframe(
                        top_queries_df[["query", "ctr", "impressions", "position"]].head(5),
                        use_container_width=True,
                        hide_index=True,
                    )

        with row_b_right:
            if has_page_data:
                pages_card = st.container()
                with pages_card:
                    st.markdown('<div class="dashboard-card-marker"></div>', unsafe_allow_html=True)
                    st.markdown('<div class="panel-title">Top Pages</div>', unsafe_allow_html=True)
                    st.markdown(
                        '<div class="dashboard-card-helper">Pages carrying the strongest value signal in the current run.</div>',
                        unsafe_allow_html=True,
                    )
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

        row_c_left, row_c_right = st.columns(2)

        with row_c_left:
            if has_source_data:
                traffic_card = st.container()
                with traffic_card:
                    st.markdown('<div class="dashboard-card-marker"></div>', unsafe_allow_html=True)
                    st.markdown('<div class="panel-title">Traffic Distribution</div>', unsafe_allow_html=True)
                    st.markdown(
                        '<div class="dashboard-card-helper">Acquisition mix based on the loaded GA4 source and medium report.</div>',
                        unsafe_allow_html=True,
                    )
                    top_sources_df = pd.DataFrame(combined["top_traffic_sources"])
                    traffic_fig = px.bar(
                        top_sources_df.head(5),
                        x="source_medium",
                        y="value",
                        color_discrete_sequence=["#8C52FF"],
                    )
                    traffic_fig.update_layout(
                        showlegend=False,
                        plot_bgcolor="#FFFFFF",
                        paper_bgcolor="#FFFFFF",
                        margin=dict(l=12, r=12, t=8, b=8),
                        font=dict(color="#162033"),
                        xaxis_title="",
                        yaxis_title="",
                    )
                    traffic_fig.update_traces(
                        marker_line_color="#7C3AED",
                        marker_line_width=0,
                        hovertemplate="<b>%{x}</b><br>Value: %{y}<extra></extra>",
                    )
                    traffic_fig.update_xaxes(tickfont=dict(color="#111111"))
                    traffic_fig.update_yaxes(tickfont=dict(color="#111111"))
                    st.plotly_chart(traffic_fig, use_container_width=True)
                    st.dataframe(top_sources_df, use_container_width=True, hide_index=True)

        with row_c_right:
            if has_behavior_data:
                behavior_card = st.container()
                with behavior_card:
                    st.markdown('<div class="dashboard-card-marker"></div>', unsafe_allow_html=True)
                    st.markdown('<div class="panel-title">User Behavior Signals</div>', unsafe_allow_html=True)
                    st.markdown(
                        '<div class="dashboard-card-helper">Behavior metrics from the loaded GA4 page and source reports.</div>',
                        unsafe_allow_html=True,
                    )

                    behavior_metrics = {
                        "Sessions": data_summary["ga4_pages"]["key_metrics"].get("sessions", "Not available"),
                        "Active Users": data_summary["ga4_pages"]["key_metrics"].get("active_users", "Not available"),
                        "Engagement Rate": format_ga4_engagement_rate_kpi(
                            data_summary["ga4_pages"]["key_metrics"].get("engagement_rate")
                        ),
                        "Source Sessions": data_summary["ga4_sources"]["key_metrics"].get("sessions", "Not available"),
                    }

                    for label, value in behavior_metrics.items():
                        st.metric(label, value)

        if has_insight_patterns:
            insights_summary_card = st.container()
            with insights_summary_card:
                st.markdown('<div class="dashboard-card-marker"></div>', unsafe_allow_html=True)
                st.markdown('<div class="panel-title">Key Insights</div>', unsafe_allow_html=True)
                insight_cols = st.columns(3)
                insight_titles = ["Low CTR Opportunity", "Growth Opportunity", "Traffic Insight"]
                for index, title in enumerate(insight_titles):
                    with insight_cols[index]:
                        st.markdown("**" + title + "**")
                        st.write(insight["patterns"][index] if len(insight["patterns"]) > index else "No insight available.")

        recommended_actions_card = st.container()
        with recommended_actions_card:
            st.markdown('<div class="dashboard-card-marker"></div>', unsafe_allow_html=True)
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

        render_priority_action_queue(results, priority_class_map)

        what_next_card = st.container()
        with what_next_card:
            st.markdown('<div class="dashboard-card-marker"></div>', unsafe_allow_html=True)
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

        render_suggested_changes_section(results)

    with right_col:
        if has_insight_patterns:
            insights_card = st.container()
            with insights_card:
                st.markdown('<div class="dashboard-card-marker dashboard-insights-card-marker"></div>', unsafe_allow_html=True)
                st.markdown('<div class="panel-title">AI Insights Feed</div>', unsafe_allow_html=True)
                st.markdown(
                    '<div class="dashboard-card-helper">A quick strategist read on the strongest patterns in the current run.</div>',
                    unsafe_allow_html=True,
                )
                for index, pattern in enumerate(insight["patterns"][:3], start=1):
                    st.markdown(f"**Insight {index}**")
                    st.write(pattern)
                    if index < min(len(insight["patterns"]), 3):
                        st.markdown('<div class="insight-divider"></div>', unsafe_allow_html=True)

        cta_card = st.container()
        with cta_card:
            st.markdown('<div class="dashboard-card-marker"></div>', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">Primary CTA</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="dashboard-card-helper">Use the recommendations below to move from insight to action.</div>',
                unsafe_allow_html=True,
            )
            st.button("View Recommendations", key="view_recommendations_button")

    export_card = st.container()
    with export_card:
        st.markdown('<div class="dashboard-card-marker"></div>', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Export Options</div>', unsafe_allow_html=True)
        render_export_section(results, inside_panel=True)

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
            safe_results = make_json_safe(results)
            st.code(json.dumps(safe_results, indent=2), language="json")



def render_analysis_page(results: dict) -> None:
    """Render the Analysis page (Traffic, Behavior, Queries, Pages)."""
    st.title("Analysis")
    st.caption("Performance data from GA4 + GSC")

    if not results:
        st.info("Run the workflow to view analysis.")
        return

    render_comparison_summary(results, ["ga4", "gsc", "semrush"])

    insight = results["insight"]
    combined = results["data_intake"]["summary"]["combined"]
    data_summary = results["data_intake"]["summary"]

    has_query_data = bool(insight["query_analysis"])
    has_page_data = bool(combined["top_pages"])
    has_source_data = bool(combined["top_traffic_sources"])
    has_behavior_data = (
        data_summary["ga4_pages"]["rows"] > 0 or data_summary["ga4_sources"]["rows"] > 0
    )

    if has_source_data or has_behavior_data:
        st.markdown("### Overview")

    if has_source_data:
        traffic_card = st.container()
        with traffic_card:
            st.markdown('<div class="dashboard-card-marker"></div>', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">Traffic Distribution</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="dashboard-card-helper">Acquisition mix from the loaded GA4 source and medium report.</div>',
                unsafe_allow_html=True,
            )
            top_sources_df = pd.DataFrame(combined["top_traffic_sources"])
            traffic_fig = px.bar(
                top_sources_df.head(5),
                x="source_medium",
                y="value",
                color_discrete_sequence=["#8C52FF"],
            )
            traffic_fig.update_layout(
                showlegend=False,
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
                margin=dict(l=12, r=12, t=8, b=8),
                font=dict(color="#162033"),
                xaxis_title="",
                yaxis_title="",
                height=320,
            )
            traffic_fig.update_traces(
                marker_line_color="#7C3AED",
                marker_line_width=0,
                hovertemplate="<b>%{x}</b><br>Value: %{y}<extra></extra>",
            )
            traffic_fig.update_xaxes(tickfont=dict(color="#111111"))
            traffic_fig.update_yaxes(tickfont=dict(color="#111111"))
            st.plotly_chart(traffic_fig, use_container_width=True)
            st.dataframe(top_sources_df, use_container_width=True, hide_index=True)

    if has_behavior_data:
        behavior_card = st.container()
        with behavior_card:
            st.markdown('<div class="dashboard-card-marker"></div>', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">User Behavior</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="dashboard-card-helper">Behavior metrics from the loaded GA4 page-title report.</div>',
                unsafe_allow_html=True,
            )
            col1, col2, col3 = st.columns(3)

            behavior_metrics = {
                "Sessions": data_summary["ga4_pages"]["key_metrics"].get("sessions", "—"),
                "Active Users": data_summary["ga4_pages"]["key_metrics"].get("active_users", "—"),
                "Engagement Rate": calculate_analysis_engagement_rate_kpi(),
            }

            with col1:
                st.metric("Sessions", behavior_metrics["Sessions"])
            with col2:
                st.metric("Users", behavior_metrics["Active Users"])
            with col3:
                st.metric("Engagement Rate", behavior_metrics["Engagement Rate"])

    if has_source_data or has_behavior_data:
        st.markdown('<div class="dashboard-section-divider"></div>', unsafe_allow_html=True)

    if has_query_data:
        st.markdown("### Search Behavior")

    if has_query_data:
        queries_card = st.container()
        with queries_card:
            st.markdown('<div class="dashboard-card-marker"></div>', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">Top Queries</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="dashboard-card-helper">Search queries with the highest impression volume from the loaded GSC data.</div>',
                unsafe_allow_html=True,
            )

            top_queries_chart_df = pd.DataFrame(insight["query_analysis"]).copy()
            top_queries_chart_df["impressions"] = pd.to_numeric(
                top_queries_chart_df["impressions"],
                errors="coerce",
            ).fillna(0)
            top_queries_chart_df["position"] = pd.to_numeric(
                top_queries_chart_df["position"],
                errors="coerce",
            ).fillna(0)
            top_queries_chart_df["ctr_display"] = top_queries_chart_df["ctr"].apply(format_ctr_value)
            top_queries_chart_df = top_queries_chart_df.sort_values("impressions", ascending=False).head(5)

            query_fig = px.bar(
                top_queries_chart_df,
                x="impressions",
                y="query",
                orientation="h",
                hover_data={
                    "query": True,
                    "impressions": ":,.0f",
                    "ctr_display": True,
                    "position": ":.2f",
                },
                labels={
                    "query": "",
                    "impressions": "Impressions",
                    "ctr_display": "CTR",
                    "position": "Position",
                },
                color_discrete_sequence=["#8C52FF"],
            )
            query_fig.update_yaxes(
                autorange="reversed",
                title="",
                tickfont={"color": "#111111", "size": 12},
                title_font={"color": "#111111"},
            )
            query_fig.update_xaxes(
                title="Impressions",
                gridcolor="#E6E8F0",
                zeroline=False,
                tickfont={"color": "#111111", "size": 12},
                title_font={"color": "#111111"},
            )
            query_fig.update_layout(
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
                font={"color": "#111111", "size": 12},
                title_font={"color": "#111111"},
                hoverlabel={
                    "bgcolor": "#FFFFFF",
                    "bordercolor": "#E6E8F0",
                    "font": {"color": "#111111"},
                },
                margin={"l": 8, "r": 12, "t": 12, "b": 24},
                height=320,
                showlegend=False,
            )
            st.plotly_chart(query_fig, use_container_width=True)

            top_queries_df = format_ctr_dataframe(top_queries_chart_df.copy())
            st.dataframe(
                top_queries_df[["query", "ctr", "impressions", "position"]],
                use_container_width=True,
                hide_index=True,
            )

    if has_page_data:
        st.markdown("### Page Performance")

    if has_page_data:
        pages_card = st.container()
        with pages_card:
            st.markdown('<div class="dashboard-card-marker"></div>', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">Top Pages</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="dashboard-card-helper">Highest-value pages from the loaded GA4 page-title report.</div>',
                unsafe_allow_html=True,
            )

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
            top_pages_chart_df = top_pages_df.copy()
            top_pages_chart_df["value"] = pd.to_numeric(top_pages_chart_df["value"], errors="coerce").fillna(0)
            top_pages_chart_df = top_pages_chart_df.sort_values("value", ascending=False).head(5)
            top_pages_chart_df["page_title_display"] = top_pages_chart_df["page_title"].apply(
                lambda title: str(title) if len(str(title)) <= 58 else f"{str(title)[:55]}..."
            )

            pages_fig = px.bar(
                top_pages_chart_df,
                x="value",
                y="page_title_display",
                orientation="h",
                hover_data={
                    "page_title": True,
                    "page_title_display": False,
                    "value": ":,.0f",
                    "metric": True,
                    "traffic_context": True,
                },
                labels={
                    "page_title_display": "",
                    "value": "Value",
                    "page_title": "Page Title",
                    "metric": "Metric",
                    "traffic_context": "Traffic Context",
                },
                color_discrete_sequence=["#8C52FF"],
            )
            pages_fig.update_yaxes(
                autorange="reversed",
                title="",
                tickfont={"color": "#111111", "size": 12},
                title_font={"color": "#111111"},
            )
            pages_fig.update_xaxes(
                title="Value",
                gridcolor="#E6E8F0",
                zeroline=False,
                tickfont={"color": "#111111", "size": 12},
                title_font={"color": "#111111"},
            )
            pages_fig.update_layout(
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
                font={"color": "#111111", "size": 12},
                title_font={"color": "#111111"},
                hoverlabel={
                    "bgcolor": "#FFFFFF",
                    "bordercolor": "#E6E8F0",
                    "font": {"color": "#111111"},
                },
                margin={"l": 8, "r": 12, "t": 12, "b": 24},
                height=340,
                showlegend=False,
            )
            st.plotly_chart(pages_fig, use_container_width=True)

            st.dataframe(
                top_pages_chart_df[["page_title", "metric", "value", "traffic_context"]],
                use_container_width=True,
                hide_index=True,
            )


def render_social_analysis_page(results: dict) -> None:
    """Render the Social Analysis page using Meta social insights."""
    st.title("Social Analysis")
    st.caption("Instagram + Facebook performance insights")

    if not results:
        st.info("Upload a Meta content export and run the workflow first on the Data Sources page.")
        return

    render_comparison_summary(results, ["social"])

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
        before_state_html = str(card["before_state"]).replace("\n", "<br>")
        suggested_change_html = str(card["example_layout_content_improvement"]).replace("\n", "<br>")
        change_body_html = (
            f"<div class='change-card-title'>{card['page_or_asset_name']}</div>"
            f"<div class='change-card-body'>"
            f"<strong>Issue:</strong><br>{card['issue']}"
            f"<br><br><strong>Why it matters:</strong><br>{card['why_it_matters']}"
            f"<br><br><strong>Recommended change:</strong><br>{card['recommended_change']}"
            f"<br><br><strong>Example headline or CTA:</strong><br>{card['example_headline_or_cta']}"
            f"</div>"
        )
        st.markdown(f"<div class='change-card'>{change_body_html}</div>", unsafe_allow_html=True)

        before_col, after_col = st.columns(2)
        with before_col:
            st.markdown('<div class="change-comparison-heading">Before</div>', unsafe_allow_html=True)
            st.markdown(
                f"<div class='mock-block'>{before_state_html}</div>",
                unsafe_allow_html=True,
            )
        with after_col:
            st.markdown('<div class="change-comparison-heading">Suggested Change</div>', unsafe_allow_html=True)
            st.markdown(
                f"<div class='mock-block'>{suggested_change_html}</div>",
                unsafe_allow_html=True,
            )

        st.write("")

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
    """Turn SEMrush position data into strategic keyword opportunity cards."""
    dataframe = semrush_positions_data.copy()
    dataframe.columns = [str(column).strip().lower() for column in dataframe.columns]

    if "keyword" not in dataframe.columns or "position" not in dataframe.columns:
        return []

    dataframe["position"] = pd.to_numeric(dataframe["position"], errors="coerce")
    if "volume" in dataframe.columns:
        dataframe["volume"] = pd.to_numeric(dataframe["volume"], errors="coerce")

    opportunity_df = dataframe[dataframe["position"].between(4, 30, inclusive="both")].copy()
    if "volume" in opportunity_df.columns:
        opportunity_df = opportunity_df[opportunity_df["volume"].fillna(0) > 0]
        opportunity_df = opportunity_df.sort_values(["position", "volume"], ascending=[True, False])
    else:
        opportunity_df = opportunity_df.sort_values("position", ascending=True)

    cards = []
    for _, row in opportunity_df.head(10).iterrows():
        position_value = int(row["position"]) if pd.notna(row["position"]) else "Not available"
        volume_value = (
            int(row["volume"]) if "volume" in opportunity_df.columns and pd.notna(row.get("volume")) else "Not available"
        )
        url_value = str(row["url"]) if "url" in opportunity_df.columns and pd.notna(row.get("url")) else "Not available"
        keyword_value = str(row["keyword"]).strip()

        if pd.notna(row["position"]) and 8 <= row["position"] <= 15:
            opportunity_type = "Quick-Win On-Page SEO"
            why_it_matters = (
                f"{keyword_value} is already ranking in a range where a focused on-page refresh can realistically push it into stronger click-driving positions."
            )
            recommended_action = (
                f"Update the title tag, H1, opening paragraph, and FAQ block on the page targeting {keyword_value}, and add 2-3 internal links from closely related pages."
            )
            why_recommendation_works = (
                "This works because the keyword already has visibility, so clearer relevance and stronger internal support can improve rankings without requiring a brand-new asset."
            )
            priority = "High"
        elif pd.notna(row["position"]) and 16 <= row["position"] <= 30:
            opportunity_type = "Content Expansion Opportunity"
            why_it_matters = (
                f"{keyword_value} has search visibility but is still too far from top positions, which usually means the current page does not cover the topic deeply enough."
            )
            recommended_action = (
                f"Expand coverage around {keyword_value} with a dedicated supporting section or article, then link it back to the primary page to strengthen topic depth."
            )
            why_recommendation_works = (
                "This works because broader coverage and supporting content help search engines connect the page cluster to the query’s intent, improving relevance and long-tail reach."
            )
            priority = "Medium"
        else:
            opportunity_type = "SEO Opportunity"
            why_it_matters = f"{keyword_value} is visible in search and still has room to capture more qualified traffic."
            recommended_action = (
                f"Refresh the page targeting {keyword_value} so the headline, snippet language, and supporting content align more tightly with search intent."
            )
            why_recommendation_works = "Better keyword-to-page alignment typically improves both ranking strength and downstream traffic quality."
            priority = "Medium"

        cards.append(
            {
                "opportunity_type": opportunity_type,
                "target": keyword_value,
                "keyword": str(row["keyword"]),
                "position": str(position_value),
                "volume": str(volume_value),
                "url": url_value,
                "why_it_matters": why_it_matters,
                "recommended_action": recommended_action,
                "why_recommendation_works": why_recommendation_works,
                "priority": priority,
            }
        )

    return cards

def build_semrush_page_cards(semrush_pages_data: pd.DataFrame) -> list[dict[str, str]]:
    """Turn SEMrush Pages Report data into page-level strategic opportunities."""
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
        page_url = str(row[url_column])

        metric_parts = []
        if traffic_value is not None:
            metric_parts.append(f"Traffic: {traffic_value}")
        if keywords_value is not None:
            metric_parts.append(f"Keywords: {keywords_value}")

        if (traffic_value or 0) >= 100 and (keywords_value or 0) >= 10:
            opportunity_type = "UX Conversion Opportunity"
            why_it_matters = (
                f"{page_url} already attracts meaningful search demand, which means weak CTA placement, trust signals, or page flow can directly suppress conversions."
            )
            recommended_action = (
                "Improve CTA visibility above the fold, add stronger provider/location trust language, and reduce friction between the main value proposition and the next step."
            )
            why_recommendation_works = (
                "This should work because improving conversion flow on a page that already earns traffic is usually faster than trying to create demand from scratch."
            )
            priority = "High"
        elif (keywords_value or 0) >= 20:
            opportunity_type = "Thin Coverage Opportunity"
            why_it_matters = (
                f"{page_url} ranks for a broad keyword set, which suggests the page could capture more traffic if it covered the supporting subtopics more completely."
            )
            recommended_action = (
                "Expand the page with deeper topic sections, related FAQs, and internal links to supporting assets so the page matches a wider set of long-tail intents."
            )
            why_recommendation_works = (
                "This should work because fuller coverage helps the page compete across more related searches and makes its relevance clearer to search engines."
            )
            priority = "High"
        else:
            opportunity_type = "Page Optimization Opportunity"
            why_it_matters = (
                f"{page_url} has organic visibility and can likely perform better with clearer messaging, structure, and trust support."
            )
            recommended_action = (
                "Refresh the headline-to-CTA flow, tighten the intro copy around user intent, and add more specific trust and conversion cues."
            )
            why_recommendation_works = (
                "This should work because pages with some existing visibility usually respond well when content structure and conversion hierarchy are clarified."
            )
            priority = "Medium"

        cards.append(
            {
                "opportunity_type": opportunity_type,
                "target": page_url,
                "page_url": str(row[url_column]),
                "metric_line": " | ".join(metric_parts) if metric_parts else "Metrics not available",
                "why_it_matters": why_it_matters,
                "recommended_action": recommended_action,
                "why_recommendation_works": why_recommendation_works,
                "priority": priority,
            }
        )

    return cards


def build_semrush_topic_cards(
    semrush_topics_data: pd.DataFrame,
    strategy_topic_opportunities: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    """Turn SEMrush Topic Opportunities data into strategic content opportunities."""
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
        opportunity_type = "Content Expansion Opportunity"
        recommended_action = (
            str(strategy_match.get("recommended_action", "")).strip()
            or str(strategy_match.get("action", "")).strip()
        )
        why_it_matters = str(strategy_match.get("why_it_matters", "")).strip()
        why_recommendation_works = ""

        gap_type = str(strategy_match.get("gap_type", "")).strip().lower()
        opportunity_type_value = str(strategy_match.get("opportunity_type", "")).strip().lower()
        if opportunity_type_value in {"local"} or gap_type == "lack of authority":
            opportunity_type = "Local / AEO-GEO Opportunity"
            if not recommended_action:
                recommended_action = (
                    "Add local provider, location, and trust signals, then strengthen FAQ and entity-style language so the content is easier for search and AI systems to cite."
                )
            why_recommendation_works = (
                "This should work because clearer local and authority signals make the page more credible for local-intent users and more quotable for AI-driven discovery."
            )
        elif gap_type in {"missing content", "weak content"}:
            opportunity_type = "Content Expansion Opportunity"
            if not recommended_action:
                recommended_action = (
                    "Create a focused page or article for this topic, then support it with FAQs and internal links from related assets."
                )
            why_recommendation_works = (
                "This should work because filling a clear content gap gives the site a stronger chance to rank for the target topic and its related long-tail searches."
            )
        elif gap_type == "poor structure":
            opportunity_type = "AEO / GEO Opportunity"
            if not recommended_action:
                recommended_action = (
                    "Reformat the content with direct-answer headings, concise summaries, and extractable FAQ blocks so it is easier to surface in AI and answer-style search results."
                )
            why_recommendation_works = (
                "This should work because answer-friendly formatting improves readability for both users and search systems looking for structured responses."
            )
        else:
            if not recommended_action:
                recommended_action = (
                    "Add the topic into an existing cluster or build a focused supporting article tied to a strong conversion or authority page."
                )
            why_recommendation_works = (
                "This should work because broader topic coverage and stronger internal linking improve both authority and discoverability."
            )

        cards.append(
            {
                "opportunity_type": opportunity_type,
                "target": topic_value,
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
                    why_it_matters
                    or (
                        "This topic can help the site close a real visibility gap and strengthen authority around a meaningful patient question."
                        if priority == "High"
                        else "This topic can extend supporting coverage and help the site capture more related long-tail intent."
                    )
                ),
                "recommended_action": recommended_action,
                "why_recommendation_works": why_recommendation_works,
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
    formatted_recommendations = collect_report_recommendations(strategy["recommendations"])
    report_date = datetime.now().strftime("%B %d, %Y").replace(" 0", " ")

    report_lines = [
        "AI Marketing Workflow Report",
        f"Report Date: {report_date}",
        "Generated by the AI Marketing Workflow System",
        "____________________________________________________________",
        "",
        "EXECUTIVE SUMMARY",
        (
            f"The strongest current opportunity is {get_first_value(insight['high_impression_low_click'], 'query')}. "
            f"The primary page to improve is {strategy['primary_page']}, and the leading traffic source is "
            f"{get_first_value(insight['top_sources'], 'source_medium')}. This report summarizes the most important "
            "insights and actions to improve visibility, traffic quality, and conversions."
        ),
        "",
        "KEY INSIGHTS",
    ]

    for item in insight["patterns"][:5]:
        report_lines.append(f"- {item}")

    report_lines.extend(["", "", "RECOMMENDED ACTIONS"])

    for category, items in formatted_recommendations.items():
        report_lines.append("")
        report_lines.append(format_heading(category))
        for item in items:
            if item["issue"]:
                report_lines.append(f"Issue: {item['issue']}")
            if item["recommendation"]:
                report_lines.append(f"Recommendation: {item['recommendation']}")
            if item["why"]:
                report_lines.append(f"Why it matters: {item['why']}")
            if item["priority"]:
                report_lines.append(f"Priority: {item['priority']}")
            report_lines.append("")

    report_lines.extend(
        [
            "",
            "PRIORITY OPPORTUNITIES",
            f"- Primary query focus: {strategy['primary_query']['query']}",
            f"- Secondary query focus: {strategy['secondary_query']['query']}",
            f"- Primary page to refresh: {strategy['primary_page']}",
            f"- Top traffic source: {get_first_value(insight['top_sources'], 'source_medium')}",
        ]
    )

    return simple_pdf_from_lines(report_lines)


def simple_pdf_from_lines(lines: list[str]) -> bytes:
    """Build a small multi-page PDF document sized for 8.5x11 output."""

    def escape_pdf_text(value: str) -> str:
        return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    wrapped_lines: list[str] = []
    for line in lines:
        text = str(line).strip()
        if not text:
            wrapped_lines.append("")
            continue
        indent = "  " if text.startswith("- ") else ""
        wrap_width = 78 if indent else 80
        segments = textwrap.wrap(text, width=wrap_width) or [text]
        for index, segment in enumerate(segments):
            wrapped_lines.append(f"{indent}{segment}" if indent and index > 0 else segment)

    page_line_limit = 40
    pages = [
        wrapped_lines[index : index + page_line_limit]
        for index in range(0, len(wrapped_lines), page_line_limit)
    ] or [[]]

    objects: list[bytes] = []
    objects.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj")

    page_object_numbers = []
    content_object_numbers = []
    next_object_number = 3

    for _ in pages:
        page_object_numbers.append(next_object_number)
        next_object_number += 1
        content_object_numbers.append(next_object_number)
        next_object_number += 1

    kids_value = " ".join(f"{page_no} 0 R" for page_no in page_object_numbers)
    objects.append(f"2 0 obj << /Type /Pages /Kids [{kids_value}] /Count {len(pages)} >> endobj".encode("latin-1"))

    for page_index, page_lines in enumerate(pages):
        page_no = page_object_numbers[page_index]
        content_no = content_object_numbers[page_index]

        content_lines = ["BT", "/F1 11 Tf", "54 736 Td", "16 TL"]
        first = True

        for line in page_lines:
            text = escape_pdf_text(line)
            if first:
                content_lines.append(f"({text}) Tj")
                first = False
            else:
                content_lines.append("T*")
                content_lines.append(f"({text}) Tj")

        content_lines.append("ET")
        content_stream = "\n".join(content_lines).encode("latin-1", errors="replace")

        objects.append(
            (
                f"{page_no} 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Contents {content_no} 0 R /Resources << /Font << /F1 {next_object_number} 0 R >> >> >> endobj"
            ).encode("latin-1")
        )
        objects.append(
            f"{content_no} 0 obj << /Length {len(content_stream)} >> stream\n".encode("latin-1")
            + content_stream
            + b"\nendstream endobj"
        )

    font_object_number = next_object_number
    objects.append(b"")
    objects[-1] = f"{font_object_number} 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj".encode(
        "latin-1"
    )

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
        load_saved_run_button = st.button("Load One Saved Run")

        st.subheader("Compare Saved Runs")
        comparison_options = [run["run_id"] for run in saved_runs]
        loaded_run_id = st.session_state.get("loaded_run_id")
        current_run_index = (
            comparison_options.index(loaded_run_id)
            if loaded_run_id in comparison_options
            else 0
        )
        comparison_default_index = 1 if len(comparison_options) > 1 else 0

        selected_current_run_id = st.selectbox(
            "Current Run",
            options=comparison_options,
            index=current_run_index,
            format_func=lambda run_id: run_labels.get(run_id, run_id),
            key="comparison_current_run_id",
        )
        selected_comparison_run_id = st.selectbox(
            "Comparison Run",
            options=comparison_options,
            index=comparison_default_index,
            format_func=lambda run_id: run_labels.get(run_id, run_id),
            key="comparison_previous_run_id",
        )
        compare_saved_runs_button = st.button("Compare Two Saved Runs")
    else:
        st.info("No saved runs yet.")
        selected_saved_run_id = None
        load_saved_run_button = False
        selected_current_run_id = None
        selected_comparison_run_id = None
        compare_saved_runs_button = False

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
        "selected_current_run_id": selected_current_run_id,
        "selected_comparison_run_id": selected_comparison_run_id,
        "compare_saved_runs_button": compare_saved_runs_button,
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
                "opportunity_type": "Social Format Opportunity",
                "target": best_post_type,
                "supporting_data": f"Best Post Type: {best_post_type}",
                "why_it_matters": (
                    "This format is currently producing the strongest results and is the best candidate to scale with repeatable hooks and topics."
                ),
                "recommended_action": (
                    "Create a repeatable content series in this format using the strongest topic angle, a sharper opening hook, and a clearer conversion CTA."
                ),
                "why_recommendation_works": (
                    "This should work because the format already has proof of traction, so scaling the same structure is a lower-risk way to grow reach and engagement."
                ),
                "priority": "High",
            }
        )

    if worst_post_type and worst_post_type != "Not available":
        cards.append(
            {
                "title": f"Improve or reduce {worst_post_type}",
                "opportunity_type": "Social Performance Gap",
                "target": worst_post_type,
                "supporting_data": f"Worst Post Type: {worst_post_type}",
                "why_it_matters": (
                    "This format is currently the weakest, which suggests it may need stronger hooks, clearer structure, or less overall emphasis."
                ),
                "recommended_action": (
                    "Test one stronger hook, one clearer CTA, and one more patient-specific framing change before deciding whether to reduce this format."
                ),
                "why_recommendation_works": (
                    "This should work because weak formats often underperform due to framing and structure, not just the format itself."
                ),
                "priority": "Medium",
            }
        )

    if top_topics:
        cards.append(
            {
                "title": f"Scale content around {top_topics[0]}",
                "opportunity_type": "Social Topic Opportunity",
                "target": top_topics[0],
                "supporting_data": f"Top Topic: {top_topics[0]}",
                "why_it_matters": (
                    "This topic is currently resonating most and should be turned into a repeatable content theme across multiple posts."
                ),
                "recommended_action": (
                    "Build a short content series around this topic with one educational post, one trust-building post, and one CTA-led post."
                ),
                "why_recommendation_works": (
                    "This should work because repeating a proven topic across several angles helps compound reach while reinforcing a winning message."
                ),
                "priority": "High",
            }
        )

    if weak_topics:
        cards.append(
            {
                "title": f"Fix or replace weak topic: {weak_topics[0]}",
                "opportunity_type": "Weak Topic Opportunity",
                "target": weak_topics[0],
                "supporting_data": f"Weak Topic: {weak_topics[0]}",
                "why_it_matters": (
                    "This topic appears to be underperforming and may not be connecting with the audience in its current angle or format."
                ),
                "recommended_action": (
                    "Re-test the topic with a stronger hook and a different format first, then reduce emphasis if it still fails to earn saves, follows, or engagement."
                ),
                "why_recommendation_works": (
                    "This should work because a topic can be weak due to presentation, and one sharper framing test can reveal whether it is still worth scaling."
                ),
                "priority": "Medium",
            }
        )

    if what_drives_saves and what_drives_saves != "Not available":
        cards.append(
            {
                "title": "Turn save-worthy content into conversion content",
                "opportunity_type": "Social Conversion Opportunity",
                "target": "Save-driving content",
                "supporting_data": what_drives_saves,
                "why_it_matters": (
                    "Content that earns saves already shows strong audience value, but it needs a clearer next-step path to drive business outcomes."
                ),
                "recommended_action": (
                    "Add a clearer next-step prompt such as booking, quiz, or consultation guidance so high-value content also moves users toward action."
                ),
                "why_recommendation_works": (
                    "This should work because the content already has strong audience value, so improving conversion guidance is usually more effective than replacing the topic."
                ),
                "priority": "High",
            }
        )

    if what_drives_follows and what_drives_follows != "Not available":
        cards.append(
            {
                "title": "Replicate follow-driving content",
                "opportunity_type": "Social Growth Opportunity",
                "target": "Follow-driving content",
                "supporting_data": what_drives_follows,
                "why_it_matters": (
                    "This content pattern is strongest for audience growth and can be scaled into a repeatable acquisition engine."
                ),
                "recommended_action": (
                    "Create 3-5 new posts using the same hook pattern, topic framing, and CTA style as the strongest follow-driving examples."
                ),
                "why_recommendation_works": (
                    "This should work because the strongest follower-growth pattern has already proven what attracts the audience you want to build."
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
                "opportunity_type": "Social Performance Gap",
                "target": "Full-funnel content performance",
                "supporting_data": issue_text,
                "why_it_matters": (
                    "This imbalance suggests the content is not yet performing strongly across the full funnel from reach to engagement to conversion."
                ),
                "recommended_action": recommended_action,
                "why_recommendation_works": (
                    "This should work because fixing the weakest stage of the funnel usually creates the clearest performance lift without needing to rebuild everything."
                ),
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


def condense_chat_text(text: str, max_sentences: int = 2) -> str:
    """Trim chat copy into a short presentation-friendly summary."""
    normalized = str(text or "").replace(" | ", ". ").replace("\n", " ").strip()
    if not normalized:
        return "Not enough grounded data is available yet."

    sentence_parts = [
        part.strip(" -")
        for part in re.split(r"(?<=[.!?])\s+", normalized)
        if part.strip(" -")
    ]
    if sentence_parts:
        return " ".join(sentence_parts[:max_sentences]).strip()

    comma_parts = [part.strip() for part in normalized.split(",") if part.strip()]
    if comma_parts:
        return ". ".join(comma_parts[:max_sentences]).strip() + "."

    return normalized


def build_chat_next_actions(*items: str, max_items: int = 3) -> str:
    """Create a short bullet list for the chat Next Action section."""
    cleaned_items = []
    for item in items:
        cleaned = str(item or "").strip().lstrip("-").strip()
        if cleaned:
            cleaned_items.append(cleaned)
        if len(cleaned_items) == max_items:
            break

    if not cleaned_items:
        cleaned_items = ["Ask a more specific follow-up so I can recommend the next move with more precision."]

    return "\n".join(f"- {item}" for item in cleaned_items[:max_items])


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
            next_action_text = build_chat_next_actions(
                "Go to Data Sources.",
                "Upload the Meta Content Export CSV.",
                "Rerun the workflow, then ask the same question again.",
            )
        elif "conversion" in message_lower and "low" in message_lower:
            issue = social_balance_problems[0] if social_balance_problems else "The current social funnel is not converting as strongly as engagement suggests."
            insight_text = condense_chat_text(issue)
            why_text = condense_chat_text("Your loaded social data suggests interest exists, but the path from attention to follow, quiz, or booking action is still too weak.")
            recommendation_text = condense_chat_text("Strengthen conversion prompts on the formats and topics already earning attention, especially by adding clearer next-step guidance, quiz prompts, or booking language.")
            next_action_text = build_chat_next_actions(
                "Start with the best-performing format.",
                "Add one direct CTA variant to the next 3 posts.",
                "Track whether follows or conversions improve after the CTA change.",
            )
            additional_ideas = [
                "Turn save-worthy content into CTA-led variants with a clearer follow or booking prompt.",
                "Use the strongest follow-driving hook again, but change the close so it pushes one clear next step.",
            ]
        elif "engagement" in message_lower and "low" in message_lower:
            issue = next((item for item in social_balance_problems if "low engagement" in item.lower()), "")
            insight_text = condense_chat_text(issue or f"{social_worst_format} is the weakest current social format.")
            why_text = condense_chat_text("Low engagement usually means the post is getting seen but the opening, framing, or payoff is not strong enough to hold attention.")
            recommendation_text = condense_chat_text("Improve the first frame and hook on the weakest format before increasing volume.")
            next_action_text = build_chat_next_actions(
                "Rewrite the next 3 low-performing posts.",
                "Make the first line or first frame create a sharper problem-solution payoff.",
                "Retest the same topic before replacing it.",
            )
            additional_ideas = [
                f"Test the strongest topic, {social_top_topic}, in a more attention-grabbing format.",
                "Repurpose a post that already drove saves into a shorter, stronger opening sequence.",
            ]
        elif any(term in message_lower for term in ["what should i post", "content works best", "what content works best"]):
            insight_text = condense_chat_text(f"{social_best_format} is the strongest current social format, and {social_top_topic} is the strongest topic theme in the loaded run.")
            why_text = condense_chat_text("The fastest social growth usually comes from scaling what is already producing saves, follows, or strong engagement, not from inventing a new content direction from scratch.")
            recommendation_text = condense_chat_text(f"Create more {social_best_format} content around {social_top_topic}, using the same style of hook that is already driving saves or follows.")
            next_action_text = build_chat_next_actions(
                "Build a 3-post content series this week.",
                "Use your strongest topic and strongest format.",
                "Keep the CTA consistent so performance is easier to compare.",
            )
            additional_ideas = [
                "Create one educational variation, one trust-building variation, and one CTA-led variation of the same topic.",
                "Turn the top save-driving pattern into a Reel and a Carousel to test format expansion.",
            ]
        else:
            insight_text = condense_chat_text(f"Your current social signals point to {social_best_format} as the strongest format and {social_top_topic} as the strongest topic, while {social_weak_topic} is lagging.")
            why_text = condense_chat_text("That gives a clear performance split between what should be scaled and what should be fixed or reduced.")
            recommendation_text = condense_chat_text("Scale the strongest format-topic combination first instead of spreading effort evenly across all content types.")
            next_action_text = build_chat_next_actions(
                "Use the next content cycle to prioritize one winning format.",
                "Build around one winning topic.",
                "Pause or reframe the weakest topic until the stronger pattern is established.",
            )
            additional_ideas = [
                "Reduce effort on the weakest topic until a stronger hook or format test is ready.",
                "Replicate the strongest follow-driving pattern with a sharper patient-acquisition CTA.",
            ]
    elif any(term in message_lower for term in ["top opportunity", "optimize first", "seo", "website", "query", "page", "traffic"]):
        if not insight:
            insight_text = "Website and SEO data is missing from the current run."
            why_text = "Without GA4, GSC, or SEMrush inputs, I cannot identify the highest-leverage website opportunity."
            recommendation_text = "Load a run with website data so the recommendation can be tied to actual search and traffic performance."
            next_action_text = build_chat_next_actions("Upload GA4, GSC, or SEMrush data and rerun the workflow.")
        else:
            top_action = priority_actions[0] if priority_actions else {}
            insight_text = condense_chat_text(
                f"The clearest website opportunity is {top_query}, with {primary_page} as the primary page to optimize first."
            )
            why_text = condense_chat_text(
                f"The loaded run shows existing visibility around {top_query} and a clear page-level focus, which means you can improve growth faster by concentrating effort instead of spreading it across multiple pages."
            )
            recommendation_text = (
                top_action.get("action")
                or f"Optimize {primary_page} first around {top_query}, tightening page structure, SERP messaging, and conversion guidance."
            )
            next_action_text = build_chat_next_actions(
                f"Start with {primary_page}.",
                f"Align the title, H1, and FAQ content to {top_query}.",
                "Tighten the CTA flow before expanding to secondary pages.",
            )
            additional_ideas = [
                f"Use {top_source} landing-page traffic as a second optimization layer so the page converts better once rankings improve.",
                "Support the primary page with one related topic asset to strengthen internal linking and topical depth.",
            ]
    elif any(term in message_lower for term in ["what should i do", "give me recommendations", "strategy", "mixed", "growth"]):
        website_action = priority_actions[0] if priority_actions else {}
        social_recommendations = build_social_recommendation_cards(results)
        top_social = social_recommendations[0] if social_recommendations else {}

        insight_text = condense_chat_text(
            f"Your loaded run shows a split opportunity: website growth is centered on {top_query}, while social momentum is strongest in {social_best_format} content."
        )
        why_text = condense_chat_text(
            "That means your next move should not be generic marketing activity. It should be one website action and one content action that both map to the strongest available signals."
        )
        recommendation_text = (
            website_action.get("action")
            or f"Optimize {primary_page} first for {top_query}, then align social content to reinforce the same patient questions and conversion themes."
        )
        next_action_text = build_chat_next_actions(
            f"Optimize {primary_page} first for {top_query}.",
            top_social.get("recommendation")
            or "Use the strongest website topic as the basis for the next social content series.",
            "Review the shared message and CTA across both channels after the next publishing cycle.",
        )
        additional_ideas = [
            "Turn the primary SEO question into a short-form social series that warms up the same patient audience.",
            "Use social save-driving content as a clue for which FAQs should move higher on the main website page.",
        ]
    else:
        insight_text = condense_chat_text(
            f"The strongest current signal is search demand around {top_query}, with {primary_page} as the clearest page to improve first. Social momentum is strongest in {social_best_format} content."
        )
        why_text = condense_chat_text(
            "The loaded run gives enough context to identify one immediate growth move, but broad questions work best when anchored to the clearest visible signal."
        )
        recommendation_text = (
            priority_actions[0].get("action")
            if priority_actions
            else "Start with the clearest loaded website or social signal rather than spreading effort across every channel."
        )
        next_action_text = build_chat_next_actions(
            "Choose one channel priority first: SEO, social, or conversion.",
            "Ask which page or content type should be optimized first.",
            "Use the next follow-up to narrow the recommendation into an execution plan.",
        )
        additional_ideas = [
            "Ask which page to optimize first.",
            "Ask what social content format to scale next.",
        ]

    insight_text = condense_chat_text(insight_text)
    why_text = condense_chat_text(why_text)
    recommendation_text = condense_chat_text(recommendation_text)

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

    target_value = (
        data.get("target")
        or data.get("keyword")
        or data.get("page_url")
        or data.get("topic")
        or "-"
    )
    supporting_parts = []
    if data.get("position"):
        supporting_parts.append(f"Position: {data.get('position', '-')}")
    if data.get("volume") and data.get("volume") != "Not available":
        supporting_parts.append(f"Volume: {data.get('volume', '-')}")
    if data.get("metric_line"):
        supporting_parts.append(str(data.get("metric_line", "-")))
    if data.get("supporting_data"):
        supporting_parts.append(str(data.get("supporting_data", "-")))
    if data.get("url") and data.get("url") != "Not available":
        url = str(data.get("url", "#"))
        supporting_parts.append(f'URL: <a href="{url}" target="_blank">{url}</a>')

    if data.get("intent_type") or data.get("opportunity_type") or data.get("gap_type"):
        tag_parts = [part for part in [data.get("intent_type"), data.get("opportunity_type"), data.get("gap_type")] if part]
        supporting_parts.append(f"Signals: {' | '.join(tag_parts)}")

    body_parts = [
        f"<strong>Opportunity Type:</strong> {data.get('opportunity_type', title)}",
        f"<strong>Target:</strong> {target_value}",
    ]
    if supporting_parts:
        body_parts.append(f"<strong>Supporting Data:</strong> {' | '.join(supporting_parts)}")
    body_parts.append(f"<strong>Why this is an opportunity:</strong> {data.get('why_it_matters', data.get('reason', ''))}")
    body_parts.append(f"<strong>Best Recommendation:</strong> {data.get('recommended_action', data.get('action', ''))}")
    if data.get("why_recommendation_works"):
        body_parts.append(f"<strong>Why it should work:</strong> {data.get('why_recommendation_works', '')}")

    body_html = "<br><br>".join(body_parts)

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

    insight = results.get("insight", {})
    strategy = results.get("strategy", {}).get("strategy", {})
    combined = results.get("data_intake", {}).get("summary", {}).get("combined", {})
    semrush_positions_data = results.get("semrush_positions_data")
    top_query = get_first_value(insight.get("high_impression_low_click", []), "query")
    primary_page = (
        str(strategy.get("primary_page", "")).strip()
        or get_first_value(combined.get("top_pages", []), "page_title")
    )
    page_label = primary_page if primary_page and primary_page != "Not available" else "priority landing page"

    if category in {"seo", "seo_keyword_strategy"}:
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
                "Match the format to the job: education for saves, authority for trust, and sharper CTA-led posts for action.",
            ],
            "post_angles": [
                f"Turn {base_topic} into a quick myth-vs-fact post.",
                f"Use {base_topic} as a provider-answer format with one clear next step.",
                "Repurpose the strongest post into a testimonial, FAQ, and checklist angle.",
            ],
            "captions": [
                "Short caption with a problem-first hook, one useful insight, and a clear CTA.",
                "Educational caption that answers one specific patient question before inviting the next step.",
                "Caption variation that uses trust language and a softer conversion prompt.",
            ],
            "hook_cta_examples": [
                "Test a stronger first-line hook that names the patient problem immediately.",
                "Pair the winning content angle with a clearer CTA such as booking, quiz, or consultation.",
                "Use the highest-performing post format to repeat the strongest hook in a shorter, sharper version.",
            ],
            "repurposing": [
                "Turn the best-performing post into a Reel, carousel, and static image variation.",
                "Reuse the same topic as a short FAQ clip, a provider quote post, and a CTA-focused version.",
                "Republish the strongest idea with a new hook before creating entirely new themes.",
            ],
            "variations": variations[:5],
        }

    next_steps = []
    if top_query != "Not available":
        next_steps.append(f"Prioritize the strongest visible opportunity around {top_query}.")
    if page_label and page_label != "priority landing page":
        next_steps.append(f"Use {page_label} as the first page to review and strengthen.")
    next_steps.extend(
        [
            "Match the next action to the highest-signal data source instead of spreading effort broadly.",
            "Choose one page or channel change to ship first, then measure the response before expanding.",
        ]
    )

    return {
        "type": "general",
        "button_label": "View strategic next steps",
        "headline": "Strategic Take Action",
        "next_steps": next_steps[:4],
    }


def render_take_action_block(payload: dict, unique_key: str) -> None:
    """Render a take-action drill-down block beneath a recommendation."""
    st.markdown('<div class="take-action-panel">', unsafe_allow_html=True)
    icon_map = {
        "seo": "↗",
        "aeo": "?",
        "geo": "◎",
        "ux_conversion": "UX",
        "content_expansion": "+",
        "social": "✦",
        "general": "→",
    }
    icon = icon_map.get(str(payload.get("type", "")), "✦")
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

        keyword_variations = payload.get("keyword_variations", [])
        if keyword_variations:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Suggested Keyword Variations</div>', unsafe_allow_html=True)
            variation_items = "".join(f"<li>{item}</li>" for item in keyword_variations)
            st.markdown(f'<ul class="take-action-list">{variation_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        meta_description_suggestions = payload.get("meta_description_suggestions", [])
        if meta_description_suggestions:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Meta Description Suggestions</div>', unsafe_allow_html=True)
            meta_items = "".join(f"<li>{item}</li>" for item in meta_description_suggestions)
            st.markdown(f'<ul class="take-action-list">{meta_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        internal_links = payload.get("internal_links", [])
        if internal_links:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Internal Linking Ideas</div>', unsafe_allow_html=True)
            link_items = "".join(f"<li>{item}</li>" for item in internal_links)
            st.markdown(f'<ul class="take-action-list">{link_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    elif payload.get("type") == "aeo":
        faq_ideas = payload.get("faq_ideas", [])
        if faq_ideas:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">FAQ Ideas</div>', unsafe_allow_html=True)
            faq_items = "".join(f"<li>{item}</li>" for item in faq_ideas)
            st.markdown(f'<ul class="take-action-list">{faq_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        answer_blocks = payload.get("answer_blocks", [])
        if answer_blocks:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Answer Block Suggestions</div>', unsafe_allow_html=True)
            answer_items = "".join(f"<li>{item}</li>" for item in answer_blocks)
            st.markdown(f'<ul class="take-action-list">{answer_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        heading_ideas = payload.get("heading_ideas", [])
        if heading_ideas:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Question-Based Heading Ideas</div>', unsafe_allow_html=True)
            heading_items = "".join(f"<li>{item}</li>" for item in heading_ideas)
            st.markdown(f'<ul class="take-action-list">{heading_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        paragraph_rewrites = payload.get("paragraph_rewrites", [])
        if paragraph_rewrites:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Answer-First Paragraph Rewrites</div>', unsafe_allow_html=True)
            rewrite_items = "".join(f"<li>{item}</li>" for item in paragraph_rewrites)
            st.markdown(f'<ul class="take-action-list">{rewrite_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        schema_recommendations = payload.get("schema_recommendations", [])
        if schema_recommendations:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Schema / Citation Recommendations</div>', unsafe_allow_html=True)
            schema_items = "".join(f"<li>{item}</li>" for item in schema_recommendations)
            st.markdown(f'<ul class="take-action-list">{schema_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        structure_examples = payload.get("structure_examples", [])
        if structure_examples:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Featured Snippet Formatting</div>', unsafe_allow_html=True)
            structure_items = "".join(f"<li>{item}</li>" for item in structure_examples)
            st.markdown(f'<ul class="take-action-list">{structure_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        ai_overview_optimizations = payload.get("ai_overview_optimizations", [])
        if ai_overview_optimizations:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">AI Overview Optimization</div>', unsafe_allow_html=True)
            overview_items = "".join(f"<li>{item}</li>" for item in ai_overview_optimizations)
            st.markdown(f'<ul class="take-action-list">{overview_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    elif payload.get("type") == "geo":
        entity_consistency_checklist = payload.get("entity_consistency_checklist", [])
        if entity_consistency_checklist:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Entity Consistency Checklist</div>', unsafe_allow_html=True)
            entity_items = "".join(f"<li>{item}</li>" for item in entity_consistency_checklist)
            st.markdown(f'<ul class="take-action-list">{entity_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        local_keyword_targets = payload.get("local_keyword_targets", [])
        if local_keyword_targets:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Local Keyword Targets</div>', unsafe_allow_html=True)
            keyword_items = "".join(f"<li>{item}</li>" for item in local_keyword_targets)
            st.markdown(f'<ul class="take-action-list">{keyword_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        city_service_page_opportunities = payload.get("city_service_page_opportunities", [])
        if city_service_page_opportunities:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">City / Service Page Opportunities</div>', unsafe_allow_html=True)
            page_items = "".join(f"<li>{item}</li>" for item in city_service_page_opportunities)
            st.markdown(f'<ul class="take-action-list">{page_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        gbp_improvements = payload.get("gbp_improvements", [])
        if gbp_improvements:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Google Business Profile Improvements</div>', unsafe_allow_html=True)
            gbp_items = "".join(f"<li>{item}</li>" for item in gbp_improvements)
            st.markdown(f'<ul class="take-action-list">{gbp_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        local_trust_signals = payload.get("local_trust_signals", [])
        if local_trust_signals:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Local Trust Signals</div>', unsafe_allow_html=True)
            trust_items = "".join(f"<li>{item}</li>" for item in local_trust_signals)
            st.markdown(f'<ul class="take-action-list">{trust_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        citation_review_recommendations = payload.get("citation_review_recommendations", [])
        if citation_review_recommendations:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Citation / Review Recommendations</div>', unsafe_allow_html=True)
            citation_items = "".join(f"<li>{item}</li>" for item in citation_review_recommendations)
            st.markdown(f'<ul class="take-action-list">{citation_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        quotable_insight_suggestions = payload.get("quotable_insight_suggestions", [])
        if quotable_insight_suggestions:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Quotable Insight Suggestions</div>', unsafe_allow_html=True)
            quote_items = "".join(f"<li>{item}</li>" for item in quotable_insight_suggestions)
            st.markdown(f'<ul class="take-action-list">{quote_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        external_trust_signal_opportunities = payload.get("external_trust_signal_opportunities", [])
        if external_trust_signal_opportunities:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">External Trust Signal Opportunities</div>', unsafe_allow_html=True)
            trust_signal_items = "".join(f"<li>{item}</li>" for item in external_trust_signal_opportunities)
            st.markdown(f'<ul class="take-action-list">{trust_signal_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    elif payload.get("type") == "ux_conversion":
        cta_rewrites = payload.get("cta_rewrites", [])
        if cta_rewrites:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">CTA Rewrites</div>', unsafe_allow_html=True)
            cta_items = "".join(f"<li>{item}</li>" for item in cta_rewrites)
            st.markdown(f'<ul class="take-action-list">{cta_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        landing_page_clarity = payload.get("landing_page_clarity", [])
        if landing_page_clarity:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Landing Page Clarity</div>', unsafe_allow_html=True)
            clarity_items = "".join(f"<li>{item}</li>" for item in landing_page_clarity)
            st.markdown(f'<ul class="take-action-list">{clarity_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        conversion_suggestions = payload.get("conversion_suggestions", [])
        if conversion_suggestions:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">CTA / Trust / Conversion Suggestions</div>', unsafe_allow_html=True)
            suggestion_items = "".join(f"<li>{item}</li>" for item in conversion_suggestions)
            st.markdown(f'<ul class="take-action-list">{suggestion_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        page_structure_fixes = payload.get("page_structure_fixes", [])
        if page_structure_fixes:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Page Structure Fixes</div>', unsafe_allow_html=True)
            structure_items = "".join(f"<li>{item}</li>" for item in page_structure_fixes)
            st.markdown(f'<ul class="take-action-list">{structure_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        friction_reduction = payload.get("friction_reduction", [])
        if friction_reduction:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Friction Reduction</div>', unsafe_allow_html=True)
            friction_items = "".join(f"<li>{item}</li>" for item in friction_reduction)
            st.markdown(f'<ul class="take-action-list">{friction_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        trust_improvements = payload.get("trust_improvements", [])
        if trust_improvements:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Trust Improvements</div>', unsafe_allow_html=True)
            trust_items = "".join(f"<li>{item}</li>" for item in trust_improvements)
            st.markdown(f'<ul class="take-action-list">{trust_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        checklist = payload.get("checklist", [])
        if checklist:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Landing Page Improvement Checklist</div>', unsafe_allow_html=True)
            checklist_items = "".join(f"<li>{item}</li>" for item in checklist)
            st.markdown(f'<ul class="take-action-list">{checklist_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        ux_recommendations = payload.get("ux_recommendations", [])
        if ux_recommendations:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">UX Recommendations</div>', unsafe_allow_html=True)
            ux_items = "".join(f"<li>{item}</li>" for item in ux_recommendations)
            st.markdown(f'<ul class="take-action-list">{ux_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    elif payload.get("type") == "content_expansion":
        supporting_content_ideas = payload.get("supporting_content_ideas", [])
        if supporting_content_ideas:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Supporting Content Ideas</div>', unsafe_allow_html=True)
            idea_items = "".join(f"<li>{item}</li>" for item in supporting_content_ideas)
            st.markdown(f'<ul class="take-action-list">{idea_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        new_page_recommendations = payload.get("new_page_recommendations", [])
        if new_page_recommendations:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">New Page / Blog Recommendations</div>', unsafe_allow_html=True)
            page_items = "".join(f"<li>{item}</li>" for item in new_page_recommendations)
            st.markdown(f'<ul class="take-action-list">{page_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        topic_cluster_suggestions = payload.get("topic_cluster_suggestions", [])
        if topic_cluster_suggestions:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Topic Cluster Expansion Suggestions</div>', unsafe_allow_html=True)
            cluster_items = "".join(f"<li>{item}</li>" for item in topic_cluster_suggestions)
            st.markdown(f'<ul class="take-action-list">{cluster_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    elif payload.get("type") == "social":
        hook_ideas = payload.get("hook_ideas", [])
        if hook_ideas:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Hook Ideas</div>', unsafe_allow_html=True)
            hook_idea_items = "".join(f"<li>{item}</li>" for item in hook_ideas)
            st.markdown(f'<ul class="take-action-list">{hook_idea_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        engagement_improvements = payload.get("engagement_improvements", [])
        if engagement_improvements:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Engagement Improvements</div>', unsafe_allow_html=True)
            engagement_items = "".join(f"<li>{item}</li>" for item in engagement_improvements)
            st.markdown(f'<ul class="take-action-list">{engagement_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        retention_strategy = payload.get("retention_strategy", [])
        if retention_strategy:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Retention Strategy</div>', unsafe_allow_html=True)
            retention_items = "".join(f"<li>{item}</li>" for item in retention_strategy)
            st.markdown(f'<ul class="take-action-list">{retention_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        format_recommendations = payload.get("format_recommendations", [])
        if format_recommendations:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Format Recommendations</div>', unsafe_allow_html=True)
            format_items = "".join(f"<li>{item}</li>" for item in format_recommendations)
            st.markdown(f'<ul class="take-action-list">{format_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        post_angles = payload.get("post_angles", [])
        if post_angles:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Post Angles</div>', unsafe_allow_html=True)
            angle_items = "".join(f"<li>{item}</li>" for item in post_angles)
            st.markdown(f'<ul class="take-action-list">{angle_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        captions = payload.get("captions", [])
        if captions:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Caption Ideas</div>', unsafe_allow_html=True)
            caption_items = "".join(f"<li>{item}</li>" for item in captions)
            st.markdown(f'<ul class="take-action-list">{caption_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

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

        hook_cta_examples = payload.get("hook_cta_examples", [])
        if hook_cta_examples:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Hook / CTA Examples</div>', unsafe_allow_html=True)
            hook_items = "".join(f"<li>{item}</li>" for item in hook_cta_examples)
            st.markdown(f'<ul class="take-action-list">{hook_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        variations = payload.get("variations", [])
        if variations:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">New Variations</div>', unsafe_allow_html=True)
            variation_items = "".join(f"<li>{variation}</li>" for variation in variations)
            st.markdown(f'<ul class="take-action-list">{variation_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        repurposing = payload.get("repurposing", [])
        if repurposing:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Repurposing Ideas</div>', unsafe_allow_html=True)
            repurpose_items = "".join(f"<li>{item}</li>" for item in repurposing)
            st.markdown(f'<ul class="take-action-list">{repurpose_items}</ul>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
    elif payload.get("type") == "general":
        next_steps = payload.get("next_steps", [])
        if next_steps:
            st.markdown('<div class="take-action-section">', unsafe_allow_html=True)
            st.markdown('<div class="take-action-section-title">Strategic Next Steps</div>', unsafe_allow_html=True)
            next_step_items = "".join(f"<li>{item}</li>" for item in next_steps)
            st.markdown(f'<ul class="take-action-list">{next_step_items}</ul>', unsafe_allow_html=True)
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

    what_next_cards = build_combined_what_next_cards(results)
    priority_class_map = {
        "High": "priority-high-pill",
        "Medium": "priority-medium-pill",
        "Low": "priority-low-pill",
    }

    st.subheader("Recommendations")
    if generated_recommendations:
        for index, recommendation in enumerate(generated_recommendations):
            display_priority = str(recommendation.get("priority", "Medium")).strip().title()
            pill_class = priority_class_map.get(display_priority, "priority-medium-pill")
            action_type = str(recommendation.get("action_type", "")).strip().lower()
            opportunity_score = round(to_comparison_number(recommendation.get("opportunity_score")) or 0)
            business_impact_score = round(to_comparison_number(recommendation.get("business_impact_score")) or 0)
            confidence_score = round(to_comparison_number(recommendation.get("confidence_score")) or 0)
            recommendation_card = {
                "category": action_type,
                "action_type": action_type,
                "issue": str(recommendation.get("insight", "") or "").strip(),
                "recommendation": str(recommendation.get("recommendation", "") or "").strip(),
                "why_it_matters": str(recommendation.get("why_it_matters", "") or "").strip(),
                "priority": display_priority,
            }

            st.markdown(
                f"""
                <div class="recommendation-card">
                    <div class="recommendation-card-top">
                        <div class="recommendation-category" style="font-size: 1.08rem;">
                            {recommendation.get("title", "Recommendation")}
                        </div>
                        <div class="{pill_class}">{display_priority} Priority</div>
                    </div>
                    <div class="recommendation-body">
                        <strong>Opportunity Score:</strong> {opportunity_score}/100
                        &nbsp;&nbsp;|&nbsp;&nbsp;
                        <strong>Business Impact:</strong> {business_impact_score}/100
                        &nbsp;&nbsp;|&nbsp;&nbsp;
                        <strong>Confidence:</strong> {confidence_score}/100
                        <br><br>
                        <strong>Insight:</strong><br>
                        {recommendation_card["issue"]}
                        <br><br>
                        <strong>Why it matters:</strong><br>
                        {recommendation_card["why_it_matters"]}
                        <br><br>
                        <strong>Recommendation:</strong><br>
                        {recommendation_card["recommendation"]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            render_recommendation_take_action_component(
                recommendation_card,
                results,
                f"generated_{action_type or 'rule'}_{index}",
                get_first_value_fn=get_first_value,
                build_semrush_opportunity_cards_fn=build_semrush_opportunity_cards,
                humanize_social_topic_fn=humanize_social_topic,
            )
    else:
        st.info("No recommendations available based on current data.")

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

    def format_assistant_response(content: str) -> str:
        section_order = ["INSIGHT", "WHY IT MATTERS", "RECOMMENDATION", "NEXT ACTION"]
        normalized_content = str(content).replace("\r\n", "\n")
        sections: dict[str, str] = {}

        for index, section in enumerate(section_order):
            marker = section
            start = normalized_content.find(marker)
            if start == -1:
                continue

            body_start = start + len(marker)
            next_positions = [
                normalized_content.find(next_section, body_start)
                for next_section in section_order[index + 1 :]
                if normalized_content.find(next_section, body_start) != -1
            ]
            end = min(next_positions) if next_positions else len(normalized_content)
            section_text = normalized_content[body_start:end].strip(" \n:")
            sections[section] = section_text.strip()

        if sections:
            html_sections = []
            for section in section_order:
                if section not in sections:
                    continue
                section_class = "chat-response-section"
                body_class = "chat-response-text"
                if section == "NEXT ACTION":
                    body_class = "chat-response-text chat-response-next"
                section_body = sections[section]
                if section == "NEXT ACTION":
                    bullet_lines = [
                        line.strip()[2:].strip()
                        for line in section_body.splitlines()
                        if line.strip().startswith("- ")
                    ]
                    if bullet_lines:
                        section_body = "<ul>" + "".join(f"<li>{item}</li>" for item in bullet_lines[:3]) + "</ul>"
                    else:
                        section_body = f"<ul><li>{section_body.strip()}</li></ul>"
                else:
                    section_body = section_body.replace("\n", "<br>")
                html_sections.append(
                    f"""
                    <div class="{section_class}">
                        <div class="chat-response-title">{section}</div>
                        <div class="{body_class}">{section_body}</div>
                    </div>
                    """
                )
            return "".join(html_sections)

        return f'<div class="chat-message-body">{content}</div>'

    prompt_columns = st.columns(2)
    for index, prompt in enumerate(suggested_prompts):
        with prompt_columns[index % 2]:
            if st.button(prompt, key=f"chat_page_prompt_chip_{index}"):
                submit_chat_message(prompt)

    if not results:
        st.info("Load a saved run or upload data first, then ask the AI agent about your marketing performance.")

    for message in st.session_state["ai_chat_messages"]:
        with st.chat_message(message["role"]):
            role = str(message["role"])
            if role == "assistant":
                st.markdown(
                    f"""
                    <div class="chat-message-wrap">
                        <div class="chat-message-card chat-message-assistant">
                            <div class="chat-message-label">AI Marketing Strategist</div>
                            {format_assistant_response(str(message["content"]))}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div class="chat-message-wrap">
                        <div class="chat-message-card chat-message-user">
                            <div class="chat-message-label">You</div>
                            <div class="chat-message-body">{message["content"]}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

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


decision_rules_data = load_decision_rules_service(DISTILLED_DIR)
decision_rules = decision_rules_data.get("rules", [])
current_results_for_rules = st.session_state.get("results", {})
query_analysis_data = (
    st.session_state.get("query_analysis", [])
    or current_results_for_rules.get("insight", {}).get("query_analysis", [])
)
top_query = query_analysis_data[0] if query_analysis_data else {}
ga4_page_metrics = (
    current_results_for_rules
    .get("data_intake", {})
    .get("summary", {})
    .get("ga4_pages", {})
    .get("key_metrics", {})
)
ga4_pages_for_rules = load_saved_ga4_pages_dataframe(st.session_state.get("loaded_run_id", ""))

if not ga4_pages_for_rules.empty:
    rule_sessions = (
        to_comparison_number(ga4_pages_for_rules["sessions"].fillna(0).sum())
        if "sessions" in ga4_pages_for_rules.columns
        else to_comparison_number(ga4_page_metrics.get("sessions"))
    )
    rule_engagement_rate = (
        to_comparison_number(ga4_pages_for_rules["engagement_rate"].fillna(0).mean())
        if "engagement_rate" in ga4_pages_for_rules.columns
        else to_comparison_number(ga4_page_metrics.get("engagement_rate"))
    )
    rule_conversions = (
        to_comparison_number(ga4_pages_for_rules["conversions"].fillna(0).sum())
        if "conversions" in ga4_pages_for_rules.columns
        else 0
    )
else:
    rule_sessions = to_comparison_number(ga4_page_metrics.get("sessions"))
    rule_engagement_rate = to_comparison_number(ga4_page_metrics.get("engagement_rate"))
    rule_conversions = to_comparison_number(ga4_page_metrics.get("conversions")) or 0

sample_data = {
    "impressions": top_query.get("impressions"),
    "ctr": top_query.get("ctr"),
    "position": top_query.get("position"),
    "sessions": rule_sessions,
    "engagement_rate": rule_engagement_rate,
    "conversions": rule_conversions,
}

triggered_rules, generated_recommendations = evaluate_decision_rules(decision_rules, sample_data)


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

    if st.sidebar.checkbox("Debug decision rules"):
        st.sidebar.write("Decision rules loaded:", len(decision_rules))
        st.sidebar.write("Decision rules version:", decision_rules_data.get("version"))
        st.sidebar.write("Triggered rules:", len(triggered_rules))
        for r in triggered_rules:
            st.sidebar.write(r["title"])


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
            st.session_state["loaded_run_version"] = loaded_run.get("run_version", "legacy")
            st.session_state["comparison_results"] = None
            st.session_state["comparison_mode"] = False
            st.session_state["comparison_current_run_id"] = None
            st.session_state["comparison_run_id"] = None
            current_results = loaded_run["results"]
            st.success(f"Loaded saved run: {loaded_run['run_id']}")
        else:
            st.error("Could not load the selected saved run.")

    if uploaded["compare_saved_runs_button"]:
        current_run_id = uploaded.get("selected_current_run_id")
        comparison_run_id = uploaded.get("selected_comparison_run_id")

        if not current_run_id or not comparison_run_id:
            st.error("Please choose both a current run and a comparison run.")
        elif current_run_id == comparison_run_id:
            st.error("Choose two different saved runs to compare.")
        else:
            loaded_run = load_saved_run(current_run_id)
            comparison_results = compare_saved_runs(current_run_id, comparison_run_id)
            if loaded_run is not None and comparison_results is not None:
                st.session_state["results"] = loaded_run["results"]
                st.session_state["ga4_debug_titles"] = loaded_run["ga4_debug_titles"]
                st.session_state["loaded_run_id"] = loaded_run["run_id"]
                st.session_state["loaded_run_version"] = loaded_run.get("run_version", "legacy")
                st.session_state["comparison_results"] = comparison_results
                st.session_state["comparison_mode"] = True
                st.session_state["comparison_current_run_id"] = current_run_id
                st.session_state["comparison_run_id"] = comparison_run_id
                current_results = loaded_run["results"]
                st.success(f"Comparison ready: {current_run_id} vs {comparison_run_id}")
            else:
                st.error("Could not compare the selected saved runs.")

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

        ga4_pages_data = normalize_ga4_page_title_dataframe(
            parse_uploaded_csv(uploaded["ga4_pages_file"], "GA4_PAGES")
        ) if uploaded["ga4_pages_file"] else None
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

        backfill_ga4_key_metrics(results, ga4_pages_data)
        results["meta_posts_data"] = meta_posts_data
        results["social_insights"] = build_social_insights(meta_posts_data)
        results["run_version"] = "v2"
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
        st.session_state["loaded_run_version"] = "v2"
        st.session_state["comparison_results"] = None
        st.session_state["comparison_mode"] = False
        st.session_state["comparison_current_run_id"] = None
        st.session_state["comparison_run_id"] = None
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
