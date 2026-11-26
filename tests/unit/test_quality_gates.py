"""Tests for rewrite length and changed-word-ratio quality gates."""

from core.validator import OutputValidator


def test_short_and_proofread_edits_are_not_forced_into_rewrite_bands():
    validator = OutputValidator()
    assert validator.quality_warnings("A short draft with one typo.", "A short draft with one error.", "natural", "balanced") == []
    assert validator.quality_warnings("word " * 30, "word " * 30, "proofread", "balanced") == []


def test_substantive_rewrite_reports_out_of_band_change_ratio():
    validator = OutputValidator()
    original = " ".join(f"word{i}" for i in range(30))
    revised = "word0 word1 word2 word3 word4 word5 word6 word7 word8 word9"

    warnings = validator.quality_warnings(original, revised, "natural", "balanced")

    assert any("length ratio" in warning for warning in warnings)
    assert any("Changed-word ratio" in warning for warning in warnings)


def test_concise_mode_allows_shorter_output_without_length_warning():
    validator = OutputValidator()
    original = " ".join(f"word{i}" for i in range(30))
    revised = " ".join(f"word{i}" for i in range(15))

    warnings = validator.quality_warnings(original, revised, "concise", "balanced")

    assert not any("length ratio" in warning for warning in warnings)
