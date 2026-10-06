"""LangChain pipeline implementations for classification and reply generation.

Matches the FWC Module 8 §18.1 Activity A reference code exactly:
one shared `llm` instance, ChatPromptTemplate → llm → StrOutputParser,
no token cap, flat temperature=0.3.
"""

from typing import Optional, Tuple
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from src.config import AppConfig, DEFAULT_MODEL_NAME
from src.prompts import CLASSIFICATION_PROMPT, REPLY_PROMPT


def get_chat_model(
    api_key: Optional[str] = None,
    model_name: str = DEFAULT_MODEL_NAME,
    temperature: float = 0.3,
    provider: str = "openai",
) -> BaseChatModel:
    """Factory function creating a configured LangChain Chat model instance.

    Args:
        api_key: Secret key. If None, ChatOpenAI attempts to read from env.
        model_name: Model identifier.
        temperature: Sampling temperature.
        provider: 'openai' or 'groq'. Adjusts base_url for Groq's OpenAI-compatible endpoint.

    Returns:
        Configured BaseChatModel instance.
    """
    kwargs = {
        "api_key": api_key or None,
        "model": model_name,
        "temperature": temperature,
    }

    if provider == "groq":
        kwargs["base_url"] = "https://api.groq.com/openai/v1"
        kwargs["reasoning_effort"] = "low"

    return ChatOpenAI(**kwargs)


def build_classification_chain(llm: BaseChatModel) -> Runnable:
    """Build Chain 1: Complaint Classification Chain.

    Pipeline: CLASSIFICATION_PROMPT | llm | StrOutputParser()
    """
    return CLASSIFICATION_PROMPT | llm | StrOutputParser()


def build_reply_chain(llm: BaseChatModel) -> Runnable:
    """Build Chain 2: Customer Reply Generation Chain.

    Pipeline: REPLY_PROMPT | llm | StrOutputParser()
    """
    return REPLY_PROMPT | llm | StrOutputParser()


def create_chains(
    config: Optional[AppConfig] = None,
) -> Tuple[Runnable, Runnable]:
    """Convenience factory to construct both chains from a single shared model.

    Args:
        config: AppConfig instance. If None, loaded from environment.

    Returns:
        Tuple of (classification_chain, reply_chain), both backed by the same
        underlying llm instance, matching the reference code's single
        `llm = ChatOpenAI(...)` shared between both chains.
    """
    cfg = config if config is not None else AppConfig.from_env()

    if cfg.llm_provider == "groq":
        active_api_key = cfg.groq_api_key if cfg.has_valid_api_key else None
        model_name = cfg.groq_model_name
    else:
        active_api_key = cfg.openai_api_key if cfg.has_valid_api_key else None
        model_name = cfg.model_name

    llm = get_chat_model(
        api_key=active_api_key,
        model_name=model_name,
        temperature=cfg.temperature,
        provider=cfg.llm_provider,
    )

    classification_chain = build_classification_chain(llm)
    reply_chain = build_reply_chain(llm)

    return classification_chain, reply_chain
