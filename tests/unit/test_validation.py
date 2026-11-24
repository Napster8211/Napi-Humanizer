"""Unit tests for input and output validation."""

import pytest
from core.schemas import RewriteRequest, EditingMode, EditingIntensity
from core.validator import OutputValidator
from core.errors import EmptyInputError, InputTooLargeError


def test_empty_input_validation():
    validator = OutputValidator()
    with pytest.raises(Exception):
        RewriteRequest(text="")

    with pytest.raises(Exception):
        RewriteRequest(text="   \n\t  ")


def test_input_too_large_validation():
    validator = OutputValidator()
    req = RewriteRequest(text="A" * 150)
    with pytest.raises(InputTooLargeError):
        validator.validate_input(req, max_chars=100)


def test_valid_input_passes():
    validator = OutputValidator()
    req = RewriteRequest(text="Valid sample sentence for rewriting.")
    validator.validate_input(req, max_chars=500)


def test_all_modes_accepted():
    for mode in EditingMode:
        req = RewriteRequest(text="Sample text", mode=mode)
        assert req.mode == mode


def test_all_intensities_accepted():
    for intensity in EditingIntensity:
        req = RewriteRequest(text="Sample text", intensity=intensity)
        assert req.intensity == intensity


def test_unsupported_mode_raises():
    with pytest.raises(ValueError):
        RewriteRequest(text="Sample text", mode="invalid_mode")


def test_unclosed_code_fence_warning():
    validator = OutputValidator()
    orig = "Here is some code:\n```python\nprint('hello')\n```"
    revised = "Here is some code:\n```python\nprint('hello')"  # Missing closing fence
    warnings = validator.verify_formatting_integrity(orig, revised)
    assert any("unclosed markdown code blocks" in w.lower() for w in warnings)
