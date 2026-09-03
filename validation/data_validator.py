"""Data Quality & Schema Validation Layer for InfraLens.

Implements input schema compliance, null detection, type enforcement,
duplicate detection, boundary validation, and output analytical completeness checks.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple
import duckdb

from config import DUCKDB_PATH

REQUIRED_RAW_FIELDS = [
    "source",
    "resource_id",
    "metric_name",
    "value",
    "unit",
    "timestamp",
    "region",
    "service_tag",
]

ALLOWED_SOURCES = {"azure_monitor", "azure_cost", "datadog"}
ALLOWED_SEVERITIES = {"Warning", "Critical"}


class ValidationResult:
    """Stores the summary and error details of a validation execution."""

    def __init__(self, passed: bool = True):
        self.passed: bool = passed
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.records_checked: int = 0
        self.valid_records: int = 0

    def add_error(self, message: str) -> None:
        self.passed = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "records_checked": self.records_checked,
            "valid_records": self.valid_records,
            "error_count": len(self.errors),
            "errors": self.errors,
            "warning_count": len(self.warnings),
            "warnings": self.warnings,
        }


def validate_raw_metric_records(records: List[Dict[str, Any]]) -> ValidationResult:
    """Validate a batch of incoming metric records from any source."""
    result = ValidationResult()
    result.records_checked = len(records)

    seen_keys: set[Tuple[str, str, str, str]] = set()

    for idx, rec in enumerate(records):
        rec_errors = []

        # 1. Missing or Null Fields
        for field in REQUIRED_RAW_FIELDS:
            val = rec.get(field)
            if val is None or val == "":
                rec_errors.append(f"Field '{field}' is null or empty")

        if rec_errors:
            for err in rec_errors:
                result.add_error(f"Record #{idx}: {err}")
            continue

        # 2. Source Validation
        source = rec["source"]
        if source not in ALLOWED_SOURCES:
            result.add_error(f"Record #{idx}: Unknown source '{source}'")

        # 3. Numeric Type & Range Validation
        val = rec["value"]
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            result.add_error(f"Record #{idx}: 'value' must be float or int, got {type(val).__name__}")
        else:
            metric = rec["metric_name"]
            if "utilization" in metric and (val < 0.0 or val > 100.0):
                result.add_error(f"Record #{idx}: Utilization metric '{metric}' value {val} out of bounds [0, 100]")
            elif "cost" in metric and val < 0.0:
                result.add_error(f"Record #{idx}: Cost metric '{metric}' value {val} cannot be negative")
            elif "error_rate" in metric and (val < 0.0 or val > 1.0):
                result.add_error(f"Record #{idx}: Error rate {val} out of bounds [0, 1]")

        # 4. Timestamp format validation
        ts = rec["timestamp"]
        if isinstance(ts, str):
            try:
                datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                result.add_error(f"Record #{idx}: Invalid ISO timestamp '{ts}'")
        elif not isinstance(ts, datetime):
            result.add_error(f"Record #{idx}: Timestamp must be string or datetime, got {type(ts).__name__}")

        # 5. Duplicate Detection
        key = (str(rec["source"]), str(rec["resource_id"]), str(rec["metric_name"]), str(rec["timestamp"]))
        if key in seen_keys:
            result.add_warning(f"Record #{idx}: Duplicate telemetry key detected: {key}")
        else:
            seen_keys.add(key)

        if not rec_errors:
            result.valid_records += 1

    return result


def validate_analytical_tables(
    conn: duckdb.DuckDBPyConnection | None = None,
    db_path: str = DUCKDB_PATH,
) -> ValidationResult:
    """Validate data completeness and mathematical integrity across DuckDB analytical tables."""
    result = ValidationResult()
    should_close = False

    if conn is None:
        conn = duckdb.connect(db_path, read_only=True)
        should_close = True

    try:
        # 1. daily_metrics_rollup checks
        res = conn.execute(
            """
            SELECT COUNT(*) FROM daily_metrics_rollup 
            WHERE date IS NULL OR resource_id IS NULL OR avg_value IS NULL OR count <= 0
            """
        ).fetchone()
        if res and res[0] > 0:
            result.add_error(f"daily_metrics_rollup has {res[0]} records with null values or invalid counts")

        # 2. anomaly_alerts checks
        res = conn.execute(
            """
            SELECT COUNT(*) FROM anomaly_alerts 
            WHERE z_score IS NULL OR severity NOT IN ('Warning', 'Critical')
            """
        ).fetchone()
        if res and res[0] > 0:
            result.add_error(f"anomaly_alerts has {res[0]} records with invalid z_score or unknown severity")

        # 3. capacity_forecasts checks
        res = conn.execute(
            """
            SELECT COUNT(*) FROM capacity_forecasts 
            WHERE current_value IS NULL OR projected_90d IS NULL OR crosses_80_threshold NOT IN (0, 1)
            """
        ).fetchone()
        if res and res[0] > 0:
            result.add_error(f"capacity_forecasts has {res[0]} records with null metrics or invalid threshold flags")

        # 4. underutilized_resources checks
        res = conn.execute(
            """
            SELECT COUNT(*) FROM underutilized_resources 
            WHERE avg_cpu > 20.0 OR avg_memory > 20.0 OR potential_monthly_saving <= 0
            """
        ).fetchone()
        if res and res[0] > 0:
            result.add_error(f"underutilized_resources has {res[0]} records violating <20% utilization or positive savings rules")

    finally:
        if should_close:
            conn.close()

    return result
