"""Azure Monitor ingestion module."""

from __future__ import annotations

from .schema import ensure_metric_contract, normalize_metric_record


def fetch_monitor_metrics():
    """Return a normalized Azure Monitor sample payload that matches the shared schema."""

    raw_rows = [
        {
            "source": "azure_monitor",
            "resource_id": "vm-prod-01",
            "metric_name": "cpu_utilization",
            "value": 64.2,
            "unit": "percent",
            "timestamp": "2026-07-11T10:00:00Z",
            "region": "centralus",
            "service_tag": "compute",
        },
        {
            "source": "azure_monitor",
            "resource_id": "vm-prod-01",
            "metric_name": "memory_utilization",
            "value": 52.5,
            "unit": "percent",
            "timestamp": "2026-07-11T10:00:00Z",
            "region": "centralus",
            "service_tag": "compute",
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
