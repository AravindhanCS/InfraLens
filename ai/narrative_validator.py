"""AI Narrative Accuracy Validation Engine.

Extracts factual claims from AI-generated narrative summaries (percentages, dollar amounts,
dates, z-scores) and cross-validates them against underlying DuckDB telemetry and analytical tables.
Flags factual hallucinations or numerical mismatches beyond an acceptable tolerance threshold (default ±5%).
"""

from __future__ import annotations

import re
from typing import Any
import duckdb

from config import DUCKDB_PATH


def extract_cost_anomaly_claims(narrative_text: str) -> dict[str, Any]:
    """Extract numerical and categorical claims from a Cost Anomaly narrative."""
    claims = {}

    # Extract resource_id
    res_match = re.search(r"###\s*⚠️\s*Cost Anomaly Detected:\s*([a-zA-Z0-9_-]+)", narrative_text)
    if not res_match:
        res_match = re.search(r"\*\*([a-zA-Z0-9_-]+)\*\*", narrative_text)
    if res_match:
        claims["resource_id"] = res_match.group(1).strip()

    # Extract daily cost spike value: spiked to **X.XX USD**
    cost_match = re.search(r"spiked to\s*\*\*([0-9.,]+)\s*([A-Za-z]+)\*\*", narrative_text, re.IGNORECASE)
    if cost_match:
        claims["spiked_cost"] = float(cost_match.group(1).replace(",", ""))

    # Extract percentage increase: **X.X%** above
    pct_match = re.search(r"\*\*([0-9.,]+)%\*\*\s*above", narrative_text)
    if pct_match:
        claims["pct_increase"] = float(pct_match.group(1).replace(",", ""))

    # Extract 30-day average: average of **X.XX USD**
    avg_match = re.search(r"average of\s*\*\*([0-9.,]+)\s*USD\*\*", narrative_text, re.IGNORECASE)
    if avg_match:
        claims["avg_30d_cost"] = float(avg_match.group(1).replace(",", ""))

    # Extract Z-score: (Z-Score: **X.XX**)
    z_match = re.search(r"Z-Score:\s*\*\*([0-9.,-]+)\*\*", narrative_text)
    if z_match:
        claims["z_score"] = float(z_match.group(1).replace(",", ""))

    return claims


def extract_capacity_risk_claims(narrative_text: str) -> dict[str, Any]:
    """Extract claims from a Capacity Risk narrative."""
    claims = {}

    # Extract resource_id
    res_match = re.search(r"###\s*📈\s*Capacity Risk Alert:\s*([a-zA-Z0-9_-]+)", narrative_text)
    if not res_match:
        res_match = re.search(r"resource\s*\*\*([a-zA-Z0-9_-]+)\*\*", narrative_text, re.IGNORECASE)
    if res_match:
        claims["resource_id"] = res_match.group(1).strip()

    # Current utilization
    curr_match = re.search(r"Current.*?average:\*\*\s*([0-9.,]+)%", narrative_text, re.IGNORECASE)
    if curr_match:
        claims["current_utilization"] = float(curr_match.group(1).replace(",", ""))

    # Projected 90D utilization
    proj_match = re.search(r"Projected 90-Day.*?:\*\*\s*([0-9.,]+)%", narrative_text, re.IGNORECASE)
    if proj_match:
        claims["projected_90d"] = float(proj_match.group(1).replace(",", ""))

    # Projected breach date
    date_match = re.search(r"Projected Breach Date.*?:\*\*\s*([0-9]{4}-[0-9]{2}-[0-9]{2}|N/A)", narrative_text, re.IGNORECASE)
    if date_match:
        claims["projected_breach_date"] = date_match.group(1).strip()

    return claims


def extract_underutilization_claims(narrative_text: str) -> dict[str, Any]:
    """Extract claims from an Underutilization Optimization report."""
    claims = {"candidates": []}

    # Extract total potential savings
    tot_match = re.search(r"Total Potential Savings:\s*([0-9.,]+)\s*USD/Month", narrative_text, re.IGNORECASE)
    if tot_match:
        claims["total_monthly_saving"] = float(tot_match.group(1).replace(",", ""))

    # Extract candidate blocks
    cand_matches = re.finditer(
        r"#### Candidate:\s*([a-zA-Z0-9_-]+).*?"
        r"Average CPU utilization:\*\*\s*([0-9.,]+)%.*?"
        r"Average Memory utilization:\*\*\s*([0-9.,]+)%.*?"
        r"Decommission Savings:\*\*\s*\*\*([0-9.,]+)\s*USD/Month\*\*",
        narrative_text,
        re.DOTALL | re.IGNORECASE,
    )
    for m in cand_matches:
        claims["candidates"].append({
            "resource_id": m.group(1).strip(),
            "avg_cpu": float(m.group(2)),
            "avg_memory": float(m.group(3)),
            "savings": float(m.group(4)),
        })

    return claims


def validate_narrative_accuracy(
    conn: duckdb.DuckDBPyConnection | None = None,
    tolerance_pct: float = 5.0,
    db_path: str = DUCKDB_PATH,
) -> dict[str, Any]:
    """Validate all generated narrative insights in DuckDB against underlying analytical tables.

    Returns a report with checked claims, passed count, failed count, and mismatches.
    """
    should_close = False
    if conn is None:
        conn = duckdb.connect(db_path, read_only=True)
        should_close = True

    results = {
        "total_checked": 0,
        "passed": 0,
        "failed": 0,
        "details": [],
    }

    try:
        # Fetch all narrative insights
        narratives = conn.execute(
            "SELECT id, scenario, resource_id, insight_text FROM narrative_insights"
        ).fetchall()

        for nid, scenario, res_id, text in narratives:
            results["total_checked"] += 1
            scenario_key = (scenario or "").lower()
            item_status = {"id": nid, "scenario": scenario, "resource_id": res_id, "errors": []}

            if "cost" in scenario_key:
                claims = extract_cost_anomaly_claims(text)
                target_res = res_id or claims.get("resource_id")
                if target_res:
                    row = conn.execute(
                        """
                        SELECT value, z_score FROM anomaly_alerts 
                        WHERE resource_id = ? AND metric_name = 'daily_cost'
                        ORDER BY timestamp DESC LIMIT 1
                        """,
                        [target_res],
                    ).fetchone()
                    if row:
                        db_val, db_z = row[0], row[1]
                        if "spiked_cost" in claims:
                            diff = abs(claims["spiked_cost"] - db_val) / max(db_val, 1e-6) * 100
                            if diff > tolerance_pct:
                                item_status["errors"].append(
                                    f"Cost mismatch: claimed ${claims['spiked_cost']:.2f}, actual ${db_val:.2f}"
                                )
                        if "z_score" in claims:
                            diff_z = abs(claims["z_score"] - db_z)
                            if diff_z > 0.5:  # Absolute z tolerance
                                item_status["errors"].append(
                                    f"Z-Score mismatch: claimed {claims['z_score']}, actual {db_z}"
                                )

            elif "capacity" in scenario_key:
                claims = extract_capacity_risk_claims(text)
                target_res = res_id or claims.get("resource_id")
                if target_res:
                    row = conn.execute(
                        """
                        SELECT current_value, projected_90d, projected_breach_date 
                        FROM capacity_forecasts 
                        WHERE resource_id = ? AND metric_name = 'cpu_utilization'
                        LIMIT 1
                        """,
                        [target_res],
                    ).fetchone()
                    if row:
                        db_curr, db_proj, db_breach = row[0], row[1], row[2]
                        if "current_utilization" in claims:
                            diff = abs(claims["current_utilization"] - db_curr)
                            if diff > tolerance_pct:
                                item_status["errors"].append(
                                    f"Current util mismatch: claimed {claims['current_utilization']}%, actual {db_curr}%"
                                )
                        if "projected_breach_date" in claims and db_breach:
                            if claims["projected_breach_date"] != str(db_breach):
                                item_status["errors"].append(
                                    f"Breach date mismatch: claimed {claims['projected_breach_date']}, actual {db_breach}"
                                )

            elif "underutilization" in scenario_key:
                claims = extract_underutilization_claims(text)
                for cand in claims.get("candidates", []):
                    c_res = cand["resource_id"]
                    row = conn.execute(
                        "SELECT avg_cpu, avg_memory, potential_monthly_saving FROM underutilized_resources WHERE resource_id = ?",
                        [c_res],
                    ).fetchone()
                    if row:
                        db_cpu, db_mem, db_save = row[0], row[1], row[2]
                        diff_cpu = abs(cand["avg_cpu"] - db_cpu)
                        diff_save = abs(cand["savings"] - db_save) / max(db_save, 1e-6) * 100
                        if diff_cpu > tolerance_pct or diff_save > tolerance_pct:
                            item_status["errors"].append(
                                f"Candidate {c_res} metrics mismatch: claimed CPU={cand['avg_cpu']}%, actual={db_cpu:.2f}%"
                            )

            if item_status["errors"]:
                results["failed"] += 1
                item_status["status"] = "FAILED"
            else:
                results["passed"] += 1
                item_status["status"] = "PASSED"

            results["details"].append(item_status)

    finally:
        if should_close:
            conn.close()

    return results
