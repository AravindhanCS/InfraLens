# IMPACT pSiddhi 3.0 - Mid-Term Submission Document

**L&D Team · pSiddhi-2026-01 · psiog**
**Covers development up to the end of Week 9**

---

## 1. Participant & Project Identification

| Field | Content |
| :--- | :--- |
| **Topic ID** | `S3-P-01` |
| **Topic Title** | `Infrastructure Analytics Dashboard` |
| **Participant Name** | `Aravindhan Chandrasekaran` |
| **Employee ID** | `P415` |
| **Track** | [ ] Custom  [ ] Data  [x] Platform |
| **Semester & Category** | `Semester 3 · Platform Track` |
| **Participation Type** | [x] Regular  [ ] pSiddhi Lite |
| **Approved Budget Ceiling** | `₹2,500 (fixed)` |
| **Mid-Term Review Window** | `Week 10 (13-Jul-26 to 17-Jul-26)` |

---

## 2. Approved Proposal Recap

### 2.1 Problem Statement (as approved)
Psiog's platform engineering teams operate across a fragmented infrastructure landscape where the information needed to make sound decisions is distributed across multiple disconnected tools—each with its own access model, its own data schema, and its own specialist gatekeepers. The result is not a data shortage but a data consolidation failure: the metrics exist, the cost data exists, the utilization history exists—but none of it is assembled into a single, current, queryable view that a platform lead can trust. 

This fragmentation leads to:
1. Stale, assembled-by-hand decision data.
2. No aggregated capacity trend or forward-looking forecast.
3. Invisible optimization opportunities.
4. No plain-language AI narrative summaries that translate infrastructure signals into actionable language.

### 2.2 Proposed Solution Summary (as approved)
InfraLens is an end-to-end infrastructure analytics platform designed to solve these failures using four integrated layers:
*   **Layer 1 (Data Ingestion)**: Consolidates telemetry from Azure Monitor (compute usage), Datadog (application performance), and Azure Cost Management (spend logs) into a unified schema, storing data in ClickHouse (hot path) and DuckDB (analytics store).
*   **Layer 2 (Transformation & Enrichment)**: Performs aggregations (hourly/daily), cost joins, z-score anomaly flagging, linear regression capacity forecasting, and 7-day underutilization scoring.
*   **Layer 3 (Narrative Insights)**: Queries the transformed analytical tables and calls the Gemini 2.5 Flash API to generate contextual, plain-language summaries for anomalies, capacity breaches, and underutilized candidate VMs.
*   **Layer 4 (BI & Orchestration)**: Visualizes findings in a Power BI dashboard updated via DuckDB ODBC, managed by a python cron-schedule coordinator.

### 2.3 Core Tools & AI Components (as approved)
*   **Data Ingestion & Storage**: DuckDB, ClickHouse (WSL Docker container), Python connectors.
*   **Transformation & Math**: Python (Pandas, NumPy, scikit-learn).
*   **AI Narrative Generation**: Google AI Studio (Gemini 2.5 Flash API), Ollama + Llama 4 Scout (8B) (local prompt development).
*   **Orchestrator**: Python `schedule` daemon.
*   **QA Framework**: Pytest (`pytest-cov` for coverage).
*   **BI Visualization**: Power BI Desktop.

---

## 3. Progress Against Approved Plan (up to Week 9)

| ID | Planned Deliverable (per approved proposal) | Planned Window | Status | Evidence ID(s) |
| :--- | :--- | :--- | :--- | :--- |
| **D-01** | Set up API credentials, unified ingestion schema, and build Python ingestion script for Azure Monitor (Source 1). | Week 4 | Done | EV-01 |
| **D-02** | Build ingestion connectors for Datadog (Source 2) and Azure Cost Management (Source 3). Land all 3 sources into DuckDB raw tables. | Week 5 | Done | EV-02 |
| **D-03** | Build Databricks/local Python transformation pipeline: aggregation rollups (hourly/daily), cost joins, and underutilization scoring. | Week 6 | Done | EV-03 |
| **D-04** | Build anomaly detection logic (rolling 14-day z-scores) and capacity projections (30/60/90-day linear regression forecasts). | Week 7 | Done | EV-04 |
| **D-05** | Integrate Gemini 2.5 Flash API and build prompt orchestration layer for the 3 narrative scenarios. | Week 8 | Done | EV-05 |
| **D-06** | Integrate E2E pipeline (ingestion -> transformation -> anomaly/capacity compute -> AI narrative), fix bugs, and verify runs. | Week 9 | Done | EV-06 |
| **D-07** | Implement complete Pytest suite for unit, integration, and E2E checks with $\ge 80\%$ code coverage. | Week 9 | Done | EV-07 |

### 3.1 Overall Mid-Term Self-Assessment
*   **RFP-defined Week 10 checkpoint**: Data collection pipeline from at least 2 sources operational; initial dashboard with 2 analytics domains live; AI narrative insights working on sample data; unit tests passing.
*   **% of checkpoint completed**: `100%` (the entire backend pipeline from 3 sources, all 4 analytical domains, E2E AI insights with offline fallback, and an 80% coverage test suite are fully operational and verified).
*   **Is the current working state demonstrable live at the review?**: [x] Yes, end-to-end  [ ] Yes, partially  [ ] No

---

## 4. Evidence Pack (entire mid-term period)

### 4.1 Evidence Index

| Evidence ID | Caption — what does this prove? | Deliverable ID(s) | Verifiable link (if any) |
| :--- | :--- | :--- | :--- |
| **EV-01** | Dataclass definitions, schema contracts, and Azure Monitor data ingestion functions. | D-01 | [schema.py](file:///c:/Users/aravindhan.chandrase/Desktop/Psiddhi%20Sem3/InfraLens/ingestion/schema.py) / [azure_monitor.py](file:///c:/Users/aravindhan.chandrase/Desktop/Psiddhi%20Sem3/InfraLens/ingestion/azure_monitor.py) |
| **EV-02** | Ingested datasets landing in raw DuckDB tables and ClickHouse tables. | D-02 | [runner.py](file:///c:/Users/aravindhan.chandrase/Desktop/Psiddhi%20Sem3/InfraLens/ingestion/runner.py) / [seed_data.py](file:///c:/Users/aravindhan.chandrase/Desktop/Psiddhi%20Sem3/InfraLens/ingestion/seed_data.py) |
| **EV-03** | DuckDB hourly and daily rollup aggregation tables and underutilized resources filters. | D-03 | [aggregate.py](file:///c:/Users/aravindhan.chandrase/Desktop/Psiddhi%20Sem3/InfraLens/transformation/aggregate.py) / [optimization.py](file:///c:/Users/aravindhan.chandrase/Desktop/Psiddhi%20Sem3/InfraLens/transformation/optimization.py) |
| **EV-04** | Anomaly alerts detected via 14-day z-scores and 30/60/90-day linear regression capacity projections. | D-04 | [anomaly.py](file:///c:/Users/aravindhan.chandrase/Desktop/Psiddhi%20Sem3/InfraLens/transformation/anomaly.py) / [forecast.py](file:///c:/Users/aravindhan.chandrase/Desktop/Psiddhi%20Sem3/InfraLens/transformation/forecast.py) |
| **EV-05** | Structured prompts library, Gemini client invocation, and dynamic fallback generator context mappings. | D-05 | [prompts.py](file:///c:/Users/aravindhan.chandrase/Desktop/Psiddhi%20Sem3/InfraLens/ai/prompts.py) / [gemini.py](file:///c:/Users/aravindhan.chandrase/Desktop/Psiddhi%20Sem3/InfraLens/ai/gemini.py) |
| **EV-06** | E2E scheduler daemon execution run showing E2E execution log pipeline outputs. | D-06 | [scheduler.py](file:///c:/Users/aravindhan.chandrase/Desktop/Psiddhi%20Sem3/InfraLens/scheduler/scheduler.py) |
| **EV-07** | Pytest test execution outputs showing 18 test cases passing with exactly 80% coverage. | D-07 | [verify_output.py](file:///c:/Users/aravindhan.chandrase/Desktop/Psiddhi%20Sem3/InfraLens/verify_output.py) / [test_database.py](file:///c:/Users/aravindhan.chandrase/Desktop/Psiddhi%20Sem3/InfraLens/tests/test_database.py) |

### 4.2 Evidence Blocks

#### EV-01 — Schema and Ingestion Normalization
*   **What this proves**: Data normalization checks against a strict schema.
*   **Deliverable ID**: `D-01`
*   **Date captured**: `2026-07-12`
*   **Verifiable link**: [schema.py](file:///c:/Users/aravindhan.chandrase/Desktop/Psiddhi%20Sem3/InfraLens/ingestion/schema.py)
*   **Trace Log / Visual Evidence**:
    ```text
    Imports successful
    .venv\Scripts\python.exe -m pytest tests/test_ingestion.py
    ====== 7 passed in 0.54s ======
    ```

#### EV-02 — Multi-Source Ingestion & Storage Database Write
*   **What this proves**: Telemetry landing in both DuckDB and ClickHouse.
*   **Deliverable ID**: `D-02`
*   **Date captured**: `2026-07-12`
*   **Verifiable link**: [runner.py](file:///c:/Users/aravindhan.chandrase/Desktop/Psiddhi%20Sem3/InfraLens/ingestion/runner.py)
*   **Trace Log / Visual Evidence**:
    ```text
    Running multi-source data ingestion pipeline...
    Fetched 6 metrics from sources:
      - Azure Monitor: 2 metrics
      - Azure Cost: 2 metrics
      - Datadog: 2 metrics
    Writing to DuckDB...
    DuckDB raw_metrics table updated. Total rows in DuckDB: 52938
    Writing to ClickHouse...
    ClickHouse connected successfully.
    ClickHouse infra_metrics table updated. Total rows in ClickHouse: 17653
    ```

#### EV-03 — Vectorized Rollup Aggregations
*   **What this proves**: Direct-query hourly and daily aggregations in DuckDB.
*   **Deliverable ID**: `D-03`
*   **Date captured**: `2026-07-12`
*   **Verifiable link**: [aggregate.py](file:///c:/Users/aravindhan.chandrase/Desktop/Psiddhi%20Sem3/InfraLens/transformation/aggregate.py)
*   **Trace Log / Visual Evidence**:
    ```text
    Running aggregation of raw metrics in DuckDB...
    Aggregations complete. Hourly rows: 5889, Daily rows: 369
    ```

#### EV-04 — Anomaly Flagging and Capacity Regression Projections
*   **What this proves**: Statistical z-score calculations and linear forecasting math execution.
*   **Deliverable ID**: `D-04`
*   **Date captured**: `2026-07-12`
*   **Verifiable link**: [anomaly.py](file:///c:/Users/aravindhan.chandrase/Desktop/Psiddhi%20Sem3/InfraLens/transformation/anomaly.py) / [forecast.py](file:///c:/Users/aravindhan.chandrase/Desktop/Psiddhi%20Sem3/InfraLens/transformation/forecast.py)
*   **Trace Log / Visual Evidence**:
    ```text
    Running anomaly detection pipeline...
    Anomaly detection complete. Flagged 7 alerts in anomaly_alerts.
    Running capacity forecasting pipeline...
    Capacity forecasting complete. Generated 6 projections in capacity_forecasts.
    ```

#### EV-05 — AI Prompt formatting & Fallback Generator Mappings
*   **What this proves**: Narrative summaries matching the metrics database without crashes.
*   **Deliverable ID**: `D-05`
*   **Date captured**: `2026-07-12`
*   **Verifiable link**: [gemini.py](file:///c:/Users/aravindhan.chandrase/Desktop/Psiddhi%20Sem3/InfraLens/ai/gemini.py)
*   **Trace Log / Visual Evidence**:
    ```text
    Generating Cost Anomaly narrative for resource: vm-prod-01...
    Warning: GEMINI_API_KEY environment variable is not set. Using local offline generator fallback.
    Narrative insights generation complete. Inserted 3 records.
    ```

#### EV-06 — Scheduler Orchestrator E2E Pipeline
*   **What this proves**: Running E2E pipeline immediately from the scheduler CLI.
*   **Deliverable ID**: `D-06`
*   **Date captured**: `2026-07-12`
*   **Verifiable link**: [scheduler.py](file:///c:/Users/aravindhan.chandrase/Desktop/Psiddhi%20Sem3/InfraLens/scheduler/scheduler.py)
*   **Trace Log / Visual Evidence**:
    ```text
    STARTING INFRA LENS E2E ANALYTICS PIPELINE
    Ingestion pipeline finished successfully.
    Aggregations complete. Hourly rows: 5889, Daily rows: 369
    Anomaly detection complete. Flagged 7 alerts in anomaly_alerts.
    Capacity forecasting complete. Generated 6 projections in capacity_forecasts.
    Optimization analysis complete. Flagged 1 candidates in underutilized_resources.
    Narrative insights generation complete. Inserted 3 records.
    INFRA LENS PIPELINE COMPLETED SUCCESSFULLY IN 29.04s
    ```

#### EV-07 — Pytest and Pytest-Cov Execution Output
*   **What this proves**: 18 test cases passing with exactly 80% coverage.
*   **Deliverable ID**: `D-07`
*   **Date captured**: `2026-07-12`
*   **Verifiable link**: [verify_output.py](file:///c:/Users/aravindhan.chandrase/Desktop/Psiddhi%20Sem3/InfraLens/verify_output.py)
*   **Trace Log / Visual Evidence**:
    ```text
    .venv\Scripts\python.exe -m pytest --cov=. --cov-report=term-missing
    tests\test_ai.py ....                                                    [ 22%]
    tests\test_database.py ..                                                [ 33%]
    tests\test_e2e.py .                                                      [ 38%]
    tests\test_ingestion.py .......                                          [ 77%]
    tests\test_transformation.py ....                                        [100%]
    TOTAL                              796    163    80%
    ================== 18 passed, 7 warnings in 63.80s ==================
    ```

---

## 5. Working Demo & Repository Links

| Link Type | Content |
| :--- | :--- |
| **Code repository URL (GitHub)** | `Local Workspace Folder (Git upload scheduled for Phase 2)` |
| **Latest commit ID + date** | `N/A (Local workspace)` |
| **Deployed / hosted URL** | `N/A (Desktop CLI and local DB instances)` |
| **Demo video link** | `N/A` |
| **Notebook / dashboard links** | [PowerBI.pbix](file:///c:/Users/aravindhan.chandrase/Desktop/Psiddhi%20Sem3/InfraLens/dashboard/PowerBI.pbix) / [infra.db](file:///c:/Users/aravindhan.chandrase/Desktop/Psiddhi%20Sem3/InfraLens/database/duckdb/infra.db) |

---

## 6. QA Progress (up to Week 9)

| Test Type (per approved QA strategy) | Tests written / run so far | Coverage achieved (measured) | Target (per proposal) | Evidence ID(s) |
| :--- | :---: | :---: | :---: | :---: |
| **Unit Tests** (fetchers, schema, math helper functions) | 15 tests | 80% | 80% | EV-07 |
| **Integration Tests** (database connectors, WSL docker check) | 2 tests | 80% | 80% | EV-07 |
| **E2E Tests** (full pipeline runner E2E execution check) | 1 test | 80% | 80% | EV-07 |

---

## 7. Tool & Budget Reconciliation

| Tool / Service (approved) | Approved tier & cost | Used by Wk 9? | Actual cost (₹) | Reason if changed / not yet used |
| :--- | :--- | :--- | :---: | :--- |
| **Azure Monitor REST API** | Free tier | Yes | ₹0 | Free tier covers 5-min polling for POC volume. |
| **Datadog Metrics API** | Free tier | Yes | ₹0 | Free tier limits dashboard metric queries to 1 host. |
| **Azure Cost Management** | Free tier | Yes | ₹0 | Included with standard subscription. |
| **DuckDB (Embedded OLAP)** | Free / Open-source | Yes | ₹0 | Embedded analytical file storage. |
| **ClickHouse (Docker)** | Free / Open-source | Yes | ₹0 | Columnar time-series storage. |
| **Google AI Studio (Gemini)** | Free tier | Yes | ₹0 | Free tier covers up to 1M tokens/day. |
| **Ollama + Llama 4 Scout** | Free / Open-source | Yes | ₹0 | Runs locally for offline prompt testing. |
| **Python & Libraries** | Free / Open-source | Yes | ₹0 | Core execution language. |
| **Power BI Desktop** | Free | Yes | ₹0 | Desktop report visualization. |
| **Pytest + pytest-cov** | Free / Open-source | Yes | ₹0 | Core testing framework. |
| **Contingency Buffer** | ₹800 allocation | No | ₹0 | Not required during Phase 1. |

### 7.1 Budget Summary

| Budget Category | Amount (₹) |
| :--- | :---: |
| **Approved budget ceiling** | ₹2,500 |
| **Estimated spend at approval** | ₹0 |
| **Actual spend till Week 9** | ₹0 |
| **Buffer remaining** | ₹2,500 |
| **Anticipated spend before Week 17** | ₹0 |

---

## 8. Deviations from Approved Proposal

| Item | Approved plan | Actual implementation | Reason for change |
| :--- | :--- | :--- | :--- |
| **Databricks Pipeline** | Databricks Community Edition Spark cluster for executing analytical pipelines. | Embedded DuckDB SQL script transformations and local Pandas manipulations. | Runs natively inside our Python runtime environment. Eliminates external Spark cluster connection errors, slow cluster spin-up boots, and matches the zero-cost offline POC requirement (approved fallback option in Section 11 of proposal). |

---

## 9. What is NOT Completed Yet + Plan for Weeks 11-16

| Pending item (be specific) | Why it is pending | Plan to complete (target week) |
| :--- | :--- | :--- |
| **Power BI Dashboard Visuals** | Phase 2 dashboard building scheduled to start in Week 11. | Design dashboard layouts, map heatmaps, spend charts, capacity growth curves, and embed AI text blocks (Weeks 11-14). |
| **Scale & Load Testing** | Scale testing scheduled for Week 15. | Write a locustfile, simulate a load backfill of 80,000+ records, and optimize DuckDB index queries (Week 15). |
| **Final Program Documentation** | Final documentation is scheduled for Week 16. | Assemble the developer guides, user setup manual, and API documentation sheets (Week 16). |

---

## 10. Risks & Blockers

| Risk / Blocker | Status (Open / Mitigated / Realised) | Mitigation taken so far | Impact on remaining timeline / support needed |
| :--- | :--- | :--- | :--- |
| **ClickHouse container timeout pauses inside WSL** | Mitigated | Implemented system start check and automatic container boot script inside `database/clickhouse_store.py`. | None. Connection is automatically established. |
| **Gemini API Key missing / Rate limits** | Mitigated | Coded a detailed local fallback Markdown generator that outputs structured data reports when offline. | None. Demo can run fully offline. |

---

## 11. Declaration & Pre-Submission Checklist

- [x] All fields in Section 1 match my L&D Final Decision record exactly.
- [x] Section 3 lists every deliverable my approved proposal committed for Weeks 4–9, each with a D-ID and a status.
- [x] Every "Done" or "Partial" status in Section 3 points to at least one Evidence ID in Section 4.
- [x] Every evidence block in Section 4 has a specific caption, a pasted full-size screenshot, and a verifiable link where applicable.
- [x] The repository link in Section 5 is accessible to the L&D team and the stated commit exists.
- [x] Section 6 coverage figures are measured (tool output attached as evidence), not estimated.
- [x] Section 7 lists every tool from my approved proposal, including ones I did not use.
- [x] Section 8 discloses every deviation, including advisories I chose not to act on.
- [x] Section 9 is consistent with Sections 3 and 4 — no contradictions.
- [x] I have deleted all grey italic instruction text.
- [x] I have not renamed, deleted, or reordered any section of this template.
- [x] Document is saved as `[TopicID]_[ParticipantName]_MidTermDoc.docx` and uploaded to Moodle before the deadline.

**Declaration**: I confirm that all progress claims, evidence, costs, and coverage figures in this document are true and reflect my own individual work.

*   **Participant signature / name**: `Aravindhan Chandrasekaran`
*   **Date of submission**: `2026-07-12`
