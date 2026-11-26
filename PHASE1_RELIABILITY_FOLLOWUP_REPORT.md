# Phase 1 Reliability Follow-up Report

## Scope

This slice adds resilient model routing and the per-run workload contract requested by the master build prompt while preserving the existing Flask architecture, mock-provider test override, public response sanitization, and Grammar-only deterministic fallback.

## Implemented

- Added `providers/llm_client.py` as the single OpenRouter/compatible-provider wrapper used by the provider factory.
- Added a six-hour in-memory OpenRouter catalog cache at `/api/v1/models`. Models are accepted only when they advertise text input and both prompt and completion prices are numerically zero. Availability is discovered at runtime; current model IDs are not the source of truth.
- Added model ordering: configured primary, configured comma-separated fallbacks, preferred discovered free instruction-following candidates, then `openrouter/free` when enabled.
- Added bounded retry behavior for provider failures, jittered backoff, per-model circuit state after three failures for 60 seconds, and a global concurrency-two semaphore shared by client instances.
- Added backward-compatible settings: `OPENROUTER_API_KEY` falls back to `LLM_API_KEY`; `LLM_MODEL_PRIMARY` falls back to `LLM_MODEL`; `LLM_TIMEOUT_MS` falls back to `LLM_TIMEOUT_SECONDS`; and legacy settings remain accepted.
- Added `MAX_WORDS_PER_RUN` with a default of 500. Sync and streaming rewrite endpoints return the public `OVER_LIMIT` envelope with the exact friendly message rather than invoking a provider.
- Added a development-only notice that free services may retain prompts for service improvement. It is not rendered when `APP_ENV=production`.
- Updated Render and README configuration examples to use the new environment names and free-router policy.

## Validation

- Full suite: **73 passed, 2 warnings**.
- Python compilation passed.
- JavaScript syntax check passed.
- `git diff --check` passed.

## Deployment procedure

Set the Render secret `OPENROUTER_API_KEY`. The committed defaults use `LLM_MODEL_PRIMARY=openrouter/free`, `LLM_ALLOW_FREE_ROUTER=true`, `LLM_TIMEOUT_MS=45000`, `LLM_MAX_RETRIES=2`, and `MAX_WORDS_PER_RUN=500`. A specific primary or comma-separated fallback list can be configured without code changes. The service queries the public catalog at startup on the first rewrite and refreshes it every six hours.

## Remaining Phase 1 / verification notes

The implementation has been tested locally with the mock provider and static checks. Live Render redeployment and browser-level verification still need to be performed after the environment change. The Phase 2 placeholder/protected-span correction and the larger Phase 3 visual/mobile redesign remain separate work.
