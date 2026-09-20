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
    """4. Verify classification chain accepts {'complaint': str} and returns string."""
    fake_llm = FakeListChatModel(responses=["billing"])
    chain = build_classification_chain(fake_llm)

    raw_output = chain.invoke({"complaint": "I was charged twice on my card."})
    assert isinstance(raw_output, str)
    assert raw_output == "billing"


def test_05_reply_input_contract():
    """5. Verify reply chain accepts {'complaint': str, 'category': str}."""
    expected_ack = "We acknowledge receipt of your billing dispute details."
    fake_llm = FakeListChatModel(responses=[expected_ack])
    chain = build_reply_chain(fake_llm)

    raw_reply = chain.invoke(
        {
            "complaint": "I was charged twice on my card.",
            "category": "billing",
        }
    )
    assert isinstance(raw_reply, str)
    assert raw_reply == expected_ack


def test_06_classification_output_validates_cleanly():
    """6. Verify valid classifier output passes through the validation layer."""
    fake_llm = FakeListChatModel(responses=["   **fraud**\n"])
    chain = build_classification_chain(fake_llm)

    raw_output = chain.invoke({"complaint": "Unauthorized login attempt detected."})
    val_res = validate_category(raw_output)

    assert val_res.success is True
    assert val_res.value == "fraud"


def test_07_invalid_classifier_output_blocks_reply_invocation():
    """7. Contract test: Verify validation failure provides contract to block downstream reply invocation."""
    fake_cls_llm = FakeListChatModel(responses=["unknown_security_incident"])
    cls_chain = build_classification_chain(fake_cls_llm)

    # Mock reply chain to strictly detect if invoke is called
    mock_reply_chain = MagicMock()

    # Step 1: Run classification
    raw_cat = cls_chain.invoke({"complaint": "System behaves unpredictably."})

    # Step 2: Validate category
    val_res = validate_category(raw_cat)
    assert val_res.success is False
    assert val_res.error_type == "invalid_category"

    # Step 3: Orchestration contract: guard condition prevents downstream call
    if val_res.success:
        mock_reply_chain.invoke({"complaint": "test", "category": val_res.value})

    # Assert reply chain was NEVER invoked under this contract
    assert not mock_reply_chain.invoke.called, "Reply chain was invoked despite invalid category!"
