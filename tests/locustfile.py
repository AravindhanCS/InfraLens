"""Locust performance & load testing definition for InfraLens analytical workload."""

from __future__ import annotations

import random
from locust import User, task, between
import duckdb
from config import DUCKDB_PATH


class InfraLensDashboardUser(User):
    """Simulates a platform engineering lead querying the InfraLens dashboard."""

    wait_time = between(0.1, 0.5)

    def on_start(self):
        """Establish a read-only DuckDB analytical connection."""
        self.conn = duckdb.connect(DUCKDB_PATH, read_only=True)

    def on_stop(self):
        """Close connection."""
        if hasattr(self, "conn") and self.conn:
            self.conn.close()

    @task(4)
    def query_compute_utilization(self):
        """Query compute utilization heatmap and time series."""
        service = random.choice(["compute", "api", "development"])
        self.conn.execute(
            """
            SELECT date, resource_id, avg_value, min_value, max_value 
            FROM daily_metrics_rollup 
            WHERE metric_name = 'cpu_utilization' AND service_tag = ?
            ORDER BY date DESC LIMIT 30
            """,
            [service],
        ).fetchall()

    @task(3)
    def query_cost_trends(self):
        """Query 30-day spend trends and top cost drivers."""
        self.conn.execute(
            """
            SELECT resource_id, SUM(avg_value) as total_spend 
            FROM daily_metrics_rollup 
            WHERE metric_name = 'daily_cost' 
            GROUP BY resource_id 
            ORDER BY total_spend DESC
            """
        ).fetchall()

    @task(2)
    def query_anomaly_callouts(self):
        """Query critical anomaly alerts."""
        self.conn.execute(
            """
            SELECT timestamp, resource_id, metric_name, value, z_score 
            FROM anomaly_alerts 
            WHERE severity = 'Critical'
            ORDER BY timestamp DESC LIMIT 20
            """
        ).fetchall()

    @task(2)
    def query_capacity_forecasts(self):
        """Query high-risk capacity forecasts (>80% threshold)."""
        self.conn.execute(
            """
            SELECT resource_id, current_value, projected_90d, projected_breach_date 
            FROM capacity_forecasts 
            WHERE crosses_80_threshold = 1
            """
        ).fetchall()

    @task(1)
    def query_narrative_insights(self):
        """Query latest AI-generated narrative cards."""
        self.conn.execute(
            """
            SELECT scenario, resource_id, insight_text 
            FROM narrative_insights 
            ORDER BY timestamp DESC LIMIT 5
            """
        ).fetchall()
