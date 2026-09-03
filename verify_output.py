import sys
import pandas as pd
import duckdb

# Reconfigure stdout/stderr to use UTF-8 encoding to avoid Windows charmap encoding errors
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


def verify():
    print("=" * 80)
    print("INFRA LENS VERIFICATION REPORT")
    print("=" * 80)

    # Connect to DuckDB
    db_path = "database/duckdb/infra.db"
    conn = duckdb.connect(db_path)

    # 1. Row Counts Summary
    print("\n[1] DATABASE TABLES ROW COUNT SUMMARY")
    print("-" * 50)
    tables = [
        "raw_metrics",
        "hourly_metrics_rollup",
        "daily_metrics_rollup",
        "anomaly_alerts",
        "capacity_forecasts",
        "underutilized_resources",
        "narrative_insights",
    ]
    for table in tables:
        try:
            cnt = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"Table: {table:25} | Row Count: {cnt}")
        except Exception as e:
            print(f"Table: {table:25} | Error: {e}")

    # 2. Critical Cost Anomalies
    print("\n[2] DETECTED COST ANOMALIES (anomaly_alerts)")
    print("-" * 50)
    try:
        anom_df = conn.execute(
            """
            SELECT timestamp, resource_id, metric_name, value, z_score, severity 
            FROM anomaly_alerts 
            WHERE metric_name = 'daily_cost' AND severity = 'Critical'
            """
        ).df()
        if anom_df.empty:
            print("No critical cost anomalies found.")
        else:
            print(anom_df.to_string(index=False))
    except Exception as e:
        print(f"Error querying cost anomalies: {e}")

    # 3. Capacity Forecast Risks
    print("\n[3] GROWING CAPACITY RISKS (capacity_forecasts)")
    print("-" * 50)
    try:
        fore_df = conn.execute(
            """
            SELECT resource_id, metric_name, current_value, projected_90d, crosses_80_threshold, projected_breach_date
            FROM capacity_forecasts 
            WHERE crosses_80_threshold = 1
            """
        ).df()
        if fore_df.empty:
            print("No capacity risks found.")
        else:
            print(fore_df.to_string(index=False))
    except Exception as e:
        print(f"Error querying capacity forecasts: {e}")

    # 4. Underutilized VMs Decommissioning Candidates
    print("\n[4] UNDERUTILIZED RESOURCES (underutilized_resources)")
    print("-" * 50)
    try:
        opt_df = conn.execute(
            """
            SELECT resource_id, avg_cpu, avg_memory, daily_cost, potential_monthly_saving, service_tag 
            FROM underutilized_resources
            """
        ).df()
        if opt_df.empty:
            print("No underutilized resources found.")
        else:
            print(opt_df.to_string(index=False))
    except Exception as e:
        print(f"Error querying underutilized resources: {e}")

    # 5. Generated AI Narrative Insights
    print("\n[5] GENERATED AI NARRATIVE INSIGHTS (narrative_insights)")
    print("-" * 50)
    try:
        results = conn.execute("SELECT scenario, resource_id, insight_text FROM narrative_insights").fetchall()
        print(f"Total AI summaries: {len(results)}")
        for idx, (scenario, res_id, text) in enumerate(results, 1):
            print("\n" + "=" * 80)
            print(f"({idx}) Scenario: {scenario.upper()} | Resource ID: {res_id or 'CONSOLIDATED'}")
            print("=" * 80)
            print(text.strip())
    except Exception as e:
        print(f"Error querying narrative insights: {e}")

    conn.close()
    print("\n" + "=" * 80)


if __name__ == "__main__":
    verify()
