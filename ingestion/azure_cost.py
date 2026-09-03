"""Azure Cost ingestion module."""

from __future__ import annotations

from .schema import ensure_metric_contract, normalize_metric_record


def fetch_cost_data():
    """Return a normalized Azure Cost sample payload that matches the shared schema."""

    raw_rows = [
        {
            "source": "azure_cost",
            "resource_id": "vm-prod-01",
            "metric_name": "daily_cost",
            "value": 124.3,
            "unit": "usd",
            "timestamp": "2026-07-11T00:00:00Z",
            "region": "centralus",
            "service_tag": "compute",
        },
        {
            "source": "azure_cost",
            "resource_id": "vm-prod-01",
            "metric_name": "monthly_cost",
            "value": 3729.0,
            "unit": "usd",
            "timestamp": "2026-07-11T00:00:00Z",
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
