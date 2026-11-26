"""Tests for bounded rewrite chunking."""

from core.chunking import split_for_rewrite


def test_short_text_remains_one_chunk():
    text = "One short paragraph."
    assert split_for_rewrite(text, max_words=3) == [text]


def test_long_text_splits_on_sentence_boundaries():
    text = "One two three. Four five six. Seven eight nine."
    chunks = split_for_rewrite(text, max_words=5)

    assert len(chunks) == 3
    assert all(len(chunk.split()) <= 5 for chunk in chunks)
    assert chunks[0].strip().endswith("three.")


def test_oversized_sentence_is_safely_word_bounded():
    text = " ".join(f"word{i}" for i in range(11)) + "."
    chunks = split_for_rewrite(text, max_words=4)

    assert all(len(chunk.split()) <= 4 for chunk in chunks)
    assert "word0" in " ".join(chunks)
    assert "word10." in " ".join(chunks)
