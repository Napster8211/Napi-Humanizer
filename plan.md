# Napi Humanizer Workspace Redesign Plan

## Product direction

Napi Humanizer remains a privacy-conscious Flask writing workspace. The redesign borrows familiar usability patterns from modern writing assistants—clear tool navigation, one primary editor, visible next actions, and progressive disclosure—without copying QuillBot branding, layout, or proprietary implementation.

## Implementation approach

- Keep the existing Flask/Jinja application, static vanilla JavaScript, API routes, Pydantic schemas, orchestrator, provider adapters, fallback behavior, and security headers.
- Replace the dense control-bar-first page with an app shell: brand header, tool navigation, short contextual tool intro, shared input/output editor, and an optional results/insights area.
- Make tools client-side modes over the existing endpoints wherever possible:
  - **Humanize / Paraphrase** uses `/api/v1/rewrite` or `/api/v1/rewrite/stream` with the selected editing mode.
  - **Grammar Checker** uses the proofread rewrite mode.
  - **Summarizer** uses concise mode and asks for substantial compression through the existing controls.
  - **Tone Changer** uses the selected professional, conversational, academic, or custom mode.
  - **Readability** uses `/api/v1/analyze` and presents descriptive metrics.
  - **AI Detector** uses the same local descriptive analysis endpoint, but explicitly avoids probability, authorship, or detector-bypass claims.
- Keep selection editing, style profiles, opt-in local history, copy/export, warnings, streaming, cancellation, metrics, and provider/fallback notices.
- Add accessible labels, focus states, semantic navigation, mobile stacking, and clear empty/loading/success states.

## Design

### Style options

- **Editorial calm** (0.06): warm paper surfaces, restrained navy ink, and a single coral action color.
- **Quiet studio** (0.08): pale blue-gray canvas, white work surfaces, indigo controls, and compact utility navigation.
- **Dark command center** (0.05): charcoal panels, neon accents, and dense technical controls.

### Chosen direction: Editorial calm

- **Design Movement:** editorial SaaS workspace with a calm, paper-like canvas and crisp utility chrome.
- **Core Principles:** orient users before configuration; make one primary action obvious; reveal advanced controls only when useful; treat analysis as guidance, not a verdict.
- **Color Philosophy:** soft ivory and ink-blue reduce visual fatigue, while coral marks the single action users should take next.
- **Layout Paradigm:** a slim horizontal tool rail leads into a wide writing canvas; tool context sits above the editor and insights sit below it.
- **Signature Elements:** coral active underline, rounded tool pills with simple text labels, and a small “descriptive insights” notice beside analysis results.
- **Interaction Philosophy:** selecting a tool changes the task language and sensible defaults without erasing user text; actions remain reversible and transparent.
- **Animation:** use short fades and subtle button transitions only; no decorative motion while text is being edited or streamed.
- **Typography System:** system sans stack for clarity, with strong 30–36px page titles, 14–16px body copy, and compact uppercase metadata labels.
- **Brand Essence:** a straightforward writing companion for people who want better wording without losing what they meant. Personality: clear, careful, practical.
- **Brand Voice:** headlines explain the job (“Make your draft clearer”); CTAs say exactly what happens (“Humanize text”, “Analyze writing”).
- **Wordmark & Logo:** retain the Napi Humanizer name with a small coral N monogram block rather than a generic lightning icon.
- **Signature Brand Color:** coral `#e36b5d`, reserved for active states and primary actions.

## Project structure

- `web_ui.py` continues to serve the single page and security headers.
- `ui/templates/index.html` owns the semantic application shell, tool navigation, shared editor, insights, and existing modals.
- `ui/static/style.css` owns the responsive editorial-calm visual system.
- `ui/static/app.js` keeps the existing safe DOM controller and adds tool state, contextual copy, and detector/readability presentation.
- `api/`, `core/`, `editing/`, and `providers/` remain the compatibility-preserving backend layers.
- `tests/` gains focused frontend-contract and AI Detector semantics regression coverage without removing existing tests.

## AI Detector semantics

AI Detector is a transparent writing-analysis view, not a classifier. It reports readability, sentence/word structure, lexical diversity, protected spans, and writing observations returned by the existing analyzer. It must say that these signals cannot determine authorship or provide a reliable AI probability. No unsupported score or detector-bypass promise is added.

## Compatibility boundary

No existing endpoint is renamed or removed. Tool navigation is UI state. Rewrite tools send the same `RewriteRequest` fields already supported by the backend. Analysis tools call the existing `/api/v1/analyze` endpoint. Provider configuration and secrets remain server-side and are not added to templates or source control.
