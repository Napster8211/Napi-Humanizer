# Phase 2 Protected-Span Reliability Report

## Completed

The validator no longer uses word-boundary assertions for punctuation-bearing factual values. That old rule could flag intact values such as `18.5%` and `$4,500,000` because `%` and `$` are non-word characters. It also risked treating a protected standalone number as present inside a larger number.

Number validation now requires the exact protected value with non-alphanumeric lookarounds. This preserves correct matching for decimals, currency, percentages, multipliers, comma-separated values, and standalone numbers. URLs, dates, citations, code, email addresses, and quotations continue to require exact preservation; quotations are now included in the validation set as well.

## Tests

Added focused regression coverage for intact currency, percentages, decimals, multipliers, dates, citations, quotations, and the standalone-number-versus-larger-number case. The complete suite passes with **76 passed, 2 warnings**.

Python compilation and `git diff --check` also pass.

## Remaining Phase 2 work

The next quality slice should add reversible `⟦P1⟧`-style placeholders around protected spans before provider calls, verify placeholder count and order, retry once with a stricter instruction when a provider damages placeholders, and retain the original affected sentence when validation still fails. Chunking, length/change-ratio quality gates, and the evaluation harness remain open after that protection pipeline is implemented.
