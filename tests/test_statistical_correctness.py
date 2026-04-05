"""
Statistical correctness tests — verify TASS engine output against
independently computed baselines to 4 decimal places.

Reference values computed via SciPy (equivalent to R output).
These tests catch regressions in the statistical computation pipeline.

Run with:  pytest tests/test_statistical_correctness.py -v
"""

import os
import sys
import pytest
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.statistics_engine import StatisticsEngine
from core.formatting import format_p_apa, sig_stars, format_stat_with_df, effect_size_label


# ══════════════════════════════════════════════════════════════════════
# Fixtures — known data with pre-computed baselines
# ══════════════════════════════════════════════════════════════════════

@pytest.fixture
def engine():
    return StatisticsEngine()


@pytest.fixture
def two_group_known():
    """Two groups with known statistical properties.

    Baselines (SciPy / R equivalent):
        Welch t = -7.5761, p = 0.000004, df = 12.9246
        Cohen's d = -3.7881
        Levene F = 0.7452, p = 0.4025
        Shapiro g1: W = 0.9577, p = 0.7882
        Shapiro g2: W = 0.9556, p = 0.7673
        CI g1: [10.5137, 12.3863]
        CI g2: [14.4917, 15.8833]
    """
    scores = pd.DataFrame({
        "score": [10.2, 12.1, 11.5, 9.8, 13.0, 10.7, 11.9, 12.4,
                  15.1, 14.3, 16.2, 13.8, 15.7, 14.9, 16.0, 15.5]
    })
    groups = pd.Series(["A"]*8 + ["B"]*8)
    return scores, groups


@pytest.fixture
def three_group_known():
    """Three groups for ANOVA/Kruskal-Wallis.

    Baselines:
        ANOVA F = 121.4587, p ≈ 0.0000, df_between = 2, df_within = 18
        eta-squared = 0.9310
        Kruskal-Wallis H = 17.5584, p = 0.000154
    """
    g1 = [10.2, 12.1, 11.5, 9.8, 13.0, 10.7, 11.9, 12.4]
    g2 = [15.1, 14.3, 16.2, 13.8, 15.7, 14.9, 16.0, 15.5]
    g3 = [20.1, 19.5, 21.0, 18.8, 20.7]
    scores = pd.DataFrame({"score": g1 + g2 + g3})
    groups = pd.Series(["A"]*8 + ["B"]*8 + ["C"]*5)
    return scores, groups


# ══════════════════════════════════════════════════════════════════════
# 1. Statistical Correctness — Two Groups (Parametric)
# ══════════════════════════════════════════════════════════════════════

class TestTwoGroupParametric:

    def test_welch_t_statistic(self, engine, two_group_known):
        scores, groups = two_group_known
        result = engine.group_comparisons(scores, groups, correction="none")
        gs = result["score"]
        assert gs.test_name == "Welch t-test"
        assert gs.test_statistic == pytest.approx(-7.5761, abs=0.001)

    def test_welch_p_value(self, engine, two_group_known):
        scores, groups = two_group_known
        result = engine.group_comparisons(scores, groups, correction="none")
        gs = result["score"]
        assert gs.p_value == pytest.approx(0.000004, abs=0.00001)

    def test_welch_df(self, engine, two_group_known):
        scores, groups = two_group_known
        result = engine.group_comparisons(scores, groups, correction="none")
        gs = result["score"]
        assert gs.df_between == pytest.approx(12.9246, abs=0.01)

    def test_cohens_d(self, engine, two_group_known):
        scores, groups = two_group_known
        result = engine.group_comparisons(scores, groups, correction="none")
        gs = result["score"]
        assert gs.effect_size == pytest.approx(-3.7881, abs=0.001)
        assert gs.effect_size_name == "Cohen's d"

    def test_levene(self, engine, two_group_known):
        scores, groups = two_group_known
        result = engine.group_comparisons(scores, groups, correction="none")
        gs = result["score"]
        assert gs.levene is not None
        f_stat, p_val, equal = gs.levene
        assert f_stat == pytest.approx(0.7452, abs=0.001)
        assert p_val == pytest.approx(0.4025, abs=0.001)
        assert equal  # p > .05 → equal variances

    def test_shapiro_wilk_per_group(self, engine, two_group_known):
        scores, groups = two_group_known
        result = engine.group_comparisons(scores, groups, correction="none")
        gs = result["score"]
        w_a, p_a, normal_a = gs.normality["A"]
        assert w_a == pytest.approx(0.9577, abs=0.001)
        assert p_a == pytest.approx(0.7882, abs=0.01)
        assert normal_a  # p > .05 → normal

    def test_confidence_intervals(self, engine, two_group_known):
        scores, groups = two_group_known
        result = engine.group_comparisons(scores, groups, correction="none")
        gs = result["score"]
        ci_a = gs.confidence_intervals["A"]
        ci_b = gs.confidence_intervals["B"]
        assert ci_a[0] == pytest.approx(10.5137, abs=0.01)
        assert ci_a[1] == pytest.approx(12.3863, abs=0.01)
        assert ci_b[0] == pytest.approx(14.4917, abs=0.01)
        assert ci_b[1] == pytest.approx(15.8833, abs=0.01)

    def test_significance_flag(self, engine, two_group_known):
        scores, groups = two_group_known
        result = engine.group_comparisons(scores, groups, correction="none")
        gs = result["score"]
        assert gs.significant is True


# ══════════════════════════════════════════════════════════════════════
# 2. Statistical Correctness — Two Groups (Non-parametric)
# ══════════════════════════════════════════════════════════════════════

class TestTwoGroupNonparametric:

    def test_mann_whitney_statistic(self, engine, two_group_known):
        scores, groups = two_group_known
        result = engine.group_comparisons(scores, groups, nonparametric=True, correction="none")
        gs = result["score"]
        assert gs.test_name == "Mann-Whitney U"
        assert gs.test_statistic == pytest.approx(0.0, abs=0.01)

    def test_mann_whitney_p(self, engine, two_group_known):
        scores, groups = two_group_known
        result = engine.group_comparisons(scores, groups, nonparametric=True, correction="none")
        gs = result["score"]
        assert gs.p_value == pytest.approx(0.000155, abs=0.001)

    def test_rank_biserial(self, engine, two_group_known):
        scores, groups = two_group_known
        result = engine.group_comparisons(scores, groups, nonparametric=True, correction="none")
        gs = result["score"]
        assert gs.effect_size == pytest.approx(1.0, abs=0.01)
        assert gs.effect_size_name == "r (rank-biserial)"

    def test_no_df_for_mann_whitney(self, engine, two_group_known):
        scores, groups = two_group_known
        result = engine.group_comparisons(scores, groups, nonparametric=True, correction="none")
        gs = result["score"]
        assert gs.df_between is None


# ══════════════════════════════════════════════════════════════════════
# 3. Statistical Correctness — Three Groups (Parametric)
# ══════════════════════════════════════════════════════════════════════

class TestThreeGroupParametric:

    def test_anova_f_statistic(self, engine, three_group_known):
        scores, groups = three_group_known
        result = engine.group_comparisons(scores, groups, correction="none")
        gs = result["score"]
        assert gs.test_name == "One-way ANOVA"
        assert gs.test_statistic == pytest.approx(121.4587, abs=0.1)

    def test_anova_p_value(self, engine, three_group_known):
        scores, groups = three_group_known
        result = engine.group_comparisons(scores, groups, correction="none")
        gs = result["score"]
        assert gs.p_value < 0.0001

    def test_anova_df(self, engine, three_group_known):
        scores, groups = three_group_known
        result = engine.group_comparisons(scores, groups, correction="none")
        gs = result["score"]
        assert gs.df_between == 2.0
        assert gs.df_within == 18.0

    def test_eta_squared(self, engine, three_group_known):
        scores, groups = three_group_known
        result = engine.group_comparisons(scores, groups, correction="none")
        gs = result["score"]
        assert gs.effect_size == pytest.approx(0.9310, abs=0.001)
        assert gs.effect_size_name == "eta-squared"

    def test_posthoc_runs_for_significant(self, engine, three_group_known):
        scores, groups = three_group_known
        result = engine.group_comparisons(scores, groups, correction="none")
        gs = result["score"]
        assert len(gs.posthoc) == 3  # 3 groups → 3 pairwise
        assert gs.posthoc_method == "Tukey HSD"


# ══════════════════════════════════════════════════════════════════════
# 4. Statistical Correctness — Three Groups (Non-parametric)
# ══════════════════════════════════════════════════════════════════════

class TestThreeGroupNonparametric:

    def test_kruskal_wallis_statistic(self, engine, three_group_known):
        scores, groups = three_group_known
        result = engine.group_comparisons(scores, groups, nonparametric=True, correction="none")
        gs = result["score"]
        assert gs.test_name == "Kruskal-Wallis"
        assert gs.test_statistic == pytest.approx(17.5584, abs=0.01)

    def test_kruskal_wallis_p(self, engine, three_group_known):
        scores, groups = three_group_known
        result = engine.group_comparisons(scores, groups, nonparametric=True, correction="none")
        gs = result["score"]
        assert gs.p_value == pytest.approx(0.000154, abs=0.001)

    def test_kruskal_wallis_df(self, engine, three_group_known):
        scores, groups = three_group_known
        result = engine.group_comparisons(scores, groups, nonparametric=True, correction="none")
        gs = result["score"]
        assert gs.df_between == 2.0

    def test_dunns_posthoc_for_nonparametric(self, engine, three_group_known):
        scores, groups = three_group_known
        result = engine.group_comparisons(scores, groups, nonparametric=True, correction="none")
        gs = result["score"]
        if gs.posthoc:
            assert gs.posthoc_method == "Dunn's test"
            assert len(gs.posthoc) == 3


# ══════════════════════════════════════════════════════════════════════
# 5. APA Formatting Correctness
# ══════════════════════════════════════════════════════════════════════

class TestAPAFormatting:

    def test_p_no_leading_zero(self):
        assert format_p_apa(0.042)[0] == "."
        assert "0." not in format_p_apa(0.042)

    def test_p_three_decimals(self):
        result = format_p_apa(0.04)
        assert result == ".040"

    def test_p_less_than_001(self):
        assert format_p_apa(0.0001) == "< .001"
        assert format_p_apa(0.0009) == "< .001"

    def test_p_exact_001(self):
        assert format_p_apa(0.001) == ".001"

    def test_sig_stars_correct(self):
        assert sig_stars(0.0001) == "***"
        assert sig_stars(0.005) == "**"
        assert sig_stars(0.03) == "*"
        assert sig_stars(0.1) == "n.s."

    def test_stat_with_df_t_test(self):
        assert format_stat_with_df("Welch t-test", 2.87, 42.3, None) == "t(42.3) = 2.87"

    def test_stat_with_df_anova(self):
        assert format_stat_with_df("One-way ANOVA", 4.12, 2.0, 57.0) == "F(2, 57) = 4.12"

    def test_stat_with_df_kruskal(self):
        assert format_stat_with_df("Kruskal-Wallis", 8.34, 2.0, None) == "H(2) = 8.34"

    def test_stat_with_df_mann_whitney(self):
        assert format_stat_with_df("Mann-Whitney U", 145.0, None, None) == "U = 145.00"

    def test_effect_size_labels(self):
        assert effect_size_label(0.1, "Cohen's d") == "negligible"
        assert effect_size_label(0.3, "Cohen's d") == "small"
        assert effect_size_label(0.6, "Cohen's d") == "medium"
        assert effect_size_label(1.2, "Cohen's d") == "large"

    def test_eta_squared_labels(self):
        assert effect_size_label(0.005, "eta-squared") == "negligible"
        assert effect_size_label(0.03, "eta-squared") == "small"
        assert effect_size_label(0.10, "eta-squared") == "medium"
        assert effect_size_label(0.20, "eta-squared") == "large"


# ══════════════════════════════════════════════════════════════════════
# 6. Edge Cases
# ══════════════════════════════════════════════════════════════════════

class TestEdgeCases:

    def test_single_entry_per_group(self, engine):
        """Groups with only 1 entry each — should not crash."""
        scores = pd.DataFrame({"score": [10.0, 20.0]})
        groups = pd.Series(["A", "B"])
        result = engine.group_comparisons(scores, groups, correction="none")
        assert "score" in result

    def test_zero_variance_group(self, engine):
        """All values identical in one group — should not crash."""
        scores = pd.DataFrame({"score": [5.0, 5.0, 5.0, 10.0, 11.0, 12.0]})
        groups = pd.Series(["A", "A", "A", "B", "B", "B"])
        result = engine.group_comparisons(scores, groups, correction="none")
        gs = result["score"]
        assert gs.test_statistic is not None

    def test_unequal_group_sizes(self, engine):
        """Groups with very different sizes."""
        scores = pd.DataFrame({"score": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30]})
        groups = pd.Series(["A"]*10 + ["B"]*2)
        result = engine.group_comparisons(scores, groups, correction="none")
        gs = result["score"]
        assert gs.p_value is not None

    def test_nan_values_dropped(self, engine):
        """NaN entries should be dropped, not crash."""
        scores = pd.DataFrame({"score": [1.0, 2.0, np.nan, 4.0, 5.0, np.nan]})
        groups = pd.Series(["A", "A", "A", "B", "B", "B"])
        result = engine.group_comparisons(scores, groups, correction="none")
        gs = result["score"]
        assert gs.test_statistic is not None

    def test_many_groups(self, engine):
        """5 groups — should use ANOVA/Kruskal-Wallis."""
        data = []
        grps = []
        for i, g in enumerate(["A", "B", "C", "D", "E"]):
            data.extend([i*10 + j for j in range(5)])
            grps.extend([g]*5)
        scores = pd.DataFrame({"score": data})
        groups = pd.Series(grps)
        result = engine.group_comparisons(scores, groups, correction="none")
        gs = result["score"]
        assert gs.test_name in ("One-way ANOVA", "Kruskal-Wallis")
        assert gs.df_between == 4.0  # 5 groups - 1

    def test_empty_text_tokens(self):
        """Empty token lists should produce zero scores."""
        from core.dictionary_engine import DictionaryEngine
        d = [{"name": "Test", "scoring": "binary", "categories": {"pos": ["happy", "good"]}}]
        engine = DictionaryEngine(d)
        scores, matches = engine.analyze([[]])
        assert scores.iloc[0]["Test__pos"] == 0.0

    def test_single_token_entry(self):
        """Single-token entry should work."""
        from core.dictionary_engine import DictionaryEngine
        d = [{"name": "Test", "scoring": "binary", "categories": {"pos": ["happy"]}}]
        engine = DictionaryEngine(d)
        scores, matches = engine.analyze([["happy"]])
        assert scores.iloc[0]["Test__pos"] == 100.0  # 1/1 * 100

    def test_stopwords_only_entry(self):
        """Entry with only stopwords — no dictionary matches expected."""
        from core.dictionary_engine import DictionaryEngine
        d = [{"name": "Test", "scoring": "binary", "categories": {"pos": ["happy", "good"]}}]
        engine = DictionaryEngine(d)
        scores, matches = engine.analyze([["the", "is", "a", "an"]])
        assert scores.iloc[0]["Test__pos"] == 0.0

    def test_all_tokens_match(self):
        """Every token matches — score should be 100%."""
        from core.dictionary_engine import DictionaryEngine
        d = [{"name": "Test", "scoring": "binary", "categories": {"pos": ["happy", "good", "great"]}}]
        engine = DictionaryEngine(d)
        scores, matches = engine.analyze([["happy", "good", "great"]])
        assert scores.iloc[0]["Test__pos"] == pytest.approx(100.0)


# ══════════════════════════════════════════════════════════════════════
# 7. N-gram Correctness
# ══════════════════════════════════════════════════════════════════════

class TestNgramCorrectness:

    def test_bigram_match_suppresses_unigram_globally(self):
        """'not happy' match should suppress 'happy' across ALL categories."""
        from core.dictionary_engine import DictionaryEngine
        d = [{
            "name": "Test",
            "scoring": "binary",
            "categories": {
                "negated": ["not happy", "not good"],
                "positive": ["happy", "good"],
            }
        }]
        engine = DictionaryEngine(d)
        scores, matches = engine.analyze([["i", "am", "not", "happy"]])
        assert "not happy" in matches[0]["Test__negated"]
        assert "happy" not in matches[0]["Test__positive"]

    def test_unmatched_ngram_constituents_still_free(self):
        """If 'not happy' is NOT in the text, 'happy' should match normally."""
        from core.dictionary_engine import DictionaryEngine
        d = [{
            "name": "Test",
            "scoring": "binary",
            "categories": {
                "negated": ["not happy"],
                "positive": ["happy"],
            }
        }]
        engine = DictionaryEngine(d)
        scores, matches = engine.analyze([["very", "happy", "today"]])
        assert "happy" in matches[0]["Test__positive"]

    def test_weighted_ngram_scoring(self):
        """Weighted scores should work with n-gram entries."""
        from core.dictionary_engine import DictionaryEngine
        d = [{
            "name": "Test",
            "scoring": "weighted",
            "categories": {
                "sentiment": {"not happy": -3, "happy": 2, "love": 4}
            }
        }]
        engine = DictionaryEngine(d)
        scores, matches = engine.analyze([["i", "am", "not", "happy", "but", "love", "life"]])
        # "not happy" = -3, "love" = 4, "happy" suppressed
        assert scores.iloc[0]["Test__sentiment"] == pytest.approx(1.0)  # -3 + 4

    def test_no_double_count_across_categories(self):
        """N-gram suppression prevents inflation of unigram category scores."""
        from core.dictionary_engine import DictionaryEngine
        d = [{
            "name": "D",
            "scoring": "count",
            "categories": {
                "phrases": ["ice cream", "hot dog"],
                "food": ["ice", "cream", "hot", "dog"],
            }
        }]
        engine = DictionaryEngine(d)
        scores, matches = engine.analyze([["i", "love", "ice", "cream", "and", "hot", "dog"]])
        # "ice cream" and "hot dog" match phrases (2)
        # "ice", "cream", "hot", "dog" all suppressed from food
        assert scores.iloc[0]["D__phrases"] == 2
        assert scores.iloc[0]["D__food"] == 0  # all suppressed
