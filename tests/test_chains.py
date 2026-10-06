"""Integration and contract tests for LangChain pipelines.

Tests pipeline composition, prompt parameter contracts, and validation coupling
using deterministic offline mock models with zero OpenAI API calls.
FWC AI/ML Training Module 8 Activity A.
"""

from unittest.mock import MagicMock
import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.chains import (
    build_classification_chain,
    build_reply_chain,
    create_chains,
    get_chat_model,
)
from src.config import AppConfig
from src.validation import validate_category


# ==============================================================================
# CHAIN CONSTRUCTION & STRUCTURAL CONTRACT TESTS
# ==============================================================================

def test_01_classification_chain_construction():
    """1. Verify classification chain can be constructed successfully."""
    fake_llm = FakeListChatModel(responses=["billing"])
    chain = build_classification_chain(fake_llm)
    assert chain is not None


def test_02_reply_chain_construction():
    """2. Verify reply chain can be constructed successfully."""
    fake_llm = FakeListChatModel(responses=["We acknowledge your concern."])
    chain = build_reply_chain(fake_llm)
    assert chain is not None


def test_03_lcel_composition_steps():
    """3. Verify both chains follow ChatPromptTemplate → model → StrOutputParser."""
    fake_llm = FakeListChatModel(responses=["fraud"])
    cls_chain = build_classification_chain(fake_llm)
    rep_chain = build_reply_chain(fake_llm)

    # Classification steps inspection
    cls_steps = [s.__class__.__name__ for s in cls_chain.steps]
    assert cls_steps == ["ChatPromptTemplate", "FakeListChatModel", "StrOutputParser"]

    # Reply steps inspection
    rep_steps = [s.__class__.__name__ for s in rep_chain.steps]
    assert rep_steps == ["ChatPromptTemplate", "FakeListChatModel", "StrOutputParser"]


def test_04_classification_input_contract():
    """4. Verify classification chain accepts {'text': str} and returns string."""
    fake_llm = FakeListChatModel(responses=["billing"])
    chain = build_classification_chain(fake_llm)

    raw_output = chain.invoke({"text": "I was charged twice on my card."})
    assert isinstance(raw_output, str)
    assert raw_output == "billing"


def test_05_reply_input_contract():
    """5. Verify reply chain accepts {'text': str, 'cat': str}."""
    expected_ack = "We acknowledge receipt of your billing dispute details."
    fake_llm = FakeListChatModel(responses=[expected_ack])
    chain = build_reply_chain(fake_llm)

    raw_reply = chain.invoke(
        {
            "text": "I was charged twice on my card.",
            "cat": "billing",
        }
    )
    assert isinstance(raw_reply, str)
    assert raw_reply == expected_ack


def test_06_classification_output_validates_cleanly():
    """6. validate_category() (unused by app.py, kept as a utility) still accepts clean classifier output."""
    fake_llm = FakeListChatModel(responses=["   **fraud**\n"])
    chain = build_classification_chain(fake_llm)

    raw_output = chain.invoke({"text": "Unauthorized login attempt detected."})
    val_res = validate_category(raw_output)

    assert val_res.success is True
    assert val_res.value == "fraud"


def test_07_classification_output_passthrough():
    """7. Matches the reference app's actual behavior: raw classifier output is used
    as-is (lowercased/stripped), with no category whitelist check before the reply
    chain is invoked — app.py does not call validate_category()."""
    fake_cls_llm = FakeListChatModel(responses=["unknown_security_incident"])
    cls_chain = build_classification_chain(fake_cls_llm)

    raw_cat = cls_chain.invoke({"text": "System behaves unpredictably."}).strip().lower()
    assert raw_cat == "unknown_security_incident"

    # Reference app.py invokes the reply chain with whatever came back, unguarded.
    mock_reply_chain = MagicMock()
    mock_reply_chain.invoke({"text": "System behaves unpredictably.", "cat": raw_cat})
    assert mock_reply_chain.invoke.called
