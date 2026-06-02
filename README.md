# InsightRx

InsightRx is an AI-powered multi-agent marketing intelligence system built with Python and Streamlit.

It is designed to take exported marketing data, structure it, analyze it, apply rule-based reasoning, prioritize opportunities, and turn those findings into strategy, execution-ready outputs, and evaluation. The system also supports saved runs and run-to-run comparison so changes in performance can be reviewed over time.

## Project Summary

InsightRx began as a Streamlit-based marketing workflow prototype and has evolved into a modular multi-agent system.

The current architecture combines:

- structured CSV intake
- rule-based intelligence
- normalized priority scoring
- agent-generated strategy
- execution-ready deliverables
- evaluation scoring
- saved-run comparison and comparison intelligence

The goal is not to replace marketing judgment, but to create a system that helps marketers move more consistently from raw data to prioritized action.

## Core Workflow

InsightRx currently follows this workflow:

`Data Intake → Insight → Decision Rules → Priority Scoring → Strategy → Execution → Evaluation → Comparison Intelligence`

At a high level:

1. raw marketing exports are loaded
2. the data is normalized into a structured format
3. insight patterns are identified
4. decision rules are evaluated across the workflow outputs
5. opportunities are priority-scored
6. strategy recommendations are generated
7. execution-ready deliverables are produced
8. outputs are evaluated for quality and alignment
9. saved runs can be compared to explain what changed

## Data Sources

InsightRx currently works from exported CSV data rather than direct platform APIs.

Supported inputs include:

- GA4 Page Title
- GA4 Session Source / Medium
- Google Search Console Queries
- SEMrush Organic Research
- SEMrush Pages
- SEMrush Topic Opportunities
- SEMrush Keyword Gap
- Meta Social Analytics

These inputs are used to support search, website, page-level, acquisition, and social analysis inside the same workflow.

## Agent Architecture

### Data Intake Agent

**Purpose**  
Convert uploaded marketing exports into a structured internal format the rest of the system can use.

**Inputs**

- GA4 Page Title export
- GA4 Session Source / Medium export
- Google Search Console query export

**Outputs**

- normalized data summaries
- row counts
- key metric summaries
- sample records for downstream agents

**Responsibilities**

- parse uploaded CSVs
- structure website and search data
- preserve enough context for later analysis
- provide consistent workflow-ready input

### Insight Agent

**Purpose**  
Identify patterns, opportunities, and weak points in the marketing data.

**Inputs**

- structured data from the Data Intake Agent

**Outputs**

- query analysis
- high-impression / low-click opportunities
- non-branded opportunities
- local-intent opportunities
- page alignment insights
- insight summaries and patterns

**Responsibilities**

- analyze search demand and click behavior
- identify visibility gaps
- surface page/query mismatches
- generate the first reasoning layer for the workflow

### Strategy Agent

**Purpose**  
Convert insights and rule-based signals into prioritized marketing strategy.

**Inputs**

- Insight Agent outputs
- SEMrush positions data
- SEMrush pages data
- SEMrush topic data
- workflow-level rule matches

**Outputs**

- strategic recommendations
- priority actions
- rule-grounded priorities
- opportunity groupings
- weekly action suggestions

**Responsibilities**

- prioritize the most important opportunities
- explain why the opportunities matter
- organize recommendations by type
- translate insight patterns into strategic action

### Execution Agent

**Purpose**  
Turn strategy into execution-ready marketing deliverables.

**Inputs**

- Strategy Agent outputs

**Outputs**

- sample titles
- H1 rewrites
- FAQs
- content structures
- CTA suggestions
- social content ideas
- other execution-ready deliverables by action type

**Responsibilities**

- create usable outputs for marketers
- keep deliverables aligned to the selected strategy
- produce structured assets rather than abstract advice

### Evaluation Agent

**Purpose**  
Evaluate whether the execution output actually solves the original issue.

**Inputs**

- Execution Agent output

**Outputs**

- evaluation score
- strengths
- weaknesses
- warnings
- suggested improvements

**Responsibilities**

- score output quality
- check whether deliverables are specific and useful
- flag weak or generic outputs
- support quality control inside the workflow

### Comparison Intelligence Layer

**Purpose**  
Compare saved runs and explain not only what changed, but also what may have caused the change.

**Inputs**

- saved workflow results from two runs
- metric snapshots
- rule matches
- strategy outputs
- normalized priority metadata

**Outputs**

- metric deltas
- rule match deltas
- strategy deltas
- priority shift summaries
- plain-English comparison insights

**Responsibilities**

- compare current run vs prior run
- identify new, resolved, and persistent rule issues
- compare priority themes across runs
- surface simple marketing intelligence about why performance changed

## Rules and Intelligence Frameworks

InsightRx uses several JSON-based intelligence files to separate reasoning logic from UI code.

### `decision_rules.json`

Location: [`reference_docs/distilled/decision_rules.json`](/Users/elizabethmccuan/Desktop/mkt399-ai-marketing-system/reference_docs/distilled/decision_rules.json)

Purpose:

- define rule-based marketing conditions
- trigger structured recommendations from workflow signals
- assign categories, priority labels, and action types

Examples of what these rules support:

- CTR opportunities
- ranking opportunities
- engagement issues
- AEO opportunities
- GEO opportunities
- social opportunities

### `metric_glossary.json`

Location: [`rules/metric_glossary.json`](/Users/elizabethmccuan/Desktop/mkt399-ai-marketing-system/rules/metric_glossary.json)

Purpose:

- define what key marketing metrics mean
- explain how they should be interpreted
- support future agent grounding and metric-aware reasoning

Examples:

- what engagement rate means in GA4
- how to interpret CTR in GSC
- what a low average position may support strategically

### `prioritization_rules.json`

Location: [`rules/prioritization_rules.json`](/Users/elizabethmccuan/Desktop/mkt399-ai-marketing-system/rules/prioritization_rules.json)

Purpose:

- provide a formal framework for ranking work by impact, effort, urgency, and confidence
- reduce arbitrary prioritization
- support normalized priority scoring

Examples:

- strong visibility / low CTR
- ranking quick wins
- high traffic / weak engagement
- social growth opportunities
- missing conversion data caution

### `best_practices_rules.json`

Location: [`reference_docs/distilled/best_practices_rules.json`](/Users/elizabethmccuan/Desktop/mkt399-ai-marketing-system/reference_docs/distilled/best_practices_rules.json)

Purpose:

- store strategic reference guidance used by the Strategy Agent
- map recommendations to broader best-practice categories
- reinforce consistency in the strategy layer

### `agent_prompt.txt`

Location: [`reference_docs/distilled/agent_prompt.txt`](/Users/elizabethmccuan/Desktop/mkt399-ai-marketing-system/reference_docs/distilled/agent_prompt.txt)

Purpose:

- provide prompt-level strategy guidance
- document how the strategy layer should think about opportunity framing and recommendation logic

## What Makes InsightRx Agentic

InsightRx is agentic because it does more than display metrics or generate one-off content.

The system follows a multi-step reasoning path:

`Data → Rule Matching → Insight → Why It Matters → Recommendation → Take Action → Evaluation`

In practice, this means:

- data is first structured
- insights are generated from that structure
- rule logic evaluates opportunities across the workflow
- the system scores and prioritizes those opportunities
- strategy recommendations are formed from both insight patterns and rule signals
- execution deliverables are produced from that strategy
- outputs are evaluated for quality before being treated as useful

This creates a chain of reasoning rather than a single prompt response.

## Current Capabilities

InsightRx currently supports:

- CSV intake
- saved runs
- run comparison
- decision-rule recommendations
- priority scoring
- strategy generation
- execution-ready deliverables
- evaluation scoring
- comparison intelligence

Inside the Streamlit app, users can:

- upload marketing exports
- run the workflow
- review dashboards and analysis views
- inspect recommendations and take-action guidance
- load prior runs
- compare one saved run against another
- view AI chat responses grounded in loaded data

## Repository Structure

Key directories:

- [`agents/`](/Users/elizabethmccuan/Desktop/mkt399-ai-marketing-system/agents)
  Agent modules for intake, insight, strategy, execution, and evaluation
- [`services/`](/Users/elizabethmccuan/Desktop/mkt399-ai-marketing-system/services)
  Shared logic such as rule evaluation and scoring
- [`rules/`](/Users/elizabethmccuan/Desktop/mkt399-ai-marketing-system/rules)
  Machine-readable intelligence frameworks
- [`reference_docs/distilled/`](/Users/elizabethmccuan/Desktop/mkt399-ai-marketing-system/reference_docs/distilled)
  Distilled prompt and strategic reference assets
- [`prompts/`](/Users/elizabethmccuan/Desktop/mkt399-ai-marketing-system/prompts)
  Prompt definitions for the agent workflow
- [`saved_runs/`](/Users/elizabethmccuan/Desktop/mkt399-ai-marketing-system/saved_runs)
  Saved workflow inputs and metadata for later reload/comparison

## Run the System

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the Streamlit app:

```bash
streamlit run app.py
```

You can also run the workflow directly from the command line:

```bash
python main.py
```

Saved workflow summaries are logged to:

[`logs/workflow_runs.csv`](/Users/elizabethmccuan/Desktop/mkt399-ai-marketing-system/logs/workflow_runs.csv)

## Future Improvements

Likely next steps for InsightRx include:

- API integrations
- stronger comparison intelligence
- more rules
- healthcare-specific compliance rules
- automated reporting

Additional practical future improvements could include:

- direct platform connectors instead of manual CSV exports
- stronger use of the metric glossary inside agents
- tighter use of prioritization rules across all recommendation paths
- more robust healthcare trust and compliance review logic
- richer multi-run trend reporting across longer time windows

## Author

Elizabeth McCuan  
MKT 399 Independent Study  
DePaul University
