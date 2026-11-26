# Napi Humanizer v3 — Phase 1 Reliability Report

## Completed in this slice

The first Phase 1 reliability slice removes the most serious trust defects identified in the audit. The synchronous public rewrite route now strips provider names, model IDs, token counts, estimated costs, internal timings, and raw provider warning text before returning JSON to browsers. Provider failures are mapped to stable vendor-neutral envelopes with `ok`, `code`, `message`, and `retryable` fields. Timeout failures tell the user to try a shorter selection; unavailable or rate-limited services use a neutral busy message.

Deterministic fallback is now restricted to the Proofread/Grammar path. Humanize, Tone, Summarizer, Clarity, Academic, Conversational, Concise, Simplify, and Custom requests no longer claim success when their LLM request fails. Grammar fallback is labeled `Basic corrections applied (limited mode).` and is intended only for basic corrections. The streaming route applies the same public sanitization to its SSE events and never sends provider/model/cost diagnostics to the browser.

The user-facing header no longer shows the configured provider, and the internal Usage cost tile has been removed. The advanced setting now explains that basic corrections are available only in Grammar mode. The UI uses a neutral amber limited-mode notice rather than a green success state. A deployment-friendly `/api/health` alias was added while retaining `/api/v1/health`.

## Files changed

- `api/routes.py`: public response sanitization, safe provider error envelope, SSE sanitization.
- `core/orchestrator.py`: Grammar-only deterministic fallback and neutral limited-mode warning.
- `web_ui.py`: `/api/health` alias.
- `ui/templates/index.html`: remove provider/cost disclosure and clarify fallback control.
- `ui/static/app.js`: remove provider/cost rendering and use honest success/limited-mode messaging.
- `ui/static/style.css`: amber limited-mode alert.
- `tests/integration/test_api.py`: public privacy and error-contract coverage.
- `tests/unit/test_orchestrator.py`: Grammar-only fallback coverage.
- `PHASE0_AUDIT_REPORT.md`: required read-only audit findings.

## Validation

The complete local test suite passes with **73 passed, 2 existing deprecation warnings**. Python compilation, JavaScript syntax checking, and `git diff --check` also pass. A local Flask smoke test confirmed HTTP 200 for both `/api/health` and `/api/v1/health`.

## Environment changes

No new secret is required in this slice. Existing `LLM_*` variables remain supported while the next Phase 1 slice introduces the requested `OPENROUTER_API_KEY`, model fallback settings, free-model discovery, retry classification, and queue controls. No key was added to source control.

## Known remaining work

The provider adapter still needs to be consolidated behind a single `llmClient.complete(...)` boundary. Free-model discovery, model fallback chains, circuit breaking, global concurrency limits, 500-word enforcement, and the development-only data-retention notice are not yet implemented. The UI still needs the Phase 3 design-system rebuild and mobile editor tabs. The live Render service will need to redeploy this commit before the public error behavior can be verified against the real OpenRouter 402 response.
