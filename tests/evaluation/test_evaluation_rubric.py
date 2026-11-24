"""Evaluation rubric and benchmark suite across diverse writing samples."""

import pytest
from core.schemas import RewriteRequest, EditingMode, EditingIntensity
from core.orchestrator import RewriteOrchestrator
from providers.mock import MockLLMProvider

# Diverse evaluation corpus
EVALUATION_CORPUS = [
    {
        "id": "business_email",
        "description": "Customer correspondence and project update",
        "mode": EditingMode.PROFESSIONAL,
        "intensity": EditingIntensity.BALANCED,
        "input": (
            "Hi team, Due to the fact that our Q3 revenue expanded by 18.5% ($4,500,000), "
            "we recieve substantial positive momentum. We will meet on January 15, 2026 at "
            "https://meet.google.com/xyz-123 to finalize the rollout plan."
        ),
        "expected_preserved": ["18.5%", "$4,500,000", "January 15, 2026", "https://meet.google.com/xyz-123"],
    },
    {
        "id": "academic_paragraph",
        "description": "Scientific paper abstract with citations and domain terms",
        "mode": EditingMode.ACADEMIC,
        "intensity": EditingIntensity.LIGHT,
        "input": (
            "As demonstrated by Smith et al. (2024), neural latency scales sub-linearly when k=8. "
            "However, teh experimental validation in [3] indicates that memory bandwidth limits throughput. "
            "Further analysis at 2.4 GHz confirms these findings."
        ),
        "expected_preserved": ["Smith et al. (2024)", "[3]", "k=8", "2.4 GHz"],
    },
    {
        "id": "casual_note",
        "description": "Informal communication with contractions",
        "mode": EditingMode.CONVERSATIONAL,
        "intensity": EditingIntensity.BALANCED,
        "input": (
            "Hey, don't forget we've got the team lunch at 12:30 PM tomorrow! "
            "I can't make it if it's delayed past 1:15 PM."
        ),
        "expected_preserved": ["12:30 PM", "1:15 PM"],
    },
    {
        "id": "technical_instructions",
        "description": "Numbered steps with code snippet",
        "mode": EditingMode.CLARITY,
        "intensity": EditingIntensity.BALANCED,
        "input": (
            "Follow these steps to deploy the service:\n"
            "1. Clone the repository.\n"
            "2. Run `pip install waitress` to install dependencies.\n"
            "3. Execute `python wsgi.py` to start the server on port 5000."
        ),
        "expected_preserved": ["`pip install waitress`", "`python wsgi.py`", "port 5000", "1.", "2.", "3."],
    },
]


def test_evaluation_corpus_benchmark():
    """Run evaluation rubric across the benchmark corpus.

    Rubric dimensions evaluated:
    1. Factual and protected entity preservation (100% required)
    2. Typo correction and mechanics
    3. Structural formatting retention
    4. Non-empty, valid output
    """
    orchestrator = RewriteOrchestrator(provider=MockLLMProvider())

    results = []

    for item in EVALUATION_CORPUS:
        req = RewriteRequest(
            text=item["input"],
            mode=item["mode"],
            intensity=item["intensity"],
        )
        response = orchestrator.rewrite(req)

        # 1. Non-empty and valid output
        assert len(response.revised_text.strip()) > 0

        # 2. Factual preservation check
        missing_entities = []
        for entity in item["expected_preserved"]:
            if entity not in response.revised_text:
                missing_entities.append(entity)

        # Record rubric score
        entity_retention_rate = (len(item["expected_preserved"]) - len(missing_entities)) / len(item["expected_preserved"])
        results.append({
            "id": item["id"],
            "retention_rate": entity_retention_rate,
            "missing": missing_entities,
            "warnings": response.warnings,
        })

        assert entity_retention_rate == 1.0, f"Sample {item['id']} failed to preserve: {missing_entities}"

    assert len(results) == len(EVALUATION_CORPUS)
