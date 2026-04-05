"""
Tests for core/formatting.py — APA 7th Edition formatting helpers.

Run with:  pytest tests/test_formatting.py -v
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.formatting import format_p_apa, sig_stars, format_stat_with_df, effect_size_label, generate_apa_note
from core.statistics_engine import GroupStats


class TestFormatPApa:
    """APA 7th p-value formatting."""

    def test_none_returns_dash(self):
        assert format_p_apa(None) == "—"

    def test_less_than_001(self):
        assert format_p_apa(0.0001) == "< .001"
        assert format_p_apa(0.0009) == "< .001"

    def test_no_leading_zero(self):
        result = format_p_apa(0.042)
        assert result.startswith(".") and not result.startswith("0.")

    def test_three_decimals(self):
        result = format_p_apa(0.042)
        assert result == ".042"

    def test_exact_values(self):
        assert format_p_apa(0.006) == ".006"
        assert format_p_apa(0.05) == ".050"
        assert format_p_apa(0.123) == ".123"
        assert format_p_apa(0.999) == ".999"

    def test_boundary_001(self):
        assert format_p_apa(0.001) == ".001"
        assert format_p_apa(0.00099) == "< .001"


class TestSigStars:
    """Significance star markers."""

    def test_none(self):
        assert sig_stars(None) == ""

    def test_three_stars(self):
        assert sig_stars(0.0001) == "***"

    def test_two_stars(self):
        assert sig_stars(0.005) == "**"

    def test_one_star(self):
        assert sig_stars(0.03) == "*"

    def test_ns(self):
        assert sig_stars(0.1) == "n.s."
        assert sig_stars(0.999) == "n.s."


class TestFormatStatWithDf:
    """Test statistic + degrees of freedom formatting."""

    def test_none_statistic(self):
        assert format_stat_with_df(None, None, None, None) == "—"

    def test_welch_t(self):
        result = format_stat_with_df("Welch t-test", 2.87, 42.3, None)
        assert result == "t(42.3) = 2.87"

    def test_anova(self):
        result = format_stat_with_df("One-way ANOVA", 4.12, 2.0, 57.0)
        assert result == "F(2, 57) = 4.12"

    def test_kruskal_wallis(self):
        result = format_stat_with_df("Kruskal-Wallis", 8.34, 2.0, None)
        assert result == "H(2) = 8.34"

    def test_mann_whitney(self):
        result = format_stat_with_df("Mann-Whitney U", 145.0, None, None)
        assert result == "U = 145.00"

    def test_no_df_fallback(self):
        result = format_stat_with_df("Unknown", 3.14, None, None)
        assert result == "3.14"


class TestEffectSizeLabel:
    """Effect size interpretation labels."""

    def test_none(self):
        assert effect_size_label(None, None) == ""
        assert effect_size_label(0.5, None) == ""

    def test_cohens_d_negligible(self):
        assert effect_size_label(0.1, "Cohen's d") == "negligible"

    def test_cohens_d_small(self):
        assert effect_size_label(0.3, "Cohen's d") == "small"

    def test_cohens_d_medium(self):
        assert effect_size_label(0.6, "Cohen's d") == "medium"

    def test_cohens_d_large(self):
        assert effect_size_label(1.2, "Cohen's d") == "large"

    def test_cohens_d_negative(self):
        # Uses absolute value
        assert effect_size_label(-0.9, "Cohen's d") == "large"

    def test_eta_squared_small(self):
        assert effect_size_label(0.03, "eta-squared") == "small"

    def test_eta_squared_medium(self):
        assert effect_size_label(0.10, "eta-squared") == "medium"

    def test_eta_squared_large(self):
        assert effect_size_label(0.20, "eta-squared") == "large"

    def test_eta_squared_h(self):
        assert effect_size_label(0.10, "eta-squared (H)") == "medium"

    def test_rank_biserial_small(self):
        assert effect_size_label(0.2, "r (rank-biserial)") == "small"

    def test_rank_biserial_large(self):
        assert effect_size_label(0.7, "r (rank-biserial)") == "large"


class TestGenerateApaNotes:
    """Auto-generated APA interpretive sentences."""

    def _make_gs(self, category="DictA__positive", test_name="Welch t-test",
                 statistic=2.87, p=0.006, df=42.3, effect=0.74,
                 effect_name="Cohen's d", significant=True):
        gs = GroupStats(category)
        gs.test_name = test_name
        gs.test_statistic = statistic
        gs.p_value = p
        gs.df_between = df
        gs.effect_size = effect
        gs.effect_size_name = effect_name
        gs.significant = significant
        return gs

    def test_significant_result(self):
        gs = self._make_gs()
        note = generate_apa_note(gs)
        assert "statistically significant" in note
        assert "t(42.3) = 2.87" in note
        assert "p = .006" in note
        assert "d = 0.74" in note
        assert "[medium]" in note

    def test_nonsignificant_result(self):
        gs = self._make_gs(p=0.342, significant=False)
        note = generate_apa_note(gs)
        assert "not statistically significant" in note
        assert "p = .342" in note

    def test_anova_result(self):
        gs = self._make_gs(test_name="One-way ANOVA", statistic=4.12,
                           df=2.0, effect=0.15, effect_name="eta-squared",
                           significant=True)
        gs.df_within = 57.0
        note = generate_apa_note(gs)
        assert "F(2, 57) = 4.12" in note
        assert "\u03b7\u00b2 = 0.15" in note  # η²
        assert "[large]" in note

    def test_empty_for_none(self):
        gs = GroupStats("test")
        assert generate_apa_note(gs) == ""

    def test_category_name_in_note(self):
        gs = self._make_gs(category="AFINN__sentiment")
        note = generate_apa_note(gs)
        assert "sentiment" in note
        assert "AFINN__" not in note  # should use short name
