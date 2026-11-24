"""Deterministic mock LLM provider for local execution and offline testing."""

import re
from typing import Dict, Any, Optional
from providers.base import BaseLLMProvider
from editing.deterministic_tools import deterministic_basic_polish, fix_punctuation_spacing


class MockLLMProvider(BaseLLMProvider):
    """Mock provider executing deterministic text improvements without external API dependencies."""

    def __init__(self, model: str = "mock-model-v1", timeout_seconds: int = 30):
        super().__init__(model=model, timeout_seconds=timeout_seconds)
        self.canned_response: Optional[str] = None
        self.simulate_error: Optional[Exception] = None

    @property
    def provider_name(self) -> str:
        return "mock"

    def set_canned_response(self, text: Optional[str]) -> None:
        """Set an explicit canned response for test verification."""
        self.canned_response = text

    def set_simulate_error(self, error: Optional[Exception]) -> None:
        """Set an exception to simulate provider failure in tests."""
        self.simulate_error = error

    def generate(
        self,
        prompt: str,
        system_instruction: str,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        if self.simulate_error:
            raise self.simulate_error

        if self.canned_response is not None:
            return self.canned_response

        # Extract source text from untrusted text delimiters if present
        match = re.search(r'<untrusted_user_text>\n?([\s\S]*?)\n?</untrusted_user_text>', prompt)
        source = match.group(1).replace(r"<\/", "</") if match else prompt

        # Perform realistic mock editing according to instructions
        # Apply deterministic polish (typos, punctuation, whitespace)
        refined = deterministic_basic_polish(source)

        # If instructions indicate Concise, remove common filler phrases
        if "concise" in system_instruction.lower():
            fillers = [
                r"\bin order to\b",
                r"\bdue to the fact that\b",
                r"\bat the present time\b",
                r"\bfor the purpose of\b",
            ]
            replacements = ["to", "because", "currently", "to"]
            for f, r in zip(fillers, replacements):
                refined = re.sub(f, r, refined, flags=re.IGNORECASE)

        # If instructions indicate Academic or Professional, expand contractions
        if "academic" in system_instruction.lower() or "professional" in system_instruction.lower():
            from editing.deterministic_tools import adjust_contractions
            refined = adjust_contractions(refined, expand=True)

        return refined
