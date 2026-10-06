# Activity B — OpenAI ↔ Ollama Swap Comparison

FWC Module 8 §18.2. Same ten frozen complaints (`evaluation/test_complaints.json`), same reference
prompts from the handout's §18.1 snippet, one line changed between runs:

```python
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)   # cloud
llm = ChatOllama(model="mistral", temperature=0.3)        # local
```

**Provider substitution note:** the live OpenAI run (`run_eval_activity_b.py openai`) failed on all
10 calls with `HTTP 429 — "You have no credits remaining"` (raw evidence in
`activity_b_results_openai.json`). The cloud data point below uses Activity A's existing
**Groq `openai/gpt-oss-20b`** benchmark instead (same 10 complaints, same cloud-API deployment
model), with OpenAI's published pricing used for the cost estimate. Local run: `mistral:latest`
(4.4GB) via Ollama, CPU only.

## Reply Quality

The bare reference prompt produced unsafe output — fabricated refunds, fake investigations, false
routing claims (e.g. *"we will refund the excess amount of $45.00"*, *"we have initiated an
investigation"*) — a prompt-engineering failure, not a model-specific one. Classification accuracy:

| Provider / Model | Correct | Notes |
|---|---|---|
| Groq `openai/gpt-oss-20b` | 10/10 | Activity A hardened prompt |
| Ollama `mistral` (local) | 8/10 | Bare prompt; missed both `loan` cases |

## Latency

| Provider / Model | Avg. total latency |
|---|---|
| Groq `openai/gpt-oss-20b` | **1,092 ms** |
| Ollama `mistral` (local, CPU) | **26,969 ms** (~27 s) |

Groq's inference hardware makes cloud ~25× faster than unaccelerated local CPU inference.

## Cost per 1,000 Requests (2 calls/complaint)

| Provider / Model | Est. cost / 1,000 complaints |
|---|---|
| OpenAI `gpt-4o-mini` (published pricing) | **≈ $0.06–0.10** |
| Groq `openai/gpt-oss-20b` | **≈ $0.02–0.05** (free tier covers this benchmark) |
| Ollama `mistral` (local) | **≈ $0** marginal — trades per-token cost for owned compute capacity |

## Data Privacy

- **Cloud (OpenAI/Groq)**: complaint text — possibly containing account numbers or PII — leaves the
  bank's infrastructure to a third party, requiring a data-processing agreement and raising
  data-residency questions.
- **Local (Ollama)**: complaint text never leaves the machine. No third-party logging, no DPA, no
  cross-border transfer question — the stronger posture for regulated financial data.

> **Follow-up**: does hardening the prompt fix Mistral's unsafe-output problem? Yes — see
> [`activity_b_followup.md`](activity_b_followup.md) for the full re-run (spoiler: guardrail
> violations drop to 0/10, but classification accuracy stays at 8/10 — a model-capability gap, not
> a prompt gap).

## Verdict

**Which would you ship for a bank, and why?** Ship the cloud API today — 27-second local latency is
unacceptable for a live chat interface, and the 10/10-vs-8/10 accuracy gap persists even with the
same hardened, guardrailed prompt on both. Always use the hardened prompt regardless of provider,
since the bare reference prompt is unsafe on either one. Reserve a local model like Mistral for an
internal, latency-tolerant, privacy-sensitive workflow where data residency outweighs both latency
and accuracy.
