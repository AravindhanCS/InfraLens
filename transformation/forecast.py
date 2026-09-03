"""Forecasting utilities for InfraLens."""

from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from database.duckdb_store import get_duckdb_connection


def forecast_usage(conn=None) -> None:
    """Project resource utilization 30, 60, and 90 days into the future using linear regression."""
    close_conn = False
    if conn is None:
        conn = get_duckdb_connection()
        close_conn = True

    print("Running capacity forecasting pipeline...")

    # Load daily utilization metrics (CPU & Memory)
    query = """
        SELECT *
        FROM daily_metrics_rollup
        WHERE metric_name IN ('cpu_utilization', 'memory_utilization')
        ORDER BY timestamp
    """
    df = conn.execute(query).df()

    if df.empty:
        print("No utilization metrics found. Skipping forecasting.")
        if close_conn:
            conn.close()
        return

    # Convert timestamp to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    forecasts_list = []

    # Group by resource and metric
    grouped = df.groupby(["resource_id", "metric_name"])

    for (resource_id, metric_name), group in grouped:
        group = group.sort_values("timestamp").reset_index(drop=True)

        if len(group) < 7:
            # Need at least 7 days of history to perform a reasonable trend analysis
            print(f"Skipping {resource_id} {metric_name}: insufficient history ({len(group)} days)")
            continue

        # Compute 30-day rolling average to smooth out daily spikes/noise
        group["rolling_avg"] = group["avg_value"].rolling(window=30, min_periods=7).mean()
        group = group.dropna(subset=["rolling_avg"]).reset_index(drop=True)

        if group.empty:
            continue

        # Prepare regression variables
        # x is the day index from start of group
        start_date = group["timestamp"].min()
        x = (group["timestamp"] - start_date).dt.days.values
        y = group["rolling_avg"].values

        # Fit linear regression: y = m * x + c
        try:
            m, c = np.polyfit(x, y, 1)
        except Exception as fit_err:
            print(f"Failed to fit regression for {resource_id} {metric_name}: {fit_err}")
            continue

        # Current state
        last_row = group.iloc[-1]
        x_now = x[-1]
        current_val = float(last_row["rolling_avg"])
        today_date = last_row["timestamp"]

        # Predict 30, 60, and 90 days out
        pred_30 = max(0.0, min(100.0, float(m * (x_now + 30) + c)))
        pred_60 = max(0.0, min(100.0, float(m * (x_now + 60) + c)))
        pred_90 = max(0.0, min(100.0, float(m * (x_now + 90) + c)))

        # Determine threshold crossing (80% utilization)
        crosses_80 = 1 if pred_90 > 80.0 else 0

        # Calculate projected breach date if utilization is growing
        projected_breach_date = None
        if current_val >= 80.0:
            projected_breach_date = today_date.strftime("%Y-%m-%d")
        elif m > 0:
            # Day index when it will hit 80%
            days_to_breach = (80.0 - c) / m - x_now
            if 0 < days_to_breach < 3650:
                try:
                    breach_dt = today_date + timedelta(days=float(days_to_breach))
                    projected_breach_date = breach_dt.strftime("%Y-%m-%d")
                except (OverflowError, ValueError):
                    projected_breach_date = None

        forecasts_list.append({
            "resource_id": resource_id,
            "metric_name": metric_name,
            "current_value": current_val,
            "growth_rate_per_day": float(m),
            "projected_30d": pred_30,
            "projected_60d": pred_60,
            "projected_90d": pred_90,
            "crosses_80_threshold": crosses_80,
            "projected_breach_date": projected_breach_date,
            "service_tag": last_row["service_tag"],
            "region": last_row["region"],
        })

    # Write forecasts to DuckDB table 'capacity_forecasts'
    if forecasts_list:
        forecasts_df = pd.DataFrame(forecasts_list)

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS capacity_forecasts (
                resource_id VARCHAR,
                metric_name VARCHAR,
                current_value DOUBLE,
                growth_rate_per_day DOUBLE,
                projected_30d DOUBLE,
                projected_60d DOUBLE,
                projected_90d DOUBLE,
                crosses_80_threshold INTEGER,
                projected_breach_date VARCHAR,
                service_tag VARCHAR,
                region VARCHAR
            )
            """
        )

        conn.execute("DELETE FROM capacity_forecasts")

        conn.executemany(
            """
            INSERT INTO capacity_forecasts (
                resource_id, metric_name, current_value, growth_rate_per_day,
                projected_30d, projected_60d, projected_90d, crosses_80_threshold,
                projected_breach_date, service_tag, region
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row["resource_id"],
                    row["metric_name"],
                    row["current_value"],
                    row["growth_rate_per_day"],
                    row["projected_30d"],
                    row["projected_60d"],
                    row["projected_90d"],
                    row["crosses_80_threshold"],
                    row["projected_breach_date"],
                    row["service_tag"],
                    row["region"],
                )
                for _, row in forecasts_df.iterrows()
            ],
        )

        forecast_count = conn.execute("SELECT COUNT(*) FROM capacity_forecasts").fetchone()[0]
        print(f"Capacity forecasting complete. Generated {forecast_count} projections in capacity_forecasts.")
    else:
        print("No forecasts generated.")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS capacity_forecasts (
                resource_id VARCHAR,
                metric_name VARCHAR,
                current_value DOUBLE,
                growth_rate_per_day DOUBLE,
                projected_30d DOUBLE,
                projected_60d DOUBLE,
                projected_90d DOUBLE,
                crosses_80_threshold INTEGER,
                projected_breach_date VARCHAR,
                service_tag VARCHAR,
                region VARCHAR
            )
            """
        )

    if close_conn:
        conn.close()
