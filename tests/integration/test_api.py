"""Integration tests for REST API endpoints."""

import json
import pytest
from providers.mock import MockLLMProvider
from providers.factory import set_provider_override
from core.errors import ProviderTimeoutError
from core.config import APP_VERSION


def test_api_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["version"] == APP_VERSION
    assert "config" in data
    assert "has_api_key" in data["config"]
    # Ensure raw secret is never present in health output
    assert "llm_api_key" not in data["config"]


def test_api_health_alias(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["version"] == APP_VERSION


def test_api_modes(client):
    response = client.get("/api/v1/modes")
    assert response.status_code == 200
    data = response.get_json()
    assert "modes" in data
    assert "intensities" in data
    mode_ids = [m["id"] for m in data["modes"]]
    assert "proofread" in mode_ids
    assert "academic" in mode_ids
    assert "clarity" in mode_ids


def test_api_rewrite_happy_path(client, mock_provider):
    payload = {
        "text": "We will recieve teh memo tomorrow.",
        "mode": "proofread",
        "intensity": "balanced",
    }
    response = client.post(
        "/api/v1/rewrite",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "revised_text" in data
    assert "metrics" in data
    assert "change_summary" in data
    assert data["mode"] == "proofread"
    assert "the memo" in data["revised_text"]


def test_api_rewrite_empty_input(client):
    payload = {"text": "   "}
    response = client.post(
        "/api/v1/rewrite",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "ValidationError" or data["error"] == "EmptyInput"


def test_api_rewrite_fallback_on_error(client, mock_provider):
    mock_provider.set_simulate_error(ProviderTimeoutError("Upstream timeout"))
    payload = {
        "text": "We will recieve teh memo tomorrow.",
        "mode": "proofread",
        "fallback_to_local": True,
    }
    response = client.post(
        "/api/v1/rewrite",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["is_fallback"] is True
    assert "receive the memo" in data["revised_text"]
    assert "provider" not in data
    assert "model" not in data
    assert "token_usage" not in data
    assert all("OpenRouter" not in warning for warning in data.get("warnings", []))


def test_api_provider_failure_is_honest_and_vendor_neutral(client, mock_provider):
    mock_provider.set_simulate_error(ProviderTimeoutError("vendor detail must not escape"))
    response = client.post(
        "/api/v1/rewrite",
        data=json.dumps({"text": "A natural rewrite is requested.", "mode": "natural", "fallback_to_local": True}),
        content_type="application/json",
    )
    assert response.status_code == 504
    data = response.get_json()
    assert data == {
        "ok": False,
        "code": "TIMEOUT",
        "message": "That took too long. Try a shorter selection.",
        "retryable": True,
    }


def test_api_analyze(client):
    payload = {"text": "The project URL is https://napstertec.com with $5,000 budget."}
    response = client.post(
        "/api/v1/analyze",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "metrics" in data
    assert "protected_spans" in data
    spans = [s["text"] for s in data["protected_spans"]]
    assert "https://napstertec.com" in spans
    assert "$5,000" in spans


def test_api_security_headers(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert "Content-Security-Policy" in response.headers
