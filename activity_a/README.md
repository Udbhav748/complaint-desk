# Activity A — Complaint Desk

FWC Module 8 §18.1. A single-file Streamlit app implementing the exact two-chain
reference architecture from the handout:

```text
Complaint → Classification Chain → Reply Chain → Conversation History
```

## Architecture

Two LangChain LCEL chains sharing one `llm` instance:

```python
llm = ChatOpenAI(model=..., temperature=0.3, base_url=...)

classify = ChatPromptTemplate.from_template(
    "Classify into billing/loan/fraud/app_issue. One word only.\n{text}"
) | llm | StrOutputParser()

reply = ChatPromptTemplate.from_template(
    "Polite 60-word acknowledgement for a {cat} complaint. Sign as XYZ Finance.\n{text}"
) | llm | StrOutputParser()
```

No input validation, no category whitelisting, no guardrails, no RAG/agents/LangGraph —
intentionally bare, matching the assignment reference. The entire implementation is
visible by opening [`app.py`](app.py).

## Provider note

> The teacher's reference uses `ChatOpenAI(model="gpt-4o-mini")`. This implementation
> uses Groq's OpenAI-compatible API (`openai/gpt-oss-20b`) because an OpenAI API key
> was not available. The application architecture, prompts, temperature, and two-chain
> workflow remain equivalent to the reference implementation — only the model/base_url
> differ.

## How to run

```bash
cd activity_a
pip install -r ../requirements.txt
streamlit run app.py
```

Requires `GROQ_API_KEY` set in a `.env` file at the repo root (see `.env.example`).

## Live demo

http://65.1.106.51:8501
