"""Test harness for scale benchmark functions."""

from __future__ import annotations

from datetime import datetime
from tests.benchmark_scale import generate_synthetic_batch, run_scale_benchmark


def test_generate_synthetic_batch():
    """Verify synthetic generation matches schema."""
    batch = generate_synthetic_batch(20, datetime.utcnow())
    assert len(batch) == 20
    rec = batch[0]
    # (src, vm, metric, val, unit, current, reg, tag)
    assert len(rec) == 8
    assert rec[0] in ["azure_monitor", "azure_cost", "datadog"]
    assert rec[4] in ["percent", "usd", "rpm"]


def test_run_scale_benchmark_sla():
    """Verify benchmark function executes and meets SLA targets."""
    res = run_scale_benchmark()
    assert res["total_records"] >= 80000
    assert res["backfill_sla_passed"] is True
    assert res["dashboard_sla_passed"] is True
