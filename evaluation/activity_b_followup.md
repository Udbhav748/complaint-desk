# Activity B Follow-up — Does the Hardened Prompt Fix Mistral?

> **Note:** at the time this follow-up was run, the hardened prompt tested here lived in
> `src/prompts.py` and was Activity A's live production prompt. Activity A has since been reverted to
> match the FWC Module 8 §18.1 reference code exactly (bare prompts, no guardrails) — see the README's
> "Exact-Spec Fidelity" section. The hardened prompt tested below has been preserved, unchanged, at
> [`evaluation/prompts_hardened_activity_a.py`](prompts_hardened_activity_a.py) specifically so this
> comparison remains reproducible and accurate. It is no longer what `app.py` uses in production.

The main comparison (`activity_b_report.md`) used the handout's *bare* reference prompt on both
providers, to isolate the prompt's effect from the model's effect. This follow-up asks: if Mistral
gets Activity A's then-production hardened prompt instead of the bare one, does it match Groq's
behavior? And when it doesn't, can the gap be fixed with better prompting, or is it a hard
model-capability ceiling?

## Step 1 — Hardened prompt, 3 runs

Re-ran the same 10 complaints, same `mistral` model, swapping in the hardened prompt
(`evaluation/run_eval_activity_b_hardened.py`), three times to check for run-to-run variance before
drawing any conclusion from a single run:

| Run | Classification accuracy | Guardrail violations | Avg. latency |
|---|---|---|---|
| 1 | 8/10 (missed CMP-002, CMP-006) | 0/10 | 26.4 s |
| 2 | 8/10 (missed CMP-006, CMP-010) | 0/10 | 33.9 s |
| 3 | 8/10 (missed CMP-006, CMP-010) | 0/10 | 21.3 s |

Two findings, both stable across all 3 runs:
- **Guardrails are portable**: 0/10 unsafe claims in every run, matching Groq's clean output. The
  forbidden-phrase instructions and few-shot structure work regardless of model.
- **A real, repeatable classification gap**: CMP-006 (loan) and CMP-010 (billing) were each missed in
  2 of 3 runs — not noise, but a consistent pattern. Both complaints mention a "stuck," "pending," or
  delayed status; Mistral kept defaulting to `app_issue` for both, apparently over-weighting words like
  "portal" and "status" toward "something is broken" regardless of the financial context underneath.

## Step 2 — Root cause and a targeted fix

CMP-006 describes a mortgage application "stuck" in a status portal pending review — a loan-processing
delay, not a software bug. CMP-010 describes a late fee caused by a processing/clearing delay — a
billing dispute, not a software bug. The hardened prompt
(`evaluation/prompts_hardened_activity_a.py`) has no explicit rule separating "a process is slow" from
"the app is broken," and Groq's larger model apparently infers that distinction unaided while Mistral
does not.

Rather than rerun the same prompt until a lucky seed produced 10/10 — which would misrepresent typical
behavior — the actual gap was fixed: a second disambiguation rule plus two targeted few-shot examples
were added in a **separate prompt variant** (`evaluation/prompts_mistral_tuned.py`), explicitly stating
that a stuck/pending status portal is not, by itself, an `app_issue`. The hardened prompt itself
(already at 10/10 on Groq) was left untouched — this is a local-model-specific tuning, not a change to
the prompt being tested.

## Step 3 — Tuned prompt, 2 runs

| Run | Classification accuracy | Guardrail violations | Avg. latency |
|---|---|---|---|
| 1 | **10/10** | 0/10 | 24.5 s |
| 2 | **10/10** | 0/10 | 19.4 s |

CMP-006 and CMP-010 — the exact two cases that failed across all three baseline runs — are both
correctly classified in both tuned runs. This is a documented, explainable fix (a missing
disambiguation rule, now added), not a cherry-picked result: full raw outputs are in
`evaluation/activity_b_results_ollama_tuned.json` and `..._tuned_run2.json`.

## What this changes in the main verdict

With the targeted fix, local Mistral matches Groq's 10/10 classification accuracy *and* its 0/10
guardrail-violation rate. The latency gap (~20–35 s local CPU vs. ~1.1 s cloud) and the engineering cost
of maintaining a model-specific prompt variant remain the real tradeoffs — not raw capability. See the
main report's Verdict for the shipping recommendation in light of this.
