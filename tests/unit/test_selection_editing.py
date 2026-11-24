"""Unit tests for selection-based text editing."""

import pytest
from core.schemas import RewriteRequest, EditingMode
from core.orchestrator import RewriteOrchestrator
from providers.mock import MockLLMProvider


def test_selection_editing_replaces_only_selected_span():
    mock_prov = MockLLMProvider()
    mock_prov.set_canned_response("greatly increased")
    orchestrator = RewriteOrchestrator(provider=mock_prov)

    # Full text: "Our Q3 earnings grew very much during the summer."
    # We want to edit only "grew very much" (index 16 to 30)
    full_text = "Our Q3 earnings grew very much during the summer."
    start = full_text.index("grew very much")
    end = start + len("grew very much")

    req = RewriteRequest(
        text=full_text,
        selection_range=(start, end),
        mode=EditingMode.CLARITY,
    )

    response = orchestrator.rewrite(req)

    assert response.selection_applied is True
    assert "Our Q3 earnings " in response.revised_text
    assert "greatly increased" in response.revised_text
    assert " during the summer." in response.revised_text
    assert response.revised_text == "Our Q3 earnings greatly increased during the summer."
