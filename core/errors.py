"""Exception hierarchy for NapsterTec Text Intelligence Engine."""

from typing import Optional, Dict, Any


class TextIntelligenceError(Exception):
    """Base exception for all Text Intelligence Engine errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigError(TextIntelligenceError):
    """Raised when configuration is invalid or required settings are missing."""
    pass


class ValidationError(TextIntelligenceError):
    """Raised when input validation fails."""
    pass


class EmptyInputError(ValidationError):
    """Raised when provided input text is empty or only whitespace."""
    pass


class InputTooLargeError(ValidationError):
    """Raised when provided input exceeds configured MAX_INPUT_CHARS."""
    pass


class UnsupportedModeError(ValidationError):
    """Raised when an unrecognized editing mode is requested."""
    pass


class ProviderError(TextIntelligenceError):
    """Base exception for external LLM provider failures."""

    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.status_code = status_code


class ProviderMissingKeyError(ProviderError):
    """Raised when an LLM provider is requested but API credentials are not set."""
    pass


class ProviderTimeoutError(ProviderError):
    """Raised when an LLM provider request times out."""
    pass


class ProviderRateLimitError(ProviderError):
    """Raised when an LLM provider returns a 429 rate limit response."""
    pass


class ProviderResponseError(ProviderError):
    """Raised when an LLM provider returns an invalid or malformed response."""
    pass


class QualityValidationError(TextIntelligenceError):
    """Raised when output fails quality or safety validation checks."""
    pass
