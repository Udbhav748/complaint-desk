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

Baseline only — both providers on the identical bare §18.1 reply prompt, same 10 complaints:

| Reply Quality Dimension | Groq | Ollama / Mistral |
|---|---|---|
| Relevance | All 10 replies address specifics of the submitted complaint (e.g. the duplicate charge, the OTP/fraud alert, the app crash) | All 10 replies address specifics of the submitted complaint, including the 2 cases it misclassified — e.g. CMP-002's reply still discusses the loan/EMI issue even though the category label was wrong |
| Professional tone | Polite, consistent "Dear Valued Customer... Best Regards, XYZ Finance" structure across all 10 | Polite, consistent "Dear Valued Customer... Best Regards, XYZ Finance Team" structure across all 10 |
| Category appropriateness | Reply content matches the predicted category in all 10 cases; the literal category word appears in 2/10 replies (CMP-003, CMP-007) | Reply content generally matches the predicted category label (not always the *expected* one, since 2/10 were misclassified); the literal category word appears in 2/10 replies (CMP-001, CMP-005) |
| Unsupported claims | 8/10 replies contain at least one unsupported operational claim (refund, "investigating", "secure your account") | 8/10 replies contain at least one unsupported operational claim (refund, "investigating", "rectify", "secure your account", "immediate steps") |
| Overall | Relevant, professional, but the bare prompt lets it over-promise in 8/10 replies | Relevant, professional, but the bare prompt lets it over-promise in 8/10 replies — same failure rate as Groq |

Both providers generate relevant, professionally worded acknowledgements on this baseline — the
measured difference is in classification (see below), not reply tone. The bare reference prompt
itself allows unsupported operational claims on **both** providers at an identical 8/10 rate, so this
is a weakness of the §18.1 prompt, not something to silently fix here. The hardened/tuned prompt work
that addresses it lives only in [`followup.md`](followup.md), scoped to Ollama.

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
