"""
Visualization engine — generates Matplotlib/Seaborn figures from session results.
Returns matplotlib Figure objects; rendering to Qt canvas handled by visualization_panel.py.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.figure
import seaborn as sns

matplotlib.use("Agg")  # Non-interactive backend; Qt canvas handles display


# ------------------------------------------------------------------
# Color palettes
# ------------------------------------------------------------------

PALETTES = {
    "default": sns.color_palette("Set2"),
    "colorblind": sns.color_palette("colorblind"),
    "grayscale": sns.color_palette("Greys_r", 8),
}


class VisualizationEngine:
    def __init__(self, palette: str = "default", fig_width: float = 10.0, fig_height: float = 6.0):
        self._palette_name = palette
        self.palette = PALETTES.get(palette, PALETTES["default"])
        self.fig_width = fig_width
        self.fig_height = fig_height

    def _new_fig(self, width=None, height=None) -> Tuple[matplotlib.figure.Figure, plt.Axes]:
        w = width or self.fig_width
        h = height or self.fig_height
        fig, ax = plt.subplots(figsize=(w, h))
        self._apply_tass_theme(fig, ax)
        return fig, ax

    def _apply_tass_theme(self, fig, ax):
        fig.patch.set_facecolor("#FFFFFF")
        ax.set_facecolor("#FFFFFF")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#CCCCCC")
        ax.spines["bottom"].set_color("#CCCCCC")
        ax.tick_params(colors="#444444")
        ax.yaxis.label.set_color("#444444")
        ax.xaxis.label.set_color("#444444")
        ax.title.set_color("#222222")
        fig.tight_layout(pad=2.0)

    # ------------------------------------------------------------------
    # Bar chart — mean category scores
    # ------------------------------------------------------------------

    def bar_chart(
        self,
        summary_df: pd.DataFrame,
        title: str = "Mean Category Scores",
        top_n: int = 20,
    ) -> matplotlib.figure.Figure:
        """
        Horizontal bar chart of top_n category mean scores.
        summary_df must have columns ['category', 'mean'].
        """
        data = summary_df.nlargest(top_n, "mean").sort_values("mean")
        fig, ax = self._new_fig(height=max(4, len(data) * 0.4))
        ax.barh(data["category"], data["mean"], color=self.palette[0])
        ax.set_xlabel("Mean Score")
        ax.set_title(title)
        fig.tight_layout()
        return fig

    # ------------------------------------------------------------------
    # Bar chart — grouped (per group means for one category)
    # ------------------------------------------------------------------

    def grouped_bar_chart(
        self,
        per_group_summary: pd.DataFrame,
        categories: Optional[List[str]] = None,
        title: str = "Mean Scores by Group",
    ) -> matplotlib.figure.Figure:
        """
        Grouped bar chart: X=groups, bars=categories (or top N categories).
        per_group_summary: columns = [group, category, mean, ...]
        """
        if categories:
            data = per_group_summary[per_group_summary["category"].isin(categories)]
        else:
            # Top 10 by overall mean
            top_cats = (
                per_group_summary.groupby("category")["mean"]
                .mean()
                .nlargest(10)
                .index.tolist()
            )
            data = per_group_summary[per_group_summary["category"].isin(top_cats)]

        pivot = data.pivot(index="category", columns="group", values="mean")
        fig, ax = self._new_fig()
        pivot.plot(kind="barh", ax=ax, color=self.palette[: len(pivot.columns)])
        ax.set_xlabel("Mean Score")
        ax.set_title(title)
        ax.legend(title="Group", bbox_to_anchor=(1.05, 1), loc="upper left")
        fig.tight_layout()
        return fig

    # ------------------------------------------------------------------
    # Box plot
    # ------------------------------------------------------------------

    def box_plot(
        self,
        scores_df: pd.DataFrame,
        group_series: pd.Series,
        category: str,
        title: Optional[str] = None,
    ) -> matplotlib.figure.Figure:
        fig, ax = self._new_fig()
        combined = pd.DataFrame({
            "score": scores_df[category],
            "group": group_series,
        })
        sns.boxplot(data=combined, x="group", y="score", ax=ax, palette=self.palette)
        ax.set_xlabel("Group")
        ax.set_ylabel("Score")
        ax.set_title(title or f"Distribution: {category}")
        fig.tight_layout()
        return fig

    # ------------------------------------------------------------------
    # Violin plot
    # ------------------------------------------------------------------

    def violin_plot(
        self,
        scores_df: pd.DataFrame,
        group_series: pd.Series,
        category: str,
        title: Optional[str] = None,
    ) -> matplotlib.figure.Figure:
        fig, ax = self._new_fig()
        combined = pd.DataFrame({
            "score": scores_df[category],
            "group": group_series,
        })
        sns.violinplot(data=combined, x="group", y="score", ax=ax, palette=self.palette)
        ax.set_xlabel("Group")
        ax.set_ylabel("Score")
        ax.set_title(title or f"Distribution: {category}")
        fig.tight_layout()
        return fig

    # ------------------------------------------------------------------
    # Heatmap
    # ------------------------------------------------------------------

    def heatmap(
        self,
        summary_df: pd.DataFrame,
        title: str = "Category Score Heatmap",
        top_n: int = 30,
    ) -> matplotlib.figure.Figure:
        """
        Heatmap of category scores (can be per-group or per-segment).
        summary_df: index=categories, columns=groups (or segments)
        OR summary_df: columns=['category', 'mean', ...] for single-group.
        """
        if "group" in summary_df.columns:
            pivot = summary_df.pivot(index="category", columns="group", values="mean")
        else:
            pivot = summary_df.set_index("category")[["mean"]]

        if len(pivot) > top_n:
            pivot = pivot.loc[pivot.mean(axis=1).nlargest(top_n).index]

        fig, ax = self._new_fig(height=max(5, len(pivot) * 0.3))
        sns.heatmap(pivot, ax=ax, cmap="YlOrRd", linewidths=0.5, annot=len(pivot) <= 20)
        ax.set_title(title)
        ax.set_xlabel("")
        ax.set_ylabel("Category")
        fig.tight_layout()
        return fig

    # ------------------------------------------------------------------
    # Word cloud
    # ------------------------------------------------------------------

    def word_cloud(
        self,
        word_matches: Dict[str, List[str]],
        title: str = "Word Cloud",
        max_words: int = 200,
    ) -> matplotlib.figure.Figure:
        """
        word_matches: {category: [word, word, ...]} flattened across all entries.
        """
        from collections import Counter
        from wordcloud import WordCloud

        all_words = []
        for words in word_matches.values():
            all_words.extend(words)
        freq = Counter(all_words)

        if not freq:
            fig, ax = self._new_fig()
            ax.text(0.5, 0.5, "No matches found", ha="center", va="center",
                    fontsize=14, color="#888888")
            ax.set_axis_off()
            return fig

        _colormaps = {"grayscale": "Greys", "colorblind": "tab10", "default": "viridis"}
        colormap = _colormaps.get(self._palette_name, "viridis")
        wc = WordCloud(
            width=1200,
            height=600,
            background_color="white",
            max_words=max_words,
            colormap=colormap,
        ).generate_from_frequencies(freq)

        fig, ax = self._new_fig(width=12, height=6)
        ax.imshow(wc, interpolation="bilinear")
        ax.set_axis_off()
        ax.set_title(title)
        fig.tight_layout()
        return fig

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def save_figure(self, fig: matplotlib.figure.Figure, path: str, dpi: int = 300):
        """Save a figure to PNG or SVG based on file extension."""
        ext = path.rsplit(".", 1)[-1].lower()
        fmt = "svg" if ext == "svg" else "png"
        fig.savefig(path, format=fmt, dpi=dpi, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
