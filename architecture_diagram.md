# InfraLens - Overall System Architecture

This document describes the end-to-end data pipelines, storage layout, mathematical transformation procedures, and AI narrative synthesis loops within the **InfraLens** infrastructure analytics platform.

---

## 1. High-Level Data Flow & Presentation Layer

The overall system architecture follows a classic data-warehouse topology: **Extract, Load, Transform, and Synthesize (ELTS)**.

```mermaid
graph TD
    %% Define Nodes
    subgraph data_sources ["Data Sources"]
        src_azure_mon["Azure Monitor API (CPU & Memory Telemetry)"]
        src_datadog["Datadog API (App Health, Requests, Latency)"]
        src_azure_cost["Azure Cost Management API (Daily Spend Records)"]
    end

    subgraph orchestrator_daemon ["Orchestrator Daemon (scheduler/scheduler.py)"]
        runner["ingestion/runner.py (Execution Trigger)"]
    end

    subgraph telemetry_storage ["Telemetry Storage Layer"]
        db_clickhouse[("ClickHouse (WSL Docker Container) - Engine: MergeTree")]
        db_duckdb[("DuckDB (Local db File) - Engine: Vectorized OLAP")]
    end

    subgraph transformation_engine ["Analytical Transformation Engine"]
        trans_agg["transformation/aggregate.py (Hourly/Daily Rollups)"]
        trans_anom["transformation/anomaly.py (Rolling 14d Z-Scores)"]
        trans_fore["transformation/forecast.py (Linear Regression)"]
        trans_opt["transformation/optimization.py (Underutilization)"]
    end

    subgraph ai_synthesis_engine ["AI Insight Synthesis Engine"]
        ai_gen["ai/insight_generator.py (Prompter Coordinator)"]
        ai_client["ai/gemini.py (Client Gateway)"]
        ai_api["Gemini 2.5 Flash API (Cloud Inference)"]
        ai_fallback["Offline Template Builder (Local Fallback)"]
    end

    subgraph bi_presentation ["BI Presentation Layer"]
        bi_dashboard["dashboard/PowerBI.pbix (Power BI Desktop)"]
    end

    %% Define Flows
    src_azure_mon --> runner
    src_datadog --> runner
    src_azure_cost --> runner

    runner --> db_clickhouse
    runner --> db_duckdb

    db_duckdb --> trans_agg
    trans_agg --> db_duckdb

    db_duckdb --> trans_anom
    db_duckdb --> trans_fore
    db_duckdb --> trans_opt

    trans_anom --> db_duckdb
    trans_fore --> db_duckdb
    trans_opt --> db_duckdb

    db_duckdb --> ai_gen
    ai_gen --> ai_client
    ai_client --> ai_api
    ai_client --> ai_fallback

    ai_api --> ai_gen
    ai_fallback --> ai_gen
    ai_gen --> db_duckdb

    db_duckdb ====> bi_dashboard
```

---

## 2. Ingestion & Storage Architecture (Layer 1)

This schema represents the synchronization pathway, highlighting the WSL2 virtual networking setup.

```mermaid
sequenceDiagram
    autonumber
    participant S as Ingestion Sources (Azure / Datadog)
    participant R as Ingestion Runner (Python Process)
    participant DDB as DuckDB Storage (local file: infra.db)
    participant CH as ClickHouse Container (WSL2 Docker Daemon)

    R->>S: Pull latest point-in-time metrics
    S-->>R: Return normalized JSON metrics
    
    R->>DDB: Create raw_metrics table if not exists
    R->>DDB: Bulk insert metrics (DuckDB API)
    
    Note over R,CH: Network Check & Self-Healing Connection Loop
    R->>CH: Connect to localhost:8123 (TCP Connection)
    alt Connection Success
        R->>CH: Insert block payload (list of tuples)
    else Connection Refused (Container Stopped)
        R->>R: Catch ConnectionError Exception
        R->>CH: Execute System Call: wsl docker start clickhouse-server-lens
        Note over CH: Boot ClickHouse Daemon (approx. 5s)
        loop Up to 5 Attempts (Interval 3s)
            R->>CH: Retry ping localhost:8123
        end
        R->>CH: Initialize Tables (MergeTree Engine)
        R->>CH: Bulk insert metric block
    end
    CH-->>R: Return insertion row count
```

---

## 3. Data Transformation & AI Narrative Flow (Layers 2 & 3)

The transformation pipeline runs inside a single database transaction session (`duckdb.connect`).

```mermaid
flowchart TD
    %% Storage Inputs
    raw[("raw_metrics Table")] --> rollup[("daily_metrics_rollup Table")]

    %% Pipeline Processes
    subgraph Anomaly_Detection ["Anomaly Detection"]
        rollup --> anom_math["Calculate 14-day rolling mean and standard deviation"]
        anom_math --> zscore{"Is z-score absolute value > 2.0?"}
        zscore -->|Yes| flag_anom["Classify severity: Warning if z-score <= 3.0, Critical if z-score > 3.0"]
        flag_anom --> tbl_anom[("anomaly_alerts Table")]
    end

    subgraph Capacity_Forecasting ["Capacity Forecasting"]
        rollup --> fore_math["Compute 30-day rolling average to smooth noise"]
        fore_math --> fit_reg["Fit Linear Regression: y = mx + c and project out 90 days"]
        fit_reg --> check_breach{"Does 90-day forecast utilization cross 80%?"}
        check_breach -->|Yes| calc_breach_date["Calculate Projected Breach Date: x = (80 - c) / m"]
        calc_breach_date --> tbl_fore[("capacity_forecasts Table")]
    end

    subgraph Underutilization_Filter ["Underutilization Filter"]
        rollup --> opt_math["Compute 7-day average CPU and Memory utilization"]
        opt_math --> check_low{"Are CPU and Memory both < 20%?"}
        check_low -->|Yes| calc_savings["Join latest Daily Cost. Monthly Savings = Daily Cost * 30"]
        calc_savings --> tbl_opt[("underutilized_resources Table")]
    end

    %% Narrative Insights Generator
    tbl_anom --> ai_orchestrator["ai/insight_generator.py (Coordinator)"]
    tbl_fore --> ai_orchestrator
    tbl_opt --> ai_orchestrator

    subgraph Narrative_Generation_Loop ["Narrative Generation Loop"]
        ai_orchestrator --> prompts["ai/prompts.py (Templates)"]
        prompts --> client["ai/gemini.py (Client Interface)"]
        client --> api["Gemini 2.5 Flash API"]
        client --> local["Offline Markdown Fallback"]
        api --> save_db[("Write to narrative_insights Table")]
        local --> save_db
    end
```

---

## 4. Power BI DirectQuery Integration (Layer 4)

Power BI Desktop utilizes the **DuckDB ODBC Driver** to query the transformation results locally:

```mermaid
flowchart LR
    pbi["Power BI Dashboard View"] --> odbc["DuckDB ODBC Driver"]
    odbc --> db[("database/duckdb/infra.db")]
    
    subgraph Dashboard_Panes ["Dashboard Panes"]
        db --> view_compute["Compute Tab: CPU & Memory Utilization Heatmaps"]
        db --> view_cost["Cost Tab: Daily Spend Trends & Anomaly Alert Cards"]
        db --> view_capacity["Capacity Tab: 30/60/90-day Projections"]
        db --> view_opt["Optimization Tab: Right-sizing & Decommission Narrative Reports"]
    end
```
