"""Document analyzer for structural segmentation, readability, and protected span extraction."""

import re
from typing import List, Tuple
from core.schemas import ProtectedSpan, TextMetrics, AnalysisResponse
from core.metrics import compute_text_metrics


class DocumentAnalyzer:
    """Analyzes text structure, readability, and protected factual entities."""

    # Regex patterns for protected entities
    URL_REGEX = re.compile(r'https?://[^\s<>"\')]+|www\.[^\s<>"\')]+', re.IGNORECASE)
    EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    CODE_BLOCK_REGEX = re.compile(r'```[\s\S]*?```|`[^`\n]+`')
    CITATION_REGEX = re.compile(r'\[(?:\d+|[A-Za-z\s]+,\s*\d{4})\]|\([A-Za-z\s]+(?:et\s+al\.)?,\s*\d{4}[^)]*\)')
    NUMBER_PERCENT_REGEX = re.compile(
        r'(?:[\$€£¥])?\d+(?:,\d{3})*(?:\.\d+)?(?:%|(?:x|k|m|b)\b|\b)',
        re.IGNORECASE
    )
    DATE_REGEX = re.compile(
        r'\b(?:(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})\b',
        re.IGNORECASE
    )
    QUOTE_REGEX = re.compile(r'"[^"\n]{3,}"|“[^”\n]{3,}”')

    def extract_protected_spans(self, text: str) -> List[ProtectedSpan]:
        """Identify spans that should be protected from unwarranted modification."""
        spans: List[ProtectedSpan] = []
        occupied_ranges: List[Tuple[int, int]] = []

        def is_overlapping(start: int, end: int) -> bool:
            return any(s < end and end <= e or start >= s and start < e for s, e in occupied_ranges)

        def add_matches(pattern: re.Pattern, span_type: str):
            for match in pattern.finditer(text):
                start, end = match.span()
                if not is_overlapping(start, end):
                    spans.append(ProtectedSpan(
                        text=match.group(0),
                        span_type=span_type,
                        start=start,
                        end=end
                    ))
                    occupied_ranges.append((start, end))

        # Order of precedence: code -> urls -> emails -> citations -> quotes -> dates -> numbers
        add_matches(self.CODE_BLOCK_REGEX, "code")
        add_matches(self.URL_REGEX, "url")
        add_matches(self.EMAIL_REGEX, "email")
        add_matches(self.CITATION_REGEX, "citation")
        add_matches(self.QUOTE_REGEX, "quotation")
        add_matches(self.DATE_REGEX, "date")
        add_matches(self.NUMBER_PERCENT_REGEX, "number")

        # Sort spans by starting index
        spans.sort(key=lambda s: s.start)
        return spans

    def analyze(self, text: str) -> AnalysisResponse:
        """Perform comprehensive analysis of input document."""
        metrics = compute_text_metrics(text)
        protected_spans = self.extract_protected_spans(text)
        paragraphs = metrics.paragraph_count
        sentences = metrics.sentence_count

        return AnalysisResponse(
            metrics=metrics,
            protected_spans=protected_spans,
            paragraphs=paragraphs,
            sentences=sentences,
            detected_language=metrics.detected_language,
        )


# Global analyzer singleton
_analyzer_instance = DocumentAnalyzer()


def get_analyzer() -> DocumentAnalyzer:
    """Return default DocumentAnalyzer instance."""
    return _analyzer_instance
