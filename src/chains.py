"""LangChain pipeline implementations for classification and reply generation.

Implements the FWC Module 8 architecture:
ChatPromptTemplate → ChatOpenAI → StrOutputParser
Organized into two decoupled, testable chains with dependency-injected LLM instances.
"""

from typing import Optional, Tuple
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from src.config import (
    AppConfig,
    DEFAULT_MODEL_NAME,
    DEFAULT_TEMP_CLASSIFICATION,
    DEFAULT_TEMP_REPLY,
    MAX_CLASSIFICATION_TOKENS,
    MAX_REPLY_TOKENS,
)
from src.prompts import CLASSIFICATION_PROMPT, REPLY_PROMPT


def get_chat_model(
    api_key: Optional[str] = None,
    model_name: str = DEFAULT_MODEL_NAME,
    temperature: float = 0.0,
    max_tokens: Optional[int] = None,
    provider: str = "openai",
) -> BaseChatModel:
    """Factory function creating a configured LangChain Chat model instance.

    Returns BaseChatModel to keep the architecture decoupled from the specific provider.
    In Activity B, this factory can instantiate ChatOllama without altering the downstream chains.

    Args:
        api_key: Secret key. If None, ChatOpenAI attempts to read from env.
        model_name: Model identifier.
        temperature: Sampling temperature controlling output variance.
        max_tokens: Maximum tokens permitted in generation output.
        provider: 'openai' or 'groq'. Adjusts base_url for Groq's OpenAI-compatible endpoint.

    Returns:
        Configured BaseChatModel instance.
    """
    kwargs = {
        "api_key": api_key or None,
        "model": model_name,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "timeout": 30.0,
        "max_retries": 2,
    }

    if provider == "groq":
        kwargs["base_url"] = "https://api.groq.com/openai/v1"
        # Increase max_tokens for Groq reasoning models to ensure the reasoning phase
        # completes successfully. Using 256 with low reasoning effort is sufficient.
        if kwargs["max_tokens"] is not None and kwargs["max_tokens"] < 256:
            kwargs["max_tokens"] = 256
        kwargs["reasoning_effort"] = "low"

    return ChatOpenAI(**kwargs)


def build_classification_chain(llm: BaseChatModel) -> Runnable:
    """Build Chain 1: Complaint Classification Chain.

    Pipeline:
        CLASSIFICATION_PROMPT | llm | StrOutputParser()

    Args:
        llm: A LangChain BaseChatModel instance configured for classification.

    Returns:
        Executable LangChain Runnable expecting {"complaint": str}.
    """
    return CLASSIFICATION_PROMPT | llm | StrOutputParser()


def build_reply_chain(llm: BaseChatModel) -> Runnable:
    """Build Chain 2: Customer Reply Generation Chain.

    Pipeline:
        REPLY_PROMPT | llm | StrOutputParser()

    Args:
        llm: A LangChain BaseChatModel instance configured for reply generation.

    Returns:
        Executable LangChain Runnable expecting {"complaint": str, "category": str}.
    """
    return REPLY_PROMPT | llm | StrOutputParser()


def create_chains(
    config: Optional[AppConfig] = None,
) -> Tuple[Runnable, Runnable]:
    """Convenience factory to construct both chains from application configuration.

    Args:
        config: AppConfig instance. If None, loaded from environment.

    Returns:
        Tuple of (classification_chain, reply_chain).
    """
    cfg = config if config is not None else AppConfig.from_env()

    if cfg.llm_provider == "groq":
        active_api_key = cfg.groq_api_key if cfg.has_valid_api_key else None
        model_name = cfg.groq_model_name
    else:
        active_api_key = cfg.openai_api_key if cfg.has_valid_api_key else None
        model_name = cfg.model_name

    classification_llm = get_chat_model(
        api_key=active_api_key,
        model_name=model_name,
        temperature=cfg.temperature_classification,
        max_tokens=cfg.max_classification_tokens,
        provider=cfg.llm_provider,
    )

    reply_llm = get_chat_model(
        api_key=active_api_key,
        model_name=model_name,
        temperature=cfg.temperature_reply,
        max_tokens=cfg.max_reply_tokens,
        provider=cfg.llm_provider,
    )

    classification_chain = build_classification_chain(classification_llm)
    reply_chain = build_reply_chain(reply_llm)

    return classification_chain, reply_chain
