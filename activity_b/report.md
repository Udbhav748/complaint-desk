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

## Reply Quality

The bare reference prompt produced unsafe output — fabricated refunds, fake investigations, false
routing claims (e.g. *"we will refund the excess amount of $45.00"*, *"we have initiated an
investigation"*) — a prompt-engineering failure, not a model-specific one. Classification accuracy:

| Provider / Model | Correct | Notes |
|---|---|---|
| Groq `openai/gpt-oss-20b` | 10/10 | Hardened prompt |
| Ollama `mistral` (local) | 8/10 → **10/10** | Bare prompt scored 8/10; hardened prompt also 8/10 (repeatable miss, see follow-up); a targeted fix for that specific gap reached 10/10 |

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

> **Follow-up**: does hardening the prompt fix Mistral's unsafe-output problem? Yes — guardrail
> violations drop to 0/10 across 3 runs. Classification stayed at 8/10 (same 2 misses, repeatably),
> but a targeted prompt fix for that specific gap brought it to 10/10, confirmed over 2 runs. Full
> story, root cause, and the fix itself: [`followup.md`](followup.md).

## Which would you ship for a bank, and why?

Ship Groq's cloud API today — with a correctly tuned prompt both providers reach 10/10 accuracy and
0/10 unsafe claims, so the deciding factor is latency, not quality: ~1.1 s cloud vs. ~20–35 s local
CPU is unacceptable for a live chat interface. Always ship the hardened, guardrailed prompt
regardless of provider, since the bare reference prompt is unsafe on either one. Reserve a local
model like Mistral for an internal, latency-tolerant, privacy-sensitive workflow where data
residency outweighs the latency cost and the overhead of maintaining a model-specific prompt
variant. This verdict is explicitly **Groq vs. Ollama** — OpenAI was never run, so it is not part of
this recommendation.
