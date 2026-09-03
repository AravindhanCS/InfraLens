"""Unit tests for the Transformation and Analytical Layer."""

from __future__ import annotations

from datetime import datetime, timedelta

import duckdb
import pytest

from transformation.aggregate import aggregate_metrics
from transformation.anomaly import detect_anomalies
from transformation.forecast import forecast_usage
from transformation.optimization import analyze_underutilization


@pytest.fixture
def mock_db_conn():
    """Create an in-memory DuckDB database and seed it with test metrics."""
    conn = duckdb.connect(":memory:")

    # Initialize raw_metrics table
    conn.execute(
        """
        CREATE TABLE raw_metrics (
            source VARCHAR,
            resource_id VARCHAR,
            metric_name VARCHAR,
            value DOUBLE,
            unit VARCHAR,
            timestamp TIMESTAMP,
            region VARCHAR,
            service_tag VARCHAR
        )
        """
    )

    # Seed 15 days of data ending today to test rollups, rolling 14-day anomalies, and 7-day underutilization
    now = datetime.utcnow()
    records = []

    for day in range(15):
        dt = now - timedelta(days=day)
        timestamp_str = dt.isoformat() + "Z"

        # 1. normal compute resource: vm-prod-01 (normal CPU/memory, cost spike on last day)
        is_last_day = day == 0
        cost_val = 300.0 if is_last_day else 100.0
        records.append(
            ("azure_monitor", "vm-prod-01", "cpu_utilization", 50.0, "percent", timestamp_str, "centralus", "compute")
        )
        records.append(
            ("azure_monitor", "vm-prod-01", "memory_utilization", 60.0, "percent", timestamp_str, "centralus", "compute")
        )
        records.append(
            ("azure_cost", "vm-prod-01", "daily_cost", cost_val, "usd", timestamp_str, "centralus", "compute")
        )

        # 2. growing compute resource: vm-prod-02 (CPU starts at 40% and grows to 80% on day 15)
        cpu_val = 80.0 - (2.0 * day)  # linear growth towards today
        records.append(
            ("azure_monitor", "vm-prod-02", "cpu_utilization", cpu_val, "percent", timestamp_str, "centralus", "compute")
        )
        records.append(
            ("azure_monitor", "vm-prod-02", "memory_utilization", 40.0, "percent", timestamp_str, "centralus", "compute")
        )

        # 3. underutilized resource: vm-dev-01 (CPU 5%, Memory 10%, cost $5)
        records.append(
            ("azure_monitor", "vm-dev-01", "cpu_utilization", 5.0, "percent", timestamp_str, "centralus", "development")
        )
        records.append(
            ("azure_monitor", "vm-dev-01", "memory_utilization", 10.0, "percent", timestamp_str, "centralus", "development")
        )
        records.append(
            ("azure_cost", "vm-dev-01", "daily_cost", 5.0, "usd", timestamp_str, "centralus", "development")
        )

    # Insert seeded records
    conn.executemany(
        """
        INSERT INTO raw_metrics (
            source, resource_id, metric_name, value, unit, timestamp, region, service_tag
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        records,
    )

    yield conn
    conn.close()


def test_aggregate_metrics(mock_db_conn):
    """Test that hourly and daily rollups aggregate correctly."""
    aggregate_metrics(mock_db_conn)

    # Verify hourly rollup
    h_count = mock_db_conn.execute("SELECT COUNT(*) FROM hourly_metrics_rollup").fetchone()[0]
    assert h_count > 0

    # Verify daily rollup avg/min/max
    res = mock_db_conn.execute(
        """
        SELECT avg_value, min_value, max_value 
        FROM daily_metrics_rollup 
        WHERE resource_id = 'vm-prod-01' AND metric_name = 'cpu_utilization'
        """
    ).fetchall()
    assert len(res) == 15
    for avg, min_v, max_v in res:
        assert avg == 50.0
        assert min_v == 50.0
        assert max_v == 50.0


def test_detect_anomalies_cost_spike(mock_db_conn):
    """Test rolling 14-day z-score flags critical anomalies."""
    aggregate_metrics(mock_db_conn)
    detect_anomalies(mock_db_conn)

    # There should be a cost anomaly flagged for vm-prod-01 on the spiked day
    alerts = mock_db_conn.execute(
        """
        SELECT resource_id, metric_name, value, severity, z_score 
        FROM anomaly_alerts 
        WHERE resource_id = 'vm-prod-01' AND metric_name = 'daily_cost'
        """
    ).fetchall()

    assert len(alerts) > 0
    assert alerts[0][3] == "Critical"
    assert alerts[0][4] > 3.0  # z-score should be above 3.0 for cost spike


def test_forecast_usage_regression(mock_db_conn):
    """Test that linear regression forecasts CPU growth and breach date."""
    aggregate_metrics(mock_db_conn)
    forecast_usage(mock_db_conn)

    # vm-prod-02 is linearly growing and should cross 80% threshold
    forecasts = mock_db_conn.execute(
        """
        SELECT resource_id, metric_name, current_value, projected_90d, crosses_80_threshold, projected_breach_date
        FROM capacity_forecasts
        WHERE resource_id = 'vm-prod-02' AND metric_name = 'cpu_utilization'
        """
    ).fetchone()

    assert forecasts is not None
    assert forecasts[2] == 66.0  # current rolling average is 66%
    assert forecasts[3] > 80.0  # 90d projection should be > 80%
    assert forecasts[4] == 1  # crosses_80_threshold is True (1)
    assert forecasts[5] is not None  # breach date is calculated


def test_analyze_underutilization(mock_db_conn):
    """Test underutilization scoring flags low-resource VMs."""
    aggregate_metrics(mock_db_conn)
    analyze_underutilization(mock_db_conn)

    # vm-dev-01 should be flagged as underutilized (CPU 5%, Memory 10% < 20%)
    cands = mock_db_conn.execute(
        """
        SELECT resource_id, avg_cpu, avg_memory, daily_cost, potential_monthly_saving
        FROM underutilized_resources
        """
    ).fetchall()

    assert len(cands) == 1
    assert cands[0][0] == "vm-dev-01"
    assert cands[0][1] == 5.0
    assert cands[0][2] == 10.0
    assert cands[0][3] == 5.0
    assert cands[0][4] == 150.0  # potential savings: $5 * 30 days
