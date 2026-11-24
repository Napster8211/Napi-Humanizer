"""Integration tests for streaming API route."""

import json
import pytest
from providers.mock import MockLLMProvider
from providers.factory import set_provider_override


def test_api_rewrite_stream_endpoint(client, mock_provider):
    payload = {
        "text": "The quick brown fox jumps over the lazy dog.",
        "mode": "proofread",
        "intensity": "balanced",
    }
    response = client.post(
        "/api/v1/rewrite/stream",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["Content-Type"]
    assert response.headers["Cache-Control"] == "no-cache"
    assert response.headers["X-Accel-Buffering"] == "no"
    assert "Connection" not in response.headers

    raw_data = response.get_data(as_text=True)
    assert "event: init" in raw_data
    assert "event: chunk" in raw_data
    assert "event: complete" in raw_data


def test_api_rewrite_selection_endpoint(client, mock_provider):
    mock_provider.set_canned_response("swiftly leaps")
    full_text = "The quick brown fox jumps over the dog."
    start = full_text.index("jumps")
    end = start + len("jumps")

    payload = {
        "text": full_text,
        "selection_range": [start, end],
        "mode": "clarity",
    }
    response = client.post(
        "/api/v1/rewrite",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["selection_applied"] is True
    assert "The quick brown fox swiftly leaps over the dog." == data["revised_text"]
