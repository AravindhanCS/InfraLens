"""Unit and integration tests for Power BI export bridge and dataset loading."""

from __future__ import annotations

import json
import os
import duckdb
import pandas as pd
import pytest

from dashboard.powerbi_connector import load_dataset
from transformation.export_for_bi import export_tables_for_bi, TABLES_TO_EXPORT


def test_export_tables_for_bi_temp(tmp_path):
    """Test exporting DuckDB tables to Parquet and CSV files in a temporary directory."""
    db_file = os.path.join(tmp_path, "test_infra.db")
    conn = duckdb.connect(db_file)

    # Create dummy tables
    conn.execute(
        """
        CREATE TABLE daily_metrics_rollup (
            date DATE,
            resource_id VARCHAR,
            metric_name VARCHAR,
            region VARCHAR,
            service_tag VARCHAR,
            avg_value DOUBLE,
            min_value DOUBLE,
            max_value DOUBLE,
            count INTEGER
        )
        """
    )
    conn.execute(
        """
        INSERT INTO daily_metrics_rollup VALUES
        ('2026-07-01', 'vm-1', 'cpu', 'centralus', 'compute', 45.0, 30.0, 60.0, 24),
        ('2026-07-02', 'vm-1', 'cpu', 'centralus', 'compute', 50.0, 35.0, 65.0, 24)
        """
    )

    conn.execute(
        """
        CREATE TABLE anomaly_alerts (
            timestamp TIMESTAMP,
            source VARCHAR,
            resource_id VARCHAR,
            metric_name VARCHAR,
            value DOUBLE,
            region VARCHAR,
            service_tag VARCHAR,
            z_score DOUBLE,
            severity VARCHAR
        )
        """
    )
    conn.execute(
        """
        INSERT INTO anomaly_alerts VALUES
        ('2026-07-02 12:00:00', 'azure_cost', 'vm-1', 'daily_cost', 200.0, 'centralus', 'compute', 3.5, 'Critical')
        """
    )

    export_dir = os.path.join(tmp_path, "processed")
    stats = export_tables_for_bi(conn=conn, output_dir=export_dir)

    # Verify return stats
    assert "daily_metrics_rollup" in stats
    assert stats["daily_metrics_rollup"] == 2
    assert "anomaly_alerts" in stats
    assert stats["anomaly_alerts"] == 1

    # Verify files created
    assert os.path.exists(os.path.join(export_dir, "daily_metrics_rollup.parquet"))
    assert os.path.exists(os.path.join(export_dir, "daily_metrics_rollup.csv"))
    assert os.path.exists(os.path.join(export_dir, "anomaly_alerts.parquet"))
    assert os.path.exists(os.path.join(export_dir, "anomaly_alerts.csv"))
    assert os.path.exists(os.path.join(export_dir, "manifest.json"))

    # Verify manifest structure
    with open(os.path.join(export_dir, "manifest.json"), "r", encoding="utf-8") as f:
        manifest = json.load(f)
        assert "exported_at" in manifest
        assert manifest["tables"]["daily_metrics_rollup"] == 2

    # Verify data content loaded from parquet matches
    df_parquet = pd.read_parquet(os.path.join(export_dir, "daily_metrics_rollup.parquet"))
    assert len(df_parquet) == 2
    assert df_parquet["resource_id"].iloc[0] == "vm-1"

    conn.close()


def test_load_dataset_fallback(tmp_path, monkeypatch):
    """Test load_dataset utility fallback behavior when database is None."""
    csv_file = tmp_path / "test_table.csv"
    csv_file.write_text("col1,col2\nval1,val2\n", encoding="utf-8")

    import dashboard.powerbi_connector as pb_mod
    monkeypatch.setattr(pb_mod, "PROCESSED_DIR", tmp_path)

    df = load_dataset("test_table", conn=None)
    assert not df.empty
    assert len(df) == 1
    assert df["col1"].iloc[0] == "val1"


def test_load_dataset_empty_nonexistent():
    """Test load_dataset returns empty DataFrame for nonexistent table."""
    df = load_dataset("non_existent_table_xyz_123", conn=None)
    assert isinstance(df, pd.DataFrame)
    assert df.empty
