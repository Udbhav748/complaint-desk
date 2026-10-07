# Activity A — Empirical Evaluation

Evaluated against **Activity A's `app.py`** — the literal FWC Module 8 §18.1 reference code (bare
2-line prompts, one shared `llm`, flat `temperature=0.3`, no input validation, no category
whitelist), run against the live Groq API.

## Evaluation Setup

| | |
|---|---|
| Provider | Groq |
| Model | `openai/gpt-oss-20b` |
| Temperature | 0.3 (shared, both chains) |
| Dataset | `test_complaints.json` (10 complaints) |
| Executed | 2026-10-06 |

## Aggregate Results

| Metric | Result |
|---|---|
| Classification accuracy | **10/10** |
| Average classification latency | ~210 ms (sum of per-case classification times / 10) |
| Average reply latency | ~745 ms |
| Average total latency | **~955 ms** |
| Replies containing unsupported claims (refund/investigation/"secure your account"/etc.) | **8/10** |

Full raw per-case data (classification output, reply text, latency): `results/groq_activity_a_reference.json`.

## Per-Case Classification

| ID | Expected | Actual | Correct |
|---|---|---|---|
| CMP-001 | billing | billing | ✅ |
| CMP-002 | loan | loan | ✅ |
| CMP-003 | fraud | fraud | ✅ |
| CMP-004 | app_issue | app_issue | ✅ |
| CMP-005 | billing | billing | ✅ |
| CMP-006 | loan | loan | ✅ |
| CMP-007 | fraud | fraud | ✅ |
| CMP-008 | app_issue | app_issue | ✅ |
| CMP-009 | app_issue | app_issue | ✅ |
| CMP-010 | billing | billing | ✅ |

Groq's `openai/gpt-oss-20b` classified all 10 cases correctly even with the bare, example-free
prompt — a stronger result than local `mistral` managed on the same bare prompt in the Activity B
comparison (8/10, see `report.md`).

## Reply Quality — Unsupported Claims

The bare reference prompt in §18.1 ("Polite 60-word acknowledgement... Sign as XYZ Finance.") has no
guardrails against the model promising things the application cannot actually do. Scanning all 10
replies for refund promises, investigation claims, and similar unsupported operational language found
**8 out of 10** contain at least one such claim. Two representative examples:

- **CMP-001 (billing)**: *"Our team is reviewing the transaction and **will issue a refund
  promptly**."* — a monetary promise with no backend to fulfill it.
- **CMP-007 (fraud)**: *"We have **initiated a full investigation**... Our fraud team will review all
  relevant logs and **secure** [the account]."* — claims of internal routing and action that never
  actually happen.

This is not a code defect — it is the literal, expected behavior of the assignment's bare reference
prompt, with no few-shot examples or negative constraints to prevent it. It directly demonstrates why
a hardened prompt (disambiguation rules, forbidden-phrase constraints) matters for a banking context,
which is explored further in Activity B's comparison and follow-up.

## Note on an Earlier Version of This Report

An earlier version of this file reported 100% classification accuracy and only 5/10 unsupported-claim
cases. Those numbers came from a now-reverted, substantially hardened prompt (few-shot examples,
disambiguation rules, explicit forbidden-phrase guardrails) that is no longer part of the live
`app.py`. This report reflects the current, exact-spec code only.
