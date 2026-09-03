"""Optimization analysis utilities for InfraLens."""

from __future__ import annotations

from database.duckdb_store import get_duckdb_connection


def analyze_underutilization(conn=None) -> None:
    """Analyze CPU and memory utilization to identify underutilized resources (<20% average)."""
    close_conn = False
    if conn is None:
        conn = get_duckdb_connection()
        close_conn = True

    print("Running underutilization optimization analysis...")

    # Query to calculate 7-day averages and join with latest daily cost
    # Flagging resources where both CPU and memory averages are less than 20%
    conn.execute(
        """
        CREATE OR REPLACE TABLE underutilized_resources AS
        WITH last_7_days AS (
            SELECT
                resource_id,
                metric_name,
                service_tag,
                region,
                avg_value
            FROM daily_metrics_rollup
            WHERE timestamp >= (SELECT MAX(timestamp) FROM daily_metrics_rollup) - INTERVAL 7 DAY
              AND metric_name IN ('cpu_utilization', 'memory_utilization')
        ),
        pivoted AS (
            SELECT
                resource_id,
                service_tag,
                region,
                AVG(CASE WHEN metric_name = 'cpu_utilization' THEN avg_value END) AS avg_cpu,
                AVG(CASE WHEN metric_name = 'memory_utilization' THEN avg_value END) AS avg_memory
            FROM last_7_days
            GROUP BY resource_id, service_tag, region
        ),
        latest_daily_cost AS (
            SELECT
                resource_id,
                avg_value AS daily_cost
            FROM (
                SELECT
                    resource_id,
                    avg_value,
                    ROW_NUMBER() OVER (PARTITION BY resource_id ORDER BY timestamp DESC) as rn
                FROM daily_metrics_rollup
                WHERE metric_name = 'daily_cost'
            )
            WHERE rn = 1
        )
        SELECT
            p.resource_id,
            COALESCE(p.avg_cpu, 0.0) AS avg_cpu,
            COALESCE(p.avg_memory, 0.0) AS avg_memory,
            COALESCE(c.daily_cost, 0.0) AS daily_cost,
            COALESCE(c.daily_cost, 0.0) * 30.0 AS potential_monthly_saving,
            p.service_tag,
            p.region
        FROM pivoted p
        LEFT JOIN latest_daily_cost c ON p.resource_id = c.resource_id
        WHERE p.avg_cpu < 20.0 AND p.avg_memory < 20.0
        """
    )

    underutil_count = conn.execute("SELECT COUNT(*) FROM underutilized_resources").fetchone()[0]
    print(f"Optimization analysis complete. Flagged {underutil_count} candidates in underutilized_resources.")

    if close_conn:
        conn.close()
