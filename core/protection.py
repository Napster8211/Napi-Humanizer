"""Reversible protection for factual spans passed through rewrite providers."""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from core.schemas import ProtectedSpan


@dataclass(frozen=True)
class ProtectedPlaceholder:
    token: str
    original: str
    span_type: str


def mask_protected_spans(
    text: str,
    spans: Sequence[ProtectedSpan],
    source_offset: int = 0,
) -> Tuple[str, List[ProtectedPlaceholder], List[ProtectedSpan]]:
    """Replace spans inside ``text`` with ordered placeholders.

    ``source_offset`` maps spans whose offsets refer to a larger source document,
    which is needed for selection-only rewrites.
    """
    selected = [
        span for span in sorted(spans, key=lambda item: item.start)
        if span.start >= source_offset and span.end <= source_offset + len(text)
    ]
    pieces: List[str] = []
    placeholders: List[ProtectedPlaceholder] = []
    prompt_spans: List[ProtectedSpan] = []
    cursor = 0
    for index, span in enumerate(selected, start=1):
        start = span.start - source_offset
        end = span.end - source_offset
        if start < cursor or start < 0 or end > len(text):
            continue
        token = f"⟦P{index}⟧"
        pieces.append(text[cursor:start])
        pieces.append(token)
        cursor = end
        placeholders.append(ProtectedPlaceholder(token, span.text, span.span_type))
        prompt_spans.append(ProtectedSpan(text=token, span_type=span.span_type, start=start, end=start + len(token)))
    pieces.append(text[cursor:])
    return "".join(pieces), placeholders, prompt_spans


def validate_placeholders(text: str, placeholders: Sequence[ProtectedPlaceholder]) -> Optional[str]:
    """Return a safe diagnostic if provider output damages placeholder count/order."""
    expected = [item.token for item in placeholders]
    actual = re.findall(r"⟦P\d+⟧", text)
    if actual != expected:
        return "Protected placeholder order or count changed."
    for token in expected:
        if text.count(token) != 1:
            return f"Protected placeholder {token} was duplicated or omitted."
    return None


def restore_protected_spans(text: str, placeholders: Sequence[ProtectedPlaceholder]) -> str:
    """Restore placeholders after validation has succeeded."""
    restored = text
    for item in placeholders:
        restored = restored.replace(item.token, item.original)
    return restored
