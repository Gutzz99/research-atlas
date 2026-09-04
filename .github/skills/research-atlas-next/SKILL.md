---
name: research-atlas-next
description: "Use when improving the Research Atlas project in the next iteration: reviewing the graph pipeline, validating architecture choices, planning the next feature or fix, and turning implementation decisions into a reusable, documented workflow. Covers data pipeline review, graph integrity checks, feature prioritization, validation steps, and devlog updates."
---

# Research Atlas Next-Iteration Skill

## Purpose

Use this skill to improve the Research Atlas codebase in a structured, evidence-driven way. It is designed for the project’s current pattern: graph-first research tooling that depends on a clean ETL flow, Neo4j ingestion, analytics, and a Streamlit dashboard.

## When to Use

Use this skill when you want to:
- review the current project state and identify the next most valuable improvement
- validate a pipeline step or graph model change before implementing it
- prioritize a feature or fix based on evidence from code, data, and architecture
- document decisions in the project’s devlog and keep implementation choices reproducible
- keep the project aligned with the foundation described in the README and devlog
- adapt the project to safe local setup and environment-driven configuration without hardcoded secrets

## Project Operating Rules

This repo has a specific operational standard that should be preserved in every iteration:

- never hardcode Neo4j credentials in application code or Compose configuration
- store local secrets in a project-local `.env` file
- keep `.env.example` as the template for teammates
- fail fast when required configuration values are missing
- treat missing environment values as a setup issue, not as a sign that business logic is broken

Required runtime values include:
- `NEO4J_URI`
- `NEO4J_USER`
- `NEO4J_PASSWORD`
- `PROCESSED_DATA_PATH` when the project is run outside the default path

Recommended local setup:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_strong_local_password
HOST_NEO4J_HTTP_PORT=7474
HOST_NEO4J_BOLT_PORT=7687
PROCESSED_DATA_PATH=data/processed/graph_data_clean.json
```

Then start the database with:

```bash
docker compose --env-file .env up -d
```

If the environment file is missing or incomplete, the correct response is to fail fast and ask for the local config to be created before continuing with pipeline work.

## Workflow

### 1. Assess the current system

Start by reading the highest-signal artifacts:
- README for overview, architecture, and intended behavior
- devlog entries for rationale and trade-offs
- pipeline entrypoints such as `run_ingestion.py`, `run_preprocessing.py`, `run_graph_loading.py`, and `run_analytics.py`
- core implementation files in `src/` for the actual data flow and constraints

Decision checks:
- Is the architecture still consistent with the project goals?
- Are there gaps between the intended design and the current implementation?
- Which subsystem is the bottleneck or the highest-value next target?

### 2. Identify the next improvement

Choose the next task based on evidence, not speculation.

Good candidates include:
- fixing graph integrity issues
- improving ingestion or preprocessing quality
- making the dashboard more usable or interpretable
- adding analytics that validate the network structure
- reducing operational friction in setup or environment configuration

Prioritization rule:
- Prefer improvements that increase trust in the graph, improve reproducibility, or make the pipeline more usable for research exploration.

### 3. Check configuration before debugging deeper

Before treating a failure as an app bug, confirm the environment is valid:
- verify required env values exist locally
- confirm Docker and Python are using the same `.env` source
- check whether the issue is a missing configuration rather than a logic defect

This project’s current status note is important: if `.env` is absent, the database and loader scripts should fail fast and stop, because the environment is incomplete. That is the expected operational behavior.

### 4. Trace the root cause before editing

Before changing code, follow this path:
- confirm how data moves through the pipeline
- check schema assumptions against actual generated nodes/edges
- verify whether failures are caused by source data, preprocessing, graph loading, or dashboard logic
- distinguish configuration issues from implementation defects
- ensure any assumption is supported by the repository’s documented design

Do not patch symptoms first. Fix the layer where the issue originates.

### 5. Implement the smallest validated change

Keep the iteration focused:
- one clear improvement objective
- limited scope
- direct connection to the current project architecture
- explicit validation of behavior after the edit

Prefer changes that:
- preserve the closed-graph constraint
- keep Neo4j ingestion deterministic and batch-friendly
- leave the dashboard and analytics understandable to a researcher

### 6. Validate behavior with the real project flow

Run the relevant checks that match the change:
- pipeline smoke test for ETL steps
- schema or graph integrity validation for data changes
- targeted script execution for analytics or loader updates
- dashboard-level checks if the change affects UI behavior
- configuration validation for env-driven startup when the change affects local execution

If a change affects data quality or graph semantics, validate those outputs directly rather than assuming the code is correct.

### 7. Record the decision trail

Document the outcome in the project devlog or an equivalent project note.

Include:
- the problem statement
- the selected design choice
- the trade-off that informed the decision
- what was validated
- what the next iteration should explore

This keeps the project reproducible and makes later improvements easier to evaluate.

## Quality Bar

A next iteration is complete only when all of the following are true:
- the project goal remains clearly aligned with the README and architecture
- the root cause was identified rather than guessed
- configuration requirements were checked before deeper debugging
- the fix or feature is scoped to the immediate next value
- validation was performed against the relevant real workflow
- the decision is documented in a traceable way

## Example Prompts

- Review the current Research Atlas pipeline and recommend the next highest-value improvement.
- Identify a graph integrity problem and propose a focused fix with validation steps.
- Improve the ingestion or preprocessing flow while preserving the system’s closed-graph design.
- Add a meaningful analytics enhancement and document the design trade-off in the devlog.
- Audit the repo for the next iteration plan based on architecture, config, and data flow.
- Check whether a configuration issue is blocking the local pipeline before making code changes.
- Harden the project setup for safe local use with `.env`-based Neo4j configuration.

## Related Customizations

Consider creating the following next:
- a project-specific instruction file for data/graph quality checks
- a prompt for reviewing ETL and graph-health issues before implementation
- a skill for dashboard UX improvements and researcher workflow validation
- a devlog template for recording design decisions and validation evidence
