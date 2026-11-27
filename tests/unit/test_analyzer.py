"""Unit tests for document analyzer and protected spans."""

import pytest
from core.analyzer import DocumentAnalyzer
from core.metrics import compute_text_metrics


def test_extract_protected_urls():
    analyzer = DocumentAnalyzer()
    text = "Visit https://napstertec.com/docs or http://api.service.io/v1 for more info."
    spans = analyzer.extract_protected_spans(text)
    url_spans = [s for s in spans if s.span_type == "url"]
    assert len(url_spans) == 2
    assert "https://napstertec.com/docs" in [s.text for s in url_spans]
    assert "http://api.service.io/v1" in [s.text for s in url_spans]


def test_extract_protected_numbers_and_currency():
    analyzer = DocumentAnalyzer()
    text = "Revenue grew by 18.5% to $4,500,000 across 42 enterprise accounts."
    spans = analyzer.extract_protected_spans(text)
    number_spans = [s.text for s in spans if s.span_type == "number"]
    assert "18.5%" in number_spans
    assert "$4,500,000" in number_spans
    assert "42" in number_spans


def test_alphanumeric_revision_tokens_are_not_split_into_standalone_numbers():
    analyzer = DocumentAnalyzer()
    spans = analyzer.extract_protected_spans(
        "Q3 revenue expanded at https://meet.google.com/xyz-123."
    )
    number_spans = [s.text for s in spans if s.span_type == "number"]
    url_spans = [s.text for s in spans if s.span_type == "url"]
    assert "3" not in number_spans
    assert url_spans == ["https://meet.google.com/xyz-123"]


def test_extract_protected_citations():
    analyzer = DocumentAnalyzer()
    text = "As established in earlier studies [1] and later confirmed (Smith et al., 2024), latency scales linearly."
    spans = analyzer.extract_protected_spans(text)
    citations = [s.text for s in spans if s.span_type == "citation"]
    assert "[1]" in citations
    assert any("Smith et al., 2024" in c for c in citations)


def test_extract_protected_dates():
    analyzer = DocumentAnalyzer()
    text = "The release occurred on January 15, 2026 and finalized by 2026-11-23."
    spans = analyzer.extract_protected_spans(text)
    dates = [s.text for s in spans if s.span_type == "date"]
    assert any("January 15, 2026" in d for d in dates)
    assert any("2026-11-23" in d for d in dates)


def test_extract_protected_code():
    analyzer = DocumentAnalyzer()
    text = "Run `pip install waitress` or inspect:\n```python\nimport sys\nprint(sys.version)\n```"
    spans = analyzer.extract_protected_spans(text)
    code_spans = [s.text for s in spans if s.span_type == "code"]
    assert "`pip install waitress`" in code_spans
    assert any("import sys" in c for c in code_spans)


def test_text_metrics_calculation():
    text = (
        "Good writing is simple and clear. "
        "Short sentences help people read easily. "
        "We make the words clean and direct."
    )
    metrics = compute_text_metrics(text)
    assert metrics.word_count > 15
    assert metrics.sentence_count == 3
    assert metrics.flesch_reading_ease > 0
    assert metrics.flesch_kincaid_grade > 0
    assert metrics.lexical_diversity > 0.5
    assert "Descriptive writing metrics" in metrics.metric_notice


def test_detector_returns_zero_and_insufficient_status_for_short_text():
    result = DocumentAnalyzer().analyze("This short draft is not long enough for a meaningful detector scan.")
    assert result.ai_likelihood_percent == 0
    assert result.detector_status == "insufficient_text"


def test_detector_returns_sentence_segments_and_bounded_percentage():
    text = " ".join([
        "In conclusion, this report demonstrates a clear result for the project team and provides useful context for the planned work."
    ] * 6) + " The team reviewed the data and approved the next practical step."
    result = DocumentAnalyzer().analyze(text)
    assert result.detector_status == "ready"
    assert 0 <= result.ai_likelihood_percent <= 100
    assert len(result.detector_segments) >= 6
    assert any(segment.flagged for segment in result.detector_segments)
    assert all(segment.start < segment.end for segment in result.detector_segments)
