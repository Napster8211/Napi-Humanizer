"""Provider-independent LLM client with dynamic OpenRouter model selection."""

import logging
import random
import threading
import time
from typing import Any, Dict, Iterator, List, Optional

import httpx

from core.errors import ProviderError, ProviderRateLimitError, ProviderTimeoutError
from providers.base import BaseLLMProvider
from providers.openai_compatible import OpenAICompatibleProvider

logger = logging.getLogger("text_intelligence.llm_client")


class FreeModelCatalog:
    """In-memory six-hour cache of currently free OpenRouter text models."""

    def __init__(self, base_url: str, refresh_seconds: int = 21600):
        self.base_url = base_url.rstrip("/")
        self.refresh_seconds = refresh_seconds
        self._models: List[str] = []
        self._loaded_at = 0.0
        self._lock = threading.Lock()

    def free_models(self) -> List[str]:
        now = time.time()
        if self._models and now - self._loaded_at < self.refresh_seconds:
            return list(self._models)
        with self._lock:
            if self._models and now - self._loaded_at < self.refresh_seconds:
                return list(self._models)
            try:
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(f"{self.base_url}/models")
                    response.raise_for_status()
                    models = response.json().get("data", [])
                free = []
                for model in models:
                    pricing = model.get("pricing") or {}
                    architecture = model.get("architecture") or {}
                    modalities = architecture.get("input_modalities") or ["text"]
                    try:
                        is_free = float(pricing.get("prompt", 1)) == 0 and float(pricing.get("completion", 1)) == 0
                    except (TypeError, ValueError):
                        is_free = False
                    if is_free and "text" in modalities:
                        free.append(model.get("id"))
                self._models = [model for model in free if model]
                self._loaded_at = now
                logger.info("Free model catalog refreshed: count=%d", len(self._models))
            except Exception as exc:
                logger.warning("Free model catalog refresh failed: category=%s", type(exc).__name__)
            return list(self._models)


class LLMClient(BaseLLMProvider):
    """Drop-in provider wrapper that rotates models safely on transient/provider failures."""

    _semaphore = threading.BoundedSemaphore(2)
    _circuit_lock = threading.Lock()
    _circuit: Dict[str, tuple] = {}

    def __init__(self, api_key: Optional[str], base_url: str, primary: str,
                 fallbacks: str = "", allow_free_router: bool = True,
                 timeout_seconds: int = 45, max_retries: int = 2,
                 catalog_refresh_seconds: int = 21600):
        super().__init__(model=primary or "openrouter/free", timeout_seconds=timeout_seconds)
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.primary = primary.strip() if primary else ""
        self.fallbacks = [item.strip() for item in fallbacks.split(",") if item.strip()]
        self.allow_free_router = allow_free_router
        self.max_retries = max_retries
        self.catalog = FreeModelCatalog(self.base_url, refresh_seconds=catalog_refresh_seconds)

    @property
    def provider_name(self) -> str:
        return "openrouter"

    def _model_chain(self) -> List[str]:
        chain = []
        if self.primary:
            chain.append(self.primary)
        chain.extend(self.fallbacks)
        if self.allow_free_router:
            free = self.catalog.free_models()
            preferred = [
                model for model in free
                if "nemotron-3-ultra" in model or "nemotron-3.5-lightning" in model
            ]
            chain.extend(preferred)
            chain.append("openrouter/free")
        return list(dict.fromkeys(chain))

    @classmethod
    def _available(cls, model: str) -> bool:
        with cls._circuit_lock:
            failures, opened_until = cls._circuit.get(model, (0, 0.0))
            return opened_until <= time.time()

    @classmethod
    def _success(cls, model: str) -> None:
        with cls._circuit_lock:
            cls._circuit.pop(model, None)

    @classmethod
    def _failure(cls, model: str) -> None:
        with cls._circuit_lock:
            failures, _ = cls._circuit.get(model, (0, 0.0))
            failures += 1
            cls._circuit[model] = (failures, time.time() + 60 if failures >= 3 else 0.0)

    def _provider(self, model: str) -> OpenAICompatibleProvider:
        return OpenAICompatibleProvider(
            api_key=self.api_key,
            base_url=self.base_url,
            model=model,
            timeout_seconds=self.timeout_seconds,
            max_retries=self.max_retries,
        )

    def _call(self, method: str, prompt: str, system_instruction: str, temperature: float, max_tokens: Optional[int], **kwargs: Any):
        last_error: Optional[Exception] = None
        acquired = self._semaphore.acquire(timeout=self.timeout_seconds)
        if not acquired:
            raise ProviderRateLimitError("LLM concurrency limit reached", status_code=429)
        try:
            for model in self._model_chain():
                if not self._available(model):
                    continue
                provider = self._provider(model)
                for attempt in range(self.max_retries + 1):
                    try:
                        result = getattr(provider, method)(prompt=prompt, system_instruction=system_instruction, temperature=temperature, max_tokens=max_tokens, **kwargs)
                        self.model = model
                        self._success(model)
                        return result
                    except (ProviderTimeoutError, ProviderRateLimitError, ProviderError) as exc:
                        last_error = exc
                        self._failure(model)
                        status = getattr(exc, "status_code", None)
                        if status in (402, 404) or attempt >= self.max_retries:
                            break
                        time.sleep((0.5 if attempt == 0 else 1.5) + random.uniform(0, 0.25))
            if last_error:
                raise last_error
            raise ProviderError("No LLM model is currently available.")
        finally:
            self._semaphore.release()

    def generate(self, prompt: str, system_instruction: str, temperature: float = 0.3, max_tokens: Optional[int] = None, **kwargs: Any) -> str:
        return self._call("generate", prompt, system_instruction, temperature, max_tokens, **kwargs)

    def generate_stream(self, prompt: str, system_instruction: str, temperature: float = 0.3, max_tokens: Optional[int] = None, **kwargs: Any) -> Iterator[str]:
        # Hold the queue slot for the whole stream so free providers cannot be overloaded.
        acquired = self._semaphore.acquire(timeout=self.timeout_seconds)
        if not acquired:
            raise ProviderRateLimitError("LLM concurrency limit reached", status_code=429)
        try:
            last_error: Optional[Exception] = None
            for model in self._model_chain():
                if not self._available(model):
                    continue
                try:
                    provider = self._provider(model)
                    chunks = provider.generate_stream(prompt=prompt, system_instruction=system_instruction, temperature=temperature, max_tokens=max_tokens, **kwargs)
                    self.model = model
                    for chunk in chunks:
                        yield chunk
                    self._success(model)
                    return
                except (ProviderTimeoutError, ProviderRateLimitError, ProviderError) as exc:
                    last_error = exc
                    self._failure(model)
            if last_error:
                raise last_error
            raise ProviderError("No LLM model is currently available.")
        finally:
            self._semaphore.release()
