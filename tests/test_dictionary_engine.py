"""
Tests for core/dictionary_engine.py

Run with:  pytest tests/test_dictionary_engine.py -v
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from core.dictionary_engine import DictionaryEngine


# ══════════════════════════════════════════════════════════════════════
# Test fixtures
# ══════════════════════════════════════════════════════════════════════

@pytest.fixture
def sentiment_dict():
    return {
        "name": "TestSentiment",
        "version": "1.0",
        "citation": "Test",
        "license": "MIT",
        "scoring": "weighted",
        "categories": {
            "positive": {"love": 3, "great": 2, "happy": 2, "wonderful": 3},
            "negative": {"hate": -3, "terrible": -2, "sad": -2, "awful": -3},
        },
    }


@pytest.fixture
def binary_dict():
    return {
        "name": "TestBinary",
        "version": "1.0",
        "citation": "Test",
        "license": "MIT",
        "scoring": "binary",
        "categories": {
            "positive": ["love", "great", "happy", "good"],
            "negative": ["hate", "terrible", "sad", "bad"],
        },
    }


@pytest.fixture
def count_dict():
    return {
        "name": "TestCount",
        "version": "1.0",
        "citation": "Test",
        "license": "MIT",
        "scoring": "count",
        "categories": {
            "keywords": ["python", "analysis", "text", "data"],
        },
    }


@pytest.fixture
def token_lists():
    return [
        ["i", "love", "this", "great", "product"],          # positive
        ["this", "is", "terrible", "and", "sad"],            # negative
        ["neutral", "statement", "with", "no", "matches"],   # no match
        ["love", "love", "love", "happy", "wonderful"],      # strong positive
    ]


# ══════════════════════════════════════════════════════════════════════
# DictionaryEngine.prepare()
# ══════════════════════════════════════════════════════════════════════

class TestPrepare:

    def test_prepare_sets_category_columns(self, sentiment_dict):
        engine = DictionaryEngine([sentiment_dict])
        engine.prepare()
        assert len(engine.category_columns) == 2
        assert "TestSentiment__positive" in engine.category_columns
        assert "TestSentiment__negative" in engine.category_columns

    def test_prepare_is_idempotent(self, sentiment_dict):
        engine = DictionaryEngine([sentiment_dict])
        engine.prepare()
        cols_first = list(engine.category_columns)
        engine.prepare()
        assert engine.category_columns == cols_first

    def test_multiple_dicts_all_categories_registered(self, sentiment_dict, binary_dict):
        engine = DictionaryEngine([sentiment_dict, binary_dict])
        engine.prepare()
        assert len(engine.category_columns) == 4  # 2 from each dict
        assert "TestSentiment__positive" in engine.category_columns
        assert "TestBinary__positive" in engine.category_columns


# ══════════════════════════════════════════════════════════════════════
# DictionaryEngine.analyze() — return shape
# ══════════════════════════════════════════════════════════════════════

class TestAnalyzeShape:

    def test_returns_tuple(self, sentiment_dict, token_lists):
        engine = DictionaryEngine([sentiment_dict])
        result = engine.analyze(token_lists)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_scores_df_shape(self, sentiment_dict, token_lists):
        engine = DictionaryEngine([sentiment_dict])
        scores_df, _ = engine.analyze(token_lists)
        assert isinstance(scores_df, pd.DataFrame)
        assert len(scores_df) == len(token_lists)
        assert set(scores_df.columns) == {"TestSentiment__positive", "TestSentiment__negative"}

    def test_word_matches_keys_match_entries(self, sentiment_dict, token_lists):
        engine = DictionaryEngine([sentiment_dict])
        _, word_matches = engine.analyze(token_lists)
        assert set(word_matches.keys()) == set(range(len(token_lists)))

    def test_empty_token_list_handled(self, sentiment_dict):
        engine = DictionaryEngine([sentiment_dict])
        scores_df, word_matches = engine.analyze([[]])
        assert len(scores_df) == 1
        # With 0 tokens score should be 0
        assert scores_df["TestSentiment__positive"].iloc[0] == 0.0


# ══════════════════════════════════════════════════════════════════════
# DictionaryEngine.analyze() — scoring correctness
# ══════════════════════════════════════════════════════════════════════

class TestScoringWeighted:

    def test_positive_words_increase_score(self, sentiment_dict):
        engine = DictionaryEngine([sentiment_dict])
        tokens = [["love", "great"]]   # weights: 3 + 2 = 5
        scores, _ = engine.analyze(tokens)
        assert scores["TestSentiment__positive"].iloc[0] == pytest.approx(5.0)

    def test_negative_words_give_negative_score(self, sentiment_dict):
        engine = DictionaryEngine([sentiment_dict])
        tokens = [["hate", "terrible"]]   # weights: -3 + -2 = -5
        scores, _ = engine.analyze(tokens)
        assert scores["TestSentiment__negative"].iloc[0] == pytest.approx(-5.0)

    def test_no_matches_gives_zero(self, sentiment_dict):
        engine = DictionaryEngine([sentiment_dict])
        tokens = [["hello", "world", "unmatched"]]
        scores, _ = engine.analyze(tokens)
        assert scores["TestSentiment__positive"].iloc[0] == 0.0
        assert scores["TestSentiment__negative"].iloc[0] == 0.0

    def test_multiple_entries_scored_independently(self, sentiment_dict):
        engine = DictionaryEngine([sentiment_dict])
        tokens = [["love"], ["hate"]]
        scores, _ = engine.analyze(tokens)
        assert scores["TestSentiment__positive"].iloc[0] > 0
        assert scores["TestSentiment__positive"].iloc[1] == 0.0


class TestScoringBinary:

    def test_binary_score_is_percentage(self, binary_dict):
        engine = DictionaryEngine([binary_dict])
        # 1 of 4 tokens matches "positive" category
        tokens = [["love", "the", "food", "here"]]
        scores, _ = engine.analyze(tokens)
        expected = (1 / 4) * 100.0
        assert scores["TestBinary__positive"].iloc[0] == pytest.approx(expected)

    def test_all_tokens_match(self, binary_dict):
        engine = DictionaryEngine([binary_dict])
        tokens = [["love", "great", "happy", "good"]]
        scores, _ = engine.analyze(tokens)
        assert scores["TestBinary__positive"].iloc[0] == pytest.approx(100.0)

    def test_zero_matches(self, binary_dict):
        engine = DictionaryEngine([binary_dict])
        tokens = [["the", "quick", "brown", "fox"]]
        scores, _ = engine.analyze(tokens)
        assert scores["TestBinary__positive"].iloc[0] == pytest.approx(0.0)


class TestScoringCount:

    def test_count_equals_number_of_matched_tokens(self, count_dict):
        engine = DictionaryEngine([count_dict])
        tokens = [["python", "is", "good", "for", "text", "analysis"]]
        scores, _ = engine.analyze(tokens)
        # "python", "text", "analysis" match — count = 3
        assert scores["TestCount__keywords"].iloc[0] == 3.0

    def test_repeated_matches_counted_each_time(self, count_dict):
        engine = DictionaryEngine([count_dict])
        tokens = [["data", "data", "data"]]
        scores, _ = engine.analyze(tokens)
        assert scores["TestCount__keywords"].iloc[0] == 3.0


# ══════════════════════════════════════════════════════════════════════
# Word matches correctness
# ══════════════════════════════════════════════════════════════════════

class TestWordMatches:

    def test_matched_words_recorded(self, sentiment_dict):
        engine = DictionaryEngine([sentiment_dict])
        tokens = [["i", "love", "this", "great", "place"]]
        _, word_matches = engine.analyze(tokens)
        pos_matches = word_matches[0]["TestSentiment__positive"]
        assert "love" in pos_matches
        assert "great" in pos_matches
        assert "i" not in pos_matches

    def test_no_matches_gives_empty_list(self, sentiment_dict):
        engine = DictionaryEngine([sentiment_dict])
        tokens = [["hello", "world"]]
        _, word_matches = engine.analyze(tokens)
        assert word_matches[0]["TestSentiment__positive"] == []
        assert word_matches[0]["TestSentiment__negative"] == []

    def test_unmatched_tokens_not_in_matches(self, binary_dict):
        engine = DictionaryEngine([binary_dict])
        tokens = [["love", "the", "cat"]]
        _, word_matches = engine.analyze(tokens)
        pos = word_matches[0]["TestBinary__positive"]
        assert "the" not in pos
        assert "cat" not in pos
        assert "love" in pos


# ══════════════════════════════════════════════════════════════════════
# Progress callback
# ══════════════════════════════════════════════════════════════════════

class TestProgressCallback:

    def test_callback_called_for_each_entry(self, sentiment_dict):
        engine = DictionaryEngine([sentiment_dict])
        calls = []
        tokens = [["love"], ["hate"], ["neutral"]]

        engine.analyze(tokens, progress_callback=lambda done, n: calls.append((done, n)))

        assert len(calls) == len(tokens)
        assert calls[-1][0] == len(tokens)
        assert calls[-1][1] == len(tokens)

    def test_callback_total_is_correct(self, sentiment_dict):
        engine = DictionaryEngine([sentiment_dict])
        totals = []
        tokens = [["a"] for _ in range(7)]
        engine.analyze(tokens, progress_callback=lambda done, n: totals.append(n))
        assert all(t == 7 for t in totals)


# ══════════════════════════════════════════════════════════════════════
# Category columns property
# ══════════════════════════════════════════════════════════════════════

class TestCategoryColumns:

    def test_auto_prepares_on_access(self, sentiment_dict):
        engine = DictionaryEngine([sentiment_dict])
        cols = engine.category_columns
        assert len(cols) == 2

    def test_columns_include_dict_name_prefix(self, sentiment_dict):
        engine = DictionaryEngine([sentiment_dict])
        for col in engine.category_columns:
            assert col.startswith("TestSentiment__")
