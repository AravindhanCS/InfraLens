import os
from google import genai
from google.genai import types

def generate_insight(system_prompt: str, prompt: str, scenario: str = "", context_data: dict = None) -> str:
    """Generate plain-language insights using Gemini 2.5 Flash, with a local fallback if API key is missing."""
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        print("Warning: GEMINI_API_KEY environment variable is not set. Using local offline generator fallback.")
        return generate_local_fallback(scenario, context_data)

    try:
        # Initialize client. The Client class automatically reads GEMINI_API_KEY from environment.
        client = genai.Client()
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
            )
        )
        return response.text
    except Exception as e:
        print(f"Error calling Gemini API: {e}. Falling back to local offline generator.")
        return generate_local_fallback(scenario, context_data)


def generate_local_fallback(scenario: str, context_data: dict | None) -> str:
    """Fallback generator that builds realistic markdown reports when Gemini is unavailable."""
    if not context_data:
        return "Insight generation failed: No context data provided for fallback."

    if scenario == "cost_anomaly":
        res_id = context_data.get("resource_id", "Unknown Resource")
        region = context_data.get("region", "Unknown Region")
        val = context_data.get("value", 0.0)
        unit = context_data.get("unit", "usd")
        z = context_data.get("z_score", 0.0)
        avg = context_data.get("avg_30d_cost", 0.0)
        pct = context_data.get("pct_increase", 0.0)
        tag = context_data.get("service_tag", "compute")

        return f"""### ⚠️ Cost Anomaly Detected: {res_id}

A critical cost anomaly has been flagged for **{res_id}** in the **{region}** region. The daily cost spiked to **{val:.2f} {unit.upper()}**, which is **{pct:.1f}%** above its 30-day average of **{avg:.2f} USD** (Z-Score: **{z:.2f}**).

**Analysis of Spend:**
- The anomaly is associated with the **{tag}** service group.
- The sudden z-score deviation points to a sharp resource expansion, likely driven by high load spikes, storage allocation increases, or unoptimized data transfers.

**Recommended Actions:**
1. **Right-size the Resource:** Verify if the VM size matches the load or if a smaller instance tier would suffice.
2. **Decommission Idle Resources:** If the resource is inactive during off-peak hours, configure auto-shutdown policies.
3. **Investigate Logs:** Check application logs for data transfer volume spikes or resource loops.
"""

    elif scenario == "capacity_risk":
        res_id = context_data.get("resource_id", "Unknown Resource")
        metric = context_data.get("metric_name", "utilization")
        curr = context_data.get("current_value", 0.0)
        proj = context_data.get("projected_90d", 0.0)
        growth = context_data.get("growth_rate_per_day", 0.0)
        breach = context_data.get("projected_breach_date", "N/A")
        region = context_data.get("region", "Unknown Region")

        metric_label = "CPU" if "cpu" in metric.lower() else "Memory"

        return f"""### 📈 Capacity Risk Alert: {res_id} ({metric_label})

The resource **{res_id}** in region **{region}** is experiencing sustained capacity growth. 
- **Current {metric_label} average:** {curr:.2f}%
- **Projected 90-Day {metric_label}:** {proj:.2f}%
- **Growth Trend:** {growth:.4f}% utilization increase per day
- **Projected Breach Date (80%):** {breach}

**Impact Analysis:**
If unaddressed, the resource is projected to exceed the safe operating threshold of 80% on **{breach}**, which increases risk of latency spikes, thread exhaustion, or system failure under peak loads.

**Recommended Pre-emptive Actions:**
1. **Scale-out or Scale-up:** Upgrade the virtual machine size or set up auto-scaling with additional node instances.
2. **Optimize Load Distribution:** Redistribute traffic or scheduling queues to less loaded servers in the cluster.
3. **Optimize Code/DB:** Inspect slow queries or optimize memory structures to lower the baseline usage.
"""

    elif scenario == "underutilization":
        candidates = context_data.get("candidates", [])
        if not candidates:
            return "No underutilized resources were found to optimize."

        markdown = "### 💡 Infrastructure Optimization & Right-Sizing Report\n\n"
        markdown += "Analysis of telemetry over the past 7 days has identified opportunities to reduce cloud spend by decommissioning or right-sizing underutilized resources.\n\n"

        total_saving = 0.0
        for cand in candidates:
            res_id = cand.get("resource_id")
            cpu = cand.get("avg_cpu", 0.0)
            mem = cand.get("avg_memory", 0.0)
            cost = cand.get("daily_cost", 0.0)
            savings = cand.get("potential_monthly_saving", 0.0)
            tag = cand.get("service_tag", "Unknown")
            total_saving += savings

            markdown += f"#### Candidate: {res_id} ({tag} tag)\n"
            markdown += f"- **Average CPU utilization:** {cpu:.2f}% (Threshold: < 20%)\n"
            markdown += f"- **Average Memory utilization:** {mem:.2f}% (Threshold: < 20%)\n"
            markdown += f"- **Current daily cost:** {cost:.2f} USD\n"
            markdown += f"- **Decommission Savings:** **{savings:.2f} USD/Month**\n"
            markdown += f"- **Confidence Level:** High (Consistently underutilized over a 7-day rolling window)\n\n"

        markdown += f"**Total Potential Savings: {total_saving:.2f} USD/Month**\n\n"
        markdown += "**Decommissioning Plan:** We recommend shutting down these resources in the next maintenance window after notifying their respective owners."
        return markdown

    return "Insight generation fallback: Unrecognized scenario."
