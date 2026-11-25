"""Unit tests for deterministic polish and legacy score helpers."""

import pytest
from editing.deterministic_tools import (
    normalize_whitespace,
    fix_punctuation_spacing,
    correct_common_typos,
    adjust_contractions,
    deterministic_basic_polish,
    calculate_legacy_score,
    deterministic_tool_rewrite,
)
from core.schemas import RewriteRequest


def test_normalize_whitespace():
    raw = "  This   has    excessive   spaces. \r\n\r\n\r\n\r\nNew paragraph.  "
    norm = normalize_whitespace(raw)
    assert norm == "This has excessive spaces.\n\nNew paragraph."


def test_fix_punctuation_spacing():
    raw = "Hello ,world .How are you ?Good ;fine :done..."
    fixed = fix_punctuation_spacing(raw)
    assert fixed == "Hello, world. How are you? Good; fine: done..."


def test_correct_common_typos():
    raw = "We will recieve teh calender untill friday."
    fixed = correct_common_typos(raw)
    assert fixed == "We will receive the calendar until friday."


def test_adjust_contractions():
    contracted = "Don't say you can't do it."
    expanded = adjust_contractions(contracted, expand=True)
    assert "do not" in expanded.lower()
    assert "cannot" in expanded.lower()

    contracted_again = adjust_contractions(expanded, expand=False)
    assert "don't" in contracted_again.lower()
    assert "can't" in contracted_again.lower()


def test_deterministic_basic_polish():
    raw = "  We  will   recieve   teh   data ,soon .  "
    polished = deterministic_basic_polish(raw)
    assert polished == "We will receive the data, soon."


def test_calculate_legacy_score_disclaimer():
    score = calculate_legacy_score("This is a simple sentence to test the scoring function.")
    assert "clarity_index" in score
    assert "flesch_reading_ease" in score
    assert "flesch_kincaid_grade" in score
    assert "notice" in score
    assert "Descriptive writing metric" in score["notice"]


def test_tool_fallback_applies_grammar_rules():
    request = RewriteRequest(text="Our company have a platform that help customers.", mode="proofread")
    result = deterministic_tool_rewrite(request, request.text)
    assert result == "Our company has a platform that helps customers."


def test_tool_fallback_applies_clarity_rules():
    request = RewriteRequest(text="In order to make the experience more easier, we added tools.", mode="clarity")
    result = deterministic_tool_rewrite(request, request.text)
    assert result == "To make the experience easier, we added tools."


def test_tool_fallback_supports_simplify_and_concise():
    simplify = RewriteRequest(text="We will subsequently demonstrate additional features.", mode="simplify")
    concise = RewriteRequest(text="We basically really need to just improve this.", mode="concise")
    assert "later" in deterministic_tool_rewrite(simplify, simplify.text)
    assert deterministic_tool_rewrite(concise, concise.text) == "We need to improve this."
