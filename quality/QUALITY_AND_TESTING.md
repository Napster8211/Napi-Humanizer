# Quality and Testing

## Evaluation rubric (score 1–5)
- Meaning preservation: no unsupported additions or material omissions.
- Grammar and mechanics.
- Clarity and readability.
- Mode/tone compliance.
- Voice preservation at Light intensity.
- Formatting/citation/technical-term preservation.
- Unnecessary-change rate: penalize edits that do not improve the text.
- Output validity and robustness.

Do not use this rubric to infer human/AI authorship or promise detector results.

## Suggested test corpus
Include short and long inputs:
- Business email and customer response.
- Academic paragraph with citation and technical terms.
- Casual note with contractions.
- Instructions with numbered steps.
- Text containing names, dates, amounts, percentages, URLs, quotations, code, and acronyms.
- Empty, whitespace-only, over-limit, malformed, and Unicode input.
- Input containing instruction-like text; it must be treated as text to edit, not as system instructions.

## Unit tests
- Mode and intensity validation.
- Protected-span extraction and comparison.
- Prompt construction and delimiters.
- Provider response parsing.
- Timeout, 401/403, 429, 5xx, malformed response, and missing-key mapping.
- Output sanity and warnings.
- Metrics calculations and edge cases.
- Deterministic local mode.

## Integration tests
- API happy path with mocked provider.
- API failure path.
- CLI basic and provider mode.
- UI output handling and XSS regression.
- No raw text in logs.

## Acceptance thresholds
- All existing and new tests pass, or every failure is explicitly documented with a reason.
- Protected values remain unchanged in test cases unless the user explicitly requested transformation.
- Basic mode does not claim an LLM call.
- Provider mode identifies provider/model without exposing credentials.
- Output never enters unsafe HTML rendering.
- No live provider call is required to run the default test suite.
