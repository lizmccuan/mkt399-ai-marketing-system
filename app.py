"""Simple Streamlit interface for the AI Marketing Workflow System."""

from __future__ import annotations

import json

import streamlit as st

from main import run_workflow
from utils.parser import parse_uploaded_csv


st.set_page_config(page_title="AI Marketing Workflow System", layout="wide")

st.title("AI Marketing Workflow System")
st.write("Upload GA4 and GSC CSV exports, then run the full marketing workflow.")

st.subheader("1. Upload CSV files")
ga4_file = st.file_uploader("Upload GA4 CSV", type="csv")
gsc_file = st.file_uploader("Upload GSC CSV", type="csv")

st.subheader("2. Run the workflow")
run_button = st.button("Run Workflow")

if run_button:
    # Convert uploaded files into cleaned DataFrames the workflow can use.
    ga4_data = parse_uploaded_csv(ga4_file, "GA4")
    gsc_data = parse_uploaded_csv(gsc_file, "GSC")

    # Run the full agent chain from intake through evaluation.
    results = run_workflow(ga4_data=ga4_data, gsc_data=gsc_data)

    st.success("Workflow complete. Results were also saved to logs/workflow_runs.csv.")

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
else:
    st.info("Upload your files and click Run Workflow to start.")
