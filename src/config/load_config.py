"""Configuration loader for the escalation decision system."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ModelConfig:
    """Configuration for a single LLM model."""

    provider: str
    model: str
    temperature: float
    env_var: str
    base_url_env: str | None = None


@dataclass
class ChatbotConfig:
    """Configuration for the support chatbot."""

    model: str
    temperature: float
    max_tokens: int


@dataclass
class Config:
    """Main application configuration."""

    active_model: str
    context_window_size: int
    models: dict[str, ModelConfig]
    chatbot: ChatbotConfig

    @classmethod
    def load(cls, config_path: str | Path) -> "Config":
        """Load configuration from YAML file."""
        with open(config_path) as f:
            data = yaml.safe_load(f)

        models = {
            name: ModelConfig(**model_data)
            for name, model_data in data["models"].items()
        }

        chatbot = ChatbotConfig(**data["chatbot"])

        return cls(
            active_model=data["active_model"],
            context_window_size=data["context_window_size"],
            models=models,
            chatbot=chatbot,
        )

    def get_model_config(self, model_name: str | None = None) -> ModelConfig:
        """Get configuration for a specific model."""
        name = model_name or self.active_model
        if name not in self.models:
            raise ValueError(f"Model '{name}' not found in config")
        return self.models[name]

    def get_api_key(self, model_config: ModelConfig) -> str:
        """Get API key from environment variable."""
        api_key = os.getenv(model_config.env_var)
        if not api_key:
            raise ValueError(
                f"Environment variable '{model_config.env_var}' not set"
            )
        return api_key

    def get_base_url(self, model_config: ModelConfig) -> str | None:
        """Get base URL from environment variable if configured."""
        if not model_config.base_url_env:
            return None
        return os.getenv(model_config.base_url_env)
