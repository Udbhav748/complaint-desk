"""Activity B — OpenAI <-> Ollama swap benchmark.

Runs the FWC Module 8 §18.1 *reference* Activity A snippet (not the hardened
production app in app.py/src/) against the same frozen 10-complaint dataset
used for Activity A, once per provider, to produce a fair side-by-side:

    classify = (ChatPromptTemplate.from_template(
        "Classify into billing/loan/fraud/app_issue. One word only.\n{text}")
        | llm | StrOutputParser())
    reply = (ChatPromptTemplate.from_template(
        "Polite 60-word acknowledgement for a {cat} complaint. Sign as XYZ Finance.\n{text}")
        | llm | StrOutputParser())

The only thing that changes between runs is the `llm` line:
    ChatOpenAI(model="gpt-4o-mini", temperature=0.3)   vs.
    ChatOllama(model="mistral", temperature=0.3)

Usage:
    python evaluation/run_eval_activity_b.py openai
    python evaluation/run_eval_activity_b.py ollama
"""

import json
import sys
import time
import platform
import importlib.metadata
from dotenv import load_dotenv

load_dotenv(".env")

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

DATASET_PATH = "evaluation/test_complaints.json"
ALLOWED_CATEGORIES = ("billing", "loan", "fraud", "app_issue")


def build_llm(provider: str):
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model="mistral", temperature=0.3)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("openai", "ollama"):
        print("Usage: python evaluation/run_eval_activity_b.py [openai|ollama]")
        sys.exit(1)

    provider = sys.argv[1]
    results_path = f"evaluation/activity_b_results_{provider}.json"

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    print(f"Activity B — provider: {provider}")
    print(f"Loaded {len(dataset)} complaints.\n")

    llm = build_llm(provider)

    classify = (
        ChatPromptTemplate.from_template(
            "Classify into billing/loan/fraud/app_issue. One word only.\n{text}"
        )
        | llm
        | StrOutputParser()
    )
    reply = (
        ChatPromptTemplate.from_template(
            "Polite 60-word acknowledgement for a {cat} complaint. Sign as XYZ Finance.\n{text}"
        )
        | llm
        | StrOutputParser()
    )

    results = []
    for case in dataset:
        case_id = case["id"]
        complaint = case["complaint"]
        expected = case["expected_category"]
        print(f"Processing {case_id}...")

        t0 = time.perf_counter()
        try:
            cat_raw = classify.invoke({"text": complaint})
        except Exception as e:
            cat_raw = f"ERROR: {e}"
        t1 = time.perf_counter()
        class_latency_ms = (t1 - t0) * 1000

        cat_clean = cat_raw.strip().lower().strip(".,;:!?`*\"'")
        actual_category = cat_clean if cat_clean in ALLOWED_CATEGORIES else "unclassified"
        is_correct = actual_category == expected

        t2 = time.perf_counter()
        try:
            reply_text = reply.invoke({"cat": actual_category, "text": complaint})
        except Exception as e:
            reply_text = f"ERROR: {e}"
        t3 = time.perf_counter()
        reply_latency_ms = (t3 - t2) * 1000

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
        })

    correct = sum(1 for r in results if r["classification_correct"])
    avg_total = sum(r["total_latency_ms"] for r in results) / len(results)

    eval_data = {
        "evaluation": {
            "name": "FWC Module 8 Activity B - OpenAI vs Ollama swap",
            "dataset": DATASET_PATH,
            "cases": len(dataset),
            "executed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "provider": provider,
            "model": "gpt-4o-mini" if provider == "openai" else "mistral",
            "temperature": 0.3,
            "accuracy": f"{correct}/{len(dataset)}",
            "avg_total_latency_ms": round(avg_total, 1),
            "python_version": platform.python_version(),
            "langchain_version": importlib.metadata.version("langchain"),
        },
        "results": results,
    }

    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(eval_data, f, indent=2)

    print(f"\nDone. {correct}/{len(dataset)} correct. Avg latency: {avg_total:.0f}ms")
    print(f"Results saved to {results_path}")


if __name__ == "__main__":
    main()
