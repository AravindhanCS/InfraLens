"""Export analytical tables from DuckDB to Parquet, CSV, and JSON for Power BI ingestion."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import duckdb

from config import DUCKDB_PATH

DEFAULT_EXPORT_DIR = "data/processed"

TABLES_TO_EXPORT = [
    "daily_metrics_rollup",
    "hourly_metrics_rollup",
    "anomaly_alerts",
    "capacity_forecasts",
    "underutilized_resources",
    "narrative_insights",
    "raw_metrics",
]


def export_tables_for_bi(
    conn: duckdb.DuckDBPyConnection | None = None,
    output_dir: str = DEFAULT_EXPORT_DIR,
    export_parquet: bool = True,
    export_csv: bool = True,
) -> dict[str, int]:
    """Export all analytical tables to Parquet and CSV files for Power BI ingestion.

    Returns a dictionary mapping table name to row count exported.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    should_close = False
    if conn is None:
        conn = duckdb.connect(DUCKDB_PATH)
        should_close = True

    export_stats = {}
    timestamp_str = datetime.utcnow().isoformat() + "Z"

    print("\n" + "-" * 50)
    print(f"Exporting analytics tables to '{output_dir}' for Power BI...")
    print("-" * 50)

    try:
        for table in TABLES_TO_EXPORT:
            # Check if table exists
            table_check = conn.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
                [table],
            ).fetchone()[0]

            if not table_check:
                print(f"  - Table '{table}' not found in database. Skipping.")
                continue

            # Row count
            row_count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            export_stats[table] = row_count

            # Parquet Export
            if export_parquet:
                parquet_file = (out_path / f"{table}.parquet").as_posix()
                conn.execute(
                    f"COPY {table} TO '{parquet_file}' (FORMAT PARQUET)"
                )

            # CSV Export
            if export_csv:
                csv_file = (out_path / f"{table}.csv").as_posix()
                conn.execute(
                    f"COPY {table} TO '{csv_file}' (HEADER, DELIMITER ',')"
                )

            print(f"  [OK] {table:25} -> {row_count:6d} rows exported")

        # Write manifest file
        manifest = {
            "exported_at": timestamp_str,
            "export_directory": str(out_path.resolve()),
            "tables": export_stats,
        }
        manifest_path = out_path / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        print(f"  [OK] Export manifest written to: {manifest_path}")
        print("-" * 50)
        print("Data export for Power BI completed successfully.\n")

    finally:
        if should_close:
            conn.close()

    return export_stats


if __name__ == "__main__":
    export_tables_for_bi()
