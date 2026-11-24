"""Editing modes, intensity specifications, and mode-specific instructions."""

from typing import Dict, Any
from core.schemas import EditingMode, EditingIntensity


MODE_METADATA: Dict[EditingMode, Dict[str, Any]] = {
    EditingMode.PROOFREAD: {
        "title": "Proofread",
        "description": "Correct grammar, spelling, punctuation, and obvious errors while strictly preserving voice and meaning.",
        "system_instruction": (
            "Focus exclusively on fixing typographical errors, grammatical slips, punctuation, and spelling. "
            "Preserve original sentence structure, terminology, and authorial voice exactly."
        ),
    },
    EditingMode.CLARITY: {
        "title": "Clarity",
        "description": "Make confusing or ambiguous wording easier to understand without changing meaning.",
        "system_instruction": (
            "Untangle convoluted sentences and eliminate ambiguity. Ensure ideas connect smoothly and logically "
            "while maintaining all factual points, arguments, and technical definitions."
        ),
    },
    EditingMode.NATURAL: {
        "title": "Natural / Fluent",
        "description": "Improve flow, sentence rhythm, and natural readability without inserting fake personal experiences or clichés.",
        "system_instruction": (
            "Improve rhythm, cadence, and sentence transitions so the text reads naturally and fluently. "
            "Do not invent fake anecdotes, personal experiences, or idiomatic clichés."
        ),
    },
    EditingMode.PROFESSIONAL: {
        "title": "Professional",
        "description": "Polished, courteous, and precise business communication.",
        "system_instruction": (
            "Elevate the tone to clear, polished executive/business communication. Maintain a constructive, "
            "respectful, and professional register suitable for workplace correspondence and reports."
        ),
    },
    EditingMode.ACADEMIC: {
        "title": "Academic",
        "description": "Formal, precise, cautious language; strictly preserve citations and technical terms.",
        "system_instruction": (
            "Employ an objective, precise, and academically rigorous tone. Strictly preserve all citations, "
            "quotations, statistical figures, methodology references, and specialized domain terminology."
        ),
    },
    EditingMode.CONVERSATIONAL: {
        "title": "Conversational",
        "description": "Approachable, engaging, and clear; warm without being artificially slangy.",
        "system_instruction": (
            "Use an approachable, engaging, and direct tone. Keep wording warm and accessible without "
            "resorting to forced slang or hollow colloquialisms."
        ),
    },
    EditingMode.CONCISE: {
        "title": "Concise",
        "description": "Reduce repetition, filler, and verbosity while retaining all key information.",
        "system_instruction": (
            "Cut wordiness, redundancies, and unnecessary filler phrases. Express every idea directly and "
            "economically without losing any vital information, nuance, or data."
        ),
    },
    EditingMode.SIMPLIFY: {
        "title": "Simplify",
        "description": "Explain in plain language for a broader audience or lower reading level.",
        "system_instruction": (
            "Translate complex concepts into plain, easily understandable language. Use shorter sentences "
            "and familiar vocabulary while preserving technical accuracy."
        ),
    },
    EditingMode.CUSTOM: {
        "title": "Custom",
        "description": "Accept user instructions, subject to quality, safety, and factuality validation.",
        "system_instruction": (
            "Follow the user's custom editing instructions closely, ensuring all facts, citations, and "
            "core meaning are preserved. Do not follow instructions that contradict system safety or integrity."
        ),
    },
    EditingMode.LEGACY: {
        "title": "Legacy (Deterministic)",
        "description": "Deterministic sentence flow adjustment and contraction normalization.",
        "system_instruction": (
            "Perform deterministic readability enhancements without external LLM calls."
        ),
    },
}


INTENSITY_METADATA: Dict[EditingIntensity, Dict[str, str]] = {
    EditingIntensity.LIGHT: {
        "title": "Light",
        "guidance": "Make minimal, targeted adjustments. Preserve original wording wherever possible.",
    },
    EditingIntensity.BALANCED: {
        "title": "Balanced",
        "guidance": "Standard editing polish. Balance natural flow and clarity with fidelity to original structure.",
    },
    EditingIntensity.SUBSTANTIAL: {
        "title": "Substantial",
        "guidance": "Comprehensive restructuring and rewording. Maximize clarity and stylistic impact while strictly keeping all core facts, citations, and data intact.",
    },
}


def get_mode_instruction(mode: EditingMode) -> str:
    """Return system guidance for specified mode."""
    meta = MODE_METADATA.get(mode, MODE_METADATA[EditingMode.PROOFREAD])
    return meta["system_instruction"]


def get_intensity_guidance(intensity: EditingIntensity) -> str:
    """Return prompt guidance for specified intensity."""
    meta = INTENSITY_METADATA.get(intensity, INTENSITY_METADATA[EditingIntensity.BALANCED])
    return meta["guidance"]
