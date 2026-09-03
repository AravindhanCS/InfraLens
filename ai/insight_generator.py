"""Orchestration script to query DuckDB and generate AI narrative insights."""

from __future__ import annotations

from datetime import datetime
import pandas as pd

from database.duckdb_store import get_duckdb_connection
from ai.gemini import generate_insight
from ai.prompts import (
    SYSTEM_PROMPT,
    COST_ANOMALY_PROMPT,
    CAPACITY_RISK_PROMPT,
    UNDERUTILIZATION_PROMPT,
)


def generate_narrative_insights(conn=None) -> None:
    """Generate plain-language insights for cost anomalies, capacity risks, and underutilization."""
    close_conn = False
    if conn is None:
        conn = get_duckdb_connection()
        close_conn = True

    print("Generating AI narrative insights...")
    now_str = datetime.utcnow().isoformat() + "Z"

    # Create narrative_insights table if it doesn't exist
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS narrative_insights (
            timestamp TIMESTAMP,
            scenario VARCHAR,
            resource_id VARCHAR,
            insight_text VARCHAR
        )
        """
    )
    # Clear existing insights to keep the dashboard fresh on refresh
    conn.execute("DELETE FROM narrative_insights")

    insights_to_insert = []

    # ----------------------------------------------------
    # SCENARIO 1: Cost Anomalies (>30% above 30-day average)
    # ----------------------------------------------------
    try:
        cost_anomaly_query = """
            WITH cost_averages AS (
                SELECT
                    resource_id,
                    AVG(avg_value) AS avg_30d_cost
                FROM daily_metrics_rollup
                WHERE metric_name = 'daily_cost'
                  AND timestamp >= (SELECT MAX(timestamp) FROM daily_metrics_rollup) - INTERVAL 30 DAY
                GROUP BY resource_id
            ),
            latest_costs AS (
                SELECT
                    resource_id,
                    timestamp,
                    avg_value AS current_cost,
                    source,
                    service_tag,
                    region,
                    unit
                FROM (
                    SELECT
                        resource_id,
                        timestamp,
                        avg_value,
                        source,
                        service_tag,
                        region,
                        unit,
                        ROW_NUMBER() OVER (PARTITION BY resource_id ORDER BY timestamp DESC) AS rn
                    FROM daily_metrics_rollup
                    WHERE metric_name = 'daily_cost'
                )
                WHERE rn = 1
            )
            SELECT
                a.timestamp,
                a.resource_id,
                a.metric_name,
                a.value,
                a.z_score,
                a.severity,
                a.service_tag,
                a.region,
                c.avg_30d_cost,
                l.unit,
                ((a.value - c.avg_30d_cost) / c.avg_30d_cost) * 100.0 AS pct_increase
            FROM anomaly_alerts a
            JOIN cost_averages c ON a.resource_id = c.resource_id
            JOIN latest_costs l ON a.resource_id = l.resource_id
            WHERE a.metric_name = 'daily_cost'
              AND a.value > c.avg_30d_cost * 1.30
        """
        cost_anomalies = conn.execute(cost_anomaly_query).df()

        for _, row in cost_anomalies.iterrows():
            resource_id = row["resource_id"]
            context_data = {
                "resource_id": resource_id,
                "region": row["region"],
                "metric_name": row["metric_name"],
                "value": float(row["value"]),
                "unit": row["unit"],
                "z_score": float(row["z_score"]),
                "avg_30d_cost": float(row["avg_30d_cost"]),
                "pct_increase": float(row["pct_increase"]),
                "service_tag": row["service_tag"],
            }
            prompt = COST_ANOMALY_PROMPT.format(**context_data)
            print(f"Generating Cost Anomaly narrative for resource: {resource_id}...")
            narrative = generate_insight(
                system_prompt=SYSTEM_PROMPT,
                prompt=prompt,
                scenario="cost_anomaly",
                context_data=context_data,
            )
            insights_to_insert.append((now_str, "cost_anomaly", resource_id, narrative))

    except Exception as e:
        print(f"Error querying/generating cost anomaly insights: {e}")

    # ----------------------------------------------------
    # SCENARIO 2: Capacity Risks (90-day utilization >80%)
    # ----------------------------------------------------
    try:
        capacity_risk_query = """
            SELECT *
            FROM capacity_forecasts
            WHERE crosses_80_threshold = 1
        """
        capacity_risks = conn.execute(capacity_risk_query).df()

        for _, row in capacity_risks.iterrows():
            resource_id = row["resource_id"]
            context_data = {
                "resource_id": resource_id,
                "metric_name": row["metric_name"],
                "current_value": float(row["current_value"]),
                "projected_90d": float(row["projected_90d"]),
                "growth_rate_per_day": float(row["growth_rate_per_day"]),
                "projected_breach_date": row["projected_breach_date"] or "N/A",
                "service_tag": row["service_tag"],
                "region": row["region"],
            }
            prompt = CAPACITY_RISK_PROMPT.format(**context_data)
            print(f"Generating Capacity Risk narrative for resource: {resource_id}...")
            narrative = generate_insight(
                system_prompt=SYSTEM_PROMPT,
                prompt=prompt,
                scenario="capacity_risk",
                context_data=context_data,
            )
            insights_to_insert.append((now_str, "capacity_risk", resource_id, narrative))

    except Exception as e:
        print(f"Error querying/generating capacity risk insights: {e}")

    # ----------------------------------------------------
    # SCENARIO 3: Underutilization Optimization (Consolidated Report)
    # ----------------------------------------------------
    try:
        underutil_query = "SELECT * FROM underutilized_resources"
        underutil_resources = conn.execute(underutil_query).df()

        if not underutil_resources.empty:
            candidates_list = ""
            candidates_data = []

            for _, row in underutil_resources.iterrows():
                candidates_list += (
                    f"- Resource: {row['resource_id']} ({row['service_tag']} service), "
                    f"Region: {row['region']}, "
                    f"7-day Avg CPU: {row['avg_cpu']:.1f}%, "
                    f"7-day Avg Memory: {row['avg_memory']:.1f}%, "
                    f"Current Daily Cost: {row['daily_cost']:.2f} USD, "
                    f"Est. Monthly Savings: {row['potential_monthly_saving']:.2f} USD\n"
                )
                candidates_data.append({
                    "resource_id": row["resource_id"],
                    "avg_cpu": float(row["avg_cpu"]),
                    "avg_memory": float(row["avg_memory"]),
                    "daily_cost": float(row["daily_cost"]),
                    "potential_monthly_saving": float(row["potential_monthly_saving"]),
                    "service_tag": row["service_tag"],
                })

            prompt = UNDERUTILIZATION_PROMPT.format(candidates_list=candidates_list)
            context_data = {"candidates": candidates_data}

            print("Generating Underutilization Optimization narrative report...")
            narrative = generate_insight(
                system_prompt=SYSTEM_PROMPT,
                prompt=prompt,
                scenario="underutilization",
                context_data=context_data,
            )
            insights_to_insert.append((now_str, "underutilization", None, narrative))
        else:
            print("No underutilized resources found to report.")

    except Exception as e:
        print(f"Error querying/generating underutilization insights: {e}")

    # ----------------------------------------------------
    # Insert Generated Insights into DuckDB
    # ----------------------------------------------------
    if insights_to_insert:
        conn.executemany(
            """
            INSERT INTO narrative_insights (
                timestamp, scenario, resource_id, insight_text
            ) VALUES (?, ?, ?, ?)
            """,
            insights_to_insert,
        )
        print(f"Narrative insights generation complete. Inserted {len(insights_to_insert)} records.")
    else:
        print("No narrative insights generated.")

    if close_conn:
        conn.close()
