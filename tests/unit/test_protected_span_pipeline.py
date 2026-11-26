"""End-to-end tests for rewrite placeholder protection."""

from core.orchestrator import RewriteOrchestrator
from core.schemas import EditingMode, RewriteRequest
from providers.mock import MockLLMProvider


def test_provider_placeholder_is_restored_to_original_factual_value():
    provider = MockLLMProvider()
    provider.set_canned_response("Revenue reached ⟦P1⟧.")
    orchestrator = RewriteOrchestrator(provider=provider)

    response = orchestrator.rewrite(RewriteRequest(
        text="Revenue reached $50,000.",
        mode=EditingMode.NATURAL,
    ))

    assert response.revised_text == "Revenue reached $50,000."
    assert response.warnings == []


def test_damaged_placeholder_keeps_original_target_with_warning():
    provider = MockLLMProvider()
    provider.set_canned_response("Revenue grew substantially.")
    orchestrator = RewriteOrchestrator(provider=provider)

    response = orchestrator.rewrite(RewriteRequest(
        text="Revenue reached $50,000.",
        mode=EditingMode.NATURAL,
    ))

    assert response.revised_text == "Revenue reached $50,000."
    assert any("original target was retained" in warning for warning in response.warnings)
    assert any("$50,000" in warning for warning in response.warnings)
