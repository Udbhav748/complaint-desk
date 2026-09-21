"""HTML safety tests for Complaint Desk rendering.

Verifies that escape_html() — applied in render_conversation() before
interpolating user-controlled content into unsafe_allow_html=True blocks —
correctly neutralises known XSS payloads while preserving normal text.

These are deterministic stdlib tests requiring no browser, no Streamlit
instance, and no external API calls.

FWC AI/ML Training Module 8 Activity A.
"""

import pytest
from app import escape_html


# ---------------------------------------------------------------------------
# XSS payload tests (the exact payloads specified by the audit directive)
# ---------------------------------------------------------------------------

def test_01_script_tag_escaped():
    """1. <script> tag is converted to safe character entities."""
    raw = "<script>alert(1)</script>"
    escaped = escape_html(raw)
    assert escaped == "&lt;script&gt;alert(1)&lt;/script&gt;"


def test_02_img_onerror_escaped():
    """2. <img src=x onerror=...> injection is fully escaped."""
    raw = "<img src=x onerror=alert(1)>"
    escaped = escape_html(raw)
    assert "onerror" in escaped          # text content preserved
    assert "&lt;img" in escaped


def test_03_angle_brackets_escaped():
    """3. Bare < and > are escaped to &lt; and &gt;."""
    raw = "Amount > $500 and < $1000"
    escaped = escape_html(raw)
    assert ">" not in escaped
    assert "<" not in escaped
    assert "&gt;" in escaped
    assert "&lt;" in escaped


def test_04_double_quotes_escaped_by_default():
    """4. Double quotes are escaped by default (quote=True is html.escape's default)."""
    raw = 'Say "hello" please'
    escaped = escape_html(raw)
    assert '"' not in escaped
    assert "&quot;" in escaped


def test_05_single_quotes_escaped():
    """5. Single quotes are escaped when quote=True (default)."""
    raw = "it's a problem"
    escaped = escape_html(raw)
    assert "&#x27;" in escaped or "'" not in escaped


def test_06_ampersands_escaped():
    """6. Ampersands are escaped to &amp;."""
    raw = "Fees & charges for Q3 & Q4"
    escaped = escape_html(raw)
    assert " & " not in escaped
    assert "&amp;" in escaped


def test_07_combined_xss_payload_escaped():
    """7. A combined HTML injection payload is fully neutralised."""
    raw = '<a href="javascript:alert(1)">click</a>'
    escaped = escape_html(raw)
    assert "<a" not in escaped
    assert "javascript" in escaped       # text survives
    assert "&lt;a" in escaped


# ---------------------------------------------------------------------------
# Safe content preservation tests (normal complaint and reply text)
# ---------------------------------------------------------------------------

def test_08_normal_complaint_text_preserved():
    """8. Standard complaint text passes through escape_html() readable."""
    raw = "I was charged twice for my monthly subscription of $29.99."
    escaped = escape_html(raw)
    assert "I was charged twice" in escaped
    assert "$29.99" in escaped


def test_09_currency_symbols_preserved():
    """9. Currency symbols (₹, $, €, £) survive escape_html() unchanged."""
    raw = "Discrepancy: ₹5,000 / $100 / €85 / £70"
    escaped = escape_html(raw)
    assert "₹5,000" in escaped
    assert "$100" in escaped
    assert "€85" in escaped
    assert "£70" in escaped


def test_10_multilingual_text_preserved():
    """10. Multilingual UTF-8 text survives escape_html() intact."""
    raw = "मेरे खाते से पैसे कट गए pero el servicio no funciona."
    escaped = escape_html(raw)
    assert "मेरे खाते से पैसे कट गए" in escaped
    assert "pero el servicio" in escaped


def test_11_normal_support_reply_preserved():
    """11. Typical LLM acknowledgement reply renders correctly after escaping."""
    raw = (
        "We acknowledge receipt of your billing concern regarding the duplicate charge. "
        "Your complaint details have been recorded under the billing category. "
        "We appreciate you bringing this to our attention."
    )
    escaped = escape_html(raw)
    assert "We acknowledge receipt" in escaped
    assert "billing" in escaped
    assert "We appreciate" in escaped


def test_12_newlines_not_escaped():
    """12. Newlines pass through escape_html() unchanged (collapsed by HTML renderer as before)."""
    raw = "First sentence.\nSecond sentence."
    escaped = escape_html(raw)
    assert "\n" in escaped


def test_13_safe_content_unchanged():
    """13. Text with no HTML-special characters is returned unchanged by escape_html()."""
    raw = "Your complaint regarding billing has been received."
    escaped = escape_html(raw)
    assert escaped == raw


def test_14_category_tokens_unchanged():
    """14. The four whitelisted category tokens are unchanged by escape_html()."""
    for token in ("billing", "loan", "fraud", "app_issue"):
        assert escape_html(token) == token
