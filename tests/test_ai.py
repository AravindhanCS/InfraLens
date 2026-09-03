"""Unit tests for the AI Narrative Insight Generation Layer."""

from __future__ import annotations

from ai.gemini import generate_local_fallback
from ai.prompts import (
    CAPACITY_RISK_PROMPT,
    COST_ANOMALY_PROMPT,
    SYSTEM_PROMPT,
    UNDERUTILIZATION_PROMPT,
)


def test_prompt_formatting():
    """Verify that the prompts format correctly with expected fields."""
    cost_prompt = COST_ANOMALY_PROMPT.format(
        resource_id="test-vm",
        service_tag="compute",
        region="westus",
        metric_name="daily_cost",
        value=200.0,
        unit="usd",
        z_score=3.5,
        avg_30d_cost=100.0,
        pct_increase=100.0,
    )
    assert "test-vm" in cost_prompt
    assert "200.00" in cost_prompt
    assert "3.50" in cost_prompt

    capacity_prompt = CAPACITY_RISK_PROMPT.format(
        resource_id="test-vm",
        service_tag="compute",
        region="westus",
        metric_name="cpu_utilization",
        current_value=75.0,
        projected_90d=85.0,
        growth_rate_per_day=0.5,
        projected_breach_date="2026-08-01",
    )
    assert "test-vm" in capacity_prompt
    assert "85.00%" in capacity_prompt
    assert "2026-08-01" in capacity_prompt

    underutil_prompt = UNDERUTILIZATION_PROMPT.format(candidates_list="- test-dev-01")
    assert "- test-dev-01" in underutil_prompt


def test_generate_local_fallback_cost_anomaly():
    """Test offline cost anomaly narrative formatting and details."""
    context = {
        "resource_id": "vm-prod-01",
        "region": "centralus",
        "value": 300.0,
        "unit": "usd",
        "z_score": 3.47,
        "avg_30d_cost": 100.0,
        "pct_increase": 200.0,
        "service_tag": "compute",
    }
    report = generate_local_fallback("cost_anomaly", context)
    assert "Cost Anomaly Detected" in report
    assert "vm-prod-01" in report
    assert "300.00 USD" in report
    assert "200.0%" in report
    assert "3.47" in report


def test_generate_local_fallback_capacity_risk():
    """Test offline capacity risk narrative formatting and details."""
    context = {
        "resource_id": "vm-prod-02",
        "metric_name": "cpu_utilization",
        "current_value": 78.5,
        "projected_90d": 95.0,
        "growth_rate_per_day": 0.55,
        "projected_breach_date": "2026-07-20",
        "region": "centralus",
    }
    report = generate_local_fallback("capacity_risk", context)
    assert "Capacity Risk Alert" in report
    assert "vm-prod-02" in report
    assert "95.00%" in report
    assert "2026-07-20" in report


def test_generate_local_fallback_underutilization():
    """Test offline underutilization report formatting and details."""
    context = {
        "candidates": [
            {
                "resource_id": "vm-dev-01",
                "avg_cpu": 5.2,
                "avg_memory": 8.5,
                "daily_cost": 10.0,
                "potential_monthly_saving": 300.0,
                "service_tag": "development",
            }
        ]
    }
    report = generate_local_fallback("underutilization", context)
    assert "Infrastructure Optimization & Right-Sizing Report" in report
    assert "vm-dev-01" in report
    assert "5.20%" in report
    assert "300.00 USD/Month" in report
    assert "Total Potential Savings: 300.00 USD/Month" in report
