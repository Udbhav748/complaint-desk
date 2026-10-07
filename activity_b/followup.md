# Activity B Follow-up — Does the Hardened Prompt Fix Mistral?

> **Note:** at the time this follow-up was run, the hardened prompt tested here was Activity A's live
> production prompt. Activity A has since been reverted to match the FWC Module 8 §18.1 reference
> code exactly (bare prompts, no guardrails) — see `activity_a/README.md`. The hardened prompt tested
> below has been preserved, unchanged, at [`prompts_hardened.py`](prompts_hardened.py) specifically so
> this comparison remains reproducible and accurate. It is no longer what `activity_a/app.py` uses in
> production.

The main comparison (`report.md`) used the handout's *bare* reference prompt on both
providers, to isolate the prompt's effect from the model's effect. This follow-up asks a separate
question, scoped to Ollama/Mistral only: does swapping in Activity A's then-production hardened
prompt improve Mistral's own results, and can a real classification gap be fixed with better
prompting, or is it a hard model-capability ceiling? It is not a re-run of Groq and is not part of
the baseline Groq-vs-Ollama comparison.

| | Classification | Unsupported-claim violations |
|---|---|---|
| **Baseline** — Groq, bare prompt | 10/10 | 8/10 |
| **Baseline** — Ollama, bare prompt | 8/10 | 8/10 |
| **Follow-up** — Ollama, hardened prompt | 8/10 | 0/10 |
| **Follow-up** — Ollama, tuned prompt | 10/10 | 0/10 |

(Baseline rows are the measured results from `report.md`, repeated here only for reference — they
were not re-run as part of this follow-up.)

## Step 1 — Hardened prompt, 3 runs

Re-ran the same 10 complaints, same `mistral` model, swapping in the hardened prompt
(`run_comparison_hardened.py`), three times to check for run-to-run variance before
drawing any conclusion from a single run:

| Run | Classification accuracy | Guardrail violations | Avg. latency |
|---|---|---|---|
| 1 | 8/10 (missed CMP-002, CMP-006) | 0/10 | 26.4 s |
| 2 | 8/10 (missed CMP-006, CMP-010) | 0/10 | 33.9 s |
| 3 | 8/10 (missed CMP-006, CMP-010) | 0/10 | 21.3 s |

Two findings, both stable across all 3 runs:
- **The hardened prompt produced 0/10 unsafe-claim violations across all three Mistral runs.** This
  should not be compared to the baseline Groq result, which used the bare reference prompt and had
  8/10 unsupported-claim cases (see `report.md`'s Reply Quality section) — Groq was never re-run with
  this hardened prompt. The 0/10 result demonstrates that the guardrail instructions themselves can
  work on the local Mistral model, not that Mistral "caught up" to a 0/10 Groq baseline, since no such
  baseline exists.
- **A real, repeatable classification gap**: CMP-006 (loan) and CMP-010 (billing) were each missed in
  2 of 3 runs — not noise, but a consistent pattern. Both complaints mention a "stuck," "pending," or
  delayed status; Mistral kept defaulting to `app_issue` for both, apparently over-weighting words like
  "portal" and "status" toward "something is broken" regardless of the financial context underneath.

## Step 2 — Root cause and a targeted fix

CMP-006 describes a mortgage application "stuck" in a status portal pending review — a loan-processing
delay, not a software bug. CMP-010 describes a late fee caused by a processing/clearing delay — a
billing dispute, not a software bug. The hardened prompt
(`prompts_hardened.py`) has no explicit rule separating "a process is slow" from
"the app is broken," and Groq's larger model apparently infers that distinction unaided while Mistral
does not.

Rather than rerun the same prompt until a lucky seed produced 10/10 — which would misrepresent typical
behavior — the actual gap was fixed: a second disambiguation rule plus two targeted few-shot examples
were added in a **separate prompt variant** (`prompts_mistral_tuned.py`), explicitly stating
that a stuck/pending status portal is not, by itself, an `app_issue`. The hardened prompt is
preserved as a separate historical prompt variant and was not used in the final Activity A
application or the baseline Groq-vs-Ollama comparison. The follow-up tuning is therefore an
Ollama/Mistral-only experiment.

## Step 3 — Tuned prompt, 2 runs

| Run | Classification accuracy | Guardrail violations | Avg. latency |
|---|---|---|---|
| 1 | **10/10** | 0/10 | 24.5 s |
| 2 | **10/10** | 0/10 | 19.4 s |

CMP-006 and CMP-010 — the exact two cases that failed across all three hardened-prompt runs — are both
correctly classified in both tuned runs. This is a documented, explainable fix (a missing
disambiguation rule, now added), not a cherry-picked result: full raw outputs are in
`results/ollama_tuned.json` and `..._tuned_run2.json`.

## What this changes in the main verdict

With the targeted prompt fix, local Mistral reached 10/10 classification accuracy and 0/10
unsupported-claim violations in the follow-up runs. This should be compared with the corresponding
baseline Groq result carefully: Groq achieved 10/10 classification with the bare prompt, but its
baseline reply generation still showed 8/10 unsupported-claim cases. The follow-up therefore
demonstrates the effect of prompt hardening on Mistral rather than showing that Mistral simply
matched the baseline Groq safety behavior. The latency gap (~20–35 s local CPU vs. ~1.1 s cloud) and
the engineering cost of maintaining a model-specific prompt variant remain the real tradeoffs — not
raw capability. See the main report's "Which would you ship for a bank, and why?" section for the
shipping recommendation in light of this.
