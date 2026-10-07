# Activity B — Groq ↔ Ollama/Mistral Comparison

FWC Module 8 §18.2. The teacher's reference uses `ChatOpenAI(model="gpt-4o-mini")`, but no OpenAI
API key/credits were available — a live OpenAI attempt failed on all 10 calls with `HTTP 429 — "You
have no credits remaining"` (`results/openai_attempt_failed.json`). **This comparison is Groq vs.
Ollama, not OpenAI vs. Ollama** — no OpenAI numbers are reported anywhere.

## Experimental Setup

Same 10 frozen complaints, same bare §18.1 prompts, `temperature=0.3`, same two-chain workflow on
both providers — only the `llm` line changes (Groq `openai/gpt-oss-20b` vs. local Ollama
`mistral`, CPU only).

## Reply Quality

Manual qualitative review of the 10 raw replies per provider (classification/latency below are
measured directly by the benchmark script):

| Dimension | Groq | Ollama / Mistral |
|---|---|---|
| Relevance | All 10 replies address complaint specifics | All 10 replies address complaint specifics, even the 2 misclassified |
| Professional tone | Consistent, polite "Dear Valued Customer...Best Regards" structure | Same, consistent across all 10 |
| Category appropriateness | Matches predicted category in all 10 | Matches predicted (not always *expected*) category label |
| Unsupported claims | **8/10** replies contain an unsupported operational claim (refund, "investigating", etc.) | **8/10** replies contain an unsupported operational claim — identical rate |

Both providers are relevant and professional; the bare §18.1 prompt allows unsupported claims at an
identical 8/10 rate on both, so this is a prompt weakness, not a provider difference. Hardened/tuned
prompt work that addresses it is a separate Ollama-only experiment — see [`followup.md`](followup.md).

## Classification Accuracy

| Provider / Model | Correct |
|---|---|
| Groq `openai/gpt-oss-20b` | 10/10 |
| Ollama `mistral` (local) | 8/10 |

(A follow-up experiment tests whether a hardened/tuned prompt closes Ollama's gap — see
[`followup.md`](followup.md); those results are not part of this baseline.)

## Latency

| Provider / Model | Avg. total latency |
|---|---|
| Groq `openai/gpt-oss-20b` | **~955 ms** |
| Ollama `mistral` (local, CPU) | **~26,969 ms** (~27 s) |

## Cost per 1,000 Requests (2 calls/complaint, 2,000 LLM calls)

| Provider / Model | Est. cost / 1,000 complaints |
|---|---|
| Groq `openai/gpt-oss-20b` | **≈ $0.06** (estimated) |
| Ollama `mistral` (local) | **≈ $0** marginal |

No token-usage metadata is recorded in the benchmark JSON, so this is an **estimated inference
cost**, not an observed invoice — the benchmark itself ran under Groq's free tier. Using Groq's
documented pricing (`openai/gpt-oss-20b`: input $0.075/1M tokens, output $0.30/1M tokens) and
representative per-call token assumptions (~350 input + ~125 output tokens/complaint → 350,000
input + 125,000 output tokens per 1,000 complaints):

```
(350,000/1,000,000 × $0.075) + (125,000/1,000,000 × $0.30) = $0.026 + $0.038 ≈ $0.06
```

Ollama's `≈ $0` marginal cost excludes the existing hardware purchase/depreciation and electricity.

## Data Privacy

| | Groq | Ollama |
|---|---|---|
| Where inference runs | Third-party cloud | Local machine |
| Complaint data leaves infrastructure? | Yes | No |
| Contractual/DPA terms | Third-party cloud provider terms and applicable DPA | No third-party model-inference provider involved |

Whether a bank must execute a particular DPA or meet other contractual/regulatory requirements
depends on its own legal/compliance setup — not a universal rule either way.

## Summary Table

| Metric | Groq | Ollama/Mistral |
|---|---|---|
| Classification | 10/10 | 8/10 |
| Reply quality | Unsafe (bare prompt), 8/10 unsupported claims | Unsafe (bare prompt), 8/10 unsupported claims |
| Avg latency | ~955 ms | ~26,969 ms |
| Cost / 1,000 | ≈ $0.06 (estimated) | ≈ $0 marginal |
| Privacy | Cloud | Local |

## Which would you ship for a bank, and why?

I would ship Groq for this application because it achieved stronger baseline classification accuracy
and dramatically lower latency (~955 ms, compared to ~26,969 ms) than local Ollama/Mistral in our test.
Although Ollama provides stronger data privacy by keeping complaint data local, its CPU latency is
much higher and makes it less suitable for an interactive customer-facing workflow. I would choose
Ollama for privacy-sensitive internal workloads where data residency is more important than response
speed.
