"""Active ingestion runner to pull latest metrics and persist to database stores."""

from __future__ import annotations

from datetime import datetime

from database.clickhouse_store import (
    get_clickhouse_client,
    init_clickhouse_tables,
    write_metrics_to_clickhouse,
)
from database.duckdb_store import get_duckdb_connection, init_duckdb_tables, write_metrics_to_duckdb
from ingestion.azure_cost import fetch_cost_data
from ingestion.azure_monitor import fetch_monitor_metrics
from ingestion.datadog import fetch_datadog_metrics


def run_ingestion():
    """Ingest current metrics from Azure Monitor, Azure Cost, and Datadog."""
    print("Running multi-source data ingestion pipeline...")

    # Fetch normalized records
    azure_monitor_records = fetch_monitor_metrics()
    azure_cost_records = fetch_cost_data()
    datadog_records = fetch_datadog_metrics()

    all_records = []
    all_records.extend(azure_monitor_records)
    all_records.extend(azure_cost_records)
    all_records.extend(datadog_records)

    print(f"Fetched {len(all_records)} metrics from sources:")
    print(f"  - Azure Monitor: {len(azure_monitor_records)} metrics")
    print(f"  - Azure Cost: {len(azure_cost_records)} metrics")
    print(f"  - Datadog: {len(datadog_records)} metrics")

    if not all_records:
        print("No new records to ingest.")
        return

    # Write to DuckDB
    print("Writing to DuckDB...")
    duck_rows = write_metrics_to_duckdb(all_records)
    print(f"DuckDB raw_metrics table updated. Total rows in DuckDB: {duck_rows}")

    # Write to ClickHouse
    print("Writing to ClickHouse...")
    try:
        ch_client = get_clickhouse_client()
        init_clickhouse_tables(ch_client)

        # Parse timestamp strings back to datetime objects for clickhouse-connect
        ch_records = []
        for r in all_records:
            r_copy = r.copy()
            ts_str = r_copy["timestamp"]
            if ts_str.endswith("Z"):
                ts_str = ts_str[:-1]
            r_copy["timestamp"] = datetime.fromisoformat(ts_str)
            ch_records.append(r_copy)

        ch_rows = write_metrics_to_clickhouse(ch_client, ch_records)
        print(f"ClickHouse infra_metrics table updated. Total rows in ClickHouse: {ch_rows}")
    except Exception as e:
        print(f"Warning: Failed to write to ClickHouse: {e}")
        print("Continuing pipeline...")

    print("Ingestion pipeline finished successfully.")


if __name__ == "__main__":
    run_ingestion()
