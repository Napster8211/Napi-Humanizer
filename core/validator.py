"""Input and output validation, protected span verification, and change summary."""

import re
import difflib
from typing import List, Tuple
from core.schemas import RewriteRequest, ProtectedSpan, ChangeSummary
from core.errors import EmptyInputError, InputTooLargeError, WordLimitError, ValidationError


class OutputValidator:
    """Validates rewritten text against source integrity constraints."""

    def validate_input(self, request: RewriteRequest, max_chars: int, max_words: int = 500) -> None:
        """Validate input text size and presence."""
        if not request.text or not request.text.strip():
            raise EmptyInputError("Input text must not be empty or whitespace-only.")
        if len(request.text) > max_chars:
            raise InputTooLargeError(
                f"Input text exceeds maximum allowed length of {max_chars} characters (received {len(request.text)})."
            )
        word_count = len(request.text.split())
        if word_count > max_words:
            raise WordLimitError(f"Please keep each run under {max_words} words.")

    def verify_protected_spans(self, original_text: str, revised_text: str, spans: List[ProtectedSpan]) -> List[str]:
        """Check whether critical protected entities from original text persist in revised text."""
        warnings: List[str] = []
        for span in spans:
            # Check if entity text appears in revised text
            # For numbers and dates, exact presence is checked
            if span.span_type in ("url", "citation", "code", "date", "email"):
                if span.text not in revised_text:
                    warnings.append(f"Protected {span.span_type} may have been altered or omitted: '{span.text}'")
            elif span.span_type == "number":
                # Check for number with word boundary
                escaped = re.escape(span.text)
                if not re.search(r'(?:\b|\A)' + escaped + r'(?:\b|\Z)', revised_text):
                    warnings.append(f"Protected number may have been altered or omitted: '{span.text}'")
        return warnings

    def verify_formatting_integrity(self, original_text: str, revised_text: str) -> List[str]:
        """Verify markdown code fence and heading integrity."""
        warnings: List[str] = []

        # Check code fence balance
        orig_fences = len(re.findall(r'```', original_text))
        rev_fences = len(re.findall(r'```', revised_text))
        if rev_fences % 2 != 0:
            warnings.append("Revised text contains unclosed markdown code blocks (odd number of ```).")
        if orig_fences > 0 and rev_fences == 0:
            warnings.append("Markdown code blocks present in original text were not retained in revision.")

        return warnings

    def compute_change_summary(self, original_text: str, revised_text: str) -> ChangeSummary:
        """Calculate word level diff statistics and summary of changes."""
        orig_words = original_text.split()
        rev_words = revised_text.split()

        matcher = difflib.SequenceMatcher(None, orig_words, rev_words)
        added = 0
        removed = 0
        modifications: List[str] = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                removed += (i2 - i1)
                added += (j2 - j1)
                if len(modifications) < 5:
                    old_phrase = " ".join(orig_words[i1:min(i1+3, i2)])
                    new_phrase = " ".join(rev_words[j1:min(j1+3, j2)])
                    modifications.append(f"Rephrased '{old_phrase}' -> '{new_phrase}'")
            elif tag == 'delete':
                removed += (i2 - i1)
                if len(modifications) < 5:
                    del_phrase = " ".join(orig_words[i1:min(i1+3, i2)])
                    modifications.append(f"Removed '{del_phrase}'")
            elif tag == 'insert':
                added += (j2 - j1)
                if len(modifications) < 5:
                    ins_phrase = " ".join(rev_words[j1:min(j1+3, j2)])
                    modifications.append(f"Added '{ins_phrase}'")

        net_change = added - removed

        return ChangeSummary(
            added_words=added,
            removed_words=removed,
            net_word_change=net_change,
            key_modifications=modifications,
        )


# Global validator singleton
_validator_instance = OutputValidator()


def get_validator() -> OutputValidator:
    """Return default OutputValidator instance."""
    return _validator_instance
