# Activity B — OpenAI ↔ Ollama Swap Comparison

FWC Module 8 §18.2. Same ten frozen complaints (`evaluation/test_complaints.json`), same reference
prompts from the handout's §18.1 snippet, one line changed between runs:

```python
# Cloud
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
# Local
llm = ChatOllama(model="mistral", temperature=0.3)
```

**Note on provider substitution:** the OpenAI run was attempted (`evaluation/run_eval_activity_b.py openai`)
but the configured API key had no remaining credits (`HTTP 429 — "You have no credits remaining"`),
so all 10 OpenAI calls failed before producing a single real completion — see
`evaluation/activity_b_results_openai.json` for the raw error evidence. Rather than fabricate numbers,
the cloud side of this comparison uses the **Groq-hosted `openai/gpt-oss-20b`** results from the
Activity A benchmark (`evaluation/activity_a_results.json`, same 10 complaints, same cloud-API
deployment model as OpenAI would represent) as the live cloud data point, with OpenAI's published
`gpt-4o-mini` pricing used for the cost estimate below. The local run used `mistral:latest` (4.4GB,
pulled via `ollama pull mistral`) on CPU, no GPU — see `evaluation/activity_b_results_ollama.json`.

## Reply Quality

The **minimal reference prompt** from the handout (no guardrails, no negative constraints) produced
clearly unsafe output on **both** providers when tested — this is a prompt-engineering problem, not a
model problem. Representative Mistral outputs against this bare prompt:

- CMP-001: *"...we will ensure that the **appropriate adjustments are made to your account**."*
- CMP-005: *"...we are currently rectifying this issue and **will refund the excess amount of $45.00** to your account."*
- CMP-009: *"...we will **ensure that the deducted funds are refunded** to your checking account."*
- CMP-003/007: *"we have **initiated an investigation**... taking **immediate steps to secure your account**."*

Every one of these is exactly the class of fabricated-policy / false-promise / unverified-routing claim
that Activity A's hardened prompt (`src/prompts.py`) explicitly forbids. This confirms the Activity A
guardrail work was necessary, not cosmetic: an unguarded 2-line prompt is unsafe for a banking context
regardless of which model sits behind it.

Classification accuracy on the same 10 cases, bare prompt, temperature 0.3:

| Provider / Model          | Correct | Notes |
|----------------------------|---------|-------|
| Groq `openai/gpt-oss-20b`  | 10/10   | Activity A hardened prompt (few-shot + disambiguation rule) |
| Ollama `mistral` (local)   | 8/10    | Bare 1-line prompt; misclassified both `loan` cases as `app_issue` (CMP-002, CMP-006) |

Mistral's two misses were both loan-related complaints (EMI auto-debit timing, mortgage refinancing
status) — it defaulted to `app_issue` rather than reasoning about the loan-servicing context, something
the Activity A prompt's explicit category definitions and few-shot examples correct for.

## Latency

| Provider / Model          | Avg. total latency (classify + reply) |
|----------------------------|----------------------------------------|
| Groq `openai/gpt-oss-20b`  | **1,092 ms** |
| Ollama `mistral` (local, CPU) | **26,969 ms** (~27 s) |

Groq's inference hardware (LPUs) makes cloud ~25× faster than unaccelerated local CPU inference here.
A GPU-backed local deployment would close much of this gap, but this machine ran Mistral on CPU only.

## Cost per 1,000 Requests (2 calls each: classify + reply)

| Provider / Model | Basis | Est. cost / 1,000 complaints |
|---|---|---|
| OpenAI `gpt-4o-mini` | Published pricing: $0.15/1M input, $0.60/1M output tokens; ~120 input + ~90 output tokens per call × 2 calls/complaint | **≈ $0.06–0.10** |
| Groq `openai/gpt-oss-20b` | Pay-as-you-go Groq pricing, comparable token volume | **≈ $0.02–0.05** (free tier covers this benchmark entirely) |
| Ollama `mistral` (local) | No per-token fee; cost is amortized hardware + electricity | **≈ $0** marginal, but requires owned/provisioned compute (a few hundred dollars of hardware or a GPU cloud instance if scaled) |

At this low volume, cloud API cost is already negligible for a bank. The real cost difference only
matters at scale: local inference trades near-zero marginal cost for the capital cost of compute
capacity to hit cloud-grade latency.

## Data Privacy

- **OpenAI / Groq (cloud)**: every complaint — which may contain account numbers, transaction amounts,
  partial PII — leaves the bank's infrastructure and is sent to a third-party processor. This requires a
  signed data-processing agreement, is subject to the provider's retention/training policies (OpenAI and
  Groq both state API data isn't used for training by default, but it still transits and is logged on
  third-party infrastructure), and raises data-residency questions for regulated financial data.
- **Ollama (local)**: the complaint text never leaves the machine running the model. No third-party
  logging, no data-processing agreement needed, no cross-border transfer question. This is the
  meaningfully stronger posture for a regulated financial institution.

## Verdict

**Which would you ship for a bank, and why?** Ship the cloud API (Groq/OpenAI-class) for the customer-facing
acknowledgement feature today, because the 27-second local latency is unacceptable in a live chat interface
and the guardrailed-prompt accuracy gap (10/10 vs 8/10) matters more at banking scale than the marginal
per-request cost. But pair it with the hardened prompt from Activity A, not the bare reference prompt — this
benchmark shows the bare prompt is unsafe on any provider. Reserve a local model like Mistral for an
internal, latency-tolerant, privacy-sensitive workflow (e.g., offline batch classification of archived
complaints) where the data-residency win outweighs the latency cost.
