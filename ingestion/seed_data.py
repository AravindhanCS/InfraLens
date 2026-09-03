"""Data seeding script to generate 30 days of historical infrastructure metrics."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import random

from database.clickhouse_store import (
    get_clickhouse_client,
    init_clickhouse_tables,
    write_metrics_to_clickhouse,
)
from database.duckdb_store import get_duckdb_connection, init_duckdb_tables, write_metrics_to_duckdb
from ingestion.schema import normalize_metric_record


def generate_historical_data(days=30):
    """Generate normalized metric and cost records spanning the past N days."""
    records = []
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)

    # 1. Generate hourly metrics
    current_time = start_time
    total_hours = days * 24

    for hour_idx in range(total_hours):
        dt = start_time + timedelta(hours=hour_idx)
        timestamp_str = dt.isoformat() + "Z"

        # vm-prod-01 (Normal compute metrics)
        cpu_val = max(0.0, min(100.0, 45.0 + random.uniform(-5.0, 5.0)))
        mem_val = max(0.0, min(100.0, 55.0 + random.uniform(-2.0, 2.0)))
        records.append(
            normalize_metric_record(
                source="azure_monitor",
                resource_id="vm-prod-01",
                metric_name="cpu_utilization",
                value=cpu_val,
                unit="percent",
                timestamp=timestamp_str,
                region="centralus",
                service_tag="compute",
            )
        )
        records.append(
            normalize_metric_record(
                source="azure_monitor",
                resource_id="vm-prod-01",
                metric_name="memory_utilization",
                value=mem_val,
                unit="percent",
                timestamp=timestamp_str,
                region="centralus",
                service_tag="compute",
            )
        )

        # vm-dev-01 (Underutilized resource)
        dev_cpu = max(0.0, min(100.0, 8.0 + random.uniform(-2.0, 2.0)))
        dev_mem = max(0.0, min(100.0, 12.0 + random.uniform(-1.0, 1.0)))
        records.append(
            normalize_metric_record(
                source="azure_monitor",
                resource_id="vm-dev-01",
                metric_name="cpu_utilization",
                value=dev_cpu,
                unit="percent",
                timestamp=timestamp_str,
                region="centralus",
                service_tag="development",
            )
        )
        records.append(
            normalize_metric_record(
                source="azure_monitor",
                resource_id="vm-dev-01",
                metric_name="memory_utilization",
                value=dev_mem,
                unit="percent",
                timestamp=timestamp_str,
                region="centralus",
                service_tag="development",
            )
        )

        # vm-prod-02 (Growing utilization capacity risk)
        # Linear growth: CPU utilization starts at 35% and grows to 80% on day 30
        growth_fraction = hour_idx / total_hours
        prod2_cpu = max(0.0, min(100.0, 35.0 + (45.0 * growth_fraction) + random.uniform(-2.0, 2.0)))
        prod2_mem = max(0.0, min(100.0, 60.0 + random.uniform(-1.0, 1.0)))
        records.append(
            normalize_metric_record(
                source="azure_monitor",
                resource_id="vm-prod-02",
                metric_name="cpu_utilization",
                value=prod2_cpu,
                unit="percent",
                timestamp=timestamp_str,
                region="centralus",
                service_tag="compute",
            )
        )
        records.append(
            normalize_metric_record(
                source="azure_monitor",
                resource_id="vm-prod-02",
                metric_name="memory_utilization",
                value=prod2_mem,
                unit="percent",
                timestamp=timestamp_str,
                region="centralus",
                service_tag="compute",
            )
        )

        # Datadog metrics (svc-api-gateway request rates and latency)
        req_rate = max(0.0, 1200.0 + random.uniform(-100.0, 100.0))
        err_rate = max(0.0, min(100.0, 0.5 + random.uniform(-0.2, 0.2)))
        records.append(
            normalize_metric_record(
                source="datadog",
                resource_id="svc-api-gateway",
                metric_name="request_rate",
                value=req_rate,
                unit="rpm",
                timestamp=timestamp_str,
                region="eastus2",
                service_tag="api",
            )
        )
        records.append(
            normalize_metric_record(
                source="datadog",
                resource_id="svc-api-gateway",
                metric_name="error_rate",
                value=err_rate,
                unit="percent",
                timestamp=timestamp_str,
                region="eastus2",
                service_tag="api",
            )
        )

    # 2. Generate daily cost metrics (1 record per day per resource)
    for day_idx in range(days):
        dt = start_time + timedelta(days=day_idx)
        # Set daily cost timestamp to the start of the day
        cost_timestamp = datetime(dt.year, dt.month, dt.day).isoformat() + "Z"

        # normal cost is ~100 USD/day, but on day 30 it spikes to 300 USD
        is_last_day = (day_idx == days - 1)
        prod1_cost = 300.0 if is_last_day else max(0.0, 100.0 + random.uniform(-5.0, 5.0))
        dev1_cost = max(0.0, 10.0 + random.uniform(-1.0, 1.0))
        prod2_cost = max(0.0, 150.0 + random.uniform(-8.0, 8.0))
        gateway_cost = max(0.0, 50.0 + random.uniform(-2.0, 2.0))

        records.append(
            normalize_metric_record(
                source="azure_cost",
                resource_id="vm-prod-01",
                metric_name="daily_cost",
                value=prod1_cost,
                unit="usd",
                timestamp=cost_timestamp,
                region="centralus",
                service_tag="compute",
            )
        )
        records.append(
            normalize_metric_record(
                source="azure_cost",
                resource_id="vm-dev-01",
                metric_name="daily_cost",
                value=dev1_cost,
                unit="usd",
                timestamp=cost_timestamp,
                region="centralus",
                service_tag="development",
            )
        )
        records.append(
            normalize_metric_record(
                source="azure_cost",
                resource_id="vm-prod-02",
                metric_name="daily_cost",
                value=prod2_cost,
                unit="usd",
                timestamp=cost_timestamp,
                region="centralus",
                service_tag="compute",
            )
        )
        records.append(
            normalize_metric_record(
                source="azure_cost",
                resource_id="svc-api-gateway",
                metric_name="daily_cost",
                value=gateway_cost,
                unit="usd",
                timestamp=cost_timestamp,
                region="eastus2",
                service_tag="api",
            )
        )

    return records


def seed_databases(days=30):
    """Generate and write historical telemetry to DuckDB and ClickHouse."""
    print(f"Generating {days} days of historical telemetry...")
    records = generate_historical_data(days=days)
    print(f"Generated {len(records)} records.")

    # Write to DuckDB
    print("Writing to DuckDB...")
    duck_rows = write_metrics_to_duckdb(records)
    print(f"DuckDB table populated. Total rows in DuckDB raw_metrics: {duck_rows}")

    # Write to ClickHouse
    print("Writing to ClickHouse...")
    try:
        ch_client = get_clickhouse_client()
        init_clickhouse_tables(ch_client)
        # Parse timestamp strings back to datetime objects for clickhouse client insertion
        ch_records = []
        for r in records:
            r_copy = r.copy()
            # Convert ISO 8601 string to datetime object
            ts_str = r_copy["timestamp"]
            if ts_str.endswith("Z"):
                ts_str = ts_str[:-1]
            r_copy["timestamp"] = datetime.fromisoformat(ts_str)
            ch_records.append(r_copy)

        ch_rows = write_metrics_to_clickhouse(ch_client, ch_records)
        print(f"ClickHouse table populated. Total rows in ClickHouse infra_metrics: {ch_rows}")
    except Exception as e:
        print(f"Warning: Failed to write to ClickHouse: {e}")
        print("Continuing pipeline...")

    print("Seeding complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30, help="Number of historical days to seed")
    args = parser.parse_args()
    seed_databases(days=args.days)
