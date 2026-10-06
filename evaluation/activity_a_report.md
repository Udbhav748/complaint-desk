# Activity A — Empirical Evaluation

## Evaluation Setup

Provider:
Groq

Model:
openai/gpt-oss-20b

Classification temperature:
0.0

Reply temperature:
0.2

Classification max tokens:
256

Reply max tokens:
300

## Aggregate Results

Classification:
10 / 10

Classification accuracy:
100.0%

Relevant replies:
10 / 10

Professional replies:
10 / 10

Policy-invention cases:
5 / 10

Average classification latency:
641.40 ms

Average reply latency:
451.08 ms

Average total latency:
1092.48 ms

## Observed Guardrail Violations
- CMP-001 — Reply made an unsupported operational claim ('will forward the details for further review').
- CMP-004 — Reply made an unsupported operational claim ('Your report has been logged') without a ticketing backend.
- CMP-005 — Reply made an unsupported routing claim ('will forward them to the appropriate team for review').
- CMP-008 — Reply made an unsupported operational claim ('Your report has been logged') without a ticketing backend.
- CMP-009 — Reply made an unsupported operational claim ('I’ve logged the details') without a ticketing backend.

## Interpretation

- classification performed correctly on the frozen 10-case set
- replies were relevant/professional where supported by the evidence
- some replies still produced unsupported operational claims despite the prompt guardrails
- this is an observed model-output limitation from this benchmark run
- the result demonstrates why empirical evaluation is necessary
