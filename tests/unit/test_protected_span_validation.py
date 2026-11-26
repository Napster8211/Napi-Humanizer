"""Regression coverage for factual protected-span validation."""

from core.schemas import ProtectedSpan
from core.validator import OutputValidator


def test_punctuation_bearing_numbers_are_not_false_warnings():
    validator = OutputValidator()
    original = "Revenue reached $4,500,000, up 18.5%, across 3 regions at 2.4x capacity."
    spans = [
        ProtectedSpan(text="$4,500,000", span_type="number", start=16, end=26),
        ProtectedSpan(text="18.5%", span_type="number", start=32, end=37),
        ProtectedSpan(text="3", span_type="number", start=51, end=52),
        ProtectedSpan(text="2.4x", span_type="number", start=64, end=68),
    ]

    assert validator.verify_protected_spans(original, original, spans) == []


def test_standalone_number_is_not_satisfied_by_larger_number():
    validator = OutputValidator()
    span = ProtectedSpan(text="3", span_type="number", start=0, end=1)

    warnings = validator.verify_protected_spans("3", "30", [span])

    assert len(warnings) == 1
    assert "3" in warnings[0]


def test_citations_dates_and_quotes_are_checked_exactly():
    validator = OutputValidator()
    original = 'Published January 15, 2026 by (Smith et al., 2024): "Keep this wording."'
    spans = [
        ProtectedSpan(text="January 15, 2026", span_type="date", start=10, end=26),
        ProtectedSpan(text="(Smith et al., 2024)", span_type="citation", start=30, end=50),
        ProtectedSpan(text='"Keep this wording."', span_type="quotation", start=52, end=72),
    ]

    assert validator.verify_protected_spans(original, original, spans) == []
    assert validator.verify_protected_spans(original, original.replace("Keep", "Retain"), spans)
