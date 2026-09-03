"""Unit tests for data validation rules and schema enforcement."""

from __future__ import annotations

import duckdb
import pytest

from validation.data_validator import (
    validate_analytical_tables,
    validate_raw_metric_records,
)


def test_validate_raw_metric_records_valid():
    valid_records = [
        {
            "source": "azure_monitor",
            "resource_id": "vm-prod-01",
            "metric_name": "cpu_utilization",
            "value": 45.5,
            "unit": "percent",
            "timestamp": "2026-07-12T10:00:00Z",
            "region": "centralus",
            "service_tag": "compute",
        },
        {
            "source": "azure_cost",
            "resource_id": "vm-prod-01",
            "metric_name": "daily_cost",
            "value": 115.0,
            "unit": "usd",
            "timestamp": "2026-07-12T10:00:00Z",
            "region": "centralus",
            "service_tag": "compute",
        },
    ]
    res = validate_raw_metric_records(valid_records)
    assert res.passed is True
    assert len(res.errors) == 0
    assert res.valid_records == 2


def test_validate_raw_metric_records_null_or_missing():
    invalid_records = [
        {
            "source": "azure_monitor",
            # resource_id missing
            "metric_name": "cpu_utilization",
            "value": 45.5,
            "unit": "percent",
            "timestamp": "2026-07-12T10:00:00Z",
            "region": "centralus",
            "service_tag": "compute",
        },
        {
            "source": "azure_cost",
            "resource_id": "vm-prod-01",
            "metric_name": "daily_cost",
            "value": None,  # null value
            "unit": "usd",
            "timestamp": "2026-07-12T10:00:00Z",
            "region": "centralus",
            "service_tag": "compute",
        },
    ]
    res = validate_raw_metric_records(invalid_records)
    assert res.passed is False
    assert len(res.errors) >= 2


def test_validate_raw_metric_records_boundary_violations():
    boundary_violations = [
        {
            "source": "azure_monitor",
            "resource_id": "vm-prod-01",
            "metric_name": "cpu_utilization",
            "value": 150.0,  # > 100%
            "unit": "percent",
            "timestamp": "2026-07-12T10:00:00Z",
            "region": "centralus",
            "service_tag": "compute",
        },
        {
            "source": "azure_cost",
            "resource_id": "vm-prod-01",
            "metric_name": "daily_cost",
            "value": -10.0,  # Negative cost
            "unit": "usd",
            "timestamp": "2026-07-12T10:00:00Z",
            "region": "centralus",
            "service_tag": "compute",
        },
    ]
    res = validate_raw_metric_records(boundary_violations)
    assert res.passed is False
    assert len(res.errors) == 2


def test_validate_raw_metric_records_duplicates_and_timestamps():
    records = [
        {
            "source": "azure_monitor",
            "resource_id": "vm-prod-01",
            "metric_name": "cpu_utilization",
            "value": 45.0,
            "unit": "percent",
            "timestamp": "invalid-timestamp-string",
            "region": "centralus",
            "service_tag": "compute",
        },
        {
            "source": "azure_monitor",
            "resource_id": "vm-prod-01",
            "metric_name": "cpu_utilization",
            "value": 45.0,
            "unit": "percent",
            "timestamp": 1234567,  # invalid type
            "region": "centralus",
            "service_tag": "compute",
        },
        {
            "source": "azure_monitor",
            "resource_id": "vm-prod-dup",
            "metric_name": "cpu_utilization",
            "value": 45.0,
            "unit": "percent",
            "timestamp": "2026-07-12T10:00:00Z",
            "region": "centralus",
            "service_tag": "compute",
        },
        {
            "source": "azure_monitor",
            "resource_id": "vm-prod-dup",
            "metric_name": "cpu_utilization",
            "value": 45.0,
            "unit": "percent",
            "timestamp": "2026-07-12T10:00:00Z",
            "region": "centralus",
            "service_tag": "compute",
        },
    ]
    res = validate_raw_metric_records(records)
    assert res.passed is False
    assert len(res.warnings) >= 1  # Duplicate detected


def test_validate_analytical_tables_errors(tmp_path):
    db_file = str(tmp_path / "test_tables_err.db")
    conn = duckdb.connect(db_file)

    conn.execute("CREATE TABLE daily_metrics_rollup (date DATE, resource_id VARCHAR, avg_value DOUBLE, count INTEGER)")
    conn.execute("CREATE TABLE anomaly_alerts (z_score DOUBLE, severity VARCHAR)")
    conn.execute("CREATE TABLE capacity_forecasts (current_value DOUBLE, projected_90d DOUBLE, crosses_80_threshold INTEGER)")
    conn.execute("CREATE TABLE underutilized_resources (avg_cpu DOUBLE, avg_memory DOUBLE, potential_monthly_saving DOUBLE)")

    conn.execute("INSERT INTO daily_metrics_rollup VALUES (NULL, 'vm-1', 45.0, 0)")
    conn.execute("INSERT INTO anomaly_alerts VALUES (NULL, 'InvalidSeverity')")
    conn.execute("INSERT INTO capacity_forecasts VALUES (NULL, 95.0, 99)")
    conn.execute("INSERT INTO underutilized_resources VALUES (85.0, 15.0, -50.0)")

    res = validate_analytical_tables(conn=conn)
    assert res.passed is False
    assert len(res.errors) == 4

    conn.close()
