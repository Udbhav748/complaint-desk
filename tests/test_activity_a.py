"""Structural smoke test for Activity A's single-file app.

Verifies app.py builds the two LCEL chains with the exact handout prompts and
step order, without making any network calls.
FWC AI/ML Training Module 8 Activity A.
"""

import sys
from pathlib import Path

import pytest

ACTIVITY_A_DIR = Path(__file__).resolve().parent.parent / "activity_a"


@pytest.fixture(scope="module")
def app_module():
    sys.path.insert(0, str(ACTIVITY_A_DIR))
    import app  # noqa: PLC0415
    yield app
    sys.path.remove(str(ACTIVITY_A_DIR))
    sys.modules.pop("app", None)


def test_01_llm_uses_flat_temperature(app_module):
    """Verify the single shared llm uses temperature=0.3, matching the handout."""
    assert app_module.llm.temperature == 0.3


def test_02_classify_chain_step_order(app_module):
    """Verify Chain 1: ChatPromptTemplate -> llm -> StrOutputParser."""
    steps = [s.__class__.__name__ for s in app_module.classify.steps]
    assert steps == ["ChatPromptTemplate", "ChatOpenAI", "StrOutputParser"]


def test_03_reply_chain_step_order(app_module):
    """Verify Chain 2: ChatPromptTemplate -> llm -> StrOutputParser."""
    steps = [s.__class__.__name__ for s in app_module.reply.steps]
    assert steps == ["ChatPromptTemplate", "ChatOpenAI", "StrOutputParser"]


def test_04_classify_prompt_matches_handout(app_module):
    """Verify the classification prompt is the bare handout snippet, verbatim."""
    template = app_module.classify.steps[0]
    assert template.messages[0].prompt.template == (
        "Classify into billing/loan/fraud/app_issue. One word only.\n{text}"
    )


def test_05_reply_prompt_matches_handout(app_module):
    """Verify the reply prompt is the bare handout snippet, verbatim."""
    template = app_module.reply.steps[0]
    assert template.messages[0].prompt.template == (
        "Polite 60-word acknowledgement for a {cat} complaint. Sign as XYZ Finance.\n{text}"
    )
