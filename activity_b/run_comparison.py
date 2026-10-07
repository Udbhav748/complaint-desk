"""Activity B — Groq <-> Ollama/Mistral swap benchmark.

Runs the FWC Module 8 §18.1 *reference* Activity A snippet against the same
frozen 10-complaint dataset used for Activity A, once per provider, to
produce a fair side-by-side:

    classify = (ChatPromptTemplate.from_template(
        "Classify into billing/loan/fraud/app_issue. One word only.\n{text}")
        | llm | StrOutputParser())
    reply = (ChatPromptTemplate.from_template(
        "Polite 60-word acknowledgement for a {cat} complaint. Sign as XYZ Finance.\n{text}")
        | llm | StrOutputParser())

The only thing that changes between runs is the `llm` line:
    ChatOpenAI(model="openai/gpt-oss-20b", base_url="https://api.groq.com/openai/v1", temperature=0.3)   vs.
    ChatOllama(model="mistral", temperature=0.3)

An OpenAI API key/credits were not available for this project, so the cloud
side of this comparison is Groq's OpenAI-compatible API, not OpenAI directly
— see `report.md` for the full disclosure.

Usage:
    python run_comparison.py groq
    python run_comparison.py ollama
"""

import json
import os
import sys
import time
import platform
import importlib.metadata
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

HERE = Path(__file__).resolve().parent
DATASET_PATH = HERE / "test_complaints.json"
ALLOWED_CATEGORIES = ("billing", "loan", "fraud", "app_issue")


def build_llm(provider: str):
    if provider == "groq":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="openai/gpt-oss-20b",
            temperature=0.3,
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY"),
        )
    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model="mistral", temperature=0.3)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("groq", "ollama"):
        print("Usage: python run_comparison.py [groq|ollama]")
        sys.exit(1)

    provider = sys.argv[1]
    results_path = HERE / "results" / f"{provider}.json"

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
            "name": "FWC Module 8 Activity B - Groq vs Ollama swap",
            "dataset": str(DATASET_PATH.relative_to(ROOT_DIR)),
            "cases": len(dataset),
            "executed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "provider": provider,
            "model": "openai/gpt-oss-20b" if provider == "groq" else "mistral",
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
