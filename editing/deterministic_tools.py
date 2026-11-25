"""Safe deterministic editing tools and local fallback transformations."""

import re
from typing import Any, Dict, Iterable

from core.metrics import compute_text_metrics
from core.schemas import EditingMode, RewriteRequest


COMMON_TYPOS: Dict[str, str] = {
    r"\bteh\b": "the", r"\brecieve\b": "receive", r"\bseperate\b": "separate",
    r"\boccured\b": "occurred", r"\buntill\b": "until", r"\bdefinately\b": "definitely",
    r"\baccomodate\b": "accommodate", r"\bacheive\b": "achieve", r"\bcalender\b": "calendar",
    r"\bwich\b": "which", r"\brecieved\b": "received", r"\bpublically\b": "publicly",
}

CONTRACTION_EXPANSIONS: Dict[str, str] = {
    r"\bdon't\b": "do not", r"\bdoesn't\b": "does not", r"\bdidn't\b": "did not",
    r"\bcan't\b": "cannot", r"\bcouldn't\b": "could not", r"\bwon't\b": "will not",
    r"\bwouldn't\b": "would not", r"\bshouldn't\b": "should not", r"\bisn't\b": "is not",
    r"\baren't\b": "are not", r"\bwasn't\b": "was not", r"\bweren't\b": "were not",
    r"\bhasn't\b": "has not", r"\bhaven't\b": "have not", r"\bhadn't\b": "had not",
    r"\bit's\b": "it is", r"\bthat's\b": "that is", r"\bwhat's\b": "what is",
    r"\bthere's\b": "there is", r"\bhere's\b": "here is",
}

CONTRACTION_CONTRACTIONS: Dict[str, str] = {value: key.strip(r"\b") for key, value in CONTRACTION_EXPANSIONS.items()}

PHRASE_POLISH: Dict[str, str] = {
    r"\bin order to\b": "to", r"\bdue to the fact that\b": "because",
    r"\bat this point in time\b": "now", r"\ba large number of\b": "many",
    r"\bfor the purpose of\b": "to", r"\bin the event that\b": "if",
    r"\bhas the ability to\b": "can", r"\bmake use of\b": "use",
    r"\bmore easier\b": "easier", r"\bmost easiest\b": "easiest",
    r"\bvery unique\b": "unique", r"\bfirst and foremost\b": "first",
}

GRAMMAR_RULES: Dict[str, str] = {
    r"\b(company|team|platform|system|tool|experience) have\b": r"\1 has",
    r"\b(company|team|platform|system|tool|experience) help\b": r"\1 helps",
    r"\b(that|which) help\b": r"\1 helps",
    r"\b(tools|features|systems|companies) is\b": r"\1 are",
    r"\b(which|that) is designed\b": r"that are designed",
    r"\b(one of the) (\w+) are\b": r"\1 \2 is",
}


def normalize_whitespace(text: str) -> str:
    """Normalize excess whitespace while preserving paragraph structure."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned_lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(cleaned_lines)).strip()


def fix_punctuation_spacing(text: str) -> str:
    """Fix common spacing around punctuation without corrupting URLs or code."""
    placeholders: Dict[str, str] = {}
    counter = 0

    def mask(match):
        nonlocal counter
        placeholder = f"__PROTECTED_SPAN_{counter}__"
        placeholders[placeholder] = match.group(0)
        counter += 1
        return placeholder

    masked = re.sub(r"```[\s\S]*?```|`[^`\n]+`|https?://[^\s<>\')]+|www\.[^\s<>\')]+", mask, text)
    masked = re.sub(r"\s+([,.?!;:])", r"\1", masked)
    masked = re.sub(r"([,.?!;:])([A-Za-z])", r"\1 \2", masked)
    masked = re.sub(r"([,?!;:]){2,}", r"\1", masked)
    masked = re.sub(r"\b([A-Za-z]+)\s+\1\b", r"\1", masked, flags=re.IGNORECASE)
    for placeholder, original in placeholders.items():
        masked = masked.replace(placeholder, original)
    return masked


def correct_common_typos(text: str) -> str:
    for pattern, replacement in COMMON_TYPOS.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def adjust_contractions(text: str, expand: bool = False) -> str:
    rules = CONTRACTION_EXPANSIONS if expand else CONTRACTION_CONTRACTIONS
    for pattern, replacement in rules.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def _apply_rules(text: str, rules: Dict[str, str]) -> str:
    for pattern, replacement in rules.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def _capitalise_sentences(text: str) -> str:
    return re.sub(r"(^|[.!?]\s+)([a-z])", lambda match: match.group(1) + match.group(2).upper(), text)


def deterministic_basic_polish(text: str) -> str:
    """Apply safe baseline spelling, grammar-adjacent, and punctuation polish."""
    if not text or not text.strip():
        return ""
    polished = normalize_whitespace(text)
    polished = correct_common_typos(polished)
    polished = _apply_rules(polished, PHRASE_POLISH)
    polished = _apply_rules(polished, GRAMMAR_RULES)
    return fix_punctuation_spacing(polished)


def _sentence_list(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]


def deterministic_tool_rewrite(request: RewriteRequest, text: str) -> str:
    """Provide useful, explicitly limited local editing when no LLM is available."""
    result = _capitalise_sentences(deterministic_basic_polish(text))
    mode = request.mode
    if mode == EditingMode.PROOFREAD:
        return result
    if mode == EditingMode.CLARITY:
        return _apply_rules(result, PHRASE_POLISH)
    if mode == EditingMode.NATURAL:
        result = _apply_rules(result, {r"\butilize\b": "use", r"\bcommence\b": "start", r"\bapproximately\b": "about"})
        return adjust_contractions(result, expand=False)
    if mode == EditingMode.PROFESSIONAL:
        result = adjust_contractions(result, expand=True)
        return _apply_rules(result, {r"\bget\b": "receive", r"\ba lot of\b": "many", r"\bkind of\b": "somewhat"})
    if mode == EditingMode.ACADEMIC:
        return adjust_contractions(result, expand=True)
    if mode == EditingMode.CONVERSATIONAL:
        return adjust_contractions(result, expand=False)
    if mode == EditingMode.SIMPLIFY:
        return _apply_rules(result, {
            r"\bapproximately\b": "about", r"\bsubsequently\b": "later", r"\bcommence\b": "start",
            r"\bdemonstrate\b": "show", r"\badditional\b": "more", r"\bfrequently\b": "often",
        })
    if mode == EditingMode.CONCISE:
        result = _apply_rules(result, PHRASE_POLISH)
        result = re.sub(r"\b(really|very|just|basically|actually)\s+", "", result, flags=re.IGNORECASE)
        return result
    if mode == EditingMode.CUSTOM:
        return result
    return result


def calculate_legacy_score(text: str) -> Dict[str, Any]:
    metrics = compute_text_metrics(text)
    ease = metrics.flesch_reading_ease
    variety = min(100.0, metrics.lexical_diversity * 120.0)
    return {
        "clarity_index": round((ease * 0.6) + (variety * 0.4), 1),
        "flesch_reading_ease": metrics.flesch_reading_ease,
        "flesch_kincaid_grade": metrics.flesch_kincaid_grade,
        "lexical_diversity": metrics.lexical_diversity,
        "avg_sentence_length": metrics.avg_sentence_length,
        "word_count": metrics.word_count,
        "notice": "Descriptive writing metric only. Does not measure or predict AI detection.",
    }
