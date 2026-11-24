"""Integration tests for CLI subcommands and legacy entry points."""

import sys
import subprocess
import pytest
from ai_detector_bypass import humanize_text, calculate_score, process_text


def test_legacy_humanize_text():
    text = "We will recieve teh memo tomorrow."
    revised = humanize_text(text, intensity="balanced", mode="proofread")
    assert "the memo" in revised
    assert "receive" in revised


def test_legacy_calculate_score():
    text = "This is a simple sentence to test scoring."
    score = calculate_score(text)
    assert "clarity_index" in score
    assert "notice" in score
    assert "Descriptive writing metric" in score["notice"]


def test_legacy_process_text():
    text = "We will recieve teh update."
    result = process_text(text)
    assert "revised_text" in result
    assert "metrics" in result
    assert "the update" in result["revised_text"]
