"""Unit tests for rewrite orchestrator and fallback handling."""

import pytest
from core.orchestrator import RewriteOrchestrator
from core.schemas import RewriteRequest, EditingMode, EditingIntensity
from providers.mock import MockLLMProvider
from core.errors import ProviderTimeoutError


def test_orchestrator_rewrite_success():
    mock_prov = MockLLMProvider()
    orchestrator = RewriteOrchestrator(provider=mock_prov)

    req = RewriteRequest(
        text="This is teh initial test draft with $1,000 revenue on January 1, 2026.",
        mode=EditingMode.PROOFREAD,
        intensity=EditingIntensity.BALANCED,
    )

    response = orchestrator.rewrite(req)
    assert response.original_text == req.text
    assert response.mode == "proofread"
    assert response.provider == "mock"
    assert response.is_fallback is False
    assert response.duration_ms >= 0.0
    assert response.request_id is not None
    assert response.metrics is not None
    assert response.change_summary is not None
    # Verified typos like 'teh' corrected
    assert "the initial test" in response.revised_text


def test_orchestrator_fallback_on_provider_error():
    mock_prov = MockLLMProvider()
    mock_prov.set_simulate_error(ProviderTimeoutError("Upstream timeout"))
    orchestrator = RewriteOrchestrator(provider=mock_prov)

    req = RewriteRequest(
        text="Draft text with teh typographical error.",
        mode=EditingMode.CLARITY,
        fallback_to_local=True,
    )

    response = orchestrator.rewrite(req)
    # Ensure fallback succeeded gracefully
    assert response.is_fallback is True
    assert "deterministic-fallback" in response.provider
    assert any("fallback" in w.lower() or "timeout" in w.lower() for w in response.warnings)
    # Check that deterministic polish was applied
    assert "the typographical error" in response.revised_text


def test_orchestrator_no_fallback_raises():
    mock_prov = MockLLMProvider()
    mock_prov.set_simulate_error(ProviderTimeoutError("Upstream timeout"))
    orchestrator = RewriteOrchestrator(provider=mock_prov)

    req = RewriteRequest(
        text="Draft text.",
        mode=EditingMode.CLARITY,
        fallback_to_local=False,
    )

    with pytest.raises(ProviderTimeoutError):
        orchestrator.rewrite(req)


def test_orchestrator_legacy_mode():
    mock_prov = MockLLMProvider()
    orchestrator = RewriteOrchestrator(provider=mock_prov)

    req = RewriteRequest(
        text="Legacy run with teh typo.",
        mode=EditingMode.LEGACY,
    )

    response = orchestrator.rewrite(req)
    assert response.is_fallback is True
    assert any("legacy" in w.lower() for w in response.warnings)
    assert "the typo" in response.revised_text


def test_orchestrator_protected_span_warning_when_altered():
    mock_prov = MockLLMProvider()
    # Mock deletes the number $50,000
    mock_prov.set_canned_response("Total revenue grew substantially.")
    orchestrator = RewriteOrchestrator(provider=mock_prov)

    req = RewriteRequest(
        text="Total revenue grew to $50,000.",
        mode=EditingMode.CONCISE,
    )

    response = orchestrator.rewrite(req)
    assert any("$50,000" in w for w in response.warnings)
