"""Scheduler and orchestrator entry point for InfraLens."""

from __future__ import annotations

import argparse
import sys
import time

import schedule

from ai.insight_generator import generate_narrative_insights
from database.duckdb_store import get_duckdb_connection
from ingestion.runner import run_ingestion
from ingestion.seed_data import seed_databases
from transformation.aggregate import aggregate_metrics
from transformation.anomaly import detect_anomalies
from transformation.export_for_bi import export_tables_for_bi
from transformation.forecast import forecast_usage
from transformation.optimization import analyze_underutilization


def run_pipeline() -> None:
    """Run the entire data collection, transformation, and AI insight pipeline end-to-end."""
    print("\n" + "=" * 60)
    print("STARTING INFRA LENS E2E ANALYTICS PIPELINE")
    print("=" * 60)
    start_time = time.time()

    try:
        # Step 1: Ingest active metrics from sources
        run_ingestion()

        # Connect to DuckDB to perform transformations and AI narrative generations in a single session
        conn = get_duckdb_connection()
        try:
            # Step 2: Data aggregations
            aggregate_metrics(conn)

            # Step 3: Anomaly detection
            detect_anomalies(conn)

            # Step 4: Forecasting
            forecast_usage(conn)

            # Step 5: Optimization Analysis
            analyze_underutilization(conn)

            # Step 6: AI Narrative Insights
            generate_narrative_insights(conn)

            # Step 7: Export analytics tables for Power BI
            export_tables_for_bi(conn)

        finally:
            conn.close()

        duration = time.time() - start_time
        print("=" * 60)
        print(f"INFRA LENS PIPELINE COMPLETED SUCCESSFULLY IN {duration:.2f}s")
        print("=" * 60 + "\n")

    except Exception as e:
        print("\n" + "!" * 60)
        print(f"PIPELINE CRITICAL FAILURE: {e}")
        print("!" * 60 + "\n")


def main() -> None:
    """Main CLI entry point for InfraLens orchestration."""
    parser = argparse.ArgumentParser(description="InfraLens CLI Orchestrator")
    parser.add_argument(
        "--seed", "-s",
        action="store_true",
        help="Seed the databases with 30 days of historical telemetry",
    )
    parser.add_argument(
        "--run", "-r",
        action="store_true",
        help="Run the E2E pipeline immediately",
    )
    parser.add_argument(
        "--schedule", "-c",
        type=int,
        metavar="MINUTES",
        help="Start the scheduler loop to run the pipeline every N minutes",
    )
    parser.add_argument(
        "--schedule-seconds",
        type=int,
        metavar="SECONDS",
        help="Start the scheduler loop to run the pipeline every N seconds (for simulation)",
    )

    args = parser.parse_args()

    # If no flags are provided, show help
    if not any(vars(args).values()):
        parser.print_help()
        sys.exit(0)

    # 1. Seeding
    if args.seed:
        seed_databases()

    # 2. Run Pipeline immediately
    if args.run:
        run_pipeline()

    # 3. Schedule pipeline execution
    if args.schedule or args.schedule_seconds:
        if args.schedule:
            interval = args.schedule
            print(f"Scheduling pipeline to run every {interval} minute(s)...")
            schedule.every(interval).minutes.do(run_pipeline)
        else:
            interval = args.schedule_seconds
            print(f"Scheduling pipeline to run every {interval} second(s)...")
            schedule.every(interval).seconds.do(run_pipeline)

        print("Scheduler started. Press Ctrl+C to exit.")
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nScheduler stopped.")


if __name__ == "__main__":
    main()
