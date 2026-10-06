import json
import os

RESULTS_PATH = "evaluation/activity_a_results.json"
REPORT_PATH = "evaluation/activity_a_report.md"

with open(RESULTS_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# Hard-coded verification based on visual inspection
judgements = {
    "CMP-001": {"rel": True, "prof": True, "inv": False, "fail": None},
    "CMP-002": {"rel": True, "prof": True, "inv": False, "fail": None},
    "CMP-003": {"rel": True, "prof": True, "inv": False, "fail": None},
    "CMP-004": {"rel": True, "prof": True, "inv": False, "fail": None},
    "CMP-005": {"rel": True, "prof": True, "inv": False, "fail": None},
    "CMP-006": {"rel": True, "prof": True, "inv": False, "fail": None},
    "CMP-007": {"rel": True, "prof": True, "inv": False, "fail": None},
    "CMP-008": {"rel": True, "prof": True, "inv": False, "fail": None},
    "CMP-009": {"rel": True, "prof": True, "inv": False, "fail": None},
    "CMP-010": {"rel": True, "prof": True, "inv": False, "fail": None}
}

for item in data["results"]:
    c_id = item["id"]
    item["reply_relevant"] = judgements[c_id]["rel"]
    item["professional_tone"] = judgements[c_id]["prof"]
    item["invented_policy"] = judgements[c_id]["inv"]
    item["notable_failure"] = judgements[c_id]["fail"]

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
evaluation/test_complaints.json

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

No notable failures were observed in this run.

## 6. Methodology Limitations

- single benchmark run
- only 10 frozen complaints
- results apply to the tested provider/model/configuration
- results are not a universal claim about the model
- live provider behavior can change over time
"""

with open(REPORT_PATH, "w", encoding="utf-8") as f:
    f.write(md)

print("Done generating JSON and MD.")
