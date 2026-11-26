"""Bounded sentence-aware chunking for provider rewrite requests."""

import re
from typing import List

_WORD_RE = re.compile(r"\S+")
_SENTENCE_RE = re.compile(r".+?(?:[.!?]+(?=\s|$)|$)", re.DOTALL)


def _word_count(value: str) -> int:
    return len(_WORD_RE.findall(value))


def split_for_rewrite(text: str, max_words: int = 350) -> List[str]:
    """Split text at paragraph then sentence boundaries, capped by word count."""
    if _word_count(text) <= max_words:
        return [text]

    chunks: List[str] = []
    current = ""

    def flush() -> None:
        nonlocal current
        if current.strip():
            chunks.append(current)
        current = ""

    # Keep blank-line paragraph boundaries in the stream instead of flattening the text.
    for paragraph in re.split(r"(\n\s*\n)", text):
        if not paragraph:
            continue
        if paragraph.isspace() and "\n" in paragraph:
            if current and not current.endswith("\n"):
                current += paragraph
            continue

        sentences = _SENTENCE_RE.findall(paragraph) or [paragraph]
        for sentence in sentences:
            if _word_count(sentence) > max_words:
                words = sentence.split()
                for start in range(0, len(words), max_words):
                    piece = " ".join(words[start:start + max_words])
                    if _word_count(current) + _word_count(piece) > max_words:
                        flush()
                    current += piece + " "
                continue
            if current and _word_count(current) + _word_count(sentence) > max_words:
                flush()
            current += sentence
    flush()
    return chunks or [text]
