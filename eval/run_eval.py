#!/usr/bin/env python3
"""Opt-in free-model evaluation harness for Napi Humanizer Phase 2.

Example:
  python eval/run_eval.py --models nvidia/nemotron-3-ultra-550b-a55b:free,openrouter/free

The harness never runs during normal application startup and writes only aggregate
metrics plus model outputs' derived scores, not source text, to the CSV.
"""

import argparse
import csv
import json
import os
import statistics
import time
from pathlib import Path

from core.config import AppConfig
from core.metrics import compute_text_metrics
from core.orchestrator import RewriteOrchestrator
from core.schemas import EditingIntensity, EditingMode, RewriteRequest
from providers.llm_client import LLMClient

BANNED_PHRASES = (
    "delve", "tapestry", "moreover", "in conclusion", "it is important to note",
    "in today's fast-paced world", "leverage", "robust", "seamless", "navigate the landscape",
)


def evaluate_model(model: str, samples: list[dict], output_dir: Path) -> list[dict]:
    client = LLMClient(
        api_key=os.getenv("OPENROUTER_API_KEY") or os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1"),
        primary=model,
        allow_free_router=False,
        timeout_seconds=max(1, int(os.getenv("LLM_TIMEOUT_MS", "45000")) // 1000),
        max_retries=int(os.getenv("LLM_MAX_RETRIES", "2")),
    )
    config = AppConfig(llm_provider="openrouter", max_words_per_run=500)
    orchestrator = RewriteOrchestrator(config=config, provider=client)
    rows = []
    for sample in samples:
        request = RewriteRequest(
            text=sample["text"],
            mode=EditingMode.NATURAL,
            intensity=EditingIntensity.BALANCED,
            fallback_to_local=False,
        )
        started = time.perf_counter()
        try:
            response = orchestrator.rewrite(request)
            latency_ms = round((time.perf_counter() - started) * 1000, 2)
            protected_ok = not any("protected" in warning.lower() for warning in response.warnings)
            ratio = len(response.revised_text.split()) / max(1, len(sample["text"].split()))
            banned_count = sum(response.revised_text.lower().count(phrase) for phrase in BANNED_PHRASES)
            original_metrics = compute_text_metrics(sample["text"])
            readability_change = round(
                response.metrics.flesch_reading_ease - original_metrics.flesch_reading_ease
                if response.metrics else 0.0,
                3,
            )
            rows.append({
                "model": model,
                "sample_id": sample["id"],
                "category": sample["category"],
                "placeholder_integrity": int(protected_ok),
                "length_ratio": round(ratio, 3),
                "banned_phrase_count": banned_count,
                "readability_change": readability_change,
                "latency_ms": latency_ms,
                "status": "ok",
            })
        except Exception as exc:
            rows.append({
                "model": model, "sample_id": sample["id"], "category": sample["category"],
                "placeholder_integrity": 0, "length_ratio": "", "banned_phrase_count": "",
                "readability_change": "", "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                "status": type(exc).__name__,
            })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", required=True, help="Comma-separated model IDs to compare")
    parser.add_argument("--samples", default="eval/samples.json")
    parser.add_argument("--output", default="eval/results.csv")
    args = parser.parse_args()
    samples = json.loads(Path(args.samples).read_text())
    models = [model.strip() for model in args.models.split(",") if model.strip()]
    rows = [row for model in models for row in evaluate_model(model, samples, Path(args.output).parent)]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print("model,placeholder_integrity,length_ratio,mean_latency_ms,statuses")
    for model in models:
        subset = [row for row in rows if row["model"] == model]
        valid = [row for row in subset if row["status"] == "ok"]
        print(",".join([
            model,
            f"{statistics.mean(row['placeholder_integrity'] for row in valid) if valid else 0:.3f}",
            f"{statistics.mean(row['length_ratio'] for row in valid) if valid else 0:.3f}",
            f"{statistics.mean(row['latency_ms'] for row in subset):.1f}",
            str(len(subset) - len(valid)),
        ]))
    print(f"Saved derived results to {output}")


if __name__ == "__main__":
    main()
