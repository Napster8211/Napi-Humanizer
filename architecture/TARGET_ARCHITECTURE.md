# Target Architecture

## High-level flow

```text
UI / CLI
   |
Request validation + mode configuration
   |
Document analysis (format, segments, protected spans, metrics)
   |
Rewrite orchestrator
   |---- Prompt/template builder
   |---- Provider adapter (OpenAI-compatible / configurable)
   |---- Timeout, retry, cancellation, fallback policy
   |
Output validation
   |---- Empty/length checks
   |---- Protected-span comparison
   |---- Markdown/format checks
   |---- Deterministic grammar/clarity checks where available
   |---- Optional quality critique and bounded revision
   |
Response: revised text + optional change summary + quality diagnostics
```

## Design principles
- Core processing should not depend on Flask or a particular provider.
- Providers implement a small interface, e.g. `rewrite(request) -> result`.
- Configuration is validated once; credentials remain server-side.
- Each request has a trace/request ID. Logs record operational metadata, not source text.
- Failures are explicit: unavailable provider, timeout, invalid response, validation warning. Do not silently return fake LLM output.
- Use structured request/result models. Prefer Pydantic if already used or if dependency cost is acceptable.

## Request model (illustrative)
- `text`: required bounded string
- `mode`: enum
- `intensity`: light/balanced/substantial
- `tone`: optional enum or string constrained by validation
- `audience`: optional string
- `instructions`: optional bounded string
- `preserve_formatting`: boolean
- `include_change_summary`: boolean

## Response model
- `original_text` (if appropriate; avoid unnecessary duplication)
- `revised_text`
- `mode`
- `provider/model` (non-secret metadata)
- `change_summary` optional
- `warnings`: list of validation warnings
- `metrics`: counts/readability estimates, explicitly not authorship probabilities
- `request_id`

## Provider abstraction
Use a thin interface and adapter. A compatible HTTP provider can be configured by base URL, model, API key, and timeout. Support an OpenAI-compatible API only if the actual provider endpoint confirms compatibility. Keep provider-specific response parsing and error mapping in the adapter. Do not add several provider SDKs unless needed.

## Orchestration
1. Validate input and mode.
2. Analyze document and identify protected spans.
3. Build a prompt with system rules, mode, user controls, and content in a clearly delimited untrusted-data section.
4. Call provider with bounded timeout and limited retry policy for transient errors only.
5. Parse response.
6. Validate output; compare protected spans and detect suspiciously large changes.
7. Optional single revision pass if a quality issue is found and configured.
8. Return output and warnings.

## Local/basic fallback
Basic deterministic tools (proofread checks, whitespace normalization, readability estimates) may be available without an LLM. The fallback must be transparent: clearly indicate `basic/local mode`; never imply that a provider rewrite occurred.
