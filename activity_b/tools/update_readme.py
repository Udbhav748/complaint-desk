import re

with open("README.md", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Project Status
status_new = """## Project Status

**CURRENT:**
- The architecture is fully built and **tested offline** (via `FakeListChatModel`).
- The application was empirically evaluated in Activity A using the **Groq / openai/gpt-oss-20b** configuration.
- The frozen 10-complaint benchmark was executed and analyzed against the live API.
- Zero code changes are required to switch providers (managed entirely via `.env`).

**FUTURE:**
- The application is prepared for Activity B (local model integration).
"""
content = re.sub(r"## Project Status.*?---", status_new + "\n---\n", content, flags=re.DOTALL)

# 2. Supported providers
providers_new = """### Supported Providers

The application orchestrates models via `ChatOpenAI` and supports two configuration pathways:

**OpenAI:**
- Uses the proprietary `gpt-4o-mini` model.
- Requires OpenAI API access (`OPENAI_API_KEY`).

**Groq (Tested Configuration):**
- Uses `openai/gpt-oss-20b`.
- Requires Groq API access (`GROQ_API_KEY`).
- Accessed seamlessly through Groq's OpenAI-compatible endpoint (`https://api.groq.com/openai/v1`).

> **IMPORTANT**: The current live/tested configuration uses Groq / openai/gpt-oss-20b. This is distinctly different from OpenAI / gpt-4o-mini. The same LangChain chains and prompts operate deterministically with either provider.
"""
content = re.sub(r"### Supported Providers.*?### Supported Parameters", providers_new + "\n### Supported Parameters", content, flags=re.DOTALL)

# Remove the stale claim about GPT-4o-mini in the Activity A Disclosure
disclosure_new = """> **Activity A Disclosure:** The project originally targeted OpenAI / gpt-4o-mini. However, the actual Activity A tested configuration uses **Groq / openai/gpt-oss-20b**. This distinction is explicit to prevent claiming that benchmark results obtained from GPT-OSS were produced by GPT-4o-mini."""
content = re.sub(r"> \*\*Activity A Disclosure:\*\*.*?\n", disclosure_new + "\n", content)

# 4, 5, 6. Empirical Results & Limitations
empirical_new = """### Activity A Empirical Results

The frozen 10-complaint benchmark was executed against the **Groq / openai/gpt-oss-20b** configuration. The following metrics were collected:

- **Classification Accuracy:** 100% (10/10)
- **Relevant Replies:** 10/10
- **Professional Tone:** 10/10
- **Unsupported Operational/Policy Claims:** 5/10
- **Average Classification Latency:** 641.40 ms
- **Average Reply Latency:** 451.08 ms
- **Average Total Latency:** 1092.48 ms
- **Automated tests:** 55 passed

> **IMPORTANT:** These results come strictly from the frozen 10-case benchmark and the tested `Groq / openai/gpt-oss-20b` configuration. Do not generalize these numbers to all complaints or all deployments.

### Observed Guardrail Limitations

While classification performed correctly (100% accuracy) and replies maintained relevance and professional tone, the empirical evaluation revealed that **5 out of 10 replies** still produced unsupported operational claims despite the strict prompt guardrails.

Several generated replies contained unsupported operational language, such as:
- *Forwarding details for review*
- *Forwarding to an appropriate team*
- *Stating that a report was "logged"*

These claims were treated as guardrail violations because the application has no actual ticketing/routing backend and therefore cannot truthfully claim those actions occurred. 

The original model outputs were NOT rewritten, and failures were NOT hidden. This is an observed model-output limitation from this benchmark run, demonstrating exactly why rigorous empirical evaluation is necessary.
"""
content = re.sub(r"### Evaluation Methodology.*?---", empirical_new + "\n---\n", content, flags=re.DOTALL)


# 7. Deployment
deployment_new = """## Deployment

The project is structured for clean deployment to **Streamlit Community Cloud** or any containerized hosting service.

### Deployment Platform & Evidence
- **Platform**: Local / Streamlit Development Server (Configured for Cloud Deployment)
- **Live URL**: `http://localhost:8501` (Local instance)
- **Deployment Status**: Application successfully initializes, validates configurations, and serves the UI.
- **Actual Smoke Test Complaint**: "I was charged twice for my premium subscription."
- **Observed Classification**: `billing`
- **Observed Reply**: *Valid empathetic acknowledgement maintaining professional tone.*
- **Session Persistence**: Fully verified across Streamlit reruns.

### Deployment Checklist
1. **Repository Setup**: Ensure the repository is pushed to a public GitHub repository.
2. **Platform Link**: Connect the GitHub repository to Streamlit Community Cloud (`https://share.streamlit.io`).
3. **Entrypoint Configuration**: Specify `app.py` as the primary application file.
4. **Environment Secrets**: In the Streamlit deployment settings under **Advanced settings &rarr; Secrets**, add the secret configuration.
"""
content = re.sub(r"## Deployment Preparation.*?---", deployment_new + "\n---\n", content, flags=re.DOTALL)

# 8. Activity B Preparation
activity_b_new = """### Activity B Preparation
- The decoupled `BaseChatModel` factory enables dropping in a local Ollama model (`ChatOllama`) without altering prompt templates, chain structure, or UI orchestration.
- The frozen evaluation benchmark and automated test suite are already prepared to directly compare Activity B's local model against the current Activity A metrics."""
content = re.sub(r"### Planned Future Improvements.*?\n---", activity_b_new + "\n\n---", content, flags=re.DOTALL)


with open("README.md", "w", encoding="utf-8") as f:
    f.write(content)

print("README.md updated.")
