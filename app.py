"""Complaint Desk — Streamlit User Interface.

Connects the two-chain LangChain workflow with defensive input/output validation,
session state conversation persistence, and clean error handling.
FWC AI/ML Training Module 8 Activity A.
"""

import logging
from datetime import datetime
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

# Unified SVG icon dictionary (simple geometric line icons, zero external dependencies)
ICONS = {
    "billing": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect><line x1="1" y1="10" x2="23" y2="10"></line></svg>',
    "loan": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>',
    "fraud": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>',
    "app_issue": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"></rect><line x1="12" y1="18" x2="12.01" y2="18"></line></svg>',
    "user": '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>',
    "support": '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>',
    "alert": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>',
    "spark": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>',
}


def init_session_state() -> None:
    """Initialize persistent conversation state in Streamlit."""
    if "messages" not in st.session_state:
        st.session_state.messages: List[Dict[str, Any]] = []
        # Support demo query parameter for visual QA and verification
        demo_mode = st.query_params.get("demo", "")
        if demo_mode == "single":
            st.session_state.messages = [
                {
                    "complaint": "I was charged twice for my subscription fee this month. Transaction ID #98234 shows two deductions of $29.99 on September 15th.",
                    "category": "billing",
                    "reply": "Thank you for contacting us regarding the duplicate charge on your account. We have logged this under our billing review team and are verifying transaction #98234. Any erroneous charges will be reversed to your original payment method within 3-5 business days.",
                    "timestamp": "10:15 AM",
                    "model": "gpt-4o-mini",
                }
            ]
        elif demo_mode == "multi":
            st.session_state.messages = [
                {
                    "complaint": "I was charged twice for my subscription fee this month. Transaction ID #98234 shows two deductions of $29.99 on September 15th.",
                    "category": "billing",
                    "reply": "Thank you for contacting us regarding the duplicate charge on your account. We have logged this under our billing review team and are verifying transaction #98234. Any erroneous charges will be reversed to your original payment method within 3-5 business days.",
                    "timestamp": "10:15 AM",
                    "model": "gpt-4o-mini",
                },
                {
                    "complaint": "The mobile application keeps crashing unexpectedly whenever I attempt to transfer funds on iOS 18.",
                    "category": "app_issue",
                    "reply": "Thank you for reporting this issue with the mobile application crashing during fund transfers on iOS 18. Our engineering team has been notified and is preparing an update to address device compatibility.",
                    "timestamp": "10:22 AM",
                    "model": "gpt-4o-mini",
                },
            ]


def inject_custom_styles() -> None:
    """Inject subtle, premium SaaS styling for typography, composer, cards, and states."""
    st.markdown(
        """
        <style>
        /* System UI Typography */
        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }

        /* Composer refinements */
        .stChatInput {
            padding-bottom: 0.25rem !important;
        }

        [data-testid="stChatInput"] {
            border-radius: 14px !important;
            border: 1.5px solid rgba(128, 128, 128, 0.22) !important;
            background-color: var(--background-color, #FFFFFF) !important;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04) !important;
            transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
        }

        [data-testid="stChatInput"]:focus-within {
            border-color: #2563EB !important;
            box-shadow: 0 4px 18px rgba(37, 99, 235, 0.15) !important;
        }

        [data-testid="stChatInput"] textarea {
            font-size: 0.94rem !important;
            line-height: 1.55 !important;
        }

        /* Category card microinteractions */
        .category-card {
            transition: transform 0.15s ease, border-color 0.15s ease;
        }
        .category-card:hover {
            transform: translateY(-2px);
            border-color: rgba(37, 99, 235, 0.35) !important;
        }

        /* Animated loading spinner */
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .loading-spinner {
            width: 14px;
            height: 14px;
            border: 2px solid rgba(37, 99, 235, 0.25);
            border-top: 2px solid #2563EB;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            flex-shrink: 0;
        }

        /* Streamlit UI polish: hide default deploy button and toolbar chrome */
        .stDeployButton, [data-testid="stToolbarActions"], [data-testid="stDecoration"] {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(config: AppConfig) -> None:
    """Render the premium SaaS product header with API configuration status indicator."""
    if config.has_valid_api_key:
        status_pill = (
            "<div style='display: inline-flex; align-items: center; gap: 6px; "
            "padding: 4px 12px; border-radius: 9999px; font-size: 0.78rem; font-weight: 600; "
            "background-color: rgba(16, 185, 129, 0.1); color: #059669; "
            "border: 1px solid rgba(16, 185, 129, 0.28); white-space: nowrap;'>"
            "<span style='width: 6px; height: 6px; border-radius: 50%; "
            "background-color: #10B981; display: inline-block;'></span>"
            "<span>API Configured</span></div>"
        )
    else:
        status_pill = (
            "<div style='display: inline-flex; align-items: center; gap: 6px; "
            "padding: 4px 12px; border-radius: 9999px; font-size: 0.78rem; font-weight: 600; "
            "background-color: rgba(239, 68, 68, 0.1); color: #DC2626; "
            "border: 1px solid rgba(239, 68, 68, 0.28); white-space: nowrap;'>"
            "<span style='width: 6px; height: 6px; border-radius: 50%; "
            "background-color: #EF4444; display: inline-block;'></span>"
            "<span>Configuration Required</span></div>"
        )

    logo_svg = (
        "<svg width='20' height='20' viewBox='0 0 24 24' fill='none' "
        "stroke='white' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'>"
        "<path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'></path>"
        "<polyline points='14 2 14 8 20 8'></polyline>"
        "<line x1='16' y1='13' x2='8' y2='13'></line>"
        "<line x1='16' y1='17' x2='8' y2='17'></line>"
        "</svg>"
    )

    header_html = f"""
    <div style="display: flex; align-items: center; justify-content: space-between; 
                flex-wrap: wrap; gap: 12px; padding: 0.2rem 0 0.85rem 0; 
                border-bottom: 1px solid rgba(128, 128, 128, 0.18); margin-bottom: 1.15rem;">
      <div style="display: flex; align-items: center; gap: 11px;">
        <div style="background: linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%); 
                    width: 38px; height: 38px; border-radius: 9px; 
                    display: flex; align-items: center; justify-content: center; 
                    box-shadow: 0 2px 5px rgba(0,0,0,0.12); flex-shrink: 0;">
          {logo_svg}
        </div>
        <div>
          <div style="font-size: 1.45rem; font-weight: 700; line-height: 1.2; letter-spacing: -0.01em;">
            Complaint Desk
          </div>
          <div style="font-size: 0.84rem; color: #6B7280; font-weight: 500;">
            AI-assisted complaint intake & response
          </div>
        </div>
      </div>
      <div>
        {status_pill}
      </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)


def render_sidebar(config: AppConfig) -> None:
    """Render the sidebar workspace and configuration panel."""
    with st.sidebar:
        # Phase 16: Workspace action
        st.subheader("Workspace")
        if st.button("Clear session", use_container_width=True, help="Reset conversation history and start a clean session"):
            st.session_state.messages = []
            st.rerun()

        st.divider()

        # Supported Categories with simple SVG icons
        st.subheader("Supported Categories")

        categories_data = [
            ("billing", "Billing", "Charges, fees & payment disputes"),
            ("loan", "Loan", "EMIs, repayments & loan accounts"),
            ("fraud", "Fraud", "Unauthorized activity & security"),
            ("app_issue", "App Issue", "Crashes, errors & technical problems"),
        ]

        cards_html = "<div style='display: flex; flex-direction: column; gap: 7px; margin-bottom: 0.5rem;'>"
        for key, name, desc in categories_data:
            cards_html += (
                f"<div style='padding: 8px 10px; border-radius: 8px; "
                f"border: 1px solid rgba(128, 128, 128, 0.16); "
                f"background: rgba(128, 128, 128, 0.03);'>"
                f"<div style='font-weight: 600; font-size: 0.84rem; display: flex; align-items: center; gap: 7px; color: var(--text-color, #1F2937);'>"
                f"<span style='display: flex; align-items: center; color: #2563EB;'>{ICONS[key]}</span>"
                f"<span>{name}</span></div>"
                f"<div style='font-size: 0.74rem; color: #6B7280; margin-top: 2px; line-height: 1.3;'>"
                f"{desc}</div></div>"
            )
        cards_html += "</div>"
        st.markdown(cards_html, unsafe_allow_html=True)

        st.divider()

        # Phase 7: Configuration section
        st.subheader("Configuration")

        api_badge_color = "#059669" if config.has_valid_api_key else "#DC2626"
        api_badge_label = "Configured" if config.has_valid_api_key else "Missing"

        config_html = (
            f"<div style='padding: 9px 11px; border-radius: 8px; "
            f"border: 1px solid rgba(128, 128, 128, 0.16); "
            f"background: rgba(128, 128, 128, 0.03); font-size: 0.81rem; "
            f"display: flex; flex-direction: column; gap: 7px;'>"
            f"<div style='display: flex; justify-content: space-between; align-items: center;'>"
            f"<span style='color: #6B7280; font-weight: 500;'>Model</span>"
            f"<code style='font-size: 0.76rem;'>{config.model_name}</code></div>"
            f"<div style='display: flex; justify-content: space-between; align-items: center;'>"
            f"<span style='color: #6B7280; font-weight: 500;'>Classification temperature</span>"
            f"<code style='font-size: 0.76rem;'>{config.temperature_classification}</code></div>"
            f"<div style='display: flex; justify-content: space-between; align-items: center;'>"
            f"<span style='color: #6B7280; font-weight: 500;'>Reply temperature</span>"
            f"<code style='font-size: 0.76rem;'>{config.temperature_reply}</code></div>"
            f"<div style='display: flex; justify-content: space-between; align-items: center;'>"
            f"<span style='color: #6B7280; font-weight: 500;'>API status</span>"
            f"<span style='font-weight: 600; font-size: 0.78rem; color: {api_badge_color};'>● {api_badge_label}</span></div>"
            f"</div>"
        )
        st.markdown(config_html, unsafe_allow_html=True)

        with st.expander("ℹ️ Hyperparameter Rationale", expanded=False):
            st.caption(
                "• **T = 0.0 (Classification):** Minimizes sampling entropy to enforce strict, deterministic argmax category assignment.\n\n"
                "• **T = 0.2 (Reply Generation):** Low-temperature sampling provides natural acknowledgment phrasing while preventing hallucinated promises or routing claims."
            )


CATEGORY_STYLES = {
    "billing": {
        "label": "Billing",
        "bg": "rgba(37, 99, 235, 0.08)",
        "text": "#1D4ED8",
        "border": "rgba(37, 99, 235, 0.3)",
    },
    "loan": {
        "label": "Loan",
        "bg": "rgba(217, 119, 6, 0.08)",
        "text": "#B45309",
        "border": "rgba(217, 119, 6, 0.3)",
    },
    "fraud": {
        "label": "Fraud",
        "bg": "rgba(220, 38, 38, 0.08)",
        "text": "#B91C1C",
        "border": "rgba(220, 38, 38, 0.3)",
    },
    "app_issue": {
        "label": "App Issue",
        "bg": "rgba(109, 40, 217, 0.08)",
        "text": "#6D28D9",
        "border": "rgba(109, 40, 217, 0.3)",
    },
}


def render_error_banner(heading: str, explanation: str) -> None:
    """Render a subtle, polished error card with SVG icon and clean typography."""
    html = f"""
    <div style="display: flex; align-items: flex-start; gap: 11px; padding: 12px 15px; 
                border-radius: 10px; border: 1px solid rgba(220, 38, 38, 0.25); 
                background: rgba(220, 38, 38, 0.05); margin-bottom: 1rem;">
      <div style="color: #DC2626; margin-top: 1px; flex-shrink: 0; display: flex;">
        {ICONS['alert']}
      </div>
      <div>
        <div style="font-weight: 700; font-size: 0.86rem; color: #991B1B; margin-bottom: 2px;">
          {heading}
        </div>
        <div style="font-size: 0.82rem; color: #B91C1C; line-height: 1.45;">
          {explanation}
        </div>
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_empty_state() -> None:
    """Render the premium empty state hero section when no complaints have been submitted."""
    empty_html = f"""
    <div style="text-align: center; padding: 2.25rem 1.5rem 1.75rem 1.5rem; margin: 0.4rem 0 1.5rem 0; 
                border-radius: 14px; border: 1px solid rgba(128, 128, 128, 0.16); 
                background: linear-gradient(180deg, rgba(37, 99, 235, 0.03) 0%, rgba(128, 128, 128, 0.01) 100%);">
      <div style="color: #2563EB; display: flex; justify-content: center; margin-bottom: 0.45rem;">
        {ICONS['spark']}
      </div>
      <h2 style="font-size: 1.48rem; font-weight: 700; margin: 0 0 0.35rem 0; letter-spacing: -0.01em;">
        Complaint Desk
      </h2>
      <p style="font-size: 0.98rem; color: var(--secondary-text-color, #4B5563); max-width: 480px; margin: 0 auto 1.25rem auto; line-height: 1.45;">
        Turn customer complaints into structured, professional intake acknowledgements.
      </p>
      <div style="display: inline-flex; align-items: center; gap: 6px; padding: 5px 13px; 
                  border-radius: 20px; font-size: 0.8rem; font-weight: 600; 
                  background: rgba(37, 99, 235, 0.08); color: #2563EB; border: 1px solid rgba(37, 99, 235, 0.22); margin-bottom: 1.45rem;">
        Start a complaint below
      </div>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 9px; max-width: 620px; margin: 0 auto 1.25rem auto; text-align: left;">
        <div class="category-card" style="padding: 9px 11px; border-radius: 9px; border: 1px solid rgba(128, 128, 128, 0.14); background: rgba(128, 128, 128, 0.03);">
          <div style="font-weight: 600; font-size: 0.83rem; display: flex; align-items: center; gap: 6px; color: #1D4ED8;">
            <span style="display: flex;">{ICONS['billing']}</span><span>Billing</span>
          </div>
          <div style="font-size: 0.73rem; color: #6B7280; margin-top: 2px;">Fees & disputes</div>
        </div>
        <div class="category-card" style="padding: 9px 11px; border-radius: 9px; border: 1px solid rgba(128, 128, 128, 0.14); background: rgba(128, 128, 128, 0.03);">
          <div style="font-weight: 600; font-size: 0.83rem; display: flex; align-items: center; gap: 6px; color: #B45309;">
            <span style="display: flex;">{ICONS['loan']}</span><span>Loan</span>
          </div>
          <div style="font-size: 0.73rem; color: #6B7280; margin-top: 2px;">EMIs & accounts</div>
        </div>
        <div class="category-card" style="padding: 9px 11px; border-radius: 9px; border: 1px solid rgba(128, 128, 128, 0.14); background: rgba(128, 128, 128, 0.03);">
          <div style="font-weight: 600; font-size: 0.83rem; display: flex; align-items: center; gap: 6px; color: #B91C1C;">
            <span style="display: flex;">{ICONS['fraud']}</span><span>Fraud</span>
          </div>
          <div style="font-size: 0.73rem; color: #6B7280; margin-top: 2px;">Security & alerts</div>
        </div>
        <div class="category-card" style="padding: 9px 11px; border-radius: 9px; border: 1px solid rgba(128, 128, 128, 0.14); background: rgba(128, 128, 128, 0.03);">
          <div style="font-weight: 600; font-size: 0.83rem; display: flex; align-items: center; gap: 6px; color: #6D28D9;">
            <span style="display: flex;">{ICONS['app_issue']}</span><span>App Issue</span>
          </div>
          <div style="font-size: 0.73rem; color: #6B7280; margin-top: 2px;">Bugs & crashes</div>
        </div>
      </div>

      <p style="font-size: 0.81rem; color: #9CA3AF; margin: 0; line-height: 1.45;">
        Describe the customer's issue in natural language.<br/>
        The system will classify it and generate a concise acknowledgement.
      </p>
    </div>
    """
    st.markdown(empty_html, unsafe_allow_html=True)


def render_conversation(messages: List[Dict[str, Any]], config: AppConfig) -> None:
    """Display the conversation history using polished, distinct message cards."""
    if not messages:
        render_empty_state()
        return

    for item in messages:
        # Phase 10: Customer message card
        timestamp = item.get("timestamp", "")
        time_badge = (
            f"<span style='font-size: 0.74rem; color: #9CA3AF; font-weight: 400;'>• {timestamp}</span>"
            if timestamp
            else ""
        )

        user_card_html = f"""
        <div style="margin-bottom: 1.15rem; padding: 0.95rem 1.15rem; border-radius: 11px; 
                    border: 1px solid rgba(128, 128, 128, 0.16); 
                    background-color: rgba(128, 128, 128, 0.035); max-width: 92%;">
          <div style="display: flex; align-items: center; gap: 7px; margin-bottom: 0.45rem;">
            <span style="display: flex; align-items: center; color: #6B7280;">{ICONS['user']}</span>
            <span style="font-weight: 700; font-size: 0.84rem; letter-spacing: 0.01em; color: var(--text-color, #1F2937);">
              Customer
            </span>
            {time_badge}
          </div>
          <div style="font-size: 0.93rem; line-height: 1.55; color: var(--text-color, #374151); word-wrap: break-word;">
            {item["complaint"]}
          </div>
        </div>
        """
        st.markdown(user_card_html, unsafe_allow_html=True)

        # Phase 12 & 13: Support acknowledgement card with visible category badge and compact metadata
        cat = item.get("category", "")
        style = CATEGORY_STYLES.get(
            cat,
            {
                "label": cat.capitalize(),
                "bg": "rgba(128, 128, 128, 0.08)",
                "text": "#374151",
                "border": "rgba(128, 128, 128, 0.2)",
            },
        )
        cat_icon = ICONS.get(cat, ICONS["billing"])

        ack_card_html = f"""
        <div style="margin-bottom: 1.75rem; padding: 1.15rem 1.25rem; border-radius: 12px; 
                    border: 1px solid rgba(128, 128, 128, 0.18); 
                    border-left: 3.5px solid #2563EB;
                    background-color: var(--background-color, #FFFFFF); 
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03); max-width: 95%;">
          
          <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 0.85rem; padding-bottom: 0.65rem; border-bottom: 1px solid rgba(128, 128, 128, 0.1);">
            <div style="display: flex; align-items: center; gap: 7px; font-weight: 700; font-size: 0.84rem; color: var(--text-color, #1F2937);">
              <span style="color: #2563EB; display: flex; align-items: center;">{ICONS['support']}</span>
              <span>Support acknowledgement</span>
            </div>
            <div style="display: inline-flex; align-items: center; gap: 6px; padding: 3px 9px; border-radius: 6px; border: 1px solid {style['border']}; background-color: {style['bg']}; color: {style['text']}; font-size: 0.74rem; font-weight: 600;">
              <span style="display: flex; align-items: center;">{cat_icon}</span>
              <span>Category: {style['label']}</span>
            </div>
          </div>

          <div style="font-size: 0.93rem; line-height: 1.6; color: var(--text-color, #374151); word-wrap: break-word; margin-bottom: 0.85rem;">
            {item["reply"]}
          </div>

          <div style="display: flex; align-items: center; gap: 16px; font-size: 0.73rem; color: #6B7280; border-top: 1px solid rgba(128, 128, 128, 0.08); padding-top: 0.55rem;">
            <div><span style="color: #9CA3AF; font-weight: 500;">Category:</span> <span style="font-weight: 600; color: var(--text-color, #4B5563);">{cat}</span></div>
            <div><span style="color: #9CA3AF; font-weight: 500;">Model:</span> <code style="font-size: 0.72rem;">{item.get('model', config.model_name)}</code></div>
          </div>
        </div>
        """
        st.markdown(ack_card_html, unsafe_allow_html=True)


def process_submission(user_input: str, config: AppConfig) -> None:
    """Orchestrate the validation, classification, and reply-generation pipeline with polished loading & error states."""
    # Step 1: Input Validation
    input_result = validate_complaint(user_input)
    if not input_result.success:
        render_error_banner(
            heading="Invalid complaint",
            explanation="Please enter a complaint between 5 and 4,000 characters.",
        )
        logger.info("Complaint validation rejected: %s", input_result.diagnostic_info)
        return

    sanitized_complaint = input_result.value

    # Verify API configuration before calling LLM
    if not config.has_valid_api_key:
        render_error_banner(
            heading="Configuration incomplete",
            explanation="Model configuration is incomplete. Add the required API key to continue.",
        )
        logger.error("Attempted pipeline execution without valid OPENAI_API_KEY.")
        return

    # Multi-stage loading state (Phase 14)
    status_placeholder = st.empty()
    status_placeholder.markdown(
        """
        <div style="display: flex; align-items: center; gap: 10px; padding: 11px 15px; 
                    border-radius: 9px; border: 1px solid rgba(37, 99, 235, 0.22); 
                    background: rgba(37, 99, 235, 0.04); color: #1E40AF; 
                    font-size: 0.86rem; font-weight: 600; margin-bottom: 1rem;">
          <div class="loading-spinner"></div>
          <span>Analyzing complaint...</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Step 2: Invoke Chain 1 (Classification)
    try:
        classification_chain, reply_chain = create_chains(config)
        raw_category = classification_chain.invoke(
            {"complaint": sanitized_complaint}
        )
    except Exception as exc:
        status_placeholder.empty()
        logger.error("Classification chain error: %s", type(exc).__name__, exc_info=False)
        render_error_banner(
            heading="Service unavailable",
            explanation="An error occurred while connecting to the classification service. Please check your API key, network connection, or quota.",
        )
        return

    # Step 3: Validate Category Whitelist
    cat_result = validate_category(raw_category)
    if not cat_result.success:
        status_placeholder.empty()
        logger.warning(
            "Category validation rejected raw output: %s", cat_result.diagnostic_info
        )
        render_error_banner(
            heading="Category verification failed",
            explanation="Unable to verify the complaint category. The response was not generated.",
        )
        return

    verified_category = cat_result.value

    # Phase 14: Transition loading state to stage 2
    status_placeholder.markdown(
        """
        <div style="display: flex; align-items: center; gap: 10px; padding: 11px 15px; 
                    border-radius: 9px; border: 1px solid rgba(37, 99, 235, 0.22); 
                    background: rgba(37, 99, 235, 0.04); color: #1E40AF; 
                    font-size: 0.86rem; font-weight: 600; margin-bottom: 1rem;">
          <div class="loading-spinner"></div>
          <span>Preparing acknowledgement...</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Step 4: Invoke Chain 2 (Reply Generation)
    try:
        reply = reply_chain.invoke(
            {
                "complaint": sanitized_complaint,
                "category": verified_category,
            }
        )
    except Exception as exc:
        status_placeholder.empty()
        logger.error("Reply chain error: %s", type(exc).__name__, exc_info=False)
        render_error_banner(
            heading="Generation unavailable",
            explanation="An error occurred while generating the customer acknowledgement. Please try submitting again.",
        )
        return

    # Clear loading state
    status_placeholder.empty()

    # Step 5: Persist interaction in session state
    now_str = datetime.now().strftime("%I:%M %p")
    st.session_state.messages.append(
        {
            "complaint": sanitized_complaint,
            "category": verified_category,
            "reply": reply.strip(),
            "timestamp": now_str,
            "model": config.model_name,
        }
    )
    st.rerun()


def main() -> None:
    """Main application entrypoint."""
    st.set_page_config(
        page_title="Complaint Desk — AI-assisted complaint intake & response",
        page_icon="📋",
        layout="centered",
    )

    # Inject modern SaaS styling
    inject_custom_styles()

    # Load configuration
    config = AppConfig.from_env()

    # Initialize session state
    init_session_state()

    # Render top SaaS header
    render_header(config)

    # Render sidebar workspace and configuration panel
    render_sidebar(config)

    # Render conversation history or empty state
    render_conversation(st.session_state.messages, config)

    # Phase 9: Complaint Composer
    user_input = st.chat_input("Describe the customer's complaint...")
    st.markdown(
        "<div style='text-align: right; font-size: 0.74rem; color: #9CA3AF; "
        "margin-top: -6px; margin-bottom: 6px; padding-right: 8px;'>"
        "5–4,000 characters</div>",
        unsafe_allow_html=True,
    )
    if user_input:
        process_submission(user_input, config)


if __name__ == "__main__":
    main()
