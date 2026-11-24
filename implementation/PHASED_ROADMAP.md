# Phased Upgrade Roadmap

## Phase 0 — Baseline and preservation
- Inspect repository, git status, files, and current behavior.
- Run CLI, web app, and tests; record failures.
- Check Python version, dependency versions, and environment assumptions.
- Create checkpoint/branch.
- Confirm existing feature inventory.

**Exit:** reproducible baseline and no user work overwritten.

## Phase 1 — Repair and stabilize existing engine
- Remove or disable destructive random rewriting as default behavior.
- Fix sentence/word handling so punctuation, capitalization, contractions, Unicode, citations, and formatting are not damaged.
- Make WordNet/NLTK resources optional and avoid network downloads on app startup; provide an explicit setup/download command if retained.
- Correct misleading detector-like scores; label metrics as descriptive writing metrics.
- Split pure processing logic from CLI and Flask.
- Add validation, bounded input, and test coverage.

**Exit:** stable deterministic basic mode, existing CLI/web flows work, tests pass.

## Phase 2 — LLM provider and rewrite modes
- Add validated configuration and `.env.example`.
- Add provider interface and one configured API adapter.
- Add mode/intensity prompt templates.
- Add timeouts and transient-error handling; no uncontrolled retries.
- Add transparent provider status and local fallback.
- Add tests with mocked provider; no test depends on live credentials.

**Exit:** end-to-end rewrite in supported modes with clear failures and no exposed keys.

## Phase 3 — Quality guardrails
- Protect numbers, proper names, citations, quotations, URLs, code, and terminology.
- Add output sanity checks and warnings.
- Add semantic-preservation evaluation set and optional bounded critique pass.
- Add change summary and before/after comparison.
- Track quality metrics without asserting authorship detection probabilities.

**Exit:** measurable quality suite and warnings for uncertain changes.

## Phase 4 — UX and usability
- Mode selector, intensity, audience/tone, custom instructions.
- Side-by-side or tabbed original/revised view.
- Copy, clear, export, loading, cancel, retry, and error states.
- Safe rendering and accessible controls.
- Responsive layout and sensible keyboard behavior.

**Exit:** functional UI with documented controls and safe output rendering.

## Phase 5 — Security and deployment readiness
- Input limits, rate limiting, secure headers, debug disabled in production.
- Production WSGI server and deployment config.
- Privacy/retention behavior, no raw text logs, secure secret handling.
- Dependency audit and configuration documentation.
- Final tests and smoke test.

**Exit:** deployable configuration and security checklist.

## Phase 6 — Optional later features (only after core is stable)
- Document history with opt-in and deletion.
- DOCX import/export and PDF export if requirements justify dependencies.
- Multi-language support with language detection and evaluation.
- User style profile (opt-in, transparent, editable, and deletable).
- Streaming output, selection-based editing, and collaboration.
- Provider/model cost tracking and configurable budgets.
