"""Unit and integration tests for the Ingestion Layer."""

from __future__ import annotations

import pytest

from ingestion.azure_cost import fetch_cost_data
from ingestion.azure_monitor import fetch_monitor_metrics
from ingestion.datadog import fetch_datadog_metrics
from ingestion.schema import (
    ensure_metric_contract,
    INFRA_METRIC_FIELDS,
    normalize_metric_record,
)


def test_normalize_metric_record_valid():
    """Test normalization with valid input parameters."""
    record = normalize_metric_record(
        source="test_source",
        resource_id="res-01",
        metric_name="cpu",
        value=50.5,
        unit="percent",
        timestamp="2026-07-12T00:00:00Z",
        region="eastus",
        service_tag="web",
    )
    assert record["source"] == "test_source"
    assert record["resource_id"] == "res-01"
    assert record["metric_name"] == "cpu"
    assert record["value"] == 50.5
    assert record["unit"] == "percent"
    assert record["timestamp"] == "2026-07-12T00:00:00Z"
    assert record["region"] == "eastus"
    assert record["service_tag"] == "web"


def test_normalize_metric_record_invalid_value_type():
    """Test normalization fails when value is not numeric."""
    with pytest.raises(TypeError):
        normalize_metric_record(
            source="test_source",
            resource_id="res-01",
            metric_name="cpu",
            value="not-numeric",
            unit="percent",
            timestamp="2026-07-12T00:00:00Z",
            region="eastus",
            service_tag="web",
        )


def test_normalize_metric_record_missing_required():
    """Test normalization fails when required string parameters are empty."""
    with pytest.raises(ValueError):
        normalize_metric_record(
            source="",
            resource_id="res-01",
            metric_name="cpu",
            value=50.5,
            unit="percent",
            timestamp="2026-07-12T00:00:00Z",
            region="eastus",
            service_tag="web",
        )


def test_ensure_metric_contract_valid():
    """Test contract enforcement with fully valid records."""
    records = [
        {
            "source": "src",
            "resource_id": "r1",
            "metric_name": "m1",
            "value": 1.0,
            "unit": "u",
            "timestamp": "t",
            "region": "reg",
            "service_tag": "tag",
        }
    ]
    validated = ensure_metric_contract(records)
    assert len(validated) == 1
    assert set(validated[0].keys()) == set(INFRA_METRIC_FIELDS)


def test_ensure_metric_contract_missing_field():
    """Test contract enforcement fails when fields are missing."""
    records = [{"source": "src", "resource_id": "r1"}]
    with pytest.raises(ValueError):
        ensure_metric_contract(records)


def test_source_fetchers():
    """Test that all three source fetchers return valid normalized metrics."""
    mon_metrics = fetch_monitor_metrics()
    cost_metrics = fetch_cost_data()
    dd_metrics = fetch_datadog_metrics()

    # Verify lists
    assert isinstance(mon_metrics, list)
    assert isinstance(cost_metrics, list)
    assert isinstance(dd_metrics, list)

    # Verify they conform to schema contract
    for record_list in [mon_metrics, cost_metrics, dd_metrics]:
        assert len(record_list) > 0
        for r in record_list:
            assert set(r.keys()) == set(INFRA_METRIC_FIELDS)


from unittest.mock import patch
from ingestion.runner import run_ingestion

def test_run_ingestion():
    """Test that runner pulls metrics and triggers database writes."""
    with patch("ingestion.runner.write_metrics_to_duckdb") as mock_duck, \
         patch("ingestion.runner.write_metrics_to_clickhouse") as mock_ch, \
         patch("ingestion.runner.get_clickhouse_client") as mock_client:
        mock_duck.return_value = 6
        mock_ch.return_value = 6
        
        run_ingestion()
        
        mock_duck.assert_called_once()
        mock_ch.assert_called_once()

