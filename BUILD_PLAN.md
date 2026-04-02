# AI Marketing Workflow System Build Plan

## Goal
Build a simple local MVP for an AI-driven marketing workflow system.

## Required workflow
1. Upload GA4 and GSC CSV files
2. Parse and clean the data
3. Run Data Intake Agent
4. Run Insight Agent
5. Run Strategy Agent
6. Run Execution Agent
7. Run Evaluation Agent
8. Save a workflow log

## System requirements
- Use Python
- Use Streamlit for the interface
- Keep code modular and easy to explain
- Use the existing folders in this repo
- Show where M2M happens
- Show where A2A happens

## M2M
GA4 and GSC CSV exports are machine-generated inputs that enter the workflow.

## A2A
Each agent passes its output to the next agent:
Data Intake -> Insight -> Strategy -> Execution -> Evaluation
