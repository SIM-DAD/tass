"""
APA 7th Edition formatting helpers for statistical output.

Used by both the Compare Panel (UI) and ExportEngine (file output).
All p-values, test statistics, and effect sizes follow APA 7th Ed. conventions.
"""

from __future__ import annotations
from typing import Optional


def format_p_apa(p: Optional[float]) -> str:
    """Format a p-value per APA 7th Edition.

    Rules:
    - No leading zero: .006 not 0.006
    - Exact to 3 decimals: p = .042
    - p < .001 only when truly < .001
    - Returns "—" for None
    """
    if p is None:
        return "—"
    if p < 0.001:
        return "< .001"
    # Format to 3 decimal places, strip leading zero
    formatted = f"{p:.3f}"                # "0.042"
    if formatted.startswith("0."):
        formatted = formatted[1:]         # ".042"
    return formatted


def sig_stars(p: Optional[float]) -> str:
    """Return APA significance stars for a p-value."""
    if p is None:
        return ""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "n.s."


def format_stat_with_df(
    test_name: Optional[str],
    statistic: Optional[float],
    df_between: Optional[float],
    df_within: Optional[float],
) -> str:
    """Format a test statistic with degrees of freedom in APA style.

    Examples:
        t(42.3) = 2.87
        F(2, 57) = 4.12
        H(2) = 8.34
        U = 145.00
    """
    if statistic is None:
        return "—"

    stat_str = f"{statistic:.2f}"

    if test_name == "Welch t-test" and df_between is not None:
        return f"t({df_between:.1f}) = {stat_str}"
    elif test_name == "One-way ANOVA" and df_between is not None and df_within is not None:
        return f"F({df_between:.0f}, {df_within:.0f}) = {stat_str}"
    elif test_name == "Kruskal-Wallis" and df_between is not None:
        return f"H({df_between:.0f}) = {stat_str}"
    elif test_name == "Mann-Whitney U":
        return f"U = {stat_str}"
    else:
        return stat_str


def effect_size_label(value: Optional[float], name: Optional[str]) -> str:
    """Return an interpretation label (small/medium/large) for an effect size.

    Cohen's d:          < 0.2 = negligible, 0.2–0.5 = small, 0.5–0.8 = medium, > 0.8 = large
    eta-squared:        < 0.01 = negligible, 0.01–0.06 = small, 0.06–0.14 = medium, > 0.14 = large
    r (rank-biserial):  < 0.1 = negligible, 0.1–0.3 = small, 0.3–0.5 = medium, > 0.5 = large
    """
    if value is None or name is None:
        return ""

    abs_val = abs(value)

    if "Cohen" in name:
        if abs_val < 0.2:
            return "negligible"
        if abs_val < 0.5:
            return "small"
        if abs_val < 0.8:
            return "medium"
        return "large"

    if "eta" in name.lower():
        if abs_val < 0.01:
            return "negligible"
        if abs_val < 0.06:
            return "small"
        if abs_val < 0.14:
            return "medium"
        return "large"

    if "rank-biserial" in name or "biserial" in name:
        if abs_val < 0.1:
            return "negligible"
        if abs_val < 0.3:
            return "small"
        if abs_val < 0.5:
            return "medium"
        return "large"

    return ""


def generate_apa_note(gs) -> str:
    """Generate an APA-style interpretive sentence for a GroupStats result.

    Example output:
        "For positive, the difference was statistically significant,
         t(42.3) = 2.87, p = .006, d = 0.74 [medium]."
    """
    if gs.test_statistic is None or gs.p_value is None:
        return ""

    cat = gs.category.split("__")[-1] if "__" in gs.category else gs.category

    stat_str = format_stat_with_df(gs.test_name, gs.test_statistic, gs.df_between, gs.df_within)
    p_str = format_p_apa(gs.p_value)

    eff_clause = ""
    if gs.effect_size is not None and gs.effect_size_name:
        label = effect_size_label(gs.effect_size, gs.effect_size_name)
        sym = "d"
        if "eta" in gs.effect_size_name.lower():
            sym = "\u03b7\u00b2"
        elif "biserial" in gs.effect_size_name:
            sym = "r"
        label_str = f" [{label}]" if label else ""
        eff_clause = f", {sym} = {abs(gs.effect_size):.2f}{label_str}"

    if gs.significant:
        return (
            f"For {cat}, the difference was statistically significant, "
            f"{stat_str}, p = {p_str}{eff_clause}."
        )
    else:
        return (
            f"For {cat}, the difference was not statistically significant, "
            f"{stat_str}, p = {p_str}{eff_clause}."
        )
