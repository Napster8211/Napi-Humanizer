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
            # Check if the exact protected entity survives. A plain substring check
            # is too permissive for a value such as "3" appearing inside "30";
            # word boundaries are too strict for punctuation-bearing values such as
            # "$4,500,000" and "18.5%". Alphanumeric lookarounds handle both cases.
            if span.span_type in ("url", "citation", "code", "date", "email", "quotation"):
                if span.text not in revised_text:
                    warnings.append(f"Protected {span.span_type} may have been altered or omitted: '{span.text}'")
            elif span.span_type == "number":
                escaped = re.escape(span.text)
                if not re.search(r'(?<![A-Za-z0-9])' + escaped + r'(?![A-Za-z0-9])', revised_text):
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

    def quality_warnings(self, original_text: str, revised_text: str, mode: str, intensity: str) -> List[str]:
        """Return quality-gate warnings for substantive rewrites.

        Very short edits and Proofread are intentionally excluded because spelling and
        punctuation fixes should not be forced into an arbitrary rewrite percentage.
        """
        original_words = original_text.split()
        if len(original_words) < 20 or mode == "proofread":
            return []
        revised_words = revised_text.split()
        warnings: List[str] = []
        if mode not in ("concise", "simplify"):
            length_ratio = len(revised_words) / max(1, len(original_words))
            if not 0.70 <= length_ratio <= 1.30:
                warnings.append(f"Output length ratio {length_ratio:.2f} is outside the safe 0.70–1.30 range.")

        summary = self.compute_change_summary(original_text, revised_text)
        changed_ratio = (summary.added_words + summary.removed_words) / max(1, len(original_words))
        bands = {
            "light": (0.10, 0.25),
            "balanced": (0.25, 0.50),
            "substantial": (0.50, 0.75),
        }
        low, high = bands.get(intensity, bands["balanced"])
        if mode not in ("concise", "simplify") and not low <= changed_ratio <= high:
            warnings.append(f"Changed-word ratio {changed_ratio:.2f} is outside the {intensity} target band.")
        return warnings


# Global validator singleton
_validator_instance = OutputValidator()


def get_validator() -> OutputValidator:
    """Return default OutputValidator instance."""
    return _validator_instance
