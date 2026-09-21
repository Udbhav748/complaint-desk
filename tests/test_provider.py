"""Deterministic tests for dynamic LLM provider configuration (OpenAI vs Groq).
Ensures base_url routing and API key evaluation correctly follows LLM_PROVIDER.
"""

from src.chains import get_chat_model
from src.config import AppConfig

def test_01_get_chat_model_openai():
    """Verify get_chat_model constructs OpenAI correctly by default."""
    model = get_chat_model(api_key="sk-test", model_name="gpt-4o-mini", provider="openai")
    # Base URL for OpenAI should be the default LangChain behavior, not Groq
    assert model.openai_api_base is None or "api.groq.com" not in model.openai_api_base
    assert model.model_name == "gpt-4o-mini"
    assert model.openai_api_key.get_secret_value() == "sk-test"

def test_02_get_chat_model_groq():
    """Verify get_chat_model modifies base_url for Groq provider."""
    model = get_chat_model(api_key="gsk-test", model_name="openai/gpt-oss-20b", provider="groq")
    assert model.openai_api_base == "https://api.groq.com/openai/v1"
    assert model.model_name == "openai/gpt-oss-20b"
    assert model.openai_api_key.get_secret_value() == "gsk-test"

def test_03_appconfig_active_model_name():
    """Verify active_model_name resolves based on provider."""
    cfg_openai = AppConfig(openai_api_key="sk-test", llm_provider="openai")
    assert cfg_openai.active_model_name == "gpt-4o-mini"

    cfg_groq = AppConfig(openai_api_key="", groq_api_key="gsk-test", llm_provider="groq")
    assert cfg_groq.active_model_name == "openai/gpt-oss-20b"

def test_04_appconfig_has_valid_credentials():
    """Verify has_valid_api_key checks the correct key based on provider."""
    # Groq provider, missing key
    cfg = AppConfig(openai_api_key="sk-test123456", groq_api_key="", llm_provider="groq")
    assert cfg.has_valid_api_key is False

    # Groq provider, valid key
    cfg = AppConfig(openai_api_key="", groq_api_key="gsk-test123456", llm_provider="groq")
    assert cfg.has_valid_api_key is True

    # OpenAI provider, missing key
    cfg = AppConfig(openai_api_key="", groq_api_key="gsk-test123456", llm_provider="openai")
    assert cfg.has_valid_api_key is False

    # OpenAI provider, valid key
    cfg = AppConfig(openai_api_key="sk-test123456", groq_api_key="", llm_provider="openai")
    assert cfg.has_valid_api_key is True
