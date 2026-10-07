import json
import os

RESULTS_PATH = "../results/groq_activity_a_reference.json"
REPORT_PATH = "../results/groq_activity_a_reference.md"

with open(RESULTS_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# Audit based on user rubric
for item in data["results"]:
    reply = item["reply"]
    item["reply_relevant"] = True
    item["professional_tone"] = True
    item["invented_policy"] = False
    item["notable_failure"] = None
    
    # Check for specific invented policies
    if item["id"] == "CMP-001":
        item["invented_policy"] = True
        item["notable_failure"] = "Reply made an unsupported operational claim ('will forward the details for further review')."
    elif item["id"] == "CMP-005":
        item["invented_policy"] = True
        item["notable_failure"] = "Reply made an unsupported routing claim ('will forward them to the appropriate team for review')."
    elif item["id"] == "CMP-004":
        item["invented_policy"] = True
        item["notable_failure"] = "Reply made an unsupported operational claim ('Your report has been logged') without a ticketing backend."
    elif item["id"] == "CMP-008":
        item["invented_policy"] = True
        item["notable_failure"] = "Reply made an unsupported operational claim ('Your report has been logged') without a ticketing backend."
    elif item["id"] == "CMP-009":
        item["invented_policy"] = True
        item["notable_failure"] = "Reply made an unsupported operational claim ('I’ve logged the details') without a ticketing backend."

# Calculate metrics
total = len(data["results"])
correct_class = sum(1 for x in data["results"] if x["classification_correct"])
relevant = sum(1 for x in data["results"] if x["reply_relevant"])
professional = sum(1 for x in data["results"] if x["professional_tone"])
invented = sum(1 for x in data["results"] if x["invented_policy"])
failures = sum(1 for x in data["results"] if x["notable_failure"] is not None)

avg_c_latency = sum(x["classification_latency_ms"] for x in data["results"]) / total
avg_r_latency = sum(x["reply_latency_ms"] for x in data["results"]) / total
avg_t_latency = sum(x["total_latency_ms"] for x in data["results"]) / total

data["summary"] = {
    "classification_correct": correct_class,
    "classification_accuracy": (correct_class / total) * 100,
    "reply_relevant": relevant,
    "professional_tone": professional,
    "invented_policy": invented,
    "failures": failures,
    "average_classification_latency_ms": avg_c_latency,
    "average_reply_latency_ms": avg_r_latency,
    "average_total_latency_ms": avg_t_latency
}

with open(RESULTS_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

# Generate MD
md = f"""# Activity A — Empirical Evaluation

## 1. Evaluation Setup

Provider: {data['evaluation']['provider']}
Model: {data['evaluation']['model']}
Classification temperature: {data['evaluation']['classification_temperature']}
Reply temperature: {data['evaluation']['reply_temperature']}
Classification token limit: {data['evaluation']['classification_max_tokens']}
Reply token limit: {data['evaluation']['reply_max_tokens']}
Python: {data['evaluation']['python_version']}
LangChain: {data['evaluation']['langchain_version']}

## 2. Frozen Evaluation Set

10 cases from:
../test_complaints.json

## 3. Case-by-Case Results

| ID | Expected | Actual | Correct | Classification ms | Reply ms | Total ms |
|---|---|---|---|---|---|---|
"""
for item in data["results"]:
    md += f"| {item['id']} | {item['expected_category']} | {item['actual_category']} | {item['classification_correct']} | {item['classification_latency_ms']:.2f} | {item['reply_latency_ms']:.2f} | {item['total_latency_ms']:.2f} |\n"

for item in data["results"]:
    md += f"\n### {item['id']}\n"
    md += f"**Complaint:** {item['complaint']}\n\n"
    md += f"**Reply:**\n{item['reply']}\n\n"
    md += f"- Reply relevant: {item['reply_relevant']}\n"
    md += f"- Professional tone: {item['professional_tone']}\n"
    md += f"- Invented policy: {item['invented_policy']}\n"
    md += f"- Notable failure: {item['notable_failure']}\n"

md += f"""
## 4. Aggregate Results

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
{avg_c_latency} ms

Average reply latency:
{avg_r_latency} ms

Average total latency:
{avg_t_latency} ms

## 5. Observed Failure Modes
"""
if failures > 0:
    for item in data["results"]:
        if item["notable_failure"]:
            md += f"- **{item['id']}**: {item['notable_failure']}\n"
else:
    md += "No notable failures were observed in this run.\n"

md += """
## 6. Methodology Limitations

- single benchmark run
- only 10 frozen complaints
- results apply to the tested provider/model/configuration
- results are not a universal claim about the model
- live provider behavior can change over time
"""

with open(REPORT_PATH, "w", encoding="utf-8") as f:
    f.write(md)

print("Done generating updated JSON and MD.")
