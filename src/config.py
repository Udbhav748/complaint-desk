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
DEFAULT_TEMP_CLASSIFICATION: float = 0.0
DEFAULT_TEMP_REPLY: float = 0.2
MAX_CLASSIFICATION_TOKENS: int = 15
MAX_REPLY_TOKENS: int = 300


@dataclass(frozen=True)
class AppConfig:
    """Immutable application configuration container."""

    openai_api_key: str
    model_name: str = DEFAULT_MODEL_NAME
    temperature_classification: float = DEFAULT_TEMP_CLASSIFICATION
    temperature_reply: float = DEFAULT_TEMP_REPLY
    max_classification_tokens: int = MAX_CLASSIFICATION_TOKENS
    max_reply_tokens: int = MAX_REPLY_TOKENS

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration from environment variables with sensible defaults."""
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        model = os.getenv("OPENAI_MODEL_NAME", DEFAULT_MODEL_NAME).strip()

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
            openai_api_key=api_key,
            model_name=model if model else DEFAULT_MODEL_NAME,
            temperature_classification=temp_cls,
            temperature_reply=temp_reply,
            max_classification_tokens=MAX_CLASSIFICATION_TOKENS,
            max_reply_tokens=MAX_REPLY_TOKENS,
        )

    @property
    def has_valid_api_key(self) -> bool:
        """Check if an API key is configured and not a placeholder."""
        if not self.openai_api_key:
            return False
        if self.openai_api_key.startswith("your_openai_api_key"):
            return False
        return len(self.openai_api_key) > 10

    def __repr__(self) -> str:
        """Mask secrets when printing or logging the configuration."""
        masked_key = (
            f"{self.openai_api_key[:3]}...{self.openai_api_key[-4:]}"
            if self.has_valid_api_key
            else "<NOT CONFIGURED>"
        )
        return (
            f"AppConfig("
            f"openai_api_key='{masked_key}', "
            f"model_name='{self.model_name}', "
            f"temperature_classification={self.temperature_classification}, "
            f"temperature_reply={self.temperature_reply}, "
            f"max_classification_tokens={self.max_classification_tokens}, "
            f"max_reply_tokens={self.max_reply_tokens})"
        )
