# AI Marketing Workflow System (MKT 399)

## Overview

This project explores how AI agents can be used to analyze marketing data and improve decision-making.

The system uses real data from Google Analytics and Google Search Console to simulate how marketing workflows can be automated using AI.

---

## Project Goal

The goal of this project is to test how AI can:

* analyze marketing performance
* identify patterns and gaps
* generate strategic recommendations
* create usable marketing content

---

## Key Concepts

### Machine-to-Machine (M2M)

Marketing data from platforms like GA4 and Search Console is exported and fed into the system as structured input.

### Agent-to-Agent (A2A)

Multiple AI agents work together in sequence, where the output of one agent becomes the input for the next.

---

## Workflow

1. Data is pulled from Google Analytics and Google Search Console
2. Data Intake Agent structures the data
3. Insight Agent analyzes performance and identifies trends
4. Strategy Agent generates recommendations
5. Execution Agent creates marketing content
6. Evaluation Agent reviews and scores outputs

---

## Agents

**Data Intake Agent**
Organizes and structures raw marketing data

**Insight Agent**
Identifies trends, gaps, and performance issues

**Strategy Agent**
Generates actionable marketing recommendations

**Execution Agent**
Creates real marketing assets (ex: landing pages, FAQs)

**Evaluation Agent**
Reviews outputs for accuracy and usefulness

---

## Example Output

One of the outputs generated in this project was a fully structured SEO landing page focused on “Botox for Migraines Cost & Savings,” created based on gaps identified in search data.

---

## Tools Used

* ChatGPT (AI agents)
* Codex (automation + system building)
* Google Analytics (GA4)
* Google Search Console
* Streamlit (planned for system interface)
* Python (for automation)

---

## What This Project Demonstrates

This project shows how AI can move beyond simple content generation and be used to:

* automate parts of the marketing workflow
* connect data to strategy and execution
* simulate real-world marketing decision systems

---

## Future Improvements

* Automate data ingestion using APIs
* Build a full interface using Streamlit
* Improve agent collaboration and accuracy
* Expand testing across multiple campaigns

---

## Run The MVP

1. Install dependencies:
   `pip install -r requirements.txt`
2. Start the Streamlit app:
   `streamlit run app.py`
3. Upload your GA4 and GSC CSV files in the app
4. Click **Run Workflow**

You can also run the workflow from the command line with:

`python main.py`

If `data/ga4.csv` and `data/gsc.csv` exist, `main.py` will use them automatically.

Each workflow run is saved to:

`logs/workflow_runs.csv`

---

## Author

Elizabeth McCuan
MKT 399 Independent Study – DePaul University
