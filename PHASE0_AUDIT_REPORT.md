# Napi Humanizer v3 — Phase 0 Audit

**Audit date:** November 26, 2026  
**Repository:** `Napster8211/Napi-Humanizer`  
**Live service:** https://napi-humanizer.onrender.com

## Current stack and file map

Napi Humanizer is a Python Flask application served by Waitress on Render. The frontend is server-rendered Jinja HTML with plain CSS and vanilla JavaScript. Pydantic models define request and response contracts. `core/orchestrator.py` prepares prompts, invokes the provider, validates protected spans, computes summaries, and exposes synchronous and SSE rewrite paths. `providers/openai_compatible.py` calls OpenRouter/OpenAI-compatible chat completions, while `providers/mock.py` supports tests and offline development. `core/analyzer.py` computes readability metrics, protected spans, and the current conservative detector signals. `core/document_extractor.py` handles transient TXT, Markdown, DOCX, and PDF uploads. The main routes are `/`, `/api/v1/rewrite`, `/api/v1/rewrite/stream`, `/api/v1/analyze`, `/api/v1/extract`, `/api/v1/modes`, and `/api/v1/health`.

The tracked application is small: the working directory is approximately 1.7 MB including generated Python caches, and the largest source assets are `ui/static/app.js` at approximately 35 KB, `ui/static/style.css` at approximately 14 KB, and `ui/templates/index.html` at approximately 14 KB. The runtime dependencies are Flask, Werkzeug, Jinja2, Waitress, httpx, requests, python-dotenv, Pydantic, pypdf, and pytest. There is no npm frontend bundle.

## Environment and LLM call flow

The current configuration uses `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_TIMEOUT_SECONDS`, `LLM_MAX_RETRIES`, `MAX_INPUT_CHARS`, `RATE_LIMIT_PER_MINUTE`, and logging controls. Render currently sets `LLM_PROVIDER=openrouter`, the OpenRouter base URL, and `LLM_MODEL=anthropic/claude-sonnet-4.6`; the key is supplied as a secret environment variable and is not committed.

The current LLM flow is: the rewrite route validates `RewriteRequest`, the orchestrator builds a protected-span prompt, the provider factory constructs `OpenAICompatibleProvider`, and that adapter sends `/chat/completions`. Provider errors are caught by the orchestrator. When fallback is enabled, the orchestrator runs deterministic rewriting for all non-legacy modes and returns a successful `RewriteResponse` with `is_fallback=true`. The response currently includes provider/model metadata, warning strings containing provider details, and estimated token/cost data.

## Live findings

The live health endpoint returned HTTP 200 and confirmed the deployed service is version `2.0.0`, configured for OpenRouter with a configured key and the Claude Sonnet model. The live rewrite endpoint returned HTTP 200 for the supplied regression text, but OpenRouter returned HTTP 402. The application then returned a green-success-compatible response using `deterministic-fallback`. The browser-facing JSON included the provider failure explanation, a provider name, a model name, warnings, and token/cost estimates. This confirms the fake-success, raw-provider-message, and internal-cost disclosure defects.

The same live response produced the expected visible wording corrections and preserved the date, URL, Q3, percentage, currency, citation, and multiplier. However, the validator emitted false protected-number warnings for `3`, `18.5%`, and `$4,500,000` even though those values were present in the output. This is caused by broad numeric-span matching and validation behavior, not by actual factual loss.

The deployed `/api/v1/health` path works, but the requested future compatibility alias `/api/health` does not yet exist. The current HTML still exposes the configured provider in the header and exposes a Usage metric with token counts and estimated cost.

## Lighthouse and responsive audit

A Lighthouse mobile audit against the live service reported:

- Performance: **75**
- Accessibility: **96**
- Best Practices: **96**
- SEO: **100**
- First Contentful Paint: **3.4 seconds**
- Time to Interactive: **3.5 seconds**

The requested Playwright geometry audit could not launch because the Python Playwright package is installed but its bundled headless browser executable is not installed in this sandbox. The installed system Chromium is available, so a follow-up browser audit can use an explicit executable path or an installed browser channel. Source inspection confirms the documented mobile risks: the two editors stack vertically, each textarea remains 260px high on narrow screens, the action bar is not sticky, and the six tool tabs are a horizontally scrollable row without an explicit edge-fade or scroll affordance. The Insights panel is expanded by default and includes six cards, including the internal Usage card.

## Confirmed defects from the master build prompt

1. Provider HTTP 402 becomes a green-looking deterministic fallback success for Humanize, Tone, Summarizer, and other non-grammar modes.
2. Provider/model names and raw provider/billing wording can reach the browser through response fields and the header.
3. False protected-number warnings appear for values that remain intact.
4. Token counts and estimated cost are rendered in the user-facing Usage tile.
5. Mobile layout does not use original/result tabs, a sticky action bar, or a visible scroll affordance for all tools.
6. Action labels and language labels are inconsistent (`Humanize text` / `Refine Text`, `EN` / `Lang: EN`).
7. The coral and beige visual system remains in place.

Additional findings are that the provider abstraction is split between the factory, orchestrator, and adapter rather than one `llmClient.complete(...)` boundary; there is no free-model discovery/cache or model fallback chain; the configured request limit is character-based rather than the requested 500-word per-run limit; and the existing `RewriteResponse` contract is optimized for internal diagnostics rather than a clean public success/error envelope.

## Proposed phased plan

**Phase 1 — Reliability and honest free-model development.** Introduce a single LLM client boundary, new environment names with backward-compatible aliases during migration, free-model discovery and in-memory refresh, model fallback and retry classification, a 10-per-minute rewrite limiter, a concurrency-two provider queue, safe public error envelopes, and grammar-only deterministic fallback. Remove provider/cost display from the UI and add a development-only processing notice. Preserve the existing provider adapters and API routes while adding `/api/health` as an alias.

**Phase 2 — Humanize quality.** Add normalization, placeholder protection/restoration for all required entity types, chunking, strict placeholder validation, quality gates, retry-on-validation-failure, and word-level diff data. Add the 40-sample evaluation harness and regression fixture.

**Phase 3 — Design system.** Replace the coral/beige tokens with the specified slate, green, and indigo system. Unify labels, remove Unicode icons, add dark mode, compact insights, keyboard shortcuts, sticky mobile action controls, original/result tabs, reduced-motion handling, and accessible touch targets. Re-run Lighthouse and browser smoke tests.

**Phase 4 — Tool depth and routes.** Add shared route shells for each tool, grammar suggestion review, summarizer controls, tone chips, readability Simplify, improved upload errors, and DOCX export.

**Phase 5 — Production readiness.** Add privacy/terms/contact pages, SEO route metadata, sitemap and robots, compression/cache headers, dependency audit, CI, mocked API and Playwright smoke tests, usage-limit hooks, and deployment documentation. Accounts and billing remain out of scope.

## Phase 0 conclusion

There is no blocker to continuing. The safest next change is Phase 1 reliability: eliminate false success and provider/cost leakage before changing the visual system. The current architecture can support that work without a stack rewrite.
