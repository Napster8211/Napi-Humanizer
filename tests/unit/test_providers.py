"""Unit tests for LLM provider adapters."""

import pytest
from providers.mock import MockLLMProvider
from providers.openai_compatible import OpenAICompatibleProvider
from core.errors import (
    ProviderMissingKeyError,
    ProviderTimeoutError,
    ProviderRateLimitError,
    ProviderError,
)


def test_mock_provider_generation():
    provider = MockLLMProvider()
    resp = provider.generate("hello world", "Proofread instructions")
    assert resp == "hello world"


def test_mock_provider_canned_response():
    provider = MockLLMProvider()
    provider.set_canned_response("Explicit revised text.")
    resp = provider.generate("hello world", "Proofread instructions")
    assert resp == "Explicit revised text."


def test_mock_provider_simulated_error():
    provider = MockLLMProvider()
    provider.set_simulate_error(ProviderRateLimitError("Rate limited"))
    with pytest.raises(ProviderRateLimitError):
        provider.generate("hello", "instructions")


def test_openai_compatible_missing_key():
    provider = OpenAICompatibleProvider(api_key=None)
    with pytest.raises(ProviderMissingKeyError):
        provider.generate("hello", "instructions")

    provider_empty = OpenAICompatibleProvider(api_key="   ")
    with pytest.raises(ProviderMissingKeyError):
        provider_empty.generate("hello", "instructions")
