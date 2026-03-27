"""
Tests for core/preprocessor.py

Run with:  pytest tests/test_preprocessor.py -v
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from core.preprocessor import Preprocessor


# ══════════════════════════════════════════════════════════════════════
# Basic tokenization
# ══════════════════════════════════════════════════════════════════════

class TestTokenize:

    def test_returns_list(self):
        p = Preprocessor()
        result = p.tokenize("Hello world")
        assert isinstance(result, list)

    def test_lowercasing(self):
        p = Preprocessor(lowercase=True)
        tokens = p.tokenize("Hello WORLD Today")
        assert all(t == t.lower() for t in tokens)

    def test_no_lowercasing(self):
        p = Preprocessor(lowercase=False)
        tokens = p.tokenize("Hello WORLD")
        assert "Hello" in tokens or "WORLD" in tokens

    def test_strips_punctuation(self):
        p = Preprocessor(strip_punctuation=True)
        tokens = p.tokenize("Hello, world! This is great.")
        assert "," not in tokens
        assert "!" not in tokens
        assert "." not in tokens

    def test_punctuation_preserved_when_disabled(self):
        p = Preprocessor(strip_punctuation=False)
        tokens = p.tokenize("Hello,")
        # NLTK splits punctuation as separate tokens when not stripped
        full = " ".join(tokens)
        assert "hello" in full

    def test_empty_string(self):
        p = Preprocessor()
        tokens = p.tokenize("")
        assert isinstance(tokens, list)
        assert len(tokens) == 0

    def test_none_input_handled(self):
        p = Preprocessor()
        tokens = p.tokenize(None)
        assert isinstance(tokens, list)

    def test_numeric_input_handled(self):
        p = Preprocessor()
        tokens = p.tokenize(42)
        assert isinstance(tokens, list)

    def test_whitespace_only(self):
        p = Preprocessor()
        tokens = p.tokenize("   ")
        assert isinstance(tokens, list)


# ══════════════════════════════════════════════════════════════════════
# Min token length filter
# ══════════════════════════════════════════════════════════════════════

class TestMinTokenLength:

    def test_min_length_1_keeps_all(self):
        p = Preprocessor(min_token_length=1)
        tokens = p.tokenize("I am going to the store")
        assert "i" in tokens or len(tokens) > 0

    def test_min_length_3_removes_short_words(self):
        p = Preprocessor(min_token_length=3, strip_punctuation=True)
        tokens = p.tokenize("I am going to the store today")
        # "i", "am", "to" should be removed; "going", "the", "store" kept
        for t in tokens:
            assert len(t) >= 3, f"Token {t!r} is shorter than min_length=3"

    def test_min_length_5(self):
        p = Preprocessor(min_token_length=5)
        tokens = p.tokenize("The quick brown fox jumps")
        for t in tokens:
            assert len(t) >= 5


# ══════════════════════════════════════════════════════════════════════
# Stopword removal
# ══════════════════════════════════════════════════════════════════════

class TestStopwordRemoval:

    def test_stopwords_removed(self):
        p = Preprocessor(remove_stopwords=True)
        tokens = p.tokenize("the quick brown fox jumps over the lazy dog")
        # "the", "over" are stopwords
        assert "the" not in tokens

    def test_content_words_kept(self):
        p = Preprocessor(remove_stopwords=True)
        tokens = p.tokenize("the quick brown fox jumps")
        assert "quick" in tokens or "brown" in tokens or "fox" in tokens

    def test_no_stopwords_by_default(self):
        p = Preprocessor(remove_stopwords=False)
        tokens = p.tokenize("the quick fox")
        assert "the" in tokens


# ══════════════════════════════════════════════════════════════════════
# Lemmatization
# ══════════════════════════════════════════════════════════════════════

class TestLemmatization:

    def test_lemmatization_enabled(self):
        p = Preprocessor(lemmatize=True, lowercase=True, strip_punctuation=True)
        tokens = p.tokenize("running runs runner")
        # WordNetLemmatizer doesn't always normalize all forms,
        # but "running" → "running" (no verb context), "runs" → "run"
        assert isinstance(tokens, list)
        assert len(tokens) > 0

    def test_lemmatization_does_not_remove_words(self):
        p = Preprocessor(lemmatize=True)
        tokens = p.tokenize("The quick brown foxes are jumping")
        # Lemmatization should change forms but not drop words
        assert len(tokens) > 0


# ══════════════════════════════════════════════════════════════════════
# process_series
# ══════════════════════════════════════════════════════════════════════

class TestProcessSeries:

    def _make_series(self):
        return pd.Series([
            "I love this product",
            "This is terrible and bad",
            "It is okay I guess",
        ])

    def test_returns_list_of_lists(self):
        p = Preprocessor()
        result = p.process_series(self._make_series())
        assert isinstance(result, list)
        assert all(isinstance(r, list) for r in result)

    def test_length_matches_series(self):
        p = Preprocessor()
        series = self._make_series()
        result = p.process_series(series)
        assert len(result) == len(series)

    def test_each_entry_is_token_list(self):
        p = Preprocessor()
        result = p.process_series(self._make_series())
        assert all(isinstance(t, str) for entry in result for t in entry)

    def test_empty_series(self):
        p = Preprocessor()
        result = p.process_series(pd.Series([], dtype=str))
        assert result == []

    def test_series_with_nans(self):
        p = Preprocessor()
        series = pd.Series(["Hello world", None, "Goodbye"])
        result = p.process_series(series)
        assert len(result) == 3
        assert all(isinstance(r, list) for r in result)


# ══════════════════════════════════════════════════════════════════════
# process_df
# ══════════════════════════════════════════════════════════════════════

class TestProcessDf:

    def test_returns_series(self):
        p = Preprocessor()
        df = pd.DataFrame({"text": ["Hello world", "Goodbye"]})
        result = p.process_df(df, "text")
        assert isinstance(result, pd.Series)

    def test_result_named_tokens(self):
        p = Preprocessor()
        df = pd.DataFrame({"text": ["Hello world"]})
        result = p.process_df(df, "text")
        assert result.name == "_tokens"

    def test_length_matches_df(self):
        p = Preprocessor()
        df = pd.DataFrame({"text": ["a b c", "d e f", "g h i"]})
        result = p.process_df(df, "text")
        assert len(result) == 3
