# Activity B — Groq ↔ Ollama/Mistral Comparison

FWC Module 8 §18.2. The assignment reference uses `ChatOpenAI(model="gpt-4o-mini")`, but no OpenAI
API key/credits were available for this project — a live OpenAI attempt failed on all 10 calls with
`HTTP 429 — "You have no credits remaining"` (`results/openai_attempt_failed.json`). **This
comparison is Groq vs. Ollama, not OpenAI vs. Ollama** — no OpenAI numbers are reported anywhere.

## Experimental Setup

Same 10 frozen complaints (`test_complaints.json`), same bare §18.1 reference prompts on both
providers, `temperature=0.3`, same two-chain workflow. Only the `llm` line changes:

```python
llm = ChatOpenAI(model="openai/gpt-oss-20b", base_url="https://api.groq.com/openai/v1", temperature=0.3)   # cloud
llm = ChatOllama(model="mistral", temperature=0.3)                                                          # local
```

(`mistral:latest`, 4.4GB, via Ollama, CPU only.)

## Reply Quality

The bare reference prompt produced unsafe output on **both** providers — fabricated refunds, fake
investigations, false routing claims (e.g. *"we will refund the excess amount of $45.00"*) — a
prompt-engineering failure of the §18.1 reference prompt itself, not a model-specific one.

## Classification Accuracy

| Provider / Model | Correct |
|---|---|
| Groq `openai/gpt-oss-20b` | 10/10 |
| Ollama `mistral` (local) | 8/10 |

A separate follow-up experiment tests whether a hardened/tuned prompt closes Ollama's gap — see
[`followup.md`](followup.md).

## Latency

| Provider / Model | Avg. total latency |
|---|---|
| Groq `openai/gpt-oss-20b` | **1,092 ms** |
| Ollama `mistral` (local, CPU) | **26,969 ms** (~27 s) |

## Cost per 1,000 Requests (2 calls/complaint)

| Provider / Model | Est. cost / 1,000 complaints |
|---|---|
| Groq `openai/gpt-oss-20b` | **≈ $0.02–0.05** (free tier covered this benchmark) |
| Ollama `mistral` (local) | **≈ $0** marginal (owned compute/electricity instead) |

## Data Privacy

| | Groq | Ollama |
|---|---|---|
| Where inference runs | Third-party cloud | Local machine |
| Complaint data leaves infrastructure? | Yes | No |
| Needs a data-processing agreement? | Yes | No |

## Summary Table

| Metric | Groq | Ollama/Mistral |
|---|---|---|
| Classification | 10/10 | 8/10 baseline |
| Reply quality | Unsafe (bare prompt) | Unsafe (bare prompt) |
| Avg latency | 1,092 ms | 26,969 ms |
| Cost / 1,000 | ≈ $0.02–0.05 | ≈ $0 marginal |
| Privacy | Cloud | Local |

## Which would you ship for a bank, and why?

I would ship Groq for this application because it achieved stronger baseline classification accuracy
and dramatically lower latency than local Ollama/Mistral in our test. Although Ollama provides
stronger data privacy by keeping complaint data local, its CPU latency is much higher and makes it
less suitable for an interactive customer-facing workflow. I would choose Ollama for
privacy-sensitive internal workloads where data residency is more important than response speed.
