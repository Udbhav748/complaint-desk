"""Complaint Desk — Streamlit User Interface.

Connects the two-chain LangChain workflow with defensive input/output validation,
session state conversation persistence, and clean error handling.
FWC AI/ML Training Module 8 Activity A.
"""

import logging
from typing import List, Dict, Any
import streamlit as st

from src.config import AppConfig, ALLOWED_CATEGORIES
from src.chains import create_chains
from src.validation import validate_complaint, validate_category

# Configure application logging (logs diagnostics locally without exposing secrets)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("complaint_desk.app")


def init_session_state() -> None:
    """Initialize persistent conversation state in Streamlit."""
    if "messages" not in st.session_state:
        st.session_state.messages: List[Dict[str, Any]] = []


def render_sidebar(config: AppConfig) -> None:
    """Render the sidebar containing configuration details and session controls."""
    with st.sidebar:
        st.header("System Configuration")

        st.markdown(f"**Model:** `{config.model_name}`")
        st.markdown(f"**Classification Temp:** `{config.temperature_classification}`")
        st.markdown(f"**Reply Temp:** `{config.temperature_reply}`")

        api_status = (
            "🟢 Configured" if config.has_valid_api_key else "🔴 Missing / Incomplete"
        )
        st.markdown(f"**API Key Status:** {api_status}")

        st.divider()

        st.header("Supported Categories")
        st.markdown(
            "- **`billing`**: Charges, fees, subscriptions, invoices\n"
            "- **`loan`**: EMI schedules, interest rates, approvals\n"
            "- **`fraud`**: Unauthorized charges, security alerts, theft\n"
            "- **`app_issue`**: Technical bugs, login errors, app crashes"
        )

        st.divider()

        if st.button("Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()


def render_conversation(messages: List[Dict[str, Any]]) -> None:
    """Display the conversation history using standard chat message components."""
    if not messages:
        st.info("Describe your complaint below to classify it and generate an acknowledgement.")
        return

    for item in messages:
        # Display user complaint
        with st.chat_message("user"):
            st.write(item["complaint"])

        # Display assistant categorization and acknowledgement
        with st.chat_message("assistant"):
            st.markdown(f"**Category:** `{item['category']}`")
            st.write(item["reply"])


def process_submission(user_input: str, config: AppConfig) -> None:
    """Orchestrate the validation, classification, and reply-generation pipeline."""
    # Step 1: Input Validation
    input_result = validate_complaint(user_input)
    if not input_result.success:
        st.warning(input_result.message)
        logger.info("Complaint validation rejected: %s", input_result.diagnostic_info)
        return

    sanitized_complaint = input_result.value

    # Verify API configuration before calling LLM
    if not config.has_valid_api_key:
        st.error(
            "OpenAI API key is missing or invalid. Please configure OPENAI_API_KEY in your .env file."
        )
        logger.error("Attempted pipeline execution without valid OPENAI_API_KEY.")
        return

    # Step 2: Invoke Chain 1 (Classification)
    try:
        with st.spinner("Classifying complaint..."):
            classification_chain, reply_chain = create_chains(config)
            raw_category = classification_chain.invoke(
                {"complaint": sanitized_complaint}
            )
    except Exception as exc:
        logger.error("Classification chain error: %s", type(exc).__name__, exc_info=False)
        st.error(
            "An error occurred while connecting to the classification service. "
            "Please check your API key, network connection, or quota."
        )
        return

    # Step 3: Validate Category Whitelist
    cat_result = validate_category(raw_category)
    if not cat_result.success:
        logger.warning(
            "Category validation rejected raw output: %s", cat_result.diagnostic_info
        )
        st.error(cat_result.message)
        # CRITICAL: Do NOT invoke Chain 2 if category is invalid
        return

    verified_category = cat_result.value

    # Step 4: Invoke Chain 2 (Reply Generation)
    try:
        with st.spinner("Generating customer acknowledgement..."):
            reply = reply_chain.invoke(
                {
                    "complaint": sanitized_complaint,
                    "category": verified_category,
                }
            )
    except Exception as exc:
        logger.error("Reply chain error: %s", type(exc).__name__, exc_info=False)
        st.error(
            "An error occurred while generating the customer acknowledgement. "
            "Please try submitting again."
        )
        return

    # Step 5: Persist interaction in session state
    st.session_state.messages.append(
        {
            "complaint": sanitized_complaint,
            "category": verified_category,
            "reply": reply.strip(),
        }
    )
    st.rerun()


def main() -> None:
    """Main application entrypoint."""
    st.set_page_config(
        page_title="Complaint Desk — LangChain Demo",
        page_icon="📋",
        layout="centered",
    )

    # Load configuration
    config = AppConfig.from_env()

    # Initialize session state
    init_session_state()

    # Main header and description
    st.title("Complaint Desk — LangChain Demo")
    st.write(
        "A two-chain LangChain customer support intake assistant. "
        "Incoming customer complaints are first classified into one of four supported categories "
        "(`billing`, `loan`, `fraud`, or `app_issue`), and a second chain generates a "
        "controlled, category-appropriate intake acknowledgement."
    )

    # Render sidebar
    render_sidebar(config)

    # Render conversation history
    render_conversation(st.session_state.messages)

    # Render chat input
    user_input = st.chat_input("Paste a customer complaint...")
    if user_input:
        process_submission(user_input, config)


if __name__ == "__main__":
    main()
