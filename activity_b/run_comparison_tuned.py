"""Activity B second follow-up — fix Mistral's loan/billing vs. app_issue confusion.

Across 3 runs of the hardened Activity A prompt, local `mistral` consistently missed
CMP-006 (loan) and/or CMP-010 (billing), both misclassified as app_issue. Rather than
rerunning until a lucky seed gives 10/10 (which would misrepresent the model), this
script applies a *targeted, documented* prompt fix (prompts_mistral_tuned.py)
that adds a second disambiguation rule + two few-shot examples for exactly this
confusion, then reruns once to see whether an actual fix — not luck — resolves it.

Usage:
    python run_comparison_tuned.py
"""

import json
import os
import sys
import time
import platform
import importlib.metadata
from pathlib import Path
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
load_dotenv(HERE.parent / ".env")

from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama

from prompts_mistral_tuned import CLASSIFICATION_PROMPT_TUNED
from prompts_hardened import REPLY_PROMPT
from validation import validate_category

DATASET_PATH = HERE / "test_complaints.json"
RUN_INDEX = sys.argv[1] if len(sys.argv) > 1 else None
RESULTS_PATH = (
    HERE / "results" / f"ollama_tuned_run{RUN_INDEX}.json"
    if RUN_INDEX
    else HERE / "results" / "ollama_tuned.json"
)

FORBIDDEN_PHRASES = [
    "forward", "forwarded", "route", "routed", "escalate", "escalated",
    "pass this along", "appropriate team", "review team", "will ensure it is reviewed",
    "investigating", "investigation", "refund", "reimburse", "waive", "waived",
    "rectify", "rectifying", "secure your account", "immediate steps",
]


def main():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    print("Activity B (tuned prompt) — provider: ollama / mistral")
    print(f"Loaded {len(dataset)} complaints.\n")

    classify_llm = ChatOllama(model="mistral", temperature=0.0)
    reply_llm = ChatOllama(model="mistral", temperature=0.2)

    classify = CLASSIFICATION_PROMPT_TUNED | classify_llm | StrOutputParser()
    reply = REPLY_PROMPT | reply_llm | StrOutputParser()

    results = []
    for case in dataset:
        case_id = case["id"]
        complaint = case["complaint"]
        expected = case["expected_category"]
        print(f"Processing {case_id}...")

        t0 = time.perf_counter()
        try:
            cat_raw = classify.invoke({"complaint": complaint})
        except Exception as e:
            cat_raw = f"ERROR: {e}"
        t1 = time.perf_counter()
        class_latency_ms = (t1 - t0) * 1000

        cat_result = validate_category(cat_raw)
        actual_category = cat_result.value if cat_result.success else "unclassified"
        is_correct = actual_category == expected

        t2 = time.perf_counter()
        try:
            reply_text = reply.invoke({"complaint": complaint, "category": actual_category})
        except Exception as e:
            reply_text = f"ERROR: {e}"
        t3 = time.perf_counter()
        reply_latency_ms = (t3 - t2) * 1000

        violations = [p for p in FORBIDDEN_PHRASES if p in reply_text.lower()]

        results.append({
            "id": case_id,
            "complaint": complaint,
            "expected_category": expected,
            "actual_category_raw": cat_raw,
            "actual_category": actual_category,
            "classification_correct": is_correct,
            "classification_latency_ms": round(class_latency_ms, 1),
            "reply": reply_text,
            "reply_latency_ms": round(reply_latency_ms, 1),
            "total_latency_ms": round(class_latency_ms + reply_latency_ms, 1),
            "guardrail_violations": violations,
        })

    correct = sum(1 for r in results if r["classification_correct"])
    avg_total = sum(r["total_latency_ms"] for r in results) / len(results)
    clean_replies = sum(1 for r in results if not r["guardrail_violations"])

    eval_data = {
        "evaluation": {
            "name": "FWC Module 8 Activity B (2nd follow-up) - Mistral with loan/billing-tuned prompt",
            "dataset": DATASET_PATH,
            "cases": len(dataset),
            "executed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "provider": "ollama",
            "model": "mistral",
            "classification_temperature": 0.0,
            "reply_temperature": 0.2,
            "prompt_variant": "evaluation/prompts_mistral_tuned.py (+DISAMBIGUATION RULE 2, +2 few-shot examples)",
            "accuracy": f"{correct}/{len(dataset)}",
            "clean_replies_no_guardrail_violation": f"{clean_replies}/{len(dataset)}",
            "avg_total_latency_ms": round(avg_total, 1),
            "python_version": platform.python_version(),
            "langchain_version": importlib.metadata.version("langchain"),
        },
        "results": results,
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(eval_data, f, indent=2)

    print(f"\nDone. {correct}/{len(dataset)} correct. {clean_replies}/{len(dataset)} replies with no guardrail-violating phrases.")
    print(f"Avg latency: {avg_total:.0f}ms")
    print(f"Results saved to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
