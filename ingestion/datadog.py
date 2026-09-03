"""Datadog ingestion module."""

from __future__ import annotations

from .schema import ensure_metric_contract, normalize_metric_record


def fetch_datadog_metrics():
    """Return a normalized Datadog sample payload that matches the shared schema."""

    raw_rows = [
        {
            "source": "datadog",
            "resource_id": "svc-api-gateway",
            "metric_name": "request_rate",
            "value": 1340.8,
            "unit": "rpm",
            "timestamp": "2026-07-11T10:05:00Z",
            "region": "eastus2",
            "service_tag": "api",
        },
        {
            "source": "datadog",
            "resource_id": "svc-api-gateway",
            "metric_name": "error_rate",
            "value": 1.2,
            "unit": "percent",
            "timestamp": "2026-07-11T10:05:00Z",
            "region": "eastus2",
            "service_tag": "api",
        },
    ]

    return ensure_metric_contract(
        [
            normalize_metric_record(
                source=row["source"],
                resource_id=row["resource_id"],
                metric_name=row["metric_name"],
                value=row["value"],
                unit=row["unit"],
                timestamp=row["timestamp"],
                region=row["region"],
                service_tag=row["service_tag"],
            )
            for row in raw_rows
        ]
    )
