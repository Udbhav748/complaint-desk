"""Complaint Desk — Streamlit app.

Matches FWC Module 8 §18.1 Activity A reference code exactly: paste a
complaint, classify it, draft a category-appropriate reply, persist the
conversation on screen. No input validation, no category whitelisting, no
custom styling — the literal two-chain demo from the handout.
"""

import streamlit as st

from src.config import AppConfig
from src.chains import create_chains

config = AppConfig.from_env()
classify, reply = create_chains(config)

st.title("Complaint Desk")

if "log" not in st.session_state:
    st.session_state.log = []

txt = st.chat_input("Paste a customer complaint…")
if txt:
    cat = classify.invoke({"text": txt}).strip().lower()
    st.session_state.log.append((txt, cat, reply.invoke({"cat": cat, "text": txt})))

for t, c, a in st.session_state.log:
    st.chat_message("user").write(t)
    st.chat_message("assistant").write(f"**[{c}]** {a}")
