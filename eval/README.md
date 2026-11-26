# Phase 2 evaluation harness

`samples.json` contains 40 synthetic samples spanning academic, business, blog, casual, technical, citation-heavy, list, multilingual, and the master regression categories.

Run the harness only when an OpenRouter key is configured:

```bash
export OPENROUTER_API_KEY=your_key
python eval/run_eval.py \
  --models nvidia/nemotron-3-ultra-550b-a55b:free,openrouter/free \
  --output eval/results.csv
```

The runner evaluates each sample for protected-span integrity, output length ratio, banned phrase count, Flesch reading-ease change, latency, and provider status. It prints a model comparison table and writes derived metrics to CSV. It does not write source text or provider outputs to the results file. The harness is opt-in and is not imported by the Flask application.

Model IDs should be obtained from the live OpenRouter catalog rather than copied from this example. Free models are rate limited, so run comparisons deliberately and stop if the provider returns rate-limit errors.
