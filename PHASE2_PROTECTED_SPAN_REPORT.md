# Phase 2 Protected-Span Reliability Report

## Completed

The validator no longer uses word-boundary assertions for punctuation-bearing factual values. That old rule could flag intact values such as `18.5%` and `$4,500,000` because `%` and `$` are non-word characters. It also risked treating a protected standalone number as present inside a larger number.

Number validation now requires the exact protected value with non-alphanumeric lookarounds. This preserves correct matching for decimals, currency, percentages, multipliers, comma-separated values, and standalone numbers. URLs, dates, citations, code, email addresses, and quotations continue to require exact preservation; quotations are now included in the validation set as well.

## Tests

Added focused regression coverage for intact currency, percentages, decimals, multipliers, dates, citations, quotations, and the standalone-number-versus-larger-number case. The complete suite passes with **76 passed, 2 warnings**.

Python compilation and `git diff --check` also pass.

## Placeholder pipeline completed

Rewrite requests now replace protected spans with ordered `⟦P1⟧`-style tokens before provider calls. Provider output is checked for exact token count and order. A damaged result receives one stricter protection retry; if that also fails, the original target is retained and a factual-safety warning identifies the protected values. Streaming output is buffered until this validation completes, so placeholder tokens are never exposed to the browser. Valid tokens are restored before the result is returned.

The pipeline is selection-aware and preserves the existing selection reconstruction behavior. New tests cover successful restoration and safe retention after a damaged provider response. The complete suite passes with **78 passed, 2 warnings**; Python compilation, JavaScript syntax validation, and `git diff --check` also pass.

## Bounded chunking completed

Provider rewrite calls now use sentence-aware chunks capped at 350 words. Paragraph breaks are retained where possible, sentences are kept together until the limit is reached, and an unusually long sentence is safely split by words. The current 500-word request limit means most requests remain a single provider call; larger allowed inputs are divided without changing the public API or selection reconstruction contract.

Chunking has focused unit coverage, and the complete suite now passes with **81 passed, 2 warnings**.

## Quality gates and evaluation harness completed

Substantive non-Proofread rewrites now receive descriptive quality checks for the 70–130% length band and the requested changed-word-ratio band: Light 10–25%, Balanced 25–50%, and Substantial 50–75%. Concise and Simplify are exempt from the general length band. If a result is outside the applicable band, the provider receives one adjusted quality instruction; if the retry remains outside the band, the first result is retained with an honest warning rather than silently claiming that the target band was met. Short edits and Proofread are intentionally exempt from percentage gates.

The `eval/` folder now contains 40 samples across the requested categories, including the master regression text, plus an opt-in `run_eval.py` harness. It compares selected models on protected-span integrity, length ratio, banned-phrase count, readability change, latency, and status, and writes derived metrics only to CSV. It is not imported by the Flask application and does not run during normal tests or deployment.

The complete suite passes with **84 passed, 2 warnings**. Python compilation, JavaScript syntax validation, JSON validation, and `git diff --check` pass.
