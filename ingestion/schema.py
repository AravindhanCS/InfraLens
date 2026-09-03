"""Shared schema contract for ingested infrastructure telemetry."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

INFRA_METRIC_FIELDS = (
    "source",
    "resource_id",
    "metric_name",
    "value",
    "unit",
    "timestamp",
    "region",
    "service_tag",
)


@dataclass(frozen=True)
class InfraMetricRecord:
    """Canonical record shape used across all sources."""

    source: str
    resource_id: str
    metric_name: str
    value: float
    unit: str
    timestamp: str
    region: str
    service_tag: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "resource_id": self.resource_id,
            "metric_name": self.metric_name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp,
            "region": self.region,
            "service_tag": self.service_tag,
        }


def normalize_metric_record(
    source: str,
    resource_id: str,
    metric_name: str,
    value: float | int,
    unit: str,
    timestamp: str | datetime,
    region: str,
    service_tag: str,
) -> dict[str, Any]:
    """Normalize a source-specific payload into the shared InfraLens schema."""

    if not source or not resource_id or not metric_name or not unit or not region or not service_tag:
        raise ValueError("All required metric fields must be populated")

    if not isinstance(value, (int, float)):
        raise TypeError("value must be numeric")

    normalized_timestamp = timestamp.isoformat() if isinstance(timestamp, datetime) else str(timestamp)

    record = InfraMetricRecord(
        source=source,
        resource_id=resource_id,
        metric_name=metric_name,
        value=float(value),
        unit=unit,
        timestamp=normalized_timestamp,
        region=region,
        service_tag=service_tag,
    )

    return record.to_dict()


def ensure_metric_contract(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate that every row conforms to the expected schema contract."""

    normalized_records: list[dict[str, Any]] = []
    for record in records:
        missing_fields = [field for field in INFRA_METRIC_FIELDS if field not in record]
        if missing_fields:
            raise ValueError(f"Missing required contract fields: {missing_fields}")
        normalized_records.append({field: record[field] for field in INFRA_METRIC_FIELDS})

    return normalized_records
