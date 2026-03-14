"""
Tests for core/statistics_engine.py

Run with:  pytest tests/test_statistics_engine.py -v
"""

import os
import sys
import pytest
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.statistics_engine import StatisticsEngine, GroupStats


# ══════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════

@pytest.fixture
def simple_scores():
    """Small DataFrame with two categories and two groups."""
    return pd.DataFrame({
        "DictA__positive": [10.0, 20.0, 15.0, 5.0, 8.0, 25.0],
        "DictA__negative": [5.0,  3.0,  4.0,  9.0, 7.0, 2.0],
    })


@pytest.fixture
def two_group_series():
    return pd.Series(["group_A", "group_B", "group_A", "group_B", "group_A", "group_B"])


@pytest.fixture
def three_group_series():
    return pd.Series(["A", "B", "C", "A", "B", "C"])


@pytest.fixture
def engine():
    return StatisticsEngine()


# ══════════════════════════════════════════════════════════════════════
# document_summary
# ══════════════════════════════════════════════════════════════════════

class TestDocumentSummary:

    def test_returns_dataframe(self, engine, simple_scores):
        result = engine.document_summary(simple_scores)
        assert isinstance(result, pd.DataFrame)

    def test_has_one_row_per_category(self, engine, simple_scores):
        result = engine.document_summary(simple_scores)
        assert len(result) == len(simple_scores.columns)

    def test_has_required_stat_columns(self, engine, simple_scores):
        result = engine.document_summary(simple_scores)
        for col in ("mean", "std", "min", "max", "median", "count"):
            assert col in result.columns

    def test_category_column_present(self, engine, simple_scores):
        result = engine.document_summary(simple_scores)
        assert "category" in result.columns

    def test_mean_is_correct(self, engine, simple_scores):
        result = engine.document_summary(simple_scores)
        pos_row = result[result["category"] == "DictA__positive"]
        expected_mean = simple_scores["DictA__positive"].mean()
        assert pos_row["mean"].iloc[0] == pytest.approx(expected_mean)

    def test_min_max_correct(self, engine, simple_scores):
        result = engine.document_summary(simple_scores)
        neg_row = result[result["category"] == "DictA__negative"]
        assert neg_row["min"].iloc[0] == pytest.approx(simple_scores["DictA__negative"].min())
        assert neg_row["max"].iloc[0] == pytest.approx(simple_scores["DictA__negative"].max())

    def test_count_equals_n_rows(self, engine, simple_scores):
        result = engine.document_summary(simple_scores)
        assert all(result["count"] == len(simple_scores))


# ══════════════════════════════════════════════════════════════════════
# group_comparisons — two groups
# ══════════════════════════════════════════════════════════════════════

class TestGroupComparisonsTwoGroups:

    def test_returns_dict_of_group_stats(self, engine, simple_scores, two_group_series):
        result = engine.group_comparisons(simple_scores, two_group_series, bonferroni=False)
        assert isinstance(result, dict)
        assert len(result) == len(simple_scores.columns)

    def test_values_are_group_stats_instances(self, engine, simple_scores, two_group_series):
        result = engine.group_comparisons(simple_scores, two_group_series, bonferroni=False)
        for v in result.values():
            assert isinstance(v, GroupStats)

    def test_default_test_is_welch_t(self, engine, simple_scores, two_group_series):
        result = engine.group_comparisons(simple_scores, two_group_series,
                                          nonparametric=False, bonferroni=False)
        for gs in result.values():
            assert gs.test_name == "Welch t-test"

    def test_nonparametric_uses_mannwhitney(self, engine, simple_scores, two_group_series):
        result = engine.group_comparisons(simple_scores, two_group_series,
                                          nonparametric=True, bonferroni=False)
        for gs in result.values():
            assert gs.test_name == "Mann-Whitney U"

    def test_p_value_present(self, engine, simple_scores, two_group_series):
        result = engine.group_comparisons(simple_scores, two_group_series, bonferroni=False)
        for gs in result.values():
            assert gs.p_value is not None
            assert 0.0 <= gs.p_value <= 1.0

    def test_test_statistic_present(self, engine, simple_scores, two_group_series):
        result = engine.group_comparisons(simple_scores, two_group_series, bonferroni=False)
        for gs in result.values():
            assert gs.test_statistic is not None
            assert isinstance(gs.test_statistic, float)

    def test_effect_size_name_for_t_test(self, engine, simple_scores, two_group_series):
        result = engine.group_comparisons(simple_scores, two_group_series,
                                          nonparametric=False, bonferroni=False)
        for gs in result.values():
            assert gs.effect_size_name == "Cohen's d"

    def test_descriptives_per_group(self, engine, simple_scores, two_group_series):
        result = engine.group_comparisons(simple_scores, two_group_series, bonferroni=False)
        for gs in result.values():
            assert "group_A" in gs.group_descriptives
            assert "group_B" in gs.group_descriptives
            for desc in gs.group_descriptives.values():
                for stat in ("mean", "std", "min", "max", "median", "n"):
                    assert stat in desc

    def test_significant_flag_set(self, engine, simple_scores, two_group_series):
        result = engine.group_comparisons(simple_scores, two_group_series, bonferroni=False)
        for gs in result.values():
            assert gs.significant is not None
            assert isinstance(gs.significant, bool)


# ══════════════════════════════════════════════════════════════════════
# group_comparisons — three groups (ANOVA)
# ══════════════════════════════════════════════════════════════════════

class TestGroupComparisonsThreeGroups:

    def test_uses_anova_for_three_groups(self, engine, simple_scores, three_group_series):
        result = engine.group_comparisons(simple_scores, three_group_series, bonferroni=False)
        for gs in result.values():
            assert gs.test_name == "One-way ANOVA"

    def test_effect_size_is_eta_squared(self, engine, simple_scores, three_group_series):
        result = engine.group_comparisons(simple_scores, three_group_series, bonferroni=False)
        for gs in result.values():
            assert gs.effect_size_name == "eta-squared"

    def test_eta_squared_in_range(self, engine, simple_scores, three_group_series):
        result = engine.group_comparisons(simple_scores, three_group_series, bonferroni=False)
        for gs in result.values():
            if gs.effect_size is not None and not np.isnan(gs.effect_size):
                assert 0.0 <= gs.effect_size <= 1.0

    def test_three_groups_in_descriptives(self, engine, simple_scores, three_group_series):
        result = engine.group_comparisons(simple_scores, three_group_series, bonferroni=False)
        for gs in result.values():
            assert len(gs.group_descriptives) == 3


# ══════════════════════════════════════════════════════════════════════
# Bonferroni correction
# ══════════════════════════════════════════════════════════════════════

class TestBonferroni:

    def test_bonferroni_makes_fewer_or_equal_significant(self, engine):
        rng = np.random.default_rng(42)
        scores = pd.DataFrame({
            f"cat{i}": rng.normal(0, 1, 100) for i in range(20)
        })
        groups = pd.Series(["A"] * 50 + ["B"] * 50)

        result_no_bonf = engine.group_comparisons(scores, groups, bonferroni=False)
        result_bonf = engine.group_comparisons(scores, groups, bonferroni=True)

        n_sig_no = sum(gs.significant for gs in result_no_bonf.values())
        n_sig_bonf = sum(gs.significant for gs in result_bonf.values())
        assert n_sig_bonf <= n_sig_no


# ══════════════════════════════════════════════════════════════════════
# per_group_summary
# ══════════════════════════════════════════════════════════════════════

class TestPerGroupSummary:

    def test_returns_dataframe(self, engine, simple_scores, two_group_series):
        result = engine.per_group_summary(simple_scores, two_group_series)
        assert isinstance(result, pd.DataFrame)

    def test_has_group_and_category_columns(self, engine, simple_scores, two_group_series):
        result = engine.per_group_summary(simple_scores, two_group_series)
        assert "group" in result.columns
        assert "category" in result.columns

    def test_n_rows_is_groups_times_categories(self, engine, simple_scores, two_group_series):
        result = engine.per_group_summary(simple_scores, two_group_series)
        n_groups = two_group_series.nunique()
        n_cats = len(simple_scores.columns)
        assert len(result) == n_groups * n_cats

    def test_mean_values_correct(self, engine, simple_scores, two_group_series):
        result = engine.per_group_summary(simple_scores, two_group_series)
        grp_a = result[
            (result["group"] == "group_A") & (result["category"] == "DictA__positive")
        ]
        expected = simple_scores.loc[two_group_series == "group_A", "DictA__positive"].mean()
        assert grp_a["mean"].iloc[0] == pytest.approx(expected)


# ══════════════════════════════════════════════════════════════════════
# GroupStats.to_dict()
# ══════════════════════════════════════════════════════════════════════

class TestGroupStatsToDict:

    def test_to_dict_contains_all_keys(self, engine, simple_scores, two_group_series):
        result = engine.group_comparisons(simple_scores, two_group_series, bonferroni=False)
        for gs in result.values():
            d = gs.to_dict()
            for key in ("category", "group_descriptives", "test_name",
                        "test_statistic", "p_value", "effect_size",
                        "effect_size_name", "significant"):
                assert key in d

    def test_to_dict_is_json_serializable(self, engine, simple_scores, two_group_series):
        import json
        result = engine.group_comparisons(simple_scores, two_group_series, bonferroni=False)
        for gs in result.values():
            json.dumps(gs.to_dict(), default=str)  # should not raise
