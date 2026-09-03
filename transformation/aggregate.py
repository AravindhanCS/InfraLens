"""Aggregation utilities for InfraLens."""

from __future__ import annotations

from database.duckdb_store import get_duckdb_connection


def aggregate_metrics(conn=None) -> None:
    """Aggregate raw metrics in DuckDB into hourly and daily rollups."""
    close_conn = False
    if conn is None:
        conn = get_duckdb_connection()
        close_conn = True

    print("Running aggregation of raw metrics in DuckDB...")

    # Create hourly metrics rollup table
    conn.execute(
        """
        CREATE OR REPLACE TABLE hourly_metrics_rollup AS
        SELECT
            source,
            resource_id,
            metric_name,
            service_tag,
            region,
            unit,
            date_trunc('hour', timestamp) AS timestamp,
            AVG(value) AS avg_value,
            MIN(value) AS min_value,
            MAX(value) AS max_value,
            COUNT(value) AS count_value
        FROM raw_metrics
        GROUP BY source, resource_id, metric_name, service_tag, region, unit, date_trunc('hour', timestamp)
        """
    )

    # Create daily metrics rollup table
    conn.execute(
        """
        CREATE OR REPLACE TABLE daily_metrics_rollup AS
        SELECT
            source,
            resource_id,
            metric_name,
            service_tag,
            region,
            unit,
            date_trunc('day', timestamp) AS timestamp,
            AVG(value) AS avg_value,
            MIN(value) AS min_value,
            MAX(value) AS max_value,
            COUNT(value) AS count_value
        FROM raw_metrics
        GROUP BY source, resource_id, metric_name, service_tag, region, unit, date_trunc('day', timestamp)
        """
    )

    h_count = conn.execute("SELECT COUNT(*) FROM hourly_metrics_rollup").fetchone()[0]
    d_count = conn.execute("SELECT COUNT(*) FROM daily_metrics_rollup").fetchone()[0]
    print(f"Aggregations complete. Hourly rows: {h_count}, Daily rows: {d_count}")

    if close_conn:
        conn.close()
