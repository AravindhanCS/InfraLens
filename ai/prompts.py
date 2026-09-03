"""Prompt templates for AI-powered infrastructure insights."""

SYSTEM_PROMPT = """You are a senior Platform Engineer and Cloud Analyst at InfraLens.
Your task is to analyze infrastructure telemetry, cost data, and capacity forecasts, and translate them into clear, actionable, plain-language insights for platform leads and non-technical stakeholders.
Avoid vague generalities. Be specific, structured, and quantitative in your recommendations. Format your response in clean markdown."""

COST_ANOMALY_PROMPT = """Analyze the following cost anomaly detected in our infrastructure:
Resource: {resource_id}
Service Tag: {service_tag}
Region: {region}
Metric: {metric_name}
Current Value: {value:.2f} {unit}
Z-Score: {z_score:.2f}
Average 30-Day Cost: {avg_30d_cost:.2f} USD
Daily Cost Increase: {pct_increase:.1f}% above average

Please write a plain-language narrative explaining:
1. The anomaly detail (resource, region, spend magnitude).
2. Likely contributing metrics (e.g. recent compute spikes, storage growth, network transfer).
3. Concrete cost optimization suggestions (e.g., right-sizing, stopping idle instances, checking logs for data transfer volume, using spot instances).
Keep the summary professional, concise (1-2 paragraphs), and direct.
"""

CAPACITY_RISK_PROMPT = """Analyze the following capacity risk forecast for our infrastructure:
Resource/Service: {resource_id}
Service Tag: {service_tag}
Region: {region}
Metric: {metric_name}
Current Utilization: {current_value:.2f}%
Projected 90-Day Utilization: {projected_90d:.2f}%
Daily Growth Rate: {growth_rate_per_day:.4f}%
Projected Breach Date (80% threshold): {projected_breach_date}

Please write a capacity risk summary explaining:
1. The service at risk and projected breach date.
2. The current growth rate and implications if unaddressed.
3. Recommended pre-emptive action (e.g., scale-out, resource tier upgrade, traffic redistribution, memory cleanup, or database indexing).
Keep it concise, actionable, and structured.
"""

UNDERUTILIZATION_PROMPT = """Analyze the following underutilized infrastructure resource candidates for right-sizing or decommissioning:
{candidates_list}

Please write a weekly consolidated optimization recommendation narrative that includes:
1. The top candidates for right-sizing or decommissioning.
2. Estimated monthly cost savings per action and in total.
3. The confidence basis for each recommendation (referencing their 7-day average CPU and memory utilization).
Ensure the tone is analytical, precise, and directly useful for budget planning.
"""
