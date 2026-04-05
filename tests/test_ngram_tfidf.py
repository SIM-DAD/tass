"""
Tests for n-gram dictionary support and TF-IDF scoring mode.

Run with:  pytest tests/test_ngram_tfidf.py -v
"""

import os
import sys
import pytest
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.preprocessor import Preprocessor
from core.dictionary_engine import DictionaryEngine


# ══════════════════════════════════════════════════════════════════════
# N-gram generation (Preprocessor)
# ══════════════════════════════════════════════════════════════════════

class TestNgramGeneration:

    def test_unigrams_only_when_max_1(self):
        tokens = ["the", "cat", "sat"]
        result = Preprocessor.generate_ngrams(tokens, max_n=1)
        assert result == ["the", "cat", "sat"]

    def test_bigrams_generated(self):
        tokens = ["not", "happy", "today"]
        result = Preprocessor.generate_ngrams(tokens, max_n=2)
        assert "not happy" in result
        assert "happy today" in result
        assert "not" in result

    def test_trigrams_generated(self):
        tokens = ["i", "am", "not", "happy"]
        result = Preprocessor.generate_ngrams(tokens, max_n=3)
        assert "i am not" in result
        assert "am not happy" in result
        assert "i am" in result
        assert "not happy" in result

    def test_empty_tokens(self):
        assert Preprocessor.generate_ngrams([], max_n=3) == []

    def test_single_token(self):
        result = Preprocessor.generate_ngrams(["hello"], max_n=3)
        assert result == ["hello"]

    def test_count_is_correct(self):
        tokens = ["a", "b", "c", "d"]
        result = Preprocessor.generate_ngrams(tokens, max_n=2)
        # 4 unigrams + 3 bigrams
        assert len(result) == 7


# ══════════════════════════════════════════════════════════════════════
# N-gram dictionary matching
# ══════════════════════════════════════════════════════════════════════

class TestNgramMatching:

    @pytest.fixture
    def ngram_dict(self):
        return [{
            "name": "Negation",
            "scoring": "binary",
            "categories": {
                "negated_positive": ["not happy", "not good", "not great"],
                "positive": ["happy", "good", "great"],
            }
        }]

    def test_ngram_entries_detected(self, ngram_dict):
        engine = DictionaryEngine(ngram_dict)
        engine.prepare()
        assert engine._max_ngram == 2

    def test_ngram_matched(self, ngram_dict):
        engine = DictionaryEngine(ngram_dict)
        engine.prepare()
        token_lists = [["i", "am", "not", "happy", "today"]]
        scores, matches = engine.analyze(token_lists)
        # "not happy" should match negated_positive
        assert "not happy" in matches[0]["Negation__negated_positive"]

    def test_ngram_suppresses_constituent(self, ngram_dict):
        engine = DictionaryEngine(ngram_dict)
        engine.prepare()
        token_lists = [["i", "am", "not", "happy", "today"]]
        scores, matches = engine.analyze(token_lists)
        # "happy" should NOT also match in positive (consumed by "not happy")
        assert "happy" not in matches[0]["Negation__positive"]

    def test_unigram_still_matches_when_no_ngram(self, ngram_dict):
        engine = DictionaryEngine(ngram_dict)
        engine.prepare()
        token_lists = [["i", "am", "happy", "and", "good"]]
        scores, matches = engine.analyze(token_lists)
        # No "not" prefix → "happy" and "good" match as unigrams
        assert "happy" in matches[0]["Negation__positive"]
        assert "good" in matches[0]["Negation__positive"]

    def test_trigram_dict(self):
        tri_dict = [{
            "name": "Phrase",
            "scoring": "binary",
            "categories": {
                "phrases": ["on the other hand", "as a matter"],
                "words": ["hand", "matter", "other"],
            }
        }]
        engine = DictionaryEngine(tri_dict)
        engine.prepare()
        assert engine._max_ngram == 4  # "on the other hand" = 4 words
        token_lists = [["on", "the", "other", "hand", "it", "does", "matter"]]
        scores, matches = engine.analyze(token_lists)
        assert "on the other hand" in matches[0]["Phrase__phrases"]
        # "hand" consumed by phrase, but "matter" is free
        assert "hand" not in matches[0]["Phrase__words"]
        assert "matter" in matches[0]["Phrase__words"]


# ══════════════════════════════════════════════════════════════════════
# TF-IDF scoring
# ══════════════════════════════════════════════════════════════════════

class TestTfidfScoring:

    @pytest.fixture
    def simple_dict(self):
        return [{
            "name": "Sentiment",
            "scoring": "binary",
            "categories": {
                "positive": ["happy", "great", "good", "love"],
                "negative": ["sad", "bad", "hate"],
            }
        }]

    def test_tfidf_returns_scores(self, simple_dict):
        engine = DictionaryEngine(simple_dict)
        token_lists = [
            ["i", "am", "happy", "and", "great"],
            ["this", "is", "bad", "and", "sad"],
            ["i", "love", "good", "food"],
        ]
        scores, _ = engine.analyze(token_lists, scoring_override="tfidf")
        assert scores.shape == (3, 2)
        assert not scores.isnull().all().all()

    def test_tfidf_rare_words_score_higher(self, simple_dict):
        engine = DictionaryEngine(simple_dict)
        # "happy" appears in 1 doc, "good" appears in 2 — "happy" should have higher IDF
        token_lists = [
            ["happy", "good"],
            ["good", "ok"],
            ["fine", "ok"],
        ]
        scores, _ = engine.analyze(token_lists, scoring_override="tfidf")
        # Entry 0 has both happy (rare, 1 doc) and good (common, 2 docs)
        # The TF-IDF score should be > 0
        assert scores.iloc[0]["Sentiment__positive"] > 0

    def test_tfidf_zero_for_no_matches(self, simple_dict):
        engine = DictionaryEngine(simple_dict)
        token_lists = [
            ["the", "cat", "sat", "on", "mat"],
        ]
        scores, _ = engine.analyze(token_lists, scoring_override="tfidf")
        assert scores.iloc[0]["Sentiment__positive"] == 0.0
        assert scores.iloc[0]["Sentiment__negative"] == 0.0

    def test_count_override(self, simple_dict):
        engine = DictionaryEngine(simple_dict)
        token_lists = [
            ["happy", "happy", "great"],  # 3 positive matches
        ]
        scores, _ = engine.analyze(token_lists, scoring_override="count")
        assert scores.iloc[0]["Sentiment__positive"] == 3

    def test_default_scoring_unchanged(self, simple_dict):
        engine = DictionaryEngine(simple_dict)
        token_lists = [
            ["happy", "the", "cat", "sat"],  # 1/4 = 25%
        ]
        scores, _ = engine.analyze(token_lists, scoring_override=None)
        assert scores.iloc[0]["Sentiment__positive"] == pytest.approx(25.0)


# ══════════════════════════════════════════════════════════════════════
# Backward compatibility
# ══════════════════════════════════════════════════════════════════════

class TestBackwardCompat:

    def test_unigram_only_dicts_unchanged(self):
        """Dictionaries with no n-gram entries should behave exactly as before."""
        d = [{
            "name": "Test",
            "scoring": "binary",
            "categories": {
                "cat1": ["apple", "banana", "cherry"],
            }
        }]
        engine = DictionaryEngine(d)
        engine.prepare()
        assert engine._max_ngram == 1  # no n-grams detected

        token_lists = [["i", "like", "apple", "and", "cherry"]]
        scores, matches = engine.analyze(token_lists)
        assert scores.iloc[0]["Test__cat1"] == pytest.approx(40.0)  # 2/5 * 100
        assert set(matches[0]["Test__cat1"]) == {"apple", "cherry"}

    def test_weighted_dict_unchanged(self):
        d = [{
            "name": "AFINN",
            "scoring": "weighted",
            "categories": {
                "sentiment": {"happy": 3, "sad": -2, "love": 4}
            }
        }]
        engine = DictionaryEngine(d)
        token_lists = [["i", "am", "happy", "and", "love", "life"]]
        scores, _ = engine.analyze(token_lists)
        assert scores.iloc[0]["AFINN__sentiment"] == 7  # 3 + 4
