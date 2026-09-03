"""DuckDB persistence helpers for InfraLens."""

from __future__ import annotations

from pathlib import Path

import duckdb

from config import DUCKDB_PATH


def get_duckdb_connection(db_path: str = DUCKDB_PATH):
    """Return a DuckDB connection and ensure the parent directory exists."""

    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(db_path)


def init_duckdb_tables(conn) -> None:
    """Create the core raw metrics table in DuckDB if it does not exist."""

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_metrics (
            source VARCHAR,
            resource_id VARCHAR,
            metric_name VARCHAR,
            value DOUBLE,
            unit VARCHAR,
            timestamp TIMESTAMP,
            region VARCHAR,
            service_tag VARCHAR
        )
        """
    )


def write_metrics_to_duckdb(records: list[dict], db_path: str = DUCKDB_PATH) -> int:
    """Insert normalized metric records into DuckDB and return the number of rows written."""

    conn = get_duckdb_connection(db_path)
    init_duckdb_tables(conn)

    if not records:
        return 0

    conn.executemany(
        """
        INSERT INTO raw_metrics (
            source,
            resource_id,
            metric_name,
            value,
            unit,
            timestamp,
            region,
            service_tag
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["source"],
                row["resource_id"],
                row["metric_name"],
                row["value"],
                row["unit"],
                row["timestamp"],
                row["region"],
                row["service_tag"],
            )
            for row in records
        ],
    )
    count = conn.execute("SELECT COUNT(*) FROM raw_metrics").fetchone()[0]
    conn.close()
    return int(count)
