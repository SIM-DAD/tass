"""
Statistics engine — descriptives, t-tests, ANOVA, post-hoc, effect sizes,
normality checks, confidence intervals, correlations, coverage.
All operations use SciPy + NumPy. Pure Python; no Qt imports.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Tuple
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
        # Degrees of freedom
        self.df_between: Optional[float] = None   # df1 (or single df for t-test)
        self.df_within: Optional[float] = None    # df2 (ANOVA only)
        # Confidence intervals: {group_name: (lower, upper)}
        self.confidence_intervals: Dict[str, Tuple[float, float]] = {}
        # Normality: {group_name: (W_statistic, p_value, is_normal)}
        self.normality: Dict[str, Tuple[float, float, bool]] = {}
        # Homogeneity of variance: (F_statistic, p_value, equal_variance_bool)
        self.levene: Optional[Tuple[float, float, bool]] = None
        # Post-hoc pairwise results: [(group_a, group_b, p_value, significant)]
        self.posthoc: List[Tuple[str, str, float, bool]] = []
        # Post-hoc method name (e.g. "Tukey HSD", "Dunn's test")
        self.posthoc_method: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "group_descriptives": self.group_descriptives,
            "test_name": self.test_name,
            "test_statistic": self.test_statistic,
            "p_value": self.p_value,
            "df_between": self.df_between,
            "df_within": self.df_within,
            "effect_size": self.effect_size,
            "effect_size_name": self.effect_size_name,
            "significant": self.significant,
            "confidence_intervals": {
                g: {"lower": ci[0], "upper": ci[1]}
                for g, ci in self.confidence_intervals.items()
            },
            "normality": {
                g: {"W": n[0], "p": n[1], "normal": n[2]}
                for g, n in self.normality.items()
            },
            "levene": {
                "F": self.levene[0], "p": self.levene[1], "equal": self.levene[2]
            } if self.levene else None,
            "posthoc": [
                {"group_a": a, "group_b": b, "p_value": p, "significant": s}
                for a, b, p, s in self.posthoc
            ],
            "posthoc_method": self.posthoc_method,
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
        correction: str = "bonferroni",
    ) -> Dict[str, GroupStats]:
        """
        Compute per-category group statistics.

        Args:
            scores_df: entry-level scores (rows=entries, cols=categories)
            group_series: Series with group labels aligned to scores_df index
            nonparametric: use Mann-Whitney U instead of t-test for 2 groups
            bonferroni: (deprecated, use correction) apply Bonferroni correction
            correction: "bonferroni", "fdr", or "none"

        Returns:
            {category_col: GroupStats}
        """
        groups = group_series.unique().tolist()
        n_groups = len(groups)
        n_categories = len(scores_df.columns)

        # Determine alpha threshold for significance
        if correction == "bonferroni":
            alpha = self.P_THRESHOLD / n_categories
        else:
            # For FDR and none, use unadjusted alpha during computation;
            # FDR adjustment is applied after all p-values are collected.
            alpha = self.P_THRESHOLD

        results: Dict[str, GroupStats] = {}

        for col in scores_df.columns:
            gs = GroupStats(category=col)

            group_data: Dict[str, np.ndarray] = {}
            for g in groups:
                mask = group_series == g
                arr = scores_df.loc[mask, col].dropna().values
                group_data[g] = arr
                gs.group_descriptives[str(g)] = _descriptives(arr)

            # --- Normality (Shapiro-Wilk per group) ---
            for g in groups:
                arr = group_data[g]
                if len(arr) >= 3:
                    try:
                        w_stat, w_p = stats.shapiro(arr)
                        gs.normality[str(g)] = (float(w_stat), float(w_p), w_p >= self.P_THRESHOLD)
                    except Exception:
                        gs.normality[str(g)] = (np.nan, np.nan, False)

            # --- Levene's test for homogeneity of variance ---
            if n_groups >= 2:
                arrays_for_levene = [group_data[g] for g in groups
                                     if len(group_data[g]) >= 2]
                if len(arrays_for_levene) >= 2:
                    try:
                        lev_stat, lev_p = stats.levene(*arrays_for_levene)
                        gs.levene = (float(lev_stat), float(lev_p), lev_p >= self.P_THRESHOLD)
                    except Exception:
                        pass

            # --- Confidence intervals (95% per group) ---
            for g in groups:
                arr = group_data[g]
                ci = _confidence_interval(arr, confidence=0.95)
                gs.confidence_intervals[str(g)] = ci

            # --- Inferential tests ---
            if n_groups == 2:
                g0, g1 = [group_data[g] for g in groups]
                if nonparametric:
                    stat, p = stats.mannwhitneyu(g0, g1, alternative="two-sided")
                    gs.test_name = "Mann-Whitney U"
                    gs.effect_size = _rank_biserial(g0, g1)
                    gs.effect_size_name = "r (rank-biserial)"
                    # Mann-Whitney: no traditional df
                else:
                    stat, p = stats.ttest_ind(g0, g1, equal_var=False)
                    gs.test_name = "Welch t-test"
                    gs.effect_size = _cohens_d(g0, g1)
                    gs.effect_size_name = "Cohen's d"
                    # Welch-Satterthwaite degrees of freedom
                    gs.df_between = _welch_df(g0, g1)
                gs.test_statistic = float(stat)
                gs.p_value = float(p)

            elif n_groups >= 3:
                arrays = [group_data[g] for g in groups]
                n_total = sum(len(a) for a in arrays)
                if nonparametric:
                    stat, p = stats.kruskal(*arrays)
                    gs.test_name = "Kruskal-Wallis"
                    gs.test_statistic = float(stat)
                    gs.p_value = float(p)
                    gs.effect_size = _kruskal_eta_squared(float(stat), n_total, n_groups)
                    gs.effect_size_name = "eta-squared (H)"
                    gs.df_between = float(n_groups - 1)   # chi-square-like df
                else:
                    stat, p = stats.f_oneway(*arrays)
                    gs.test_name = "One-way ANOVA"
                    gs.test_statistic = float(stat)
                    gs.p_value = float(p)
                    gs.effect_size = _eta_squared(arrays)
                    gs.effect_size_name = "eta-squared"
                    gs.df_between = float(n_groups - 1)
                    gs.df_within = float(n_total - n_groups)

                # --- Post-hoc (if omnibus is significant) ---
                if gs.p_value is not None and gs.p_value < alpha:
                    if nonparametric:
                        gs.posthoc = _dunns_test(groups, group_data, alpha)
                        gs.posthoc_method = "Dunn's test"
                    else:
                        gs.posthoc = _tukey_hsd(groups, group_data, alpha)
                        gs.posthoc_method = "Tukey HSD"

            if gs.p_value is not None:
                gs.significant = gs.p_value < alpha

            results[col] = gs

        # --- FDR (Benjamini-Hochberg) correction ---
        if correction == "fdr" and len(results) > 1:
            _apply_fdr(results, self.P_THRESHOLD)

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
    # Correlation matrix
    # ------------------------------------------------------------------

    def correlation_matrix(
        self,
        scores_df: pd.DataFrame,
        method: str = "pearson",
    ) -> pd.DataFrame:
        """
        Compute pairwise correlation between all category columns.

        Args:
            scores_df: entry-level scores (rows=entries, cols=categories)
            method: "pearson" or "spearman"

        Returns:
            Square DataFrame with correlation coefficients.
        """
        numeric = scores_df.select_dtypes(include=[np.number])
        return numeric.corr(method=method)

    def correlation_pvalues(
        self,
        scores_df: pd.DataFrame,
        method: str = "pearson",
    ) -> pd.DataFrame:
        """
        Compute p-values for pairwise correlations.

        Returns:
            Square DataFrame with p-values.
        """
        numeric = scores_df.select_dtypes(include=[np.number])
        cols = numeric.columns
        n = len(cols)
        pvals = pd.DataFrame(np.ones((n, n)), index=cols, columns=cols)

        for i in range(n):
            for j in range(i + 1, n):
                a = numeric.iloc[:, i].dropna()
                b = numeric.iloc[:, j].dropna()
                # Align on shared non-NaN indices
                shared = a.index.intersection(b.index)
                if len(shared) < 3:
                    pvals.iloc[i, j] = np.nan
                    pvals.iloc[j, i] = np.nan
                    continue
                if method == "spearman":
                    _, p = stats.spearmanr(a[shared], b[shared])
                else:
                    _, p = stats.pearsonr(a[shared], b[shared])
                pvals.iloc[i, j] = p
                pvals.iloc[j, i] = p

        return pvals

    # ------------------------------------------------------------------
    # Dictionary coverage
    # ------------------------------------------------------------------

    def coverage_stats(
        self,
        scores_df: pd.DataFrame,
        word_matches: Dict,
        token_counts: Optional[List[int]] = None,
    ) -> pd.DataFrame:
        """
        Compute dictionary coverage statistics per category.

        Args:
            scores_df: entry-level scores
            word_matches: {entry_idx: {category: [matched_words]}}
            token_counts: list of token counts per entry (len = n_entries)

        Returns:
            DataFrame with columns: category, entries_matched, entries_total,
            entry_coverage_pct, total_matches, mean_matches_per_entry,
            tokens_covered_pct (if token_counts provided).
        """
        n_entries = len(scores_df)
        categories = scores_df.columns.tolist()
        rows = []

        for cat in categories:
            matched_entries = 0
            total_matches = 0
            total_tokens_matched = 0

            for idx in range(n_entries):
                entry_matches = word_matches.get(idx, {}).get(cat, [])
                if entry_matches:
                    matched_entries += 1
                    total_matches += len(entry_matches)
                    total_tokens_matched += len(entry_matches)

            entry_coverage = (matched_entries / n_entries * 100) if n_entries > 0 else 0
            mean_matches = total_matches / n_entries if n_entries > 0 else 0

            row = {
                "category": cat,
                "entries_matched": matched_entries,
                "entries_total": n_entries,
                "entry_coverage_pct": round(entry_coverage, 2),
                "total_matches": total_matches,
                "mean_matches_per_entry": round(mean_matches, 4),
            }

            if token_counts is not None and len(token_counts) == n_entries:
                total_tokens = sum(token_counts)
                row["tokens_covered_pct"] = (
                    round(total_tokens_matched / total_tokens * 100, 2)
                    if total_tokens > 0 else 0
                )

            rows.append(row)

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


def _confidence_interval(arr: np.ndarray, confidence: float = 0.95) -> Tuple[float, float]:
    """Compute confidence interval for the mean using t-distribution."""
    if len(arr) < 2:
        return (np.nan, np.nan)
    mean = np.mean(arr)
    se = stats.sem(arr)
    h = se * stats.t.ppf((1 + confidence) / 2, len(arr) - 1)
    return (float(mean - h), float(mean + h))


def _kruskal_eta_squared(h_stat: float, n_total: int, k: int) -> float:
    """Eta-squared approximation for Kruskal-Wallis H statistic."""
    if n_total <= k:
        return 0.0
    return float((h_stat - k + 1) / (n_total - k))


def _welch_df(a: np.ndarray, b: np.ndarray) -> float:
    """Welch-Satterthwaite degrees of freedom for unequal-variance t-test."""
    n1, n2 = len(a), len(b)
    if n1 < 2 or n2 < 2:
        return float(n1 + n2 - 2)
    v1, v2 = np.var(a, ddof=1), np.var(b, ddof=1)
    num = (v1 / n1 + v2 / n2) ** 2
    denom = (v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1)
    if denom == 0:
        return float(n1 + n2 - 2)
    return float(num / denom)


def _tukey_hsd(
    groups: list,
    group_data: Dict[str, np.ndarray],
    alpha: float,
) -> List[Tuple[str, str, float, bool]]:
    """
    Tukey HSD pairwise comparisons.
    Returns list of (group_a, group_b, p_value, significant).
    """
    from itertools import combinations

    group_names = [str(g) for g in groups]
    all_data = np.concatenate([group_data[g] for g in groups])
    all_labels = np.concatenate([[str(g)] * len(group_data[g]) for g in groups])

    # Use scipy's tukey_hsd (available since scipy 1.8)
    arrays = [group_data[g].astype(float) for g in groups]
    try:
        result = stats.tukey_hsd(*arrays)
        posthoc = []
        for i, j in combinations(range(len(groups)), 2):
            p = float(result.pvalue[i][j])
            posthoc.append((group_names[i], group_names[j], p, p < alpha))
        return posthoc
    except Exception:
        # Fallback: pairwise t-tests with Bonferroni
        pairs = list(combinations(range(len(groups)), 2))
        n_pairs = len(pairs)
        posthoc = []
        for i, j in pairs:
            a, b = group_data[groups[i]], group_data[groups[j]]
            if len(a) < 2 or len(b) < 2:
                continue
            _, p = stats.ttest_ind(a, b, equal_var=False)
            p_adj = min(float(p) * n_pairs, 1.0)  # Bonferroni
            posthoc.append((group_names[i], group_names[j], p_adj, p_adj < alpha))
        return posthoc


def _apply_fdr(results: Dict[str, 'GroupStats'], alpha: float):
    """Apply Benjamini-Hochberg FDR correction to significance flags in-place."""
    # Collect all p-values with their keys
    items = [(k, gs) for k, gs in results.items() if gs.p_value is not None]
    if not items:
        return

    # Sort by p-value ascending
    items.sort(key=lambda x: x[1].p_value)
    m = len(items)

    # Benjamini-Hochberg: p_adjusted[i] = p[i] * m / rank
    # Then enforce monotonicity (adjusted p can't decrease as rank increases)
    adjusted = []
    for rank, (k, gs) in enumerate(items, 1):
        adj_p = min(gs.p_value * m / rank, 1.0)
        adjusted.append((k, gs, adj_p))

    # Enforce monotonicity from bottom up
    for i in range(len(adjusted) - 2, -1, -1):
        adjusted[i] = (adjusted[i][0], adjusted[i][1],
                        min(adjusted[i][2], adjusted[i + 1][2]))

    # Apply adjusted significance
    for k, gs, adj_p in adjusted:
        gs.significant = adj_p < alpha


def _dunns_test(
    groups: list,
    group_data: Dict[str, np.ndarray],
    alpha: float,
) -> List[Tuple[str, str, float, bool]]:
    """
    Dunn's test: pairwise Mann-Whitney U with Bonferroni correction.
    The correct nonparametric post-hoc for Kruskal-Wallis.
    Returns list of (group_a, group_b, adjusted_p_value, significant).
    """
    from itertools import combinations

    group_names = [str(g) for g in groups]
    pairs = list(combinations(range(len(groups)), 2))
    n_pairs = len(pairs)

    posthoc = []
    for i, j in pairs:
        a, b = group_data[groups[i]], group_data[groups[j]]
        if len(a) < 1 or len(b) < 1:
            continue
        try:
            _, p = stats.mannwhitneyu(a, b, alternative="two-sided")
            p_adj = min(float(p) * n_pairs, 1.0)  # Bonferroni correction
            posthoc.append((group_names[i], group_names[j], p_adj, p_adj < alpha))
        except Exception:
            continue
    return posthoc
