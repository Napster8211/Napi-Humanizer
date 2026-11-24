"""Unit tests for language detection, token cost estimation, and style profiles."""

import pytest
from core.schemas import RewriteRequest, StyleProfile, EditingMode
from core.metrics import detect_language, estimate_tokens_and_cost
from core.prompt_builder import build_system_instruction


def test_detect_language():
    en_text = "The quick brown fox jumps over the lazy dog and runs in the park."
    es_text = "El rápido zorro marrón salta sobre el perro perezoso y corre por el parque."
    fr_text = "Le renard brun rapide saute par-dessus le chien paresseux et court dans le parc."
    de_text = "Der schnelle braune Fuchs springt über den faulen Hund und läuft in den Park."

    assert detect_language(en_text) == "en"
    assert detect_language(es_text) == "es"
    assert detect_language(fr_text) == "fr"
    assert detect_language(de_text) == "de"


def test_estimate_tokens_and_cost():
    prompt = "This is a prompt with approximately twenty-five characters."
    completion = "This is a response."
    usage = estimate_tokens_and_cost(prompt, completion)

    assert usage.prompt_tokens > 0
    assert usage.completion_tokens > 0
    assert usage.total_tokens == usage.prompt_tokens + usage.completion_tokens
    assert usage.estimated_cost_usd > 0.0


def test_style_profile_system_instruction():
    profile = StyleProfile(
        name="ExecutiveTech",
        preferred_tone="Decisive and succinct",
        target_audience="CTOs and VP Engineering",
        forbidden_words=["delve", "game-changer", "robust"],
        custom_guidelines="Never start sentences with 'Furthermore'.",
    )
    req = RewriteRequest(
        text="Sample text",
        mode=EditingMode.PROFESSIONAL,
        style_profile=profile,
    )
    system_inst = build_system_instruction(req, detected_language="en")

    assert "APPLIED STYLE PROFILE: ExecutiveTech" in system_inst
    assert "Decisive and succinct" in system_inst
    assert "CTOs and VP Engineering" in system_inst
    assert "delve, game-changer, robust" in system_inst
    assert "Never start sentences with 'Furthermore'" in system_inst
