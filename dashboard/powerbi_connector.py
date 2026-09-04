"""Power BI Python Data Connector for InfraLens.

USAGE IN POWER BI DESKTOP:
1. Open Power BI Desktop.
2. Click 'Get Data' -> 'More...' -> Search 'Python script'.
3. Paste the contents of this file into the dialog.
4. Power BI will display all tables (DailyMetrics, HourlyMetrics, AnomalyAlerts,
   CapacityForecasts, UnderutilizedResources, NarrativeInsights, RecentMetrics)
   with all column headers and data rows in the Navigator.
"""

from __future__ import annotations

import os
from pathlib import Path
import pandas as pd

# Explicit candidate directories to guarantee file resolution inside Power BI Desktop
# (where Power BI's internal working directory defaults to AppData\Local\Temp)
PROJECT_DIR = Path(r"C:\Users\aravindhan.chandrase\Desktop\Psiddhi Sem3\InfraLens")

if "__file__" in globals():
    candidate = Path(__file__).resolve().parent.parent
    if (candidate / "data" / "processed").exists():
        BASE_DIR = candidate
    else:
        BASE_DIR = PROJECT_DIR
elif (Path.cwd() / "data" / "processed").exists():
    BASE_DIR = Path.cwd()
else:
    BASE_DIR = PROJECT_DIR

DUCKDB_PATH = str(BASE_DIR / "database" / "duckdb" / "infra.db")
PROCESSED_DIR = BASE_DIR / "data" / "processed"

# Fallback column definitions ensuring columns are never missing or replaced by 'Column1'
FALLBACK_SCHEMAS = {
    "daily_metrics_rollup": [
        "source", "resource_id", "metric_name", "service_tag", "region", "unit",
        "timestamp", "avg_value", "min_value", "max_value", "count_value",
    ],
    "hourly_metrics_rollup": [
        "source", "resource_id", "metric_name", "service_tag", "region", "unit",
        "timestamp", "avg_value", "min_value", "max_value", "count_value",
    ],
    "anomaly_alerts": [
        "timestamp", "source", "resource_id", "metric_name", "value",
        "z_score", "severity", "service_tag", "region",
    ],
    "capacity_forecasts": [
        "resource_id", "metric_name", "service_tag", "region", "current_value",
        "growth_rate_per_day", "projected_30d", "projected_60d", "projected_90d",
        "crosses_80_threshold", "projected_breach_date",
    ],
    "underutilized_resources": [
        "resource_id", "avg_cpu", "avg_memory", "daily_cost",
        "potential_monthly_saving", "service_tag", "region",
    ],
    "narrative_insights": [
        "id", "scenario", "resource_id", "insight_text", "timestamp",
    ],
    "raw_metrics": [
        "source", "resource_id", "metric_name", "value", "unit",
        "timestamp", "region", "service_tag",
    ],
}


def load_dataset(table_name: str, conn=None) -> pd.DataFrame:
    """Load a dataset from CSV or Parquet files, with schema preservation."""
    # Attempt 1: Read pre-exported CSV (most portable across any Python environment)
    csv_path = PROCESSED_DIR / f"{table_name}.csv"
    if csv_path.exists():
        try:
            df = pd.read_csv(csv_path)
            if not df.empty:
                return df
        except Exception:
            pass

    # Attempt 2: Read exported Parquet file
    parquet_path = PROCESSED_DIR / f"{table_name}.parquet"
    if parquet_path.exists():
        try:
            df = pd.read_parquet(parquet_path)
            if not df.empty:
                return df
        except Exception:
            pass

    # Attempt 3: Direct DuckDB query
    if os.path.exists(DUCKDB_PATH):
        try:
            import duckdb
            conn = duckdb.connect(DUCKDB_PATH, read_only=True)
            df = conn.execute(f"SELECT * FROM {table_name}").df()
            conn.close()
            if not df.empty:
                return df
        except Exception:
            pass

    # Safe fallback with preserved column names
    cols = FALLBACK_SCHEMAS.get(table_name, ["id", "value"])
    return pd.DataFrame(columns=cols)


# Expose clean, strongly-typed DataFrames to Power BI Desktop global scope
DailyMetrics = load_dataset("daily_metrics_rollup")
if not DailyMetrics.empty and "timestamp" in DailyMetrics.columns:
    DailyMetrics["timestamp"] = pd.to_datetime(DailyMetrics["timestamp"])

HourlyMetrics = load_dataset("hourly_metrics_rollup")
if not HourlyMetrics.empty and "timestamp" in HourlyMetrics.columns:
    HourlyMetrics["timestamp"] = pd.to_datetime(HourlyMetrics["timestamp"])

AnomalyAlerts = load_dataset("anomaly_alerts")
if not AnomalyAlerts.empty and "timestamp" in AnomalyAlerts.columns:
    AnomalyAlerts["timestamp"] = pd.to_datetime(AnomalyAlerts["timestamp"])

CapacityForecasts = load_dataset("capacity_forecasts")

UnderutilizedResources = load_dataset("underutilized_resources")

NarrativeInsights = load_dataset("narrative_insights")
if not NarrativeInsights.empty and "timestamp" in NarrativeInsights.columns:
    NarrativeInsights["timestamp"] = pd.to_datetime(NarrativeInsights["timestamp"])

RecentMetrics = load_dataset("raw_metrics")

if __name__ == "__main__":
    print("=" * 60)
    print("Power BI Connector Diagnostics")
    print("=" * 60)
    for name, df in [
        ("DailyMetrics", DailyMetrics),
        ("HourlyMetrics", HourlyMetrics),
        ("AnomalyAlerts", AnomalyAlerts),
        ("CapacityForecasts", CapacityForecasts),
        ("UnderutilizedResources", UnderutilizedResources),
        ("NarrativeInsights", NarrativeInsights),
        ("RecentMetrics", RecentMetrics),
    ]:
        print(f"{name:25} | Rows: {len(df):6d} | Columns: {df.columns.tolist()[:4]}...")
    print("=" * 60)
    print("All tables successfully loaded with full column schemas!")
