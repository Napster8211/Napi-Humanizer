"""Unit tests for streaming rewrite generator and SSE events."""

import json
import pytest
from core.schemas import RewriteRequest, EditingMode
from core.orchestrator import RewriteOrchestrator
from providers.mock import MockLLMProvider


def test_orchestrator_rewrite_stream_events():
    mock_prov = MockLLMProvider()
    orchestrator = RewriteOrchestrator(provider=mock_prov)

    req = RewriteRequest(
        text="The team will meet tomorrow to discuss project Alpha.",
        mode=EditingMode.PROOFREAD,
    )

    events = list(orchestrator.rewrite_stream(req))
    assert len(events) >= 3

    # Check init event
    init_event = events[0]
    assert "event: init" in init_event
    assert "data: " in init_event
    init_data = json.loads(init_event.split("data: ")[1])
    assert "request_id" in init_data
    assert init_data["provider"] == "mock"

    # Check chunk events
    chunk_events = [e for e in events if "event: chunk" in e]
    assert len(chunk_events) > 0

    # Check complete event
    complete_event = events[-1]
    assert "event: complete" in complete_event
    complete_data = json.loads(complete_event.split("data: ")[1])
    assert "revised_text" in complete_data
    assert "token_usage" in complete_data
    assert complete_data["token_usage"]["total_tokens"] > 0
