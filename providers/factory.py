"""Factory for instantiating LLM providers."""

from typing import Optional
from core.config import AppConfig, get_config
from providers.base import BaseLLMProvider
from providers.mock import MockLLMProvider
from providers.openai_compatible import OpenAICompatibleProvider

_override_provider: Optional[BaseLLMProvider] = None


def set_provider_override(provider: Optional[BaseLLMProvider]) -> None:
    """Set or clear a provider override (used in testing)."""
    global _override_provider
    _override_provider = provider


def get_provider(config: Optional[AppConfig] = None) -> BaseLLMProvider:
    """Return configured provider instance."""
    global _override_provider
    if _override_provider is not None:
        return _override_provider

    cfg = config or get_config()
    provider_type = cfg.llm_provider.lower()

    if provider_type in ("openai", "openrouter", "custom"):
        return OpenAICompatibleProvider(
            api_key=cfg.llm_api_key,
            base_url=cfg.llm_base_url,
            model=cfg.llm_model,
            timeout_seconds=cfg.llm_timeout_seconds,
            max_retries=cfg.llm_max_retries,
        )

    # Default to deterministic mock provider
    return MockLLMProvider(
        model=cfg.llm_model or "mock-model-v1",
        timeout_seconds=cfg.llm_timeout_seconds,
    )
