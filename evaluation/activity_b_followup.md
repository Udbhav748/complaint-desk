# Activity B Follow-up — Does the Hardened Prompt Fix Mistral?

The main comparison (`activity_b_report.md`) used the handout's *bare* reference prompt on both
providers, to isolate the prompt's effect from the model's effect. This follow-up asks: if Mistral
gets Activity A's actual hardened prompt (`src/prompts.py`) instead of the bare one, does it match
Groq's behavior?

Re-ran the same 10 complaints, same `mistral` model, swapping in the hardened prompt
(`evaluation/run_eval_activity_b_hardened.py`):

| Metric | Bare prompt | Hardened prompt |
|---|---|---|
| Classification accuracy | 8/10 | 8/10 (same score, different misses — fixed CMP-002, newly missed CMP-010) |
| Replies with guardrail-violating phrases | Several (forwarding/refund/investigation claims) | **0/10 — fully clean** |
| Avg. total latency | ~27.0 s | ~34.1 s (longer prompt → more tokens to process) |

**The guardrails are portable**: the forbidden-phrase instructions and few-shot structure eliminated
every unsafe claim (false refunds, false investigations, false routing) on Mistral too, matching
Groq's clean output.

**Classification accuracy did not improve** — Mistral still missed 2/10 cases, but a different 2.
It correctly caught `loan` on CMP-002 after the fix but newly missed `billing` on CMP-010, and still
missed `loan` on CMP-006 — both times defaulting to `app_issue`. This is a **model-capability gap**,
not a prompt-engineering gap: hardening the prompt fixes safety, not classification ceiling. Full raw
outputs: `evaluation/activity_b_results_ollama_hardened.json`.
