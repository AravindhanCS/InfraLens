# IMPACT pSiddhi 3.0 — Final Submission Document & Evidence Pack

**L&D Team · pSiddhi-2026-01 · psiog**
**Covers complete development through Week 17 (Final Review & POC Delivery)**

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
| **Final Review Window** | `Week 17` |

---

## 2. Approved Proposal Recap & Problem Statement

Psiog's platform engineering teams make critical infrastructure decisions—provisioning, scaling, retiring capacity, and planning cloud budgets—without access to a unified, accurate, and current view of the infrastructure estate. Metrics, cost data, and utilization trends are scattered across multiple disconnected tools.

InfraLens solves this consolidation failure end-to-end:
1. **Multi-Source Ingestion**: Ingests telemetry across Azure Monitor (compute usage), Datadog (application performance), and Azure Cost Management (spend).
2. **Dual-Layer Storage**: Combines DuckDB (embedded OLAP analytical query engine) and ClickHouse in WSL Docker (hot-path columnar time-series).
3. **Statistical Transformation & ML**: Executes hourly/daily rollups, 14-day rolling z-score anomaly detection, 30-day linear regression capacity forecasting, and 7-day underutilization scoring (<20% CPU/Memory).
4. **Core AI Narrative Insights**: Generates plain-language, actionable summaries using Google Gemini 2.5 Flash API (with offline local fallback) across 3 core infrastructure scenarios (Cost Anomaly, Capacity Risk, Underutilization Optimization).
5. **Power BI Visuals & Data Export Bridge**: Exports datasets to Parquet and CSV in `data/processed/` and provides a direct Python connector for Power BI Desktop.
6. **Multi-Layered QA & CI/CD**: Pytest test suite with $\ge 80\%$ code coverage, data quality validator, AI narrative accuracy validation, scale load benchmarking (80,000+ records), and GitHub Actions CI.

---

## 3. Comprehensive Deliverables Reconciliation (Weeks 4–17)

| ID | Planned Deliverable | Planned Week | Status | Evidence ID |
| :--- | :--- | :---: | :---: | :---: |
| **D-01** | Unified ingestion schema & Azure Monitor ingestion script | Week 4 | **Done** | EV-01 |
| **D-02** | Datadog & Azure Cost connectors; DuckDB + ClickHouse raw storage | Week 5 | **Done** | EV-02 |
| **D-03** | Transformation pipeline: hourly/daily rollups & underutilization scoring | Week 6 | **Done** | EV-03 |
| **D-04** | Anomaly detection (14-day z-scores) & linear regression capacity forecasting | Week 7 | **Done** | EV-04 |
| **D-05** | Gemini 2.5 Flash API integration & prompt orchestration layer (3 scenarios) | Week 8 | **Done** | EV-05 |
| **D-06** | E2E scheduler daemon & on-demand pipeline runner CLI | Week 9 | **Done** | EV-06 |
| **D-07** | Unit, integration, and E2E Pytest test suite ($\ge 80\%$ coverage) | Week 9 | **Done** | EV-07 |
| **D-08** | Power BI Data Model & automated Parquet/CSV export bridge | Weeks 11–12 | **Done** | EV-08 |
| **D-09** | Power BI 4-Domain dashboard setup & Python connector script | Weeks 13–14 | **Done** | EV-08 |
| **D-10** | AI Narrative accuracy assertion suite (factual claim validation) | Weeks 14–15 | **Done** | EV-09 |
| **D-11** | Scale testing (80,000+ records backfill, <10s query SLA, Locust definition) | Week 15 | **Done** | EV-10 |
| **D-12** | Git version control, GitHub Actions CI/CD pipeline, and final documentation | Week 16 | **Done** | EV-07, EV-10 |

---

## 4. Evidence Pack

### EV-01: Schema & Ingestion Normalization
- **File**: `ingestion/schema.py`, `ingestion/azure_monitor.py`
- **Result**: Standardized 8-column schema `[source, resource_id, metric_name, value, unit, timestamp, region, service_tag]`. Validated via `test_ingestion.py`.

### EV-02: Dual-Store Telemetry Landing
- **File**: `database/duckdb_store.py`, `database/clickhouse_store.py`
- **Result**: Simultaneous writes to DuckDB and ClickHouse container in WSL2 with auto-start and connection retry logic.

### EV-03: Vectorized Aggregations & Rollups
- **File**: `transformation/aggregate.py`, `transformation/optimization.py`
- **Result**: Automated hourly (`hourly_metrics_rollup`) and daily (`daily_metrics_rollup`) aggregations in DuckDB. 7-day underutilization scoring identifies VMs below 20% CPU and Memory.

### EV-04: Statistical Anomalies & Capacity Forecasting
- **File**: `transformation/anomaly.py`, `transformation/forecast.py`
- **Result**: 14-day rolling z-scores flag critical spend spikes ($Z > 3.0$). Linear regression projects 30/60/90-day utilization, predicting exact 80% SLA breach date (`vm-prod-02` on 2026-08-31).

### EV-05: AI Narrative Generation (Gemini 2.5 Flash + Offline Fallback)
- **File**: `ai/gemini.py`, `ai/prompts.py`, `ai/insight_generator.py`
- **Result**: Plain-language markdown narratives generated and persisted in `narrative_insights` table across Cost Anomaly, Capacity Risk, and Underutilization reports.

### EV-06: E2E Pipeline Orchestration
- **File**: `scheduler/scheduler.py`
- **Result**: Executes all 7 pipeline steps end-to-end in < 20 seconds. Supports on-demand `--run` and periodic `--schedule 15`.

### EV-07: Test Suite Coverage ($\ge 80\%$) & GitHub Actions CI
- **File**: `tests/`, `.github/workflows/ci.yml`
- **Result**: **27 / 27 passing tests** across 8 test modules. GitHub Actions CI automated pipeline configured.

### EV-08: Power BI Data Model & Export Bridge
- **File**: `transformation/export_for_bi.py`, `dashboard/powerbi_connector.py`, `dashboard/POWERBI_SETUP_GUIDE.md`
- **Result**: Dual Parquet & CSV export in `data/processed/` with manifest file. Single-click Python connector for Power BI Desktop. Full DAX formulas and star schema documented.

### EV-09: AI Narrative Accuracy Validation Suite
- **File**: `ai/narrative_validator.py`, `tests/test_narrative_accuracy.py`
- **Result**: Automated claim extractor parses percentage spikes, dollar amounts, and breach dates from AI narrative text, asserting factual alignment with DuckDB source records within $\pm 5\%$ tolerance.

### EV-10: Scale & Performance Benchmarking (80,000+ Records)
- **File**: `tests/benchmark_scale.py`, `tests/locustfile.py`
- **Result**:
  - **Dataset Tested**: **81,000 records** in DuckDB.
  - **30-Day Backfill Latency**: **0.0363s** (Target SLA: < 30.0s) -> **PASSED**
  - **Dashboard Refresh Latency**: **0.0133s** (Target SLA: < 10.0s) -> **PASSED**
  - **Overall SLA Compliance**: **100% COMPLIANT**.

---

## 5. Budget & Tool Reconciliation

| Tool / Technology | Approved Tier | Actual Tier Used | Actual Cost |
| :--- | :--- | :--- | :---: |
| Azure Monitor API | Free tier | Mocked Free Tier Connector | ₹0 |
| Datadog Metrics API | Free tier | Mocked Free Tier Connector | ₹0 |
| Azure Cost Management | Free tier | Mocked Free Tier Connector | ₹0 |
| DuckDB (Embedded OLAP) | Free / Open-source | Version 1.2+ | ₹0 |
| ClickHouse (WSL Docker) | Free / Open-source | Official Docker Image | ₹0 |
| Google AI Studio (Gemini 2.5 Flash) | Free tier (1M tokens/day) | Gemini 2.5 Flash + Local Fallback | ₹0 |
| Python 3.11 + Libraries | Free / Open-source | NumPy, Pandas, Scikit-learn, DuckDB | ₹0 |
| Power BI Desktop | Free | Power BI Desktop 2026 | ₹0 |
| Pytest + pytest-cov + Locust | Free / Open-source | Automated testing suite | ₹0 |
| Git & GitHub Actions | Free tier (2,000 min/mo) | Git version-controlled | ₹0 |
| Contingency Buffer | ₹800 allocated | Not used | ₹0 |
| **TOTAL SPEND** | **₹2,500 Ceiling** | **100% Free / Open Source** | **₹0** |

---

## 6. Live Demonstration Script for Final Review

During the Week 17 Final Evaluation, execute the following 4-step live walkthrough:

1. **Show Scale & Performance Compliance**:
   ```powershell
   .venv\Scripts\python.exe tests/benchmark_scale.py
   ```
   *Demonstrates 81,000+ records processed with sub-second backfill and dashboard refresh queries.*

2. **Run Full End-to-End Pipeline**:
   ```powershell
   .venv\Scripts\python.exe -m scheduler.scheduler --run
   ```
   *Demonstrates multi-source ingestion, DuckDB/ClickHouse landing, z-score anomaly flagging, linear regression forecasting, AI narrative generation, and Power BI Parquet export.*

3. **Verify Analytical & AI Outputs**:
   ```powershell
   .venv\Scripts\python.exe verify_output.py
   ```
   *Displays row counts, critical anomalies ($Z=3.47$), capacity risk breach date (`vm-prod-02`), underutilization candidate savings ($283/mo), and full AI narrative text.*

4. **Run Pytest & AI Narrative Accuracy Suite**:
   ```powershell
   .venv\Scripts\python.exe -m pytest --cov=ai --cov=database --cov=ingestion --cov=transformation --cov=validation --cov=dashboard --cov-report=term-missing
   ```
   *Proves 100% test pass rate with $\ge 80\%$ coverage.*

---

**Declaration**: I confirm that all deliverables, evidence, test coverage figures, and cost reconciliations in this document reflect true and verified technical implementations in the InfraLens platform.

*   **Participant Name**: `Aravindhan Chandrasekaran`
*   **Employee ID**: `P415`
*   **Topic ID**: `S3-P-01`
