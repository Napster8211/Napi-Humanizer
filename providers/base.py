"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Iterator


class BaseLLMProvider(ABC):
    """Abstract interface for LLM provider adapters."""

    def __init__(self, model: str, timeout_seconds: int = 30):
        self.model = model
        self.timeout_seconds = timeout_seconds

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider service."""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_instruction: str,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """Generate response text for prompt and system instruction."""
        pass

    def generate_stream(
        self,
        prompt: str,
        system_instruction: str,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> Iterator[str]:
        """Yield response chunks for prompt and system instruction."""
        full_text = self.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        # Default fallback chunk generator by words/spaces
        words = full_text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
