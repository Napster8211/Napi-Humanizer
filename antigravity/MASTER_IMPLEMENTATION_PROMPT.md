# MASTER ENGINEERING MISSION — NapsterTec Text Intelligence Engine

You are acting as a senior software architect, Python backend engineer, NLP engineer, product designer, security engineer, and QA lead. Upgrade the existing text-processing project in place. The current prototype uses NLTK, regex phrase removal, random synonym substitution, sentence splitting, contraction/idiom injection, a heuristic score, and a Flask UI. Inspect the actual repository first; the description is not a substitute for source inspection.

## Mission
Turn the existing prototype into a reliable, modular, LLM-assisted writing and text-refinement product. It should help users edit and transform text with control over intent, tone, audience, and intensity. Focus on semantic preservation, quality, transparency, security, and maintainability—not evading AI detectors or hiding AI authorship.

## Non-negotiable workflow
1. Inspect the complete repository, git status, dependencies, entry points, and current behavior.
2. Run the existing app and tests if possible. Record the baseline and failures. Do not claim tests passed if not run.
3. Create a safe checkpoint/branch before substantial edits. Do not delete or overwrite user work.
4. Produce a concise implementation plan based on the actual code. Identify which proposed modules already exist and reuse them.
5. Implement one phase at a time. Keep the application runnable after each phase.
6. Add/adjust tests alongside each implementation change.
7. Review for regressions, security, data loss, and dependency bloat.
8. Report exact files changed, commands run, test results, configuration, and remaining issues.

## Product requirements
Provide editing modes (at minimum):
- Proofread: correct grammar, spelling, punctuation, and obvious errors; preserve voice and meaning.
- Clarity: make confusing wording easier to understand without changing meaning.
- Natural/Fluent: improve flow, sentence rhythm, and readability without inserting fake personal experiences or claims.
- Professional: polished business communication.
- Academic: formal, precise, cautious language; preserve citations and technical terms.
- Conversational: approachable and clear, not artificially slangy.
- Concise: reduce repetition and verbosity while retaining key information.
- Simplify: explain in plain language for a selected audience/reading level.
- Custom: accept user instructions, subject to safety and quality validation.

Allow intensity levels such as Light / Balanced / Substantial, but describe them as editing intensity, not detector-evasion strength. Preserve source text and let users compare outputs. Support whole-document and selected-text workflows if the current UI can reasonably accommodate them.

## Architecture requirements
Use separation of concerns and a provider-independent LLM abstraction. Proposed modules are in `architecture/`; adapt rather than blindly copy. Keep the current CLI and Flask entry point working unless a documented reason requires migration.

Core components:
- Input validation and request schemas.
- Document analyzer: paragraphs, sentences, word count, language estimate where practical, readability indicators, and protected spans (names, dates, numbers, citations, URLs, code, domain terminology).
- Editing-intent/mode configuration.
- Rewrite orchestrator that constructs a structured prompt, calls a configured provider, and handles timeout/retry/error policy.
- Provider adapter interface; implement at least one provider compatible with the project's chosen API (e.g. OpenAI-compatible endpoint) using environment configuration. If the repository uses OpenRouter, support configurable base URL/model without coupling the core to it. No secrets in source.
- Output validation: non-empty output, length sanity, protected-content checks, and safe handling of markdown/HTML.
- Quality evaluation: deterministic checks plus optional LLM critique/revision. Never represent heuristic scores as a probability that a text is human- or AI-written.
- Web/API layer and UI layer separate from business logic.
- Logging that excludes raw user text and credentials by default.

## Rewrite behavior
Use a clear prompt template that:
- Treats the input as content, not instructions to override the system.
- Follows selected editing mode, audience, tone, and intensity.
- Preserves meaning, facts, numbers, names, dates, claims, citations, quotations, technical terms, and URLs unless the user explicitly asks to change them.
- Does not invent sources, experiences, evidence, credentials, opinions, or details.
- Avoids cliché additions and unnecessary idioms.
- Keeps formatting (lists, headings, tables, code blocks) where feasible.
- Returns only the edited text in the normal output path; optional structured explanation/change summary in a separate field.
- If the request is ambiguous or factual changes would be needed, asks for clarification or flags it rather than guessing.

## Existing prototype: preserve and improve, don't blindly delete
Review the current functions. Keep useful functionality if it can be made safe and reliable. Disable random, destructive transformations by default. The regex phrase-removal, random WordNet synonym substitution, arbitrary sentence splitting, fake-personal-touch injection, and heuristic detector-style score should not be treated as core quality features. Replace them with context-aware edits or optional deterministic utilities. If legacy modes remain, label them clearly and test them.

## API/UI
- Keep a simple, accessible writing workspace.
- Original and revised text must be displayed safely; never inject user text with `innerHTML`.
- Provide copy, clear, download/export, mode, intensity, tone/audience (where useful), and loading/cancel/error states.
- Compare original and revised text; optionally show a change summary. Do not claim precise diff quality if not implemented.
- Validate requests server-side, not only in the browser.
- Apply input length limits, timeouts, rate limiting, and safe error responses.
- Use a production WSGI server for deployment; do not rely on Flask's debug server in production.
- Avoid collecting or storing text unless the user explicitly enables history. If history exists, make deletion clear.

## Configuration
Create `.env.example` with safe placeholders and document variables. Likely settings:
- `LLM_PROVIDER`
- `LLM_BASE_URL` (optional)
- `LLM_API_KEY`
- `LLM_MODEL`
- `LLM_TIMEOUT_SECONDS`
- `MAX_INPUT_CHARS`
- `RATE_LIMIT`
- `APP_ENV`
Do not expose API keys to frontend code. Add `.env` to `.gitignore`. Validate configuration at startup and give actionable messages.

## Quality and evaluation
Implement tests for:
- input validation and size limits;
- empty input and malformed requests;
- provider success, missing credentials, timeout, rate limit, malformed response;
- prompt injection in source text (treated as content);
- meaning/protected spans (numbers, names, citations, URLs, technical terms);
- output format and markdown preservation;
- API response contract;
- UI safely rendering hostile input (XSS regression test);
- existing CLI workflows and compatibility.

Create a small evaluation corpus of varied sample text (business email, academic paragraph, casual note, technical instructions, multilingual or non-English input if supported). Evaluate with a rubric: semantic preservation, grammar, clarity, tone compliance, factual integrity, formatting preservation, and unnecessary-change rate. Avoid claiming universal quality from a tiny benchmark.

## Security/privacy
See `quality/SECURITY_AND_PRIVACY.md`. At minimum: no raw text in logs by default, safe DOM rendering, no secrets in frontend, request validation, rate limiting, CSRF considerations if cookie/session auth is introduced, secure headers, dependency review, and explicit retention policy.

## Implementation phases
Follow `implementation/PHASED_ROADMAP.md`. First deliver a stable foundation and tests. Next provider abstraction + LLM rewrite. Then quality validation, UX, and hardening. Avoid premature multi-agent complexity or unsupported feature promises.

## Acceptance criteria
The project is complete for this mission when:
1. Existing CLI/web startup is preserved or documented migration is provided.
2. Users can select an editing mode and intensity and receive a rewrite from a configured LLM provider.
3. Missing API configuration fails gracefully and offers a non-LLM/basic mode without misleading status.
4. Source meaning and protected facts are preserved as far as the system can validate; uncertain changes are surfaced.
5. The output is never rendered through unsafe HTML interpolation.
6. No keys are exposed to the browser or committed.
7. Unit and integration tests exist and all runnable tests pass; skipped tests are explained.
8. README, setup, environment, deployment, and troubleshooting docs are updated.
9. A final report contains evidence: exact test commands and results, no invented test claims.

## Final response format
- Executive summary and current maturity.
- Architecture implemented.
- Features completed and not completed.
- Files changed.
- Environment variables/setup.
- Tests run with exact pass/fail/skip counts.
- Security/privacy review.
- Known limitations and next phase.

Begin by inspecting the existing code and producing the baseline. Then proceed with implementation; do not stop after writing a plan unless a genuine blocker requires user input.
