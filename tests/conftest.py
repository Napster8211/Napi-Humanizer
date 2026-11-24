"""Pytest test configuration and shared fixtures."""

import os
import pytest
from core.config import AppConfig
from web_ui import create_app
from providers.mock import MockLLMProvider
from providers.factory import set_provider_override


@pytest.fixture(autouse=True)
def reset_provider():
    """Ensure clean provider state for every test."""
    set_provider_override(None)
    yield
    set_provider_override(None)


@pytest.fixture
def test_config():
    """Return test AppConfig instance."""
    return AppConfig(
        app_env="testing",
        debug=True,
        llm_provider="mock",
        max_input_chars=5000,
        rate_limit_per_minute=100,
        llm_timeout_seconds=5,
    )


@pytest.fixture
def client(test_config):
    """Flask test client fixture."""
    app = create_app(test_config)
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_provider():
    """Fixture providing configurable mock provider."""
    provider = MockLLMProvider()
    set_provider_override(provider)
    return provider
