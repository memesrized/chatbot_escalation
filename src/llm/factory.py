"""LLM factory for creating LangChain chat models."""

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

from src.config.load import Config, ModelConfig


def create_chat_model(
    config: Config, model_name: str | None = None
) -> BaseChatModel:
    """
    Create a LangChain chat model from configuration.

    Args:
        config: Application configuration
        model_name: Optional model name to override active_model

    Returns:
        Initialized LangChain chat model
    """
    model_config = config.get_model_config(model_name)
    api_key = config.get_api_key(model_config)
    base_url = config.get_base_url(model_config)

    model_kwargs = {
        "temperature": model_config.temperature,
    }

    # Add optional model configuration parameters
    if model_config.max_tokens is not None:
        model_kwargs["max_tokens"] = model_config.max_tokens
    
    if model_config.timeout is not None:
        model_kwargs["timeout"] = model_config.timeout
    
    if model_config.max_retries is not None:
        model_kwargs["max_retries"] = model_config.max_retries

    # Add base_url for custom endpoints
    if base_url:
        model_kwargs["base_url"] = base_url

    # Initialize model using LangChain's init_chat_model
    return init_chat_model(
        model=model_config.model,
        model_provider=model_config.provider,
        api_key=api_key,
        **model_kwargs,
    )
