"""Tests for AI Narrative Accuracy and factual claim verification."""

from __future__ import annotations

import duckdb
import pytest

from ai.narrative_validator import (
    extract_capacity_risk_claims,
    extract_cost_anomaly_claims,
    extract_underutilization_claims,
    validate_narrative_accuracy,
)


def test_extract_cost_anomaly_claims():
    sample_text = """### ⚠️ Cost Anomaly Detected: vm-prod-01

A critical cost anomaly has been flagged for **vm-prod-01** in the **centralus** region. The daily cost spiked to **300.00 USD**, which is **165.8%** above its 30-day average of **112.88 USD** (Z-Score: **3.47**).
"""
    claims = extract_cost_anomaly_claims(sample_text)
    assert claims["resource_id"] == "vm-prod-01"
    assert claims["spiked_cost"] == 300.00
    assert claims["pct_increase"] == 165.8
    assert claims["avg_30d_cost"] == 112.88
    assert claims["z_score"] == 3.47


def test_extract_capacity_risk_claims():
    sample_text = """### 📈 Capacity Risk Alert: vm-prod-02 (CPU)

The resource **vm-prod-02** in region **centralus** is experiencing sustained capacity growth. 
- **Current CPU average:** 64.34%
- **Projected 90-Day CPU:** 100.00%
- **Growth Trend:** 0.5004% utilization increase per day
- **Projected Breach Date (80%):** 2026-08-31
"""
    claims = extract_capacity_risk_claims(sample_text)
    assert claims["resource_id"] == "vm-prod-02"
    assert claims["current_utilization"] == 64.34
    assert claims["projected_90d"] == 100.00
    assert claims["projected_breach_date"] == "2026-08-31"


def test_extract_underutilization_claims():
    sample_text = """### 💡 Infrastructure Optimization & Right-Sizing Report

#### Candidate: vm-dev-01 (development tag)
- **Average CPU utilization:** 8.07% (Threshold: < 20%)
- **Average Memory utilization:** 12.03% (Threshold: < 20%)
- **Current daily cost:** 9.43 USD
- **Decommission Savings:** **283.03 USD/Month**
- **Confidence Level:** High

**Total Potential Savings: 283.03 USD/Month**
"""
    claims = extract_underutilization_claims(sample_text)
    assert claims["total_monthly_saving"] == 283.03
    assert len(claims["candidates"]) == 1
    assert claims["candidates"][0]["resource_id"] == "vm-dev-01"
    assert claims["candidates"][0]["avg_cpu"] == 8.07
    assert claims["candidates"][0]["savings"] == 283.03


def test_validate_narrative_accuracy_on_temp_db(tmp_path):
    db_file = str(tmp_path / "test_val.db")
    conn = duckdb.connect(db_file)

    conn.execute("CREATE TABLE narrative_insights (id INTEGER, scenario VARCHAR, resource_id VARCHAR, insight_text VARCHAR)")
    conn.execute("CREATE TABLE anomaly_alerts (resource_id VARCHAR, metric_name VARCHAR, value DOUBLE, z_score DOUBLE, timestamp TIMESTAMP)")
    conn.execute("CREATE TABLE capacity_forecasts (resource_id VARCHAR, metric_name VARCHAR, current_value DOUBLE, projected_90d DOUBLE, projected_breach_date VARCHAR)")
    conn.execute("CREATE TABLE underutilized_resources (resource_id VARCHAR, avg_cpu DOUBLE, avg_memory DOUBLE, potential_monthly_saving DOUBLE)")

    conn.execute("INSERT INTO anomaly_alerts VALUES ('vm-prod-01', 'daily_cost', 300.0, 3.47, '2026-07-12 00:00:00')")
    conn.execute("INSERT INTO capacity_forecasts VALUES ('vm-prod-02', 'cpu_utilization', 64.34, 100.0, '2026-08-31')")
    conn.execute("INSERT INTO underutilized_resources VALUES ('vm-dev-01', 8.07, 12.03, 283.03)")

    conn.execute(
        "INSERT INTO narrative_insights VALUES "
        "(1, 'cost_anomaly', 'vm-prod-01', '### ⚠️ Cost Anomaly Detected: vm-prod-01\\n\\nSpiked to **300.00 USD** (Z-Score: **3.47**)'), "
        "(2, 'capacity_risk', 'vm-prod-02', '### 📈 Capacity Risk Alert: vm-prod-02 (CPU)\\n\\n- **Current CPU average:** 64.34%\\n- **Projected 90-Day CPU:** 100.00%\\n- **Projected Breach Date (80%):** 2026-08-31'), "
        "(3, 'underutilization', 'CONSOLIDATED', '### 💡 Infrastructure Optimization & Right-Sizing Report\\n\\n#### Candidate: vm-dev-01 (development tag)\\n- **Average CPU utilization:** 8.07%\\n- **Average Memory utilization:** 12.03%\\n- **Decommission Savings:** **283.03 USD/Month**\\n\\n**Total Potential Savings: 283.03 USD/Month**')"
    )

    report = validate_narrative_accuracy(conn=conn)
    assert report["total_checked"] == 3
    assert report["passed"] == 3
    assert report["failed"] == 0

    conn.close()
