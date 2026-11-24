"""Application configuration module."""

import os
from typing import Optional
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class AppConfig:
    """Strongly typed application configuration."""
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "5000")))
    host: str = field(default_factory=lambda: os.getenv("HOST", "127.0.0.1"))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() in ("true", "1", "yes"))

    # Provider configuration
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "mock").lower())
    llm_api_key: Optional[str] = field(default_factory=lambda: os.getenv("LLM_API_KEY"))
    llm_base_url: str = field(default_factory=lambda: os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1"))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "anthropic/claude-3.5-sonnet"))
    llm_timeout_seconds: int = field(default_factory=lambda: int(os.getenv("LLM_TIMEOUT_SECONDS", "30")))
    llm_max_retries: int = field(default_factory=lambda: int(os.getenv("LLM_MAX_RETRIES", "2")))

    # Security limits
    max_input_chars: int = field(default_factory=lambda: int(os.getenv("MAX_INPUT_CHARS", "15000")))
    rate_limit_per_minute: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")))

    # Logging and privacy
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())
    log_raw_user_text: bool = field(
        default_factory=lambda: os.getenv("LOG_RAW_USER_TEXT", "false").lower() in ("true", "1")
    )

    def validate(self) -> None:
        """Validate critical configuration invariants."""
        if self.max_input_chars <= 0:
            raise ValueError(f"MAX_INPUT_CHARS must be positive, got {self.max_input_chars}")
        if self.llm_timeout_seconds <= 0:
            raise ValueError(f"LLM_TIMEOUT_SECONDS must be positive, got {self.llm_timeout_seconds}")
        if self.rate_limit_per_minute <= 0:
            raise ValueError(f"RATE_LIMIT_PER_MINUTE must be positive, got {self.rate_limit_per_minute}")
        if self.llm_provider not in ("mock", "openai", "openrouter", "custom", "none", "local"):
            raise ValueError(f"Unsupported LLM_PROVIDER: {self.llm_provider}")

    def safe_dict(self) -> dict:
        """Return non-sensitive config dict safe for logging and client diagnostic display."""
        return {
            "app_env": self.app_env,
            "port": self.port,
            "host": self.host,
            "debug": self.debug,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "llm_base_url": self.llm_base_url,
            "llm_timeout_seconds": self.llm_timeout_seconds,
            "has_api_key": bool(self.llm_api_key and self.llm_api_key.strip()),
            "max_input_chars": self.max_input_chars,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "log_raw_user_text": self.log_raw_user_text,
        }


# Global singleton instance
_config_instance: Optional[AppConfig] = None


def get_config(reload: bool = False) -> AppConfig:
    """Return initialized AppConfig instance."""
    global _config_instance
    if _config_instance is None or reload:
        cfg = AppConfig()
        cfg.validate()
        _config_instance = cfg
    return _config_instance
