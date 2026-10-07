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

Baseline only — both providers on the identical bare §18.1 reply prompt, same 10 complaints. Reply
relevance, professionalism, category appropriateness, and unsupported-claim behavior were assessed
through manual qualitative review of the 10 generated replies in each provider's raw results file;
classification accuracy and latency (below) were measured directly by the benchmark script.

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
| Groq `openai/gpt-oss-20b` | **~955 ms** |
| Ollama `mistral` (local, CPU) | **26,969 ms** (~27 s) |

## Cost per 1,000 Requests (2 calls/complaint)

| Provider / Model | Est. cost / 1,000 complaints |
|---|---|
| Groq `openai/gpt-oss-20b` | **≈ $0.02–0.05** (free tier covered this benchmark) |
| Ollama `mistral` (local) | **≈ $0** marginal (owned compute/electricity instead) |

### Cost Calculation Method

Each complaint requires 2 LLM calls (1 classification + 1 reply generation), so 1,000 complaints
require 2,000 LLM calls. The benchmark JSON does not record token-usage metadata, so the
`$0.02–0.05` figure is an **estimate based on representative token usage**, not a measured billing
amount. Using Groq's documented pricing for `openai/gpt-oss-20b` — input `$0.075 / 1M tokens`,
output `$0.30 / 1M tokens` — and assuming representative, clearly-labelled token counts:

```
Estimated cost = (input_tokens / 1,000,000 × input_price) + (output_tokens / 1,000,000 × output_price)
```

- Classification call: ~150 input tokens (prompt + complaint), ~5 output tokens (one word)
- Reply call: ~200 input tokens (prompt + complaint), ~120 output tokens (60-word reply)
- Per complaint: (350 input + 125 output) tokens
- Per 1,000 complaints (2,000 calls): 350,000 input tokens + 125,000 output tokens

```
(350,000 / 1,000,000 × $0.075) + (125,000 / 1,000,000 × $0.30)
= $0.02625 + $0.0375
= ≈ $0.064
```

This lands close to, if a little above, the quoted `$0.02–0.05` range depending on actual reply
length and prompt overhead — both are estimates, not invoices. This is an estimated inference
cost, not an observed invoice amount; the benchmark itself was completed under the applicable
Groq free-tier usage.

For Ollama, `≈ $0` marginal cost excludes the user's existing hardware purchase/depreciation and
electricity costs — it reflects only the marginal cost of an additional inference call on
already-owned hardware.

## Data Privacy

| | Groq | Ollama |
|---|---|---|
| Where inference runs | Third-party cloud | Local machine |
| Complaint data leaves infrastructure? | Yes | No |
| Data-processing / contractual terms | Third-party cloud provider terms and applicable DPA | No third-party model-inference provider involved |

Groq inference occurs through a third-party cloud service, so complaint data leaves the
application's local infrastructure. Ollama runs inference locally, so complaint data can remain
within the organization's infrastructure. Whether a bank must execute a particular DPA or satisfy
additional contractual/regulatory requirements depends on the organization's legal/compliance
setup and provider agreement — this is not legal advice, and neither a DPA nor its absence is
universally mandatory.

## Summary Table

| Metric | Groq | Ollama/Mistral |
|---|---|---|
| Classification | 10/10 | 8/10 baseline |
| Reply quality | Unsafe (bare prompt) | Unsafe (bare prompt) |
| Avg latency | ~955 ms | 26,969 ms |
| Cost / 1,000 | ≈ $0.02–0.05 | ≈ $0 marginal |
| Privacy | Cloud | Local |

## Which would you ship for a bank, and why?

I would ship Groq for this application because it achieved stronger baseline classification accuracy
and dramatically lower latency (~955 ms, compared to ~26,969 ms) than local Ollama/Mistral in our test.
Although Ollama provides stronger data privacy by keeping complaint data local, its CPU latency is
much higher and makes it less suitable for an interactive customer-facing workflow. I would choose
Ollama for privacy-sensitive internal workloads where data residency is more important than response
speed.
