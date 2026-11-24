"""Legacy compatibility entry point for NapsterTec Text Intelligence Engine.

Preserves compatibility with previous function names and CLI invocations while
replacing destructive random edits and misleading detector scores with safe,
reliable, and transparent text refinement.
"""

import sys
import argparse
import warnings
from typing import Dict, Any, Optional

from core.schemas import RewriteRequest, EditingMode, EditingIntensity
from core.orchestrator import get_orchestrator
from editing.deterministic_tools import deterministic_basic_polish, calculate_legacy_score


def humanize_text(text: str, intensity: str = "balanced", mode: str = "natural") -> str:
    """Legacy helper: Refines text for natural flow and readability.

    Note: Random synonym replacement and phrase deletions are disabled by default
    to prevent semantic corruption. Uses the modern text intelligence orchestrator.
    """
    warnings.warn(
        "humanize_text is deprecated. Use core.orchestrator.RewriteOrchestrator.rewrite instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    # Map intensity string
    intensity_map = {
        "light": EditingIntensity.LIGHT,
        "balanced": EditingIntensity.BALANCED,
        "substantial": EditingIntensity.SUBSTANTIAL,
        "high": EditingIntensity.SUBSTANTIAL,
    }
    mode_map = {
        "natural": EditingMode.NATURAL,
        "fluent": EditingMode.NATURAL,
        "proofread": EditingMode.PROOFREAD,
        "clarity": EditingMode.CLARITY,
        "professional": EditingMode.PROFESSIONAL,
        "academic": EditingMode.ACADEMIC,
        "conversational": EditingMode.CONVERSATIONAL,
        "concise": EditingMode.CONCISE,
        "simplify": EditingMode.SIMPLIFY,
        "legacy": EditingMode.LEGACY,
    }

    selected_intensity = intensity_map.get(intensity.lower(), EditingIntensity.BALANCED)
    selected_mode = mode_map.get(mode.lower(), EditingMode.NATURAL)

    orchestrator = get_orchestrator()
    req = RewriteRequest(
        text=text,
        mode=selected_mode,
        intensity=selected_intensity,
        fallback_to_local=True,
    )
    response = orchestrator.rewrite(req)
    return response.revised_text


def calculate_score(text: str) -> Dict[str, Any]:
    """Legacy helper: Calculates descriptive readability metrics.

    Note: Replaces legacy detector-evasion heuristics with objective readability metrics.
    """
    return calculate_legacy_score(text)


def process_text(text: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Legacy helper: Processes text and returns result with metrics."""
    opts = options or {}
    intensity = opts.get("intensity", "balanced")
    mode = opts.get("mode", "natural")

    revised = humanize_text(text, intensity=intensity, mode=mode)
    score = calculate_score(revised)

    return {
        "original_text": text,
        "revised_text": revised,
        "metrics": score,
        "notice": "Transformed safely via NapsterTec Text Intelligence Engine.",
    }


def main():
    """CLI entry point for legacy script."""
    parser = argparse.ArgumentParser(
        description="NapsterTec Text Intelligence — Legacy Compatibility CLI"
    )
    parser.add_argument("input_text", nargs="?", help="Input text to edit (or pass via stdin)")
    parser.add_argument("--mode", default="natural", choices=["proofread", "clarity", "natural", "professional", "academic", "conversational", "concise", "simplify", "legacy"], help="Editing mode")
    parser.add_argument("--intensity", default="balanced", choices=["light", "balanced", "substantial"], help="Editing intensity")
    parser.add_argument("--score-only", action="store_true", help="Calculate readability score without rewriting")

    args = parser.parse_args()

    input_text = args.input_text
    if not input_text:
        if not sys.stdin.isatty():
            input_text = sys.stdin.read()
        else:
            print("Error: No input text provided. Provide text as argument or pipe via stdin.", file=sys.stderr)
            sys.exit(1)

    if args.score_only:
        score = calculate_score(input_text)
        print(f"Readability Index: {score['clarity_index']}/100")
        print(f"Flesch Reading Ease: {score['flesch_reading_ease']}")
        print(f"Flesch-Kincaid Grade: {score['flesch_kincaid_grade']}")
        print(f"Lexical Diversity: {score['lexical_diversity']}")
        print(f"Note: {score['notice']}")
        sys.exit(0)

    revised = humanize_text(input_text, intensity=args.intensity, mode=args.mode)
    print(revised)


if __name__ == "__main__":
    main()
