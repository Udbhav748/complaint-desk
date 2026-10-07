# Activity B — Groq ↔ Ollama/Mistral Comparison

FWC Module 8 §18.2. Same ten frozen complaints (`test_complaints.json`), same reference
prompts from the handout's §18.1 snippet, one line changed between runs:

```python
llm = ChatOpenAI(model="openai/gpt-oss-20b", base_url="https://api.groq.com/openai/v1", temperature=0.3)   # cloud
llm = ChatOllama(model="mistral", temperature=0.3)                                                          # local
```

**Provider disclosure:** the assignment reference uses `ChatOpenAI(model="gpt-4o-mini")`, but no
OpenAI API key/credits were available for this project — a live OpenAI attempt failed on all 10
calls with `HTTP 429 — "You have no credits remaining"` (raw evidence in
`results/openai_attempt_failed.json`). **This comparison is Groq vs. Ollama, not OpenAI vs. Ollama.**
The cloud data point below is Groq's `openai/gpt-oss-20b` (same 10 complaints, same cloud-API
deployment model Activity A actually runs — see `results/groq_activity_a_reference.md`). Local run:
`mistral:latest` (4.4GB) via Ollama, CPU only. No OpenAI numbers are reported anywhere in this repo.

## Baseline Comparison — Bare Reference Prompt

The number below is the baseline: **both providers run the identical, unmodified §18.1 prompts**
(`"Classify into billing/loan/fraud/app_issue. One word only.\n{text}"` and `"Polite 60-word
acknowledgement for a {cat} complaint. Sign as XYZ Finance.\n{text}"`), `temperature=0.3`, same 10
complaints. Only the `llm` line differs (Groq vs. Ollama). No hardening, no few-shot examples, no
guardrails on either side.

| Provider / Model | Prompt | Correct |
|---|---|---|
| Groq `openai/gpt-oss-20b` | Bare reference prompt | 10/10 |
| Ollama `mistral` (local) | Bare reference prompt | 8/10 |

The bare reference prompt also produced unsafe reply output on both providers — fabricated refunds,
fake investigations, false routing claims (e.g. *"we will refund the excess amount of $45.00"*, *"we
have initiated an investigation"*) — a prompt-engineering failure of the §18.1 reference prompt
itself, not something specific to either model.

**This 10/10 vs. 8/10 result is the baseline Groq-vs-Ollama comparison.** It is not the final word on
Mistral's capability — see the follow-up experiment below, which is a separate, later test that
swaps in a hardened/tuned prompt on Ollama only (Groq's side of that follow-up is unchanged, still
running the bare prompt).

## Latency

| Provider / Model | Avg. total latency |
|---|---|
| Groq `openai/gpt-oss-20b` | **1,092 ms** |
| Ollama `mistral` (local, CPU) | **26,969 ms** (~27 s) |

Groq's inference hardware makes cloud ~25× faster than unaccelerated local CPU inference.

## Cost per 1,000 Requests (2 calls/complaint)

| Provider / Model | Est. cost / 1,000 complaints | Basis |
|---|---|---|
| Groq `openai/gpt-oss-20b` | **≈ $0.02–0.05** | Published Groq per-token pricing; free tier covered this benchmark |
| Ollama `mistral` (local) | **≈ $0** marginal | No per-token fee — trades it for owned compute/electricity cost |

> OpenAI `gpt-4o-mini` pricing is not included here — it was never actually benchmarked in this
> project, so a cost figure for it would be an unverified estimate, not a measurement.

## Data Privacy

| | Groq | Ollama |
|---|---|---|
| Where inference runs | Third-party cloud | Local machine |
| Complaint data leaves infrastructure? | Yes | No |
| Needs a data-processing agreement? | Yes | No |
| Cross-border transfer question? | Possible | None |

- **Groq**: complaint text — possibly containing account numbers or PII — leaves the bank's
  infrastructure to a third party, requiring a data-processing agreement and raising
  data-residency questions.
- **Ollama**: complaint text never leaves the machine. No third-party logging, no DPA, no
  cross-border transfer question — the stronger posture for regulated financial data.

## Follow-up Experiment — Hardened/Tuned Prompt on Ollama Only

This is a separate experiment, run *after* the baseline above, to answer a different question: does
better prompting fix Mistral's unsafe output and its 2-case classification miss? It reruns **Ollama
only** with a hardened prompt, then a further-tuned prompt — it is not a re-run of Groq and must not
be read as part of the baseline comparison.

| Run | Provider | Prompt | Classification | Guardrail violations |
|---|---|---|---|---|
| Baseline (above) | Groq | Bare reference | 10/10 | — |
| Baseline (above) | Ollama | Bare reference | 8/10 | present |
| Follow-up | Ollama | Hardened | 8/10 (same 2 misses, 3 runs) | 0/10 |
| Follow-up | Ollama | Tuned (hardened + targeted fix) | **10/10** (2 runs) | 0/10 |

Guardrail violations drop to 0/10 as soon as the hardened prompt is applied; the classification gap
needed a further targeted fix on top of that to reach 10/10. Full story, root cause, and the fix
itself: [`followup.md`](followup.md).

## Which would you ship for a bank, and why?

On the baseline bare-prompt comparison, Groq already classifies 10/10 vs. Ollama's 8/10, and Groq is
~25× faster (~1.1 s vs. ~20–35 s local CPU) — unacceptable latency for a live chat interface either
way for Ollama. Ship Groq's cloud API today. Separately, the bare reference prompt is unsafe on
**both** providers (fabricated refunds/investigations), so ship the hardened, guardrailed prompt
regardless of provider — the follow-up experiment shows it also closes Ollama's remaining accuracy
gap, so prompt hardening, not model choice, is what fixes correctness here. Latency, not quality, is
still the deciding factor against shipping a local model for a live interface. Reserve a local model
like Mistral for an internal, latency-tolerant, privacy-sensitive workflow where data residency
outweighs the latency cost and the overhead of maintaining a model-specific prompt variant. This
verdict is explicitly **Groq vs. Ollama** — OpenAI was never run, so it is not part of this
recommendation.
