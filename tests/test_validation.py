"""Deterministic unit tests for input and category validation.

Covers all 24 required validation boundaries without invoking external LLM APIs.
FWC AI/ML Training Module 8 Activity A.
"""

import pytest
from src.validation import (
    validate_complaint,
    validate_category,
    normalize_category,
    ERR_EMPTY_INPUT,
    ERR_INPUT_TOO_SHORT,
    ERR_INPUT_TOO_LONG,
    ERR_INVALID_INPUT,
    ERR_INVALID_CATEGORY,
)


# ==============================================================================
# INPUT VALIDATION TESTS (Tests 1 to 11)
# ==============================================================================

def test_01_valid_complaint():
    """1. Verify standard valid complaint string passes validation."""
    raw = "I noticed an unexpected fee on my monthly statement."
    res = validate_complaint(raw)
    assert res.success is True
    assert res.value == raw
    assert res.error_type is None


def test_02_surrounding_whitespace_trimmed():
    """2. Verify leading and trailing whitespace is stripped."""
    raw = "   \n\t  My loan EMI was debited twice today.  \t\n  "
    res = validate_complaint(raw)
    assert res.success is True
    assert res.value == "My loan EMI was debited twice today."


def test_03_empty_string_rejected():
    """3. Verify empty string is rejected with ERR_EMPTY_INPUT."""
    res = validate_complaint("")
    assert res.success is False
    assert res.error_type == ERR_EMPTY_INPUT
    assert "Please enter a customer complaint" in res.message


def test_04_whitespace_only_rejected():
    """4. Verify whitespace-only input is rejected with ERR_EMPTY_INPUT."""
    res = validate_complaint("   \n\t   \r  ")
    assert res.success is False
    assert res.error_type == ERR_EMPTY_INPUT


def test_05_non_string_input_rejected():
    """5. Verify non-string inputs (None, dict, int) are rejected safely."""
    for invalid_val in [None, 12345, ["complaint text"], {"text": "bad"}]:
        res = validate_complaint(invalid_val)
        assert res.success is False
        assert res.error_type == ERR_INVALID_INPUT
        assert "valid text string" in res.message


def test_06_input_too_short_rejected():
    """6. Verify input shorter than 5 characters is rejected with ERR_INPUT_TOO_SHORT."""
    for short_text in ["a", "Help", " EMI"]:
        res = validate_complaint(short_text)
        assert res.success is False
        assert res.error_type == ERR_INPUT_TOO_SHORT
        assert "too short" in res.message


def test_07_input_too_long_rejected():
    """7. Verify input longer than 4000 characters is rejected with ERR_INPUT_TOO_LONG."""
    long_text = "A" * 4001
    res = validate_complaint(long_text)
    assert res.success is False
    assert res.error_type == ERR_INPUT_TOO_LONG
    assert "exceeds the maximum allowed length" in res.message

    # Boundary check: exactly 4000 characters should pass
    exact_boundary_text = "B" * 4000
    res_boundary = validate_complaint(exact_boundary_text)
    assert res_boundary.success is True
    assert len(res_boundary.value) == 4000


def test_08_normal_punctuation_preserved():
    """8. Verify standard punctuation is preserved without destructive sanitization."""
    raw = "What happened?! My bill is $45.00 higher than expected; please check invoice #102-A."
    res = validate_complaint(raw)
    assert res.success is True
    assert res.value == raw


def test_09_currency_symbols_preserved():
    """9. Verify Indian Rupee, Dollar, Euro, and Pound symbols are preserved."""
    raw = "Discrepancy observed across charges: ₹5,000, $100, €85, and £70."
    res = validate_complaint(raw)
    assert res.success is True
    assert res.value == raw


def test_10_multilingual_text_preserved():
    """10. Verify multilingual UTF-8 text (Hindi, Spanish, French, Japanese) is preserved."""
    multilingual = "मेरे खाते से पैसे कट गए pero el servicio no funciona. C'est inacceptable. アプリがクラッシュしました。"
    res = validate_complaint(multilingual)
    assert res.success is True
    assert res.value == multilingual


def test_11_forbidden_control_characters_rejected():
    """11. Verify unprintable control characters (null bytes, bells) are rejected."""
    raw_with_null = "Payment failed\x00 due to server error."
    res = validate_complaint(raw_with_null)
    assert res.success is False
    assert res.error_type == ERR_INVALID_INPUT
    assert "non-printable control characters" in res.message


# ==============================================================================
# CATEGORY VALIDATION TESTS (Tests 12 to 24)
# ==============================================================================

def test_12_billing_accepted():
    """12. Verify 'billing' is accepted as a valid category."""
    res = validate_category("billing")
    assert res.success is True
    assert res.value == "billing"


def test_13_loan_accepted():
    """13. Verify 'loan' is accepted as a valid category."""
    res = validate_category("loan")
    assert res.success is True
    assert res.value == "loan"


def test_14_fraud_accepted():
    """14. Verify 'fraud' is accepted as a valid category."""
    res = validate_category("fraud")
    assert res.success is True
    assert res.value == "fraud"


def test_15_app_issue_accepted():
    """15. Verify 'app_issue' is accepted as a valid category."""
    res = validate_category("app_issue")
    assert res.success is True
    assert res.value == "app_issue"


def test_16_case_normalization():
    """16. Verify uppercase and mixed-case outputs normalize to lowercase."""
    for raw, expected in [("BILLING", "billing"), ("Loan", "loan"), ("FRAUD", "fraud"), ("APP_ISSUE", "app_issue")]:
        res = validate_category(raw)
        assert res.success is True
        assert res.value == expected


def test_17_surrounding_whitespace():
    """17. Verify surrounding whitespace is stripped during category validation."""
    res = validate_category("   fraud   \n\t")
    assert res.success is True
    assert res.value == "fraud"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Category: billing", "billing"),
        ("Classification: loan", "loan"),
        ("Output: fraud", "fraud"),
        ("category: app_issue.", "app_issue"),
    ],
)
def test_18_category_prefix_parsing(raw, expected):
    """18. Verify 'Category:' / 'Classification:' prefix is removed and maps to exact expected category."""
    res = validate_category(raw)
    assert res.success is True
    assert res.value == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("**billing**", "billing"),
        ("`loan`", "loan"),
        ("*fraud*", "fraud"),
        ("***app_issue***", "app_issue"),
    ],
)
def test_19_markdown_formatting_removed(raw, expected):
    """19. Verify surrounding markdown formatting is removed and maps to exact expected category."""
    res = validate_category(raw)
    assert res.success is True
    assert res.value == expected


def test_20_app_issue_underscore_preserved():
    """20. Verify underscore in 'app_issue' is strictly preserved."""
    assert normalize_category("app_issue") == "app_issue"
    res = validate_category("app_issue")
    assert res.success is True
    assert res.value == "app_issue"


def test_21_appissue_rejected():
    """21. Verify missing underscore 'appissue' is strictly rejected."""
    res = validate_category("appissue")
    assert res.success is False
    assert res.error_type == ERR_INVALID_CATEGORY
    assert res.value is None


def test_22_billing_issue_rejected():
    """22. Verify out-of-spec variation 'billing_issue' is rejected."""
    res = validate_category("billing_issue")
    assert res.success is False
    assert res.error_type == ERR_INVALID_CATEGORY
    assert res.value is None


def test_23_unknown_category_rejected():
    """23. Verify arbitrary unknown categories do NOT map into fake categories."""
    for unknown in ["general_inquiry", "support", "refund", "uncategorized", "random_topic"]:
        res = validate_category(unknown)
        assert res.success is False
        assert res.error_type == ERR_INVALID_CATEGORY
        assert res.value is None


def test_24_non_string_classification_rejected():
    """24. Verify None or non-string classifier output is safely rejected."""
    for non_str in [None, 123, {"cat": "billing"}, []]:
        res = validate_category(non_str)
        assert res.success is False
        assert res.error_type == ERR_INVALID_CATEGORY
        assert res.value is None
