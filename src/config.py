"""Configuration management and constants for Complaint Desk.

Handles environment variable loading, hyperparameter configuration,
and immutable constants like permitted complaint categories.
"""

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Tuple
from dotenv import load_dotenv

# Locate and load the .env file from the project root directory
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

# Canonical complaint categories required by FWC Module 8
ALLOWED_CATEGORIES: Tuple[str, ...] = ("billing", "loan", "fraud", "app_issue")

# Default hyperparameter values
DEFAULT_MODEL_NAME: str = "gpt-4o-mini"
DEFAULT_GROQ_MODEL_NAME: str = "openai/gpt-oss-20b"
DEFAULT_PROVIDER: str = "openai"
DEFAULT_TEMP_CLASSIFICATION: float = 0.0
DEFAULT_TEMP_REPLY: float = 0.2
MAX_CLASSIFICATION_TOKENS: int = 15
MAX_REPLY_TOKENS: int = 300


@dataclass(frozen=True)
class AppConfig:
    """Immutable application configuration container."""

    openai_api_key: str
    groq_api_key: str = ""
    llm_provider: str = DEFAULT_PROVIDER
    model_name: str = DEFAULT_MODEL_NAME
    groq_model_name: str = DEFAULT_GROQ_MODEL_NAME
    temperature_classification: float = DEFAULT_TEMP_CLASSIFICATION
    temperature_reply: float = DEFAULT_TEMP_REPLY
    max_classification_tokens: int = MAX_CLASSIFICATION_TOKENS
    max_reply_tokens: int = MAX_REPLY_TOKENS

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration from environment variables with sensible defaults."""
        openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        groq_key = os.getenv("GROQ_API_KEY", "").strip()
        provider = os.getenv("LLM_PROVIDER", DEFAULT_PROVIDER).strip().lower()

        # Ensure provider is valid
        if provider not in ("openai", "groq"):
            provider = DEFAULT_PROVIDER

        openai_model = os.getenv("OPENAI_MODEL_NAME", DEFAULT_MODEL_NAME).strip()
        groq_model = os.getenv("GROQ_MODEL_NAME", DEFAULT_GROQ_MODEL_NAME).strip()

        try:
            temp_cls = float(
                os.getenv("TEMPERATURE_CLASSIFICATION", str(DEFAULT_TEMP_CLASSIFICATION))
            )
        except ValueError:
            temp_cls = DEFAULT_TEMP_CLASSIFICATION

        try:
            temp_reply = float(
                os.getenv("TEMPERATURE_REPLY", str(DEFAULT_TEMP_REPLY))
            )
        except ValueError:
            temp_reply = DEFAULT_TEMP_REPLY

        return cls(
            openai_api_key=openai_key,
            groq_api_key=groq_key,
            llm_provider=provider,
            model_name=openai_model if openai_model else DEFAULT_MODEL_NAME,
            groq_model_name=groq_model if groq_model else DEFAULT_GROQ_MODEL_NAME,
            temperature_classification=temp_cls,
            temperature_reply=temp_reply,
            max_classification_tokens=MAX_CLASSIFICATION_TOKENS,
            max_reply_tokens=MAX_REPLY_TOKENS,
        )

    @property
    def active_model_name(self) -> str:
        """Return the correct model name based on the active provider."""
        return self.groq_model_name if self.llm_provider == "groq" else self.model_name

    @property
    def has_valid_api_key(self) -> bool:
        """Check if an API key is configured for the ACTIVE provider."""
        if self.llm_provider == "groq":
            return bool(
                self.groq_api_key
                and not self.groq_api_key.startswith("your_groq_api_key")
                and len(self.groq_api_key) > 10
            )
        else:
            return bool(
                self.openai_api_key
                and not self.openai_api_key.startswith("your_openai_api_key")
                and len(self.openai_api_key) > 10
            )

    def __repr__(self) -> str:
        """Mask secrets when printing or logging the configuration."""
        def mask(key: str) -> str:
            if not key or key.startswith("your_") or len(key) < 10:
                return "<NOT CONFIGURED>"
            return f"{key[:3]}...{key[-4:]}"

        return (
            f"AppConfig("
            f"llm_provider='{self.llm_provider}', "
            f"openai_api_key='{mask(self.openai_api_key)}', "
            f"groq_api_key='{mask(self.groq_api_key)}', "
            f"model_name='{self.model_name}', "
            f"groq_model_name='{self.groq_model_name}', "
            f"temperature_classification={self.temperature_classification}, "
            f"temperature_reply={self.temperature_reply}, "
            f"max_classification_tokens={self.max_classification_tokens}, "
            f"max_reply_tokens={self.max_reply_tokens})"
        )
