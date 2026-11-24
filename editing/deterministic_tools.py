"""Safe deterministic editing tools and local fallback transformations."""

import re
from typing import Any, List, Dict, Tuple
from core.schemas import TextMetrics
from core.metrics import compute_text_metrics


# Common typographical slips and contractions
COMMON_TYPOS: Dict[str, str] = {
    r"\bteh\b": "the",
    r"\brecieve\b": "receive",
    r"\bseperate\b": "separate",
    r"\boccured\b": "occurred",
    r"\buntill\b": "until",
    r"\bdefinately\b": "definitely",
    r"\baccomodate\b": "accommodate",
    r"\bacheive\b": "achieve",
    r"\bcalender\b": "calendar",
}

CONTRACTION_EXPANSIONS: Dict[str, str] = {
    r"\bdon't\b": "do not",
    r"\bdoesn't\b": "does not",
    r"\bdidn't\b": "did not",
    r"\bcan't\b": "cannot",
    r"\bcouldn't\b": "could not",
    r"\bwon't\b": "will not",
    r"\bwouldn't\b": "would not",
    r"\bshouldn't\b": "should not",
    r"\bisn't\b": "is not",
    r"\baren't\b": "are not",
    r"\bwasn't\b": "was not",
    r"\bweren't\b": "were not",
    r"\bhasn't\b": "has not",
    r"\bhaven't\b": "have not",
    r"\bhadn't\b": "had not",
    r"\bit's\b": "it is",
    r"\bthat's\b": "that is",
    r"\bwhat's\b": "what is",
    r"\bthere's\b": "there is",
    r"\bhere's\b": "here is",
}

CONTRACTION_CONTRACTIONS: Dict[str, str] = {
    r"\bdo not\b": "don't",
    r"\bdoes not\b": "doesn't",
    r"\bdid not\b": "didn't",
    r"\bcannot\b": "can't",
    r"\bcould not\b": "couldn't",
    r"\bwill not\b": "won't",
    r"\bwould not\b": "wouldn't",
    r"\bshould not\b": "shouldn't",
    r"\bis not\b": "isn't",
    r"\bare not\b": "aren't",
    r"\bwas not\b": "wasn't",
    r"\bwere not\b": "weren't",
    r"\bhas not\b": "hasn't",
    r"\bhave not\b": "haven't",
    r"\bhad not\b": "hadn't",
    r"\bit is\b": "it's",
    r"\bthat is\b": "that's",
    r"\bwhat is\b": "what's",
    r"\bthere is\b": "there's",
}


def normalize_whitespace(text: str) -> str:
    """Normalize excess whitespace while preserving paragraph structure and indents."""
    # Normalize Windows CRLF to LF
    text = text.replace("\r\n", "\n")
    # Clean multiple spaces on single lines without damaging newlines
    lines = text.split("\n")
    cleaned_lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in lines]
    # Keep at most two consecutive newlines
    result = "\n".join(cleaned_lines)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()


def fix_punctuation_spacing(text: str) -> str:
    """Fix common spacing around punctuation marks without corrupting URLs or code."""
    # Mask URLs and code blocks first so colons and dots inside them are not corrupted
    placeholders: Dict[str, str] = {}
    counter = 0

    def mask(match):
        nonlocal counter
        ph = f"__PROTECTED_SPAN_{counter}__"
        placeholders[ph] = match.group(0)
        counter += 1
        return ph

    # Protect code and URLs
    masked_text = re.sub(r'```[\s\S]*?```|`[^`\n]+`|https?://[^\s<>"\')]+|www\.[^\s<>"\')]+', mask, text)

    # Remove space before punctuation marks: , . ! ? ; :
    masked_text = re.sub(r'\s+([,.\?!;:])', r'\1', masked_text)
    # Ensure a single space after punctuation when followed by a word character
    masked_text = re.sub(r'([,.\?!;:])([A-Za-z])', r'\1 \2', masked_text)
    # Clean repeated punctuation (except ellipsis ...)
    masked_text = re.sub(r'([,\?!;:]){2,}', r'\1', masked_text)
    # Remove accidental repeated words e.g. "the the"
    masked_text = re.sub(r'\b([A-Za-z]+)\s+\1\b', r'\1', masked_text, flags=re.IGNORECASE)

    # Restore placeholders
    for ph, orig in placeholders.items():
        masked_text = masked_text.replace(ph, orig)

    return masked_text


def correct_common_typos(text: str) -> str:
    """Correct obvious typographical errors using regex dictionary."""
    for pattern, replacement in COMMON_TYPOS.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def adjust_contractions(text: str, expand: bool = False) -> str:
    """Safely expand or contract common English phrases."""
    rules = CONTRACTION_EXPANSIONS if expand else CONTRACTION_CONTRACTIONS
    for pattern, replacement in rules.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def deterministic_basic_polish(text: str) -> str:
    """Apply safe deterministic baseline polish without external LLM calls.

    Steps:
    1. Whitespace normalization
    2. Typo correction
    3. Punctuation spacing cleanup
    """
    if not text or not text.strip():
        return ""

    polished = normalize_whitespace(text)
    polished = correct_common_typos(polished)
    polished = fix_punctuation_spacing(polished)
    return polished


def calculate_legacy_score(text: str) -> Dict[str, Any]:
    """Calculate descriptive readability and sentence metrics.

    Note: This replaces the legacy detector score. Heuristic values describe
    sentence variation and lexical statistics, never AI detection probability.
    """
    metrics = compute_text_metrics(text)
    # Compute descriptive score based on balanced reading ease and sentence diversity
    # Scaled 0 to 100 for descriptive readability
    ease = metrics.flesch_reading_ease
    variety = min(100.0, metrics.lexical_diversity * 120.0)
    composite_clarity = round((ease * 0.6) + (variety * 0.4), 1)

    return {
        "clarity_index": composite_clarity,
        "flesch_reading_ease": metrics.flesch_reading_ease,
        "flesch_kincaid_grade": metrics.flesch_kincaid_grade,
        "lexical_diversity": metrics.lexical_diversity,
        "avg_sentence_length": metrics.avg_sentence_length,
        "word_count": metrics.word_count,
        "notice": "Descriptive writing metric only. Does not measure or predict AI detection.",
    }
