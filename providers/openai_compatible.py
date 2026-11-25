"""OpenAI-compatible and OpenRouter provider adapter."""

import time
import json
import logging
from typing import Dict, Any, Optional, Iterator
import httpx

from providers.base import BaseLLMProvider
from core.errors import (
    ProviderMissingKeyError,
    ProviderTimeoutError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderError,
)

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(BaseLLMProvider):
    """Adapter for OpenAI, OpenRouter, and compatible REST completion endpoints."""

    def __init__(
        self,
        api_key: Optional[str],
        base_url: str = "https://openrouter.ai/api/v1",
        model: str = "anthropic/claude-3.5-sonnet",
        timeout_seconds: int = 30,
        max_retries: int = 2,
    ):
        super().__init__(model=model, timeout_seconds=timeout_seconds)
        self.api_key = api_key
        # Ensure clean trailing slash handling
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries

    @property
    def provider_name(self) -> str:
        if "openrouter" in self.base_url.lower():
            return "openrouter"
        if "openai" in self.base_url.lower():
            return "openai"
        return "openai-compatible"

    def _get_headers(self) -> Dict[str, str]:
        if not self.api_key or not self.api_key.strip():
            raise ProviderMissingKeyError(
                "LLM API key is not configured. Set LLM_API_KEY environment variable or switch to mock/local mode."
            )
        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json",
            "User-Agent": "NapsterTec-Text-Intelligence/1.0",
        }
        if "openrouter" in self.base_url.lower():
            headers["HTTP-Referer"] = "https://github.com/napstertec/text-intelligence"
            headers["X-Title"] = "NapsterTec Text Intelligence Engine"
        return headers

    def generate(
        self,
        prompt: str,
        system_instruction: str,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """Call the chat completions endpoint with bounded retry and error mapping."""
        url = f"{self.base_url}/chat/completions"
        headers = self._get_headers()

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=float(self.timeout_seconds)) as client:
                    response = client.post(url, json=payload, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices")
                    if not choices or not isinstance(choices, list):
                        raise ProviderResponseError("Invalid response format: 'choices' field is missing or empty.")
                    message = choices[0].get("message", {})
                    content = message.get("content")
                    if content is None:
                        raise ProviderResponseError("Invalid response format: 'content' field is missing.")
                    return content.strip()

                elif response.status_code == 401 or response.status_code == 403:
                    raise ProviderMissingKeyError(
                        f"Authentication failed ({response.status_code}). Please verify your LLM_API_KEY credentials.",
                        status_code=response.status_code,
                    )

                elif response.status_code == 429:
                    if attempt < self.max_retries:
                        sleep_time = (2 ** attempt) * 1.5
                        logger.warning("Rate limited (429). Retrying in %.1f seconds...", sleep_time)
                        time.sleep(sleep_time)
                        continue
                    raise ProviderRateLimitError(
                        "Upstream LLM provider rate limit exceeded (429). Please try again shortly.",
                        status_code=429,
                    )

                elif response.status_code in (500, 502, 503, 504):
                    if attempt < self.max_retries:
                        sleep_time = (2 ** attempt) * 1.0
                        logger.warning("Server error (%d). Retrying in %.1f seconds...", response.status_code, sleep_time)
                        time.sleep(sleep_time)
                        continue
                    raise ProviderError(
                        f"Upstream provider temporary error ({response.status_code}).",
                        status_code=response.status_code,
                    )

                elif response.status_code == 402:
                    raise ProviderResponseError(
                        "OpenRouter rejected the request with HTTP 402. Check account credits, billing, or model access.",
                        status_code=402,
                    )

                else:
                    raise ProviderResponseError(
                        f"Upstream provider returned unexpected HTTP {response.status_code}.",
                        status_code=response.status_code,
                    )

            except httpx.TimeoutException as exc:
                last_error = ProviderTimeoutError(
                    f"Request to LLM provider timed out after {self.timeout_seconds} seconds."
                )
                if attempt < self.max_retries:
                    time.sleep(1.0)
                    continue
                raise last_error from exc

            except httpx.RequestError as exc:
                last_error = ProviderError(f"Network error communicating with LLM provider: {type(exc).__name__}")
                if attempt < self.max_retries:
                    time.sleep(1.0)
                    continue
                raise last_error from exc

        if last_error:
            raise last_error
        raise ProviderError("Failed to generate response after retries.")

    def generate_stream(
        self,
        prompt: str,
        system_instruction: str,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> Iterator[str]:
        """Stream response chunks from completion endpoint."""
        url = f"{self.base_url}/chat/completions"
        headers = self._get_headers()

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        try:
            with httpx.Client(timeout=float(self.timeout_seconds)) as client:
                with client.stream("POST", url, json=payload, headers=headers) as response:
                    if response.status_code != 200:
                        # Reuse the synchronous adapter for identical status mapping,
                        # bounded retries, and response validation. Yield its result
                        # so streaming never silently completes with an empty output.
                        fallback_text = self.generate(
                            prompt, system_instruction, temperature, max_tokens, **kwargs
                        )
                        if fallback_text:
                            yield fallback_text
                        return

                    for line in response.iter_lines():
                        line = line.strip()
                        if not line or line.startswith(":"):
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk_json = json.loads(data_str)
                                choices = chunk_json.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue

        except (ProviderMissingKeyError, ProviderTimeoutError, ProviderRateLimitError, ProviderResponseError, ProviderError):
            raise
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(
                f"Request to LLM provider timed out after {self.timeout_seconds} seconds."
            ) from exc
        except httpx.RequestError as exc:
            raise ProviderError(
                f"Network error communicating with LLM provider: {type(exc).__name__}"
            ) from exc
