"""Orchestrator coordinating analysis, prompt building, provider invocation, streaming, and validation."""

import json
import logging
import time
import uuid
from typing import Any, Dict, Iterator, List, Optional, Tuple

from core.analyzer import DocumentAnalyzer, get_analyzer
from core.config import AppConfig, get_config
from core.errors import ProviderError, ProviderMissingKeyError
from core.metrics import compute_text_metrics, estimate_tokens_and_cost
from core.prompt_builder import build_system_instruction, build_user_prompt
from core.protection import (
    ProtectedPlaceholder,
    mask_protected_spans,
    restore_protected_spans,
    validate_placeholders,
)
from core.schemas import EditingMode, RewriteRequest, RewriteResponse
from core.validator import OutputValidator, get_validator
from editing.deterministic_tools import deterministic_tool_rewrite
from providers.base import BaseLLMProvider
from providers.factory import get_provider

logger = logging.getLogger("text_intelligence")


class RewriteOrchestrator:
    """Coordinates the end-to-end rewrite pipeline for both response modes."""

    def __init__(self, config: Optional[AppConfig] = None, analyzer: Optional[DocumentAnalyzer] = None,
                 validator: Optional[OutputValidator] = None, provider: Optional[BaseLLMProvider] = None):
        self.config = config or get_config()
        self.analyzer = analyzer or get_analyzer()
        self.validator = validator or get_validator()
        self._provider = provider

    @property
    def provider(self) -> BaseLLMProvider:
        if self._provider is not None:
            return self._provider
        return get_provider(self.config)

    def _prepare_selection(self, request: RewriteRequest) -> Dict[str, Any]:
        if request.selection_range:
            start, end = request.selection_range
            target = request.text[start:end]
            return {
                "is_selection": True,
                "target_text": target,
                "context_before": request.text[:start],
                "context_after": request.text[end:],
                "document_context": request.text,
                "start": start,
                "end": end,
            }
        return {
            "is_selection": False,
            "target_text": request.text,
            "context_before": "",
            "context_after": "",
            "document_context": None,
            "start": 0,
            "end": len(request.text),
        }

    @staticmethod
    def _sse(event: str, data: Dict[str, Any]) -> str:
        return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

    def _request_context(self, request: RewriteRequest) -> Tuple[Dict[str, Any], List[Any], List[ProtectedPlaceholder], str, str]:
        self.validator.validate_input(
            request,
            max_chars=self.config.max_input_chars,
            max_words=self.config.max_words_per_run,
        )
        analysis = self.analyzer.analyze(request.text)
        selection = self._prepare_selection(request)
        if selection["is_selection"]:
            spans = [s for s in analysis.protected_spans if s.start >= selection["start"] and s.end <= selection["end"]]
        else:
            spans = analysis.protected_spans
        target_text, placeholders, prompt_spans = mask_protected_spans(
            selection["target_text"],
            spans,
            source_offset=selection["start"],
        )
        system = build_system_instruction(request, detected_language=analysis.detected_language)
        prompt = build_user_prompt(
            request,
            protected_spans=prompt_spans,
            text_to_edit=target_text,
            document_context=selection["document_context"],
        )
        return selection, analysis.protected_spans, placeholders, system, prompt

    @staticmethod
    def _restore_provider_output(
        provider: BaseLLMProvider,
        prompt: str,
        system: str,
        masked_target: str,
        original_target: str,
        placeholders: List[ProtectedPlaceholder],
    ) -> Tuple[str, List[str]]:
        """Validate provider placeholders and retry once before retaining source text."""
        output = provider.generate(prompt=prompt, system_instruction=system)
        if not placeholders:
            return output, []
        failure = validate_placeholders(output, placeholders)
        if failure is None:
            return restore_protected_spans(output, placeholders), []

        strict_system = system + (
            "\nSTRICT PROTECTION RETRY: The target contains protected tokens. "
            "Copy every token such as ⟦P1⟧ exactly once and in the same order. "
            "Do not spell out, delete, duplicate, or move protected tokens."
        )
        retry_output = provider.generate(prompt=prompt, system_instruction=strict_system)
        retry_failure = validate_placeholders(retry_output, placeholders)
        if retry_failure is None:
            return restore_protected_spans(retry_output, placeholders), []

        protected_names = ", ".join(item.original for item in placeholders[:5])
        warning = (
            "Protected placeholder validation failed; the original target was retained "
            f"for factual safety ({protected_names})."
        )
        return original_target, [warning]

    def _reconstruct(self, selection: Dict[str, Any], target: str) -> str:
        if selection["is_selection"]:
            return selection["context_before"] + target + selection["context_after"]
        return target

    def _response(self, request: RewriteRequest, request_id: str, start_time: float, selection: Dict[str, Any],
                  original_spans: List[Any], revised_text: str, provider_name: str, model_name: str,
                  is_fallback: bool, warnings: Optional[List[str]] = None) -> RewriteResponse:
        all_warnings = list(warnings or [])
        all_warnings.extend(self.validator.verify_protected_spans(request.text, revised_text, original_spans))
        all_warnings.extend(self.validator.verify_formatting_integrity(request.text, revised_text))
        summary = self.validator.compute_change_summary(request.text, revised_text) if request.include_change_summary else None
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            "Rewrite completed: req_id=%s mode=%s intensity=%s provider=%s duration_ms=%.1f warnings_count=%d fallback=%s selection=%s",
            request_id, request.mode.value, request.intensity.value, provider_name, duration_ms,
            len(all_warnings), is_fallback, selection["is_selection"],
        )
        return RewriteResponse(
            original_text=request.text, revised_text=revised_text, mode=request.mode.value,
            intensity=request.intensity.value, provider=provider_name, model=model_name,
            is_fallback=is_fallback, warnings=all_warnings, change_summary=summary,
            metrics=compute_text_metrics(revised_text), token_usage=estimate_tokens_and_cost(request.text, revised_text),
            selection_applied=selection["is_selection"], request_id=request_id, duration_ms=duration_ms,
        )

    def rewrite(self, request: RewriteRequest) -> RewriteResponse:
        start_time = time.perf_counter()
        request_id = str(uuid.uuid4())
        selection, spans, placeholders, system, prompt = self._request_context(request)
        target = selection["target_text"]
        warnings: List[str] = []
        is_fallback = False
        provider_name = "deterministic-local"
        model_name = "rule-based-engine"

        if request.mode == EditingMode.LEGACY:
            revised_target = deterministic_tool_rewrite(request, target)
            warnings.append("Processed via legacy deterministic engine (no LLM call).")
            is_fallback = True
        else:
            try:
                provider = self.provider
                provider_name, model_name = provider.provider_name, provider.model
                revised_target, protection_warnings = self._restore_provider_output(
                    provider, prompt, system, target, target, placeholders
                )
                warnings.extend(protection_warnings)
            except (ProviderMissingKeyError, ProviderError) as exc:
                if not request.fallback_to_local or request.mode != EditingMode.PROOFREAD:
                    raise
                revised_target = deterministic_tool_rewrite(request, target)
                provider_name, model_name, is_fallback = "deterministic-fallback", "rule-based-engine", True
                warnings.append("Basic corrections applied (limited mode).")

        revised_text = self._reconstruct(selection, revised_target)
        return self._response(request, request_id, start_time, selection, spans, revised_text,
                              provider_name, model_name, is_fallback, warnings)

    def rewrite_stream(self, request: RewriteRequest) -> Iterator[str]:
        """Yield SSE events while producing the same final response contract as rewrite()."""
        start_time = time.perf_counter()
        request_id = str(uuid.uuid4())
        try:
            selection, spans, placeholders, system, prompt = self._request_context(request)
            target = selection["target_text"]
            provider_name = "deterministic-local"
            model_name = "rule-based-engine"
            is_fallback = False
            warnings: List[str] = []
            active_provider = None
            if request.mode != EditingMode.LEGACY:
                try:
                    active_provider = self.provider
                    provider_name, model_name = active_provider.provider_name, active_provider.model
                except (ProviderMissingKeyError, ProviderError):
                    # Provider construction failures are handled by the same fallback path below.
                    active_provider = None
            yield self._sse("init", {
                "request_id": request_id, "provider": provider_name, "model": model_name,
                "mode": request.mode.value, "is_selection": selection["is_selection"],
            })

            if request.mode == EditingMode.LEGACY:
                revised_target = deterministic_tool_rewrite(request, target)
                is_fallback = True
                warnings.append("Processed via legacy deterministic engine (no LLM call).")
                yield self._sse("chunk", {"chunk": revised_target})
            else:
                try:
                    provider = active_provider or self.provider
                    provider_name, model_name = provider.provider_name, provider.model
                    # Init identifies the actual provider after lazy construction.
                    yield self._sse("provider", {"provider": provider_name, "model": model_name})
                    chunks: List[str] = []
                    for chunk in provider.generate_stream(prompt=prompt, system_instruction=system):
                        if chunk:
                            chunks.append(chunk)
                    streamed_target = "".join(chunks)
                    if not streamed_target.strip():
                        raise ProviderError("Provider returned an empty streaming response.")
                    if placeholders:
                        failure = validate_placeholders(streamed_target, placeholders)
                        if failure is None:
                            revised_target = restore_protected_spans(streamed_target, placeholders)
                        else:
                            strict_system = system + (
                                "\nSTRICT PROTECTION RETRY: Copy every protected token such as "
                                "⟦P1⟧ exactly once and in the same order."
                            )
                            retry_target = provider.generate(prompt=prompt, system_instruction=strict_system)
                            if validate_placeholders(retry_target, placeholders) is None:
                                revised_target = restore_protected_spans(retry_target, placeholders)
                            else:
                                revised_target = target
                                warnings.append(
                                    "Protected placeholder validation failed; the original target was retained for factual safety."
                                )
                    else:
                        revised_target = streamed_target
                    yield self._sse("chunk", {"chunk": revised_target})
                except (ProviderMissingKeyError, ProviderError) as exc:
                    if not request.fallback_to_local or request.mode != EditingMode.PROOFREAD:
                        yield self._sse("error", {"code": "ProviderError", "message": "The rewrite provider was unavailable."})
                        return
                    revised_target = deterministic_tool_rewrite(request, target)
                    provider_name, model_name, is_fallback = "deterministic-fallback", "rule-based-engine", True
                    warnings.append("Basic corrections applied (limited mode).")
                    # Tell clients to replace partial provider output rather than append a duplicate fallback.
                    yield self._sse("reset", {"text": revised_target})
                    yield self._sse("chunk", {"chunk": revised_target})

            revised_text = self._reconstruct(selection, revised_target)
            response = self._response(request, request_id, start_time, selection, spans, revised_text,
                                      provider_name, model_name, is_fallback, warnings)
            yield self._sse("complete", response.model_dump())
        except Exception:
            logger.exception("Unexpected streaming rewrite failure: request_id=%s", request_id)
            yield self._sse("error", {"code": "InternalError", "message": "An unexpected error occurred."})


_orchestrator_instance: Optional[RewriteOrchestrator] = None


def get_orchestrator() -> RewriteOrchestrator:
    """Return configured RewriteOrchestrator singleton."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = RewriteOrchestrator()
    return _orchestrator_instance
