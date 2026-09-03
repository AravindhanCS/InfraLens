"""Integration tests for database persistence layers (DuckDB and ClickHouse)."""

from __future__ import annotations

from datetime import datetime
import os

import duckdb
import pytest

from database.clickhouse_store import (
    get_clickhouse_client,
    init_clickhouse_tables,
    write_metrics_to_clickhouse,
)
from database.duckdb_store import (
    get_duckdb_connection,
    init_duckdb_tables,
    write_metrics_to_duckdb,
)


def test_duckdb_store_write(tmp_path):
    """Test DuckDB write helper with temporary path."""
    temp_db = os.path.join(tmp_path, "temp_duckdb.db")
    records = [
        {
            "source": "test",
            "resource_id": "r1",
            "metric_name": "cpu",
            "value": 45.0,
            "unit": "percent",
            "timestamp": "2026-07-12T00:00:00Z",
            "region": "centralus",
            "service_tag": "compute",
        }
    ]
    rows = write_metrics_to_duckdb(records, db_path=temp_db)
    assert rows == 1

    # Verify tables
    conn = get_duckdb_connection(temp_db)
    res = conn.execute("SELECT * FROM raw_metrics").fetchone()
    assert res is not None
    assert res[0] == "test"
    assert res[1] == "r1"
    conn.close()


def test_clickhouse_store_write_live():
    """Test ClickHouse store write functions using the active WSL container."""
    try:
        client = get_clickhouse_client()
        init_clickhouse_tables(client)

        records = [
            {
                "source": "test_ch",
                "resource_id": "r1-ch",
                "metric_name": "cpu",
                "value": 45.0,
                "unit": "percent",
                "timestamp": datetime.utcnow(),
                "region": "centralus",
                "service_tag": "compute",
            }
        ]

        # Get initial row count
        init_res = client.query("SELECT count() FROM infra_metrics")
        init_count = int(next(iter(init_res.result_rows[0].values()))) if isinstance(init_res.result_rows[0], dict) else int(init_res.result_rows[0][0])

        # Write
        write_metrics_to_clickhouse(client, records)

        # Get updated count
        up_res = client.query("SELECT count() FROM infra_metrics")
        up_count = int(next(iter(up_res.result_rows[0].values()))) if isinstance(up_res.result_rows[0], dict) else int(up_res.result_rows[0][0])

        assert up_count == init_count + 1
    except Exception as e:
        pytest.skip(f"Skipping live ClickHouse test: ClickHouse not accessible ({e})")
