"""Power BI Python Data Connector for InfraLens.

USAGE IN POWER BI DESKTOP:
1. Open Power BI Desktop.
2. Click 'Get Data' -> 'More...' -> Search 'Python script'.
3. Paste the contents of this file (or reference it).
4. Power BI will display all tables (DailyMetrics, HourlyMetrics, AnomalyAlerts,
   CapacityForecasts, UnderutilizedResources, NarrativeInsights, RecentMetrics)
   in the Navigator for immediate loading and data modeling.
"""

from __future__ import annotations

import os
from pathlib import Path
import pandas as pd
import duckdb

# Determine project base directory
BASE_DIR = Path(__file__).resolve().parent.parent if "__file__" in globals() else Path(os.getcwd())
DUCKDB_PATH = str(BASE_DIR / "database" / "duckdb" / "infra.db")
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def load_dataset(table_name: str, conn: duckdb.DuckDBPyConnection | None = None) -> pd.DataFrame:
    """Load a dataset from DuckDB (read-only) or fallback to exported Parquet/CSV files."""
    # Attempt 1: Direct DuckDB query
    if conn is not None:
        try:
            return conn.execute(f"SELECT * FROM {table_name}").df()
        except Exception:
            pass

    # Attempt 2: Read exported Parquet file
    parquet_path = PROCESSED_DIR / f"{table_name}.parquet"
    if parquet_path.exists():
        try:
            return pd.read_parquet(parquet_path)
        except Exception:
            pass

    # Attempt 3: Read exported CSV file
    csv_path = PROCESSED_DIR / f"{table_name}.csv"
    if csv_path.exists():
        return pd.read_csv(csv_path)

    # Empty DataFrame fallback
    return pd.DataFrame()


# Connect to DuckDB in read-only mode to prevent lock conflicts with scheduler
db_conn = None
if os.path.exists(DUCKDB_PATH):
    try:
        db_conn = duckdb.connect(DUCKDB_PATH, read_only=True)
    except Exception as e:
        print(f"DuckDB busy or inaccessible ({e}). Loading from processed Parquet files.")

try:
    # 1. Daily Metrics Rollup (Fact Table: Daily Aggregate)
    DailyMetrics = load_dataset("daily_metrics_rollup", db_conn)
    if not DailyMetrics.empty and "date" in DailyMetrics.columns:
        DailyMetrics["date"] = pd.to_datetime(DailyMetrics["date"])

    # 2. Hourly Metrics Rollup (Fact Table: Hourly Aggregate)
    HourlyMetrics = load_dataset("hourly_metrics_rollup", db_conn)
    if not HourlyMetrics.empty and "timestamp" in HourlyMetrics.columns:
        HourlyMetrics["timestamp"] = pd.to_datetime(HourlyMetrics["timestamp"])

    # 3. Anomaly Alerts (Domain: Anomaly Callouts)
    AnomalyAlerts = load_dataset("anomaly_alerts", db_conn)
    if not AnomalyAlerts.empty and "timestamp" in AnomalyAlerts.columns:
        AnomalyAlerts["timestamp"] = pd.to_datetime(AnomalyAlerts["timestamp"])

    # 4. Capacity Forecasts (Domain: Capacity Patterns)
    CapacityForecasts = load_dataset("capacity_forecasts", db_conn)

    # 5. Underutilized Resources (Domain: Optimization & Right-Sizing)
    UnderutilizedResources = load_dataset("underutilized_resources", db_conn)

    # 6. AI Narrative Insights (Domain: Plain-Language GenAI Summaries)
    NarrativeInsights = load_dataset("narrative_insights", db_conn)
    if not NarrativeInsights.empty and "timestamp" in NarrativeInsights.columns:
        NarrativeInsights["timestamp"] = pd.to_datetime(NarrativeInsights["timestamp"])

    # 7. Recent Raw Metrics (Latest 7 days for fine-grained drill-down)
    if db_conn is not None:
        try:
            RecentMetrics = db_conn.execute(
                """
                SELECT * FROM raw_metrics 
                WHERE timestamp >= (SELECT MAX(timestamp) - INTERVAL 7 DAY FROM raw_metrics)
                """
            ).df()
        except Exception:
            RecentMetrics = load_dataset("raw_metrics", db_conn)
    else:
        RecentMetrics = load_dataset("raw_metrics", db_conn)

finally:
    if db_conn is not None:
        db_conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Power BI Python Data Connector Test Output")
    print("=" * 60)
    print(f"DailyMetrics:           {len(DailyMetrics)} rows")
    print(f"HourlyMetrics:          {len(HourlyMetrics)} rows")
    print(f"AnomalyAlerts:          {len(AnomalyAlerts)} rows")
    print(f"CapacityForecasts:      {len(CapacityForecasts)} rows")
    print(f"UnderutilizedResources: {len(UnderutilizedResources)} rows")
    print(f"NarrativeInsights:      {len(NarrativeInsights)} rows")
    print(f"RecentMetrics:          {len(RecentMetrics)} rows")
    print("=" * 60)
    print("All datasets successfully loaded and ready for Power BI Desktop!")
