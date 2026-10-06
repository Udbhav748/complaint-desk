import json

RESULTS_PATH = "evaluation/activity_a_results.json"
REPORT_PATH = "evaluation/activity_a_report.md"

with open(RESULTS_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

correct_class = data["summary"]["classification_correct"]
relevant = data["summary"]["reply_relevant"]
professional = data["summary"]["professional_tone"]
invented = data["summary"]["invented_policy"]
failures = data["summary"]["failures"]
avg_c_latency = data["summary"]["average_classification_latency_ms"]
avg_r_latency = data["summary"]["average_reply_latency_ms"]
avg_t_latency = data["summary"]["average_total_latency_ms"]

# Generate MD
md = f"""# Activity A — Empirical Evaluation

## Evaluation Setup

Provider:
{data['evaluation']['provider'].capitalize()}

Model:
{data['evaluation']['model']}

Classification temperature:
{data['evaluation']['classification_temperature']}

Reply temperature:
{data['evaluation']['reply_temperature']}

Classification max tokens:
{data['evaluation']['classification_max_tokens']}

Reply max tokens:
{data['evaluation']['reply_max_tokens']}

## Aggregate Results

Classification:
{correct_class} / 10

Classification accuracy:
{data['summary']['classification_accuracy']}%

Relevant replies:
{relevant} / 10

Professional replies:
{professional} / 10

Policy-invention cases:
{invented} / 10

Average classification latency:
{avg_c_latency:.2f} ms

Average reply latency:
{avg_r_latency:.2f} ms

Average total latency:
{avg_t_latency:.2f} ms

## Observed Guardrail Violations
"""
for item in data["results"]:
    if item["notable_failure"]:
        md += f"- {item['id']} — {item['notable_failure']}\n"

md += """
## Interpretation

- classification performed correctly on the frozen 10-case set
- replies were relevant/professional where supported by the evidence
- some replies still produced unsupported operational claims despite the prompt guardrails
- this is an observed model-output limitation from this benchmark run
- the result demonstrates why empirical evaluation is necessary
"""

with open(REPORT_PATH, "w", encoding="utf-8") as f:
    f.write(md)

print("Done regenerating MD.")
