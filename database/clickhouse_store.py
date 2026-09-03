"""ClickHouse persistence helpers for InfraLens."""

from __future__ import annotations

import clickhouse_connect

from config import (
    CLICKHOUSE_DB,
    CLICKHOUSE_HOST,
    CLICKHOUSE_PASSWORD,
    CLICKHOUSE_PORT,
    CLICKHOUSE_USERNAME,
)


import subprocess
import time

def get_clickhouse_client(
    host: str = CLICKHOUSE_HOST,
    port: int = CLICKHOUSE_PORT,
    username: str = CLICKHOUSE_USERNAME,
    password: str = CLICKHOUSE_PASSWORD,
    database: str = CLICKHOUSE_DB,
):
    """Return a ClickHouse client connection using the configured host and port."""
    try:
        client = clickhouse_connect.get_client(
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
        )
        client.ping()
        return client
    except Exception as e:
        print(f"ClickHouse connection failed: {e}. Attempting to start ClickHouse container in WSL...")
        try:
            # Attempt to start the container
            subprocess.run(["wsl", "docker", "start", "clickhouse-server-lens"], capture_output=True)
            
            # Retry connection for up to 5 attempts (15 seconds)
            for attempt in range(5):
                time.sleep(3)
                try:
                    print(f"Retrying connection to ClickHouse, attempt {attempt+1}/5...")
                    client = clickhouse_connect.get_client(
                        host=host,
                        port=port,
                        username=username,
                        password=password,
                        database=database,
                    )
                    client.ping()
                    print("ClickHouse connected successfully.")
                    return client
                except Exception as connect_err:
                    print(f"Attempt {attempt+1}/5 failed: {connect_err}")
            raise Exception("ClickHouse failed to respond after auto-start attempts.")
        except Exception as auto_start_err:
            print(f"Failed to auto-start ClickHouse container: {auto_start_err}")
            # Raise original exception if auto-start failed or connection still fails
            raise e


def init_clickhouse_tables(client) -> None:
    """Create the raw metrics table in ClickHouse if it does not exist."""

    client.command(
        """
        CREATE TABLE IF NOT EXISTS infra_metrics (
            source String,
            resource_id String,
            metric_name String,
            value Float64,
            unit String,
            timestamp DateTime,
            region String,
            service_tag String
        )
        ENGINE = MergeTree
        ORDER BY (timestamp, source, resource_id)
        """
    )


def write_metrics_to_clickhouse(client, records: list[dict]) -> int:
    """Insert records into the ClickHouse infra_metrics table and return the row count."""

    if not records:
        return 0

    column_names = [
        "source",
        "resource_id",
        "metric_name",
        "value",
        "unit",
        "timestamp",
        "region",
        "service_tag",
    ]

    data = [
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
    ]

    client.insert("infra_metrics", data, column_names=column_names)
    result = client.query("SELECT count() FROM infra_metrics")
    if result.result_rows:
        row = result.result_rows[0]
        if isinstance(row, dict):
            return int(next(iter(row.values())))
        elif isinstance(row, (list, tuple)) and len(row) > 0:
            return int(row[0])
    return 0
