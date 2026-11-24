"""Text intelligence metrics calculation module."""

import re
import math
from typing import List, Tuple
from core.schemas import TextMetrics, TokenUsage


# Common language stopword signatures
LANGUAGE_SIGNATURES = {
    "es": {"el", "la", "de", "que", "y", "en", "un", "ser", "se", "no", "haber", "por", "con", "para"},
    "fr": {"le", "la", "de", "et", "un", "une", "dans", "pour", "que", "qui", "sur", "avec", "est"},
    "de": {"der", "die", "das", "und", "in", "den", "von", "zu", "mit", "sich", "auf", "fuer", "ist"},
    "it": {"il", "lo", "la", "di", "e", "in", "un", "una", "per", "con", "che", "del", "della"},
    "en": {"the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it", "for", "not", "on", "with"},
}


def detect_language(text: str) -> str:
    """Detect dominant natural language based on frequency of common function words."""
    words = [w.lower() for w in re.findall(r"\b[A-Za-zÀ-ÿ]+\b", text)]
    if not words:
        return "en"

    word_set = set(words)
    best_lang = "en"
    best_overlap = 0

    for lang, stopwords in LANGUAGE_SIGNATURES.items():
        overlap = len(word_set & stopwords)
        if overlap > best_overlap:
            best_overlap = overlap
            best_lang = lang

    return best_lang


def estimate_tokens_and_cost(prompt_text: str, completion_text: str) -> TokenUsage:
    """Estimate token usage and cost (~4 chars per token)."""
    prompt_tokens = max(1, math.ceil(len(prompt_text) / 4.0)) if prompt_text else 0
    completion_tokens = max(1, math.ceil(len(completion_text) / 4.0)) if completion_text else 0
    total_tokens = prompt_tokens + completion_tokens

    # Standard model tier pricing estimate: $3 / 1M prompt, $15 / 1M completion
    prompt_cost = (prompt_tokens / 1_000_000.0) * 3.0
    completion_cost = (completion_tokens / 1_000_000.0) * 15.0
    estimated_cost_usd = round(prompt_cost + completion_cost, 6)

    return TokenUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_cost_usd=estimated_cost_usd,
    )


def count_syllables_in_word(word: str) -> int:
    """Estimate syllable count in a single English word deterministically."""
    word = word.lower().strip()
    if not word:
        return 0
    if len(word) <= 3:
        return 1

    # Remove non-alphabetic endings
    word = re.sub(r'(?:[^laeiouy]|ed|es|e)$', '', word)
    if not word:
        return 1

    syllables = len(re.findall(r'[aeiouy]{1,2}', word))
    return max(1, syllables)


def compute_text_metrics(text: str) -> TextMetrics:
    """Compute structural and readability metrics for input text.

    All scores are descriptive readability indicators.
    They must never be used to represent AI/human authorship probabilities.
    """
    if not text or not text.strip():
        return TextMetrics(
            char_count=0,
            word_count=0,
            sentence_count=0,
            paragraph_count=0,
            avg_sentence_length=0.0,
            avg_word_length=0.0,
            flesch_reading_ease=0.0,
            flesch_kincaid_grade=0.0,
            lexical_diversity=0.0,
            reading_time_minutes=0.0,
            detected_language="en",
        )

    clean_text = text.strip()
    char_count = len(clean_text)

    # Detect language
    lang = detect_language(clean_text)

    # Paragraph count
    paragraphs = [p for p in re.split(r'\n\s*\n', clean_text) if p.strip()]
    paragraph_count = max(1, len(paragraphs))

    # Sentence splitting (handling abbreviations, numbers, etc.)
    sentence_matches = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9"\'])', clean_text)
    sentence_count = max(1, len([s for s in sentence_matches if s.strip()]))

    # Words
    words = re.findall(r"\b[A-Za-z0-9'-]+\b", clean_text)
    word_count = len(words)

    if word_count == 0:
        return TextMetrics(
            char_count=char_count,
            word_count=0,
            sentence_count=sentence_count,
            paragraph_count=paragraph_count,
            avg_sentence_length=0.0,
            avg_word_length=0.0,
            flesch_reading_ease=0.0,
            flesch_kincaid_grade=0.0,
            lexical_diversity=0.0,
            reading_time_minutes=0.0,
            detected_language=lang,
        )

    # Word lengths
    total_word_chars = sum(len(w) for w in words)
    avg_word_length = round(total_word_chars / word_count, 2)

    # Sentence lengths
    avg_sentence_length = round(word_count / sentence_count, 2)

    # Syllables
    total_syllables = sum(count_syllables_in_word(w) for w in words)
    syllables_per_word = total_syllables / word_count

    # Flesch Reading Ease: 206.835 - 1.015 * (words/sentence) - 84.6 * (syllables/word)
    fre = 206.835 - (1.015 * avg_sentence_length) - (84.6 * syllables_per_word)
    flesch_reading_ease = round(max(0.0, min(100.0, fre)), 1)

    # Flesch-Kincaid Grade Level: 0.39 * (words/sentence) + 11.8 * (syllables/word) - 15.59
    fkgl = (0.39 * avg_sentence_length) + (11.8 * syllables_per_word) - 15.59
    flesch_kincaid_grade = round(max(0.0, min(18.0, fkgl)), 1)

    # Lexical diversity (Type-Token Ratio)
    unique_words = set(w.lower() for w in words)
    lexical_diversity = round(len(unique_words) / word_count, 3)

    # Estimated reading time (average 200 words per minute)
    reading_time_minutes = round(word_count / 200.0, 2)

    return TextMetrics(
        char_count=char_count,
        word_count=word_count,
        sentence_count=sentence_count,
        paragraph_count=paragraph_count,
        avg_sentence_length=avg_sentence_length,
        avg_word_length=avg_word_length,
        flesch_reading_ease=flesch_reading_ease,
        flesch_kincaid_grade=flesch_kincaid_grade,
        lexical_diversity=lexical_diversity,
        reading_time_minutes=reading_time_minutes,
        detected_language=lang,
    )
