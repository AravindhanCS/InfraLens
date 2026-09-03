"""End-to-End integration tests for the full InfraLens pipeline."""

from __future__ import annotations

import os

import duckdb
import pytest

from ai.insight_generator import generate_narrative_insights
from database.duckdb_store import init_duckdb_tables, write_metrics_to_duckdb
from ingestion.seed_data import generate_historical_data
from transformation.aggregate import aggregate_metrics
from transformation.anomaly import detect_anomalies
from transformation.forecast import forecast_usage
from transformation.optimization import analyze_underutilization


@pytest.fixture
def temp_db_path(tmp_path):
    """Fixture providing a path to a temporary DuckDB database file."""
    db_file = os.path.join(tmp_path, "test_infra_e2e.db")
    yield db_file
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except OSError:
            pass


def test_full_pipeline_e2e(temp_db_path):
    """Run E2E pipeline tests from historical seeding through to AI insight narrative generation."""
    # 1. Seed historical records into the temp database
    records = generate_historical_data(days=15)
    write_metrics_to_duckdb(records, db_path=temp_db_path)

    # Verify ingestion counts
    conn = duckdb.connect(temp_db_path)
    try:
        raw_count = conn.execute("SELECT COUNT(*) FROM raw_metrics").fetchone()[0]
        assert raw_count > 0

        # 2. Run aggregations
        aggregate_metrics(conn)
        assert conn.execute("SELECT COUNT(*) FROM daily_metrics_rollup").fetchone()[0] > 0

        # 3. Run anomaly detection
        detect_anomalies(conn)
        # Verify anomaly_alerts table exists
        assert conn.execute("SELECT COUNT(*) FROM anomaly_alerts").fetchone()[0] >= 0

        # 4. Run forecasting
        forecast_usage(conn)
        assert conn.execute("SELECT COUNT(*) FROM capacity_forecasts").fetchone()[0] > 0

        # 5. Run underutilization scoring
        analyze_underutilization(conn)
        assert conn.execute("SELECT COUNT(*) FROM underutilized_resources").fetchone()[0] > 0

        # 6. Run AI narrative generation
        # Since GEMINI_API_KEY may or may not be set in the test runner,
        # this will test live API or fallback path gracefully
        generate_narrative_insights(conn)
        assert conn.execute("SELECT COUNT(*) FROM narrative_insights").fetchone()[0] > 0

    finally:
        conn.close()
