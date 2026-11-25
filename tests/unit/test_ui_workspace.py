"""Regression tests for the tool-oriented writing workspace."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "ui" / "templates" / "index.html"
SCRIPT = ROOT / "ui" / "static" / "app.js"


def test_workspace_exposes_clear_writing_tools():
    content = TEMPLATE.read_text(encoding="utf-8")
    for tool_id in ("humanize", "detector", "grammar", "summarizer", "tone", "readability"):
        assert f'data-tool="{tool_id}"' in content
    assert 'id="originalText"' in content
    assert 'id="revisedText"' in content
    assert 'id="refineBtn"' in content
    assert 'id="analyzeBtn"' in content


def test_detector_uses_descriptive_non_classifier_language():
    template = TEMPLATE.read_text(encoding="utf-8")
    script = SCRIPT.read_text(encoding="utf-8")
    combined = template + script
    assert "No reliable AI probability" in combined
    assert "authorship verdict" in combined
    assert "detectorNotice" in combined
    assert "innerHTML" not in script


def test_existing_api_endpoints_are_not_replaced_by_tool_state():
    script = SCRIPT.read_text(encoding="utf-8")
    assert 'fetch("/api/v1/rewrite"' in script
    assert 'fetch("/api/v1/rewrite/stream"' in script
    assert 'fetch("/api/v1/analyze"' in script


def test_document_uploader_is_transient_and_format_limited():
    template = TEMPLATE.read_text(encoding="utf-8")
    script = SCRIPT.read_text(encoding="utf-8")
    assert 'id="documentFile"' in template
    assert 'accept=".txt,.md,.markdown,.docx,.pdf"' in template
    assert 'fetch("/api/v1/extract"' in script
    assert "uploads are not stored" in template.lower()
