"""Prompt templates for Complaint Desk classification and reply chains.

Matches FWC Module 8 §18.1 Activity A reference code exactly — bare, minimal
prompts with no guardrails, no few-shot examples, no disambiguation rules.
"""

from langchain_core.prompts import ChatPromptTemplate

CLASSIFICATION_PROMPT = ChatPromptTemplate.from_template(
    "Classify into billing/loan/fraud/app_issue. One word only.\n{text}"
)

REPLY_PROMPT = ChatPromptTemplate.from_template(
    "Polite 60-word acknowledgement for a {cat} complaint. Sign as XYZ Finance.\n{text}"
)
