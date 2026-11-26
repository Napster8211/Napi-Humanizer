"""Document analyzer for structural segmentation, readability, and protected span extraction."""

import re
from typing import List, Tuple
from core.schemas import DetectorSegment, ProtectedSpan, TextMetrics, AnalysisResponse
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
    SENTENCE_REGEX = re.compile(r"[^.!?\n]+(?:[.!?]+|$)", re.MULTILINE)
    BOILERPLATE_PATTERNS = (
        (re.compile(r"\b(in conclusion|to summarize|overall|it is important to note)\b", re.I), "formulaic transition"),
        (re.compile(r"\b(furthermore|moreover|additionally|consequently)\b", re.I), "stacked transition"),
        (re.compile(r"\b(this (?:highlights|demonstrates|underscores|ensures))\b", re.I), "generic explanatory phrase"),
        (re.compile(r"\bplays a (?:crucial|important|significant) role\b", re.I), "generic emphasis phrase"),
    )

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

    def _sentence_segments(self, text: str) -> List[Tuple[str, int, int]]:
        """Return sentence-like spans with source offsets for safe UI highlighting."""
        return [
            (match.group(0), match.start(), match.end())
            for match in self.SENTENCE_REGEX.finditer(text)
            if match.group(0).strip()
        ]

    def detect_linguistic_signals(self, text: str) -> Tuple[int, str, List[DetectorSegment]]:
        """Estimate AI-like linguistic signals conservatively and transparently.

        This intentionally does not use Flesch or other readability metrics. It requires
        enough text, flags only sentences with multiple observable signals, and returns
        an estimate based on flagged words rather than an authorship verdict.
        """
        segments = self._sentence_segments(text)
        word_count = len(re.findall(r"\b[A-Za-z0-9'-]+\b", text))
        if word_count < 80 or len(segments) < 3:
            return 0, "insufficient_text", [
                DetectorSegment(text=value, start=start, end=end)
                for value, start, end in segments
            ]

        starts = [
            re.findall(r"[A-Za-z]+", value.strip().lower())[:1][0]
            for value, _, _ in segments
            if re.findall(r"[A-Za-z]+", value.strip())
        ]
        repeated_starts = {word for word in starts if starts.count(word) > 1}
        word_lengths = [len(re.findall(r"\b[A-Za-z0-9'-]+\b", value)) for value, _, _ in segments]
        median_length = sorted(word_lengths)[len(word_lengths) // 2]
        analyzed: List[DetectorSegment] = []
        flagged_words = 0

        for value, start, end in segments:
            reasons: List[str] = []
            lower = value.lower()
            for pattern, reason in self.BOILERPLATE_PATTERNS:
                if pattern.search(lower):
                    reasons.append(reason)
            first_word_match = re.search(r"[A-Za-z]+", value)
            if first_word_match and first_word_match.group(0).lower() in repeated_starts:
                reasons.append("repeated sentence opening")
            sentence_word_count = len(re.findall(r"\b[A-Za-z0-9'-]+\b", value))
            if sentence_word_count == median_length and len(word_lengths) >= 5:
                reasons.append("uniform sentence length")

            score = len(reasons)
            flagged = score >= 2
            if flagged:
                flagged_words += sentence_word_count
            analyzed.append(DetectorSegment(
                text=value,
                start=start,
                end=end,
                flagged=flagged,
                signal_score=score,
                reasons=reasons,
            ))

        likelihood = round((flagged_words / max(1, word_count)) * 100)
        return max(0, min(100, likelihood)), "ready", analyzed

    def analyze(self, text: str) -> AnalysisResponse:
        """Perform comprehensive analysis of input document."""
        metrics = compute_text_metrics(text)
        protected_spans = self.extract_protected_spans(text)
        paragraphs = metrics.paragraph_count
        sentences = metrics.sentence_count
        ai_likelihood_percent, detector_status, detector_segments = self.detect_linguistic_signals(text)

        return AnalysisResponse(
            metrics=metrics,
            protected_spans=protected_spans,
            paragraphs=paragraphs,
            sentences=sentences,
            detected_language=metrics.detected_language,
            ai_likelihood_percent=ai_likelihood_percent,
            detector_status=detector_status,
            detector_segments=detector_segments,
        )


# Global analyzer singleton
_analyzer_instance = DocumentAnalyzer()


def get_analyzer() -> DocumentAnalyzer:
    """Return default DocumentAnalyzer instance."""
    return _analyzer_instance
