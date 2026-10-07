"""Complaint Desk — Streamlit app.

Matches FWC Module 8 §18.1 Activity A reference code exactly: paste a
complaint, classify it, draft a category-appropriate reply, persist the
conversation on screen. No input validation, no category whitelisting, no
custom styling — the literal two-chain demo from the handout, in one file.
"""

import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

classify = (
    ChatPromptTemplate.from_template(
        "Classify into billing/loan/fraud/app_issue. One word only.\n{text}"
    )
    | llm
    | StrOutputParser()
)

reply = (
    ChatPromptTemplate.from_template(
        "Polite 60-word acknowledgement for a {cat} complaint. Sign as XYZ Finance.\n{text}"
    )
    | llm
    | StrOutputParser()
)

st.title("Complaint Desk — LangChain demo")

if "log" not in st.session_state:
    st.session_state.log = []

txt = st.chat_input("Paste a customer complaint…")

if txt:
    cat = classify.invoke({"text": txt}).strip().lower()
    st.session_state.log.append(
        (txt, cat, reply.invoke({"cat": cat, "text": txt}))
    )

for t, c, a in st.session_state.log:
    st.chat_message("user").write(t)
    st.chat_message("assistant").write(f"**[{c}]** {a}")
