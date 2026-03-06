"""
Statistics engine — descriptives, t-tests, ANOVA, effect sizes.
All operations use SciPy + NumPy. Pure Python; no Qt imports.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
from scipy import stats


class GroupStats:
    """Descriptive + inferential statistics for one category across groups."""

    def __init__(self, category: str):
        self.category = category
        self.group_descriptives: Dict[str, Dict[str, float]] = {}
        self.test_name: Optional[str] = None
        self.test_statistic: Optional[float] = None
        self.p_value: Optional[float] = None
        self.effect_size: Optional[float] = None
        self.effect_size_name: Optional[str] = None
        self.significant: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "group_descriptives": self.group_descriptives,
            "test_name": self.test_name,
            "test_statistic": self.test_statistic,
            "p_value": self.p_value,
            "effect_size": self.effect_size,
            "effect_size_name": self.effect_size_name,
            "significant": self.significant,
        }


class StatisticsEngine:
    """
    Computes descriptive and inferential statistics on entry-level score DataFrames.
    """

    P_THRESHOLD = 0.05

    # ------------------------------------------------------------------
    # Document-level (aggregate over entire dataset)
    # ------------------------------------------------------------------

    def document_summary(self, scores_df: pd.DataFrame) -> pd.DataFrame:
        """
        Returns a summary DataFrame with mean, SD, min, max, median for every category.
        Rows = categories, Columns = stat names.
        """
        numeric = scores_df.select_dtypes(include=[np.number])
        summary = pd.DataFrame({
            "mean": numeric.mean(),
            "std": numeric.std(),
            "min": numeric.min(),
            "max": numeric.max(),
            "median": numeric.median(),
            "count": numeric.count(),
        })
        summary.index.name = "category"
        return summary.reset_index()

    # ------------------------------------------------------------------
    # Group comparisons
    # ------------------------------------------------------------------

    def group_comparisons(
        self,
        scores_df: pd.DataFrame,
        group_series: pd.Series,
        nonparametric: bool = False,
        bonferroni: bool = True,
    ) -> Dict[str, GroupStats]:
        """
        Compute per-category group statistics.

        Args:
            scores_df: entry-level scores (rows=entries, cols=categories)
            group_series: Series with group labels aligned to scores_df index
            nonparametric: use Mann-Whitney U instead of t-test for 2 groups
            bonferroni: apply Bonferroni correction to p-values

        Returns:
            {category_col: GroupStats}
        """
        groups = group_series.unique().tolist()
        n_groups = len(groups)
        n_categories = len(scores_df.columns)
        alpha = self.P_THRESHOLD / n_categories if bonferroni else self.P_THRESHOLD

        results: Dict[str, GroupStats] = {}

        for col in scores_df.columns:
            gs = GroupStats(category=col)

            group_data: Dict[str, np.ndarray] = {}
            for g in groups:
                mask = group_series == g
                arr = scores_df.loc[mask, col].dropna().values
                group_data[g] = arr
                gs.group_descriptives[str(g)] = _descriptives(arr)

            if n_groups == 2:
                g0, g1 = [group_data[g] for g in groups]
                if nonparametric:
                    stat, p = stats.mannwhitneyu(g0, g1, alternative="two-sided")
                    gs.test_name = "Mann-Whitney U"
                    gs.effect_size = _rank_biserial(g0, g1)
                    gs.effect_size_name = "r (rank-biserial)"
                else:
                    stat, p = stats.ttest_ind(g0, g1, equal_var=False)
                    gs.test_name = "Welch t-test"
                    gs.effect_size = _cohens_d(g0, g1)
                    gs.effect_size_name = "Cohen's d"
                gs.test_statistic = float(stat)
                gs.p_value = float(p)

            elif n_groups >= 3:
                arrays = [group_data[g] for g in groups]
                stat, p = stats.f_oneway(*arrays)
                gs.test_name = "One-way ANOVA"
                gs.test_statistic = float(stat)
                gs.p_value = float(p)
                gs.effect_size = _eta_squared(arrays)
                gs.effect_size_name = "eta-squared"

            if gs.p_value is not None:
                gs.significant = gs.p_value < alpha

            results[col] = gs

        return results

    # ------------------------------------------------------------------
    # Per-group descriptives
    # ------------------------------------------------------------------

    def per_group_summary(
        self,
        scores_df: pd.DataFrame,
        group_series: pd.Series,
    ) -> pd.DataFrame:
        """
        Returns a DataFrame with descriptive stats per group per category.
        """
        combined = scores_df.copy()
        combined["_group"] = group_series.values
        rows = []
        for g, grp in combined.groupby("_group"):
            for col in scores_df.columns:
                d = _descriptives(grp[col].dropna().values)
                rows.append({"group": g, "category": col, **d})
        return pd.DataFrame(rows)


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------

def _descriptives(arr: np.ndarray) -> Dict[str, float]:
    if len(arr) == 0:
        return {"mean": np.nan, "std": np.nan, "min": np.nan,
                "max": np.nan, "median": np.nan, "n": 0}
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0,
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "median": float(np.median(arr)),
        "n": int(len(arr)),
    }


def _cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 2 or len(b) < 2:
        return np.nan
    mean_diff = np.mean(a) - np.mean(b)
    pooled_sd = np.sqrt(
        ((len(a) - 1) * np.var(a, ddof=1) + (len(b) - 1) * np.var(b, ddof=1))
        / (len(a) + len(b) - 2)
    )
    if pooled_sd == 0:
        return 0.0
    return float(mean_diff / pooled_sd)


def _eta_squared(arrays: List[np.ndarray]) -> float:
    grand_mean = np.mean(np.concatenate(arrays))
    ss_between = sum(len(a) * (np.mean(a) - grand_mean) ** 2 for a in arrays)
    ss_total = sum(np.sum((a - grand_mean) ** 2) for a in arrays)
    if ss_total == 0:
        return 0.0
    return float(ss_between / ss_total)


def _rank_biserial(a: np.ndarray, b: np.ndarray) -> float:
    """Rank-biserial correlation as effect size for Mann-Whitney U."""
    n1, n2 = len(a), len(b)
    if n1 == 0 or n2 == 0:
        return np.nan
    u1, _ = stats.mannwhitneyu(a, b, alternative="two-sided")
    return float(1 - (2 * u1) / (n1 * n2))
