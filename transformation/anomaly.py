"""Anomaly detection utilities for InfraLens."""

from __future__ import annotations

import numpy as np
import pandas as pd

from database.duckdb_store import get_duckdb_connection


def detect_anomalies(conn=None) -> None:
    """Calculate rolling 14-day z-scores for metrics and flag outliers."""
    close_conn = False
    if conn is None:
        conn = get_duckdb_connection()
        close_conn = True

    print("Running anomaly detection pipeline...")

    # Load daily metrics rollup
    query = "SELECT * FROM daily_metrics_rollup ORDER BY timestamp"
    df = conn.execute(query).df()

    if df.empty:
        print("No daily metrics found. Skipping anomaly detection.")
        if close_conn:
            conn.close()
        return

    # Convert timestamp to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    anomalies_list = []

    # Group by resource and metric to calculate z-scores over time
    grouped = df.groupby(["resource_id", "metric_name"])

    for (resource_id, metric_name), group in grouped:
        group = group.sort_values("timestamp")

        # Rolling 14-day calculations
        # Using closed='both' or rolling over a 14D window. Since we have daily rows,
        # window=14 corresponds to 14 days. min_periods=3 allows starting early.
        rolling_mean = group["avg_value"].rolling(window=14, min_periods=3).mean()
        rolling_std = group["avg_value"].rolling(window=14, min_periods=3).std()

        # Compute z-score
        # Handle cases where std is 0 or NaN
        z_scores = np.where(
            rolling_std > 0,
            (group["avg_value"] - rolling_mean) / rolling_std,
            0.0,
        )

        group = group.copy()
        group["z_score"] = z_scores

        # Filter anomalies where absolute z-score is greater than 2.0
        flagged = group[np.abs(group["z_score"]) > 2.0]

        for _, row in flagged.iterrows():
            z = abs(row["z_score"])
            severity = "Critical" if z > 3.0 else "Warning"

            anomalies_list.append({
                "timestamp": row["timestamp"].isoformat(),
                "source": row["source"],
                "resource_id": row["resource_id"],
                "metric_name": row["metric_name"],
                "value": float(row["avg_value"]),
                "z_score": float(row["z_score"]),
                "severity": severity,
                "service_tag": row["service_tag"],
                "region": row["region"],
            })

    # Write anomalies to DuckDB table 'anomaly_alerts'
    if anomalies_list:
        anomalies_df = pd.DataFrame(anomalies_list)

        # Initialize/overwrite anomaly_alerts table in DuckDB
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS anomaly_alerts (
                timestamp TIMESTAMP,
                source VARCHAR,
                resource_id VARCHAR,
                metric_name VARCHAR,
                value DOUBLE,
                z_score DOUBLE,
                severity VARCHAR,
                service_tag VARCHAR,
                region VARCHAR
            )
            """
        )

        # Clear existing alerts before writing new ones to avoid duplicate alerts on re-run
        conn.execute("DELETE FROM anomaly_alerts")

        # Insert using executemany
        conn.executemany(
            """
            INSERT INTO anomaly_alerts (
                timestamp, source, resource_id, metric_name, value, z_score, severity, service_tag, region
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row["timestamp"],
                    row["source"],
                    row["resource_id"],
                    row["metric_name"],
                    row["value"],
                    row["z_score"],
                    row["severity"],
                    row["service_tag"],
                    row["region"],
                )
                for _, row in anomalies_df.iterrows()
            ],
        )

        alert_count = conn.execute("SELECT COUNT(*) FROM anomaly_alerts").fetchone()[0]
        print(f"Anomaly detection complete. Flagged {alert_count} alerts in anomaly_alerts.")
    else:
        print("No anomalies detected.")
        # Ensure table exists even if empty
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS anomaly_alerts (
                timestamp TIMESTAMP,
                source VARCHAR,
                resource_id VARCHAR,
                metric_name VARCHAR,
                value DOUBLE,
                z_score DOUBLE,
                severity VARCHAR,
                service_tag VARCHAR,
                region VARCHAR
            )
            """
        )

    if close_conn:
        conn.close()
