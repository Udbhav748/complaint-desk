import os
import sys
import json
import time
import platform
import importlib.metadata
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(".env")
os.environ["LLM_PROVIDER"] = "groq"

from src.config import AppConfig
from src.chains import create_chains

config = AppConfig.from_env()

# Evaluation dataset
DATASET_PATH = "evaluation/test_complaints.json"
RESULTS_PATH = "evaluation/activity_a_results.json"

def main():
    if not os.path.exists(DATASET_PATH):
        print(f"Dataset not found at {DATASET_PATH}")
        sys.exit(1)
        
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        
    print(f"Loaded {len(dataset)} complaints.")
    print(f"{'ID':<10} | {'Expected Category'}")
    print("-" * 30)
    for case in dataset:
        print(f"{case['id']:<10} | {case['expected_category']}")
        
    c_chain, r_chain = create_chains(config)
    
    results = []
    
    # Tracking
    total_class_latency = 0.0
    total_reply_latency = 0.0
    
    for case in dataset:
        case_id = case["id"]
        complaint = case["complaint"]
        expected = case["expected_category"]
        print(f"\nProcessing {case_id}...")
        
        # Classification
        t0 = time.perf_counter()
        try:
            actual_raw = c_chain.invoke({"text": complaint})
        except Exception as e:
            actual_raw = f"ERROR: {e}"
        t1 = time.perf_counter()
        class_latency = (t1 - t0) * 1000
        total_class_latency += class_latency
        
        # Normalize category
        actual_category = actual_raw.strip().lower()
        if actual_category not in ["billing", "loan", "fraud", "app_issue"]:
            actual_category = "unclassified"
            
        is_correct = (actual_category == expected)
        
        # Reply
        t2 = time.perf_counter()
        if actual_category != "unclassified":
            try:
                reply = r_chain.invoke({"text": complaint, "cat": actual_category})
            except Exception as e:
                reply = f"ERROR: {e}"
        else:
            reply = "Validation failed. Unclassified."
        t3 = time.perf_counter()
        reply_latency = (t3 - t2) * 1000
        total_reply_latency += reply_latency
        
        total_latency = class_latency + reply_latency
        
        res_obj = {
            "id": case_id,
            "complaint": complaint,
            "expected_category": expected,
            "actual_category_raw": actual_raw,
            "actual_category": actual_category,
            "classification_correct": is_correct,
            "classification_latency_ms": class_latency,
            "reply": reply,
            "reply_latency_ms": reply_latency,
            "total_latency_ms": total_latency,
            "validation_passed": actual_category != "unclassified",
            "reply_relevant": None, # Fill later
            "professional_tone": None, # Fill later
            "invented_policy": None, # Fill later
            "notable_failure": None, # Fill later
            "reply_requirements": case.get("reply_requirements", "")
        }
        results.append(res_obj)

    eval_data = {
        "evaluation": {
            "name": "FWC Module 8 Activity A - Complaint Desk",
            "dataset": DATASET_PATH,
            "cases": len(dataset),
            "executed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "provider": config.llm_provider,
            "model": config.active_model_name,
            "temperature": config.temperature,
            "python_version": platform.python_version(),
            "langchain_version": importlib.metadata.version('langchain'),
            "status": "COMPLETED"
        },
        "results": results,
    }
    
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(eval_data, f, indent=2)
        
    print(f"\nDone. Results saved to {RESULTS_PATH}")

if __name__ == "__main__":
    main()
