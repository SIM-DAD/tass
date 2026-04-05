"""
Export engine — writes analysis results to CSV, Excel (multi-sheet), and chart files.
Appends citation block to text-based exports.
"""

from __future__ import annotations
import datetime
import os
from typing import Optional, List, Dict, Any
import pandas as pd
import matplotlib.figure

from core.citation import citation_block
from core.formatting import format_p_apa, sig_stars, format_stat_with_df, effect_size_label


class ExportEngine:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # CSV export
    # ------------------------------------------------------------------

    def export_csv(
        self,
        entry_scores: pd.DataFrame,
        raw_df: Optional[pd.DataFrame] = None,
        filename: str = "tass_results.csv",
        metadata_columns: Optional[List[str]] = None,
    ) -> str:
        path = os.path.join(self.output_dir, filename)

        if raw_df is not None and metadata_columns:
            meta = raw_df[metadata_columns].reset_index(drop=True)
            out = pd.concat([meta, entry_scores.reset_index(drop=True)], axis=1)
        else:
            out = entry_scores.copy()

        out.to_csv(path, index=False, encoding="utf-8")

        # Append citation block
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(citation_block())

        return path

    # ------------------------------------------------------------------
    # Excel export (multi-sheet)
    # ------------------------------------------------------------------

    def export_excel(
        self,
        entry_scores: pd.DataFrame,
        summary_df: Optional[pd.DataFrame] = None,
        group_stats_df: Optional[pd.DataFrame] = None,
        raw_df: Optional[pd.DataFrame] = None,
        metadata_columns: Optional[List[str]] = None,
        method_info: Optional[Dict[str, Any]] = None,
        filename: str = "tass_results.xlsx",
    ) -> str:
        path = os.path.join(self.output_dir, filename)

        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            # Sheet 1: Raw scores (with metadata if available)
            if raw_df is not None and metadata_columns:
                meta = raw_df[metadata_columns].reset_index(drop=True)
                raw_sheet = pd.concat([meta, entry_scores.reset_index(drop=True)], axis=1)
            else:
                raw_sheet = entry_scores.copy()
            raw_sheet.to_excel(writer, sheet_name="Raw Scores", index=False)

            # Sheet 2: Summary statistics
            if summary_df is not None:
                summary_df.to_excel(writer, sheet_name="Summary Statistics", index=False)
            else:
                summary_placeholder = pd.DataFrame({"Note": ["Run analysis to generate summary."]})
                summary_placeholder.to_excel(writer, sheet_name="Summary Statistics", index=False)

            # Sheet 3: Group comparison results
            if group_stats_df is not None:
                group_stats_df.to_excel(writer, sheet_name="Group Comparisons", index=False)
            else:
                group_placeholder = pd.DataFrame({"Note": ["Define groups to generate comparisons."]})
                group_placeholder.to_excel(writer, sheet_name="Group Comparisons", index=False)

            # Sheet 4: Method documentation
            if method_info:
                method_rows = [
                    {"Parameter": k, "Value": str(v)}
                    for k, v in method_info.items()
                ]
                method_df = pd.DataFrame(method_rows)
            else:
                method_df = pd.DataFrame({
                    "Parameter": [
                        "TASS Version",
                        "Export Date",
                        "Note",
                    ],
                    "Value": [
                        "1.0.0",
                        datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                        "Full method info available when exported from an active analysis session.",
                    ],
                })
            method_df.to_excel(writer, sheet_name="Method", index=False)

            # Sheet 5: Citation
            citation_df = pd.DataFrame({
                "Format": ["APA", "MLA", "Chicago", "DOI"],
                "Citation": [
                    _apa(), _mla(), _chicago(), _doi()
                ],
            })
            citation_df.to_excel(writer, sheet_name="Citation", index=False)

        return path

    # ------------------------------------------------------------------
    # APA-formatted table export
    # ------------------------------------------------------------------

    def export_apa_table(
        self,
        group_stats: Dict[str, Any],
        group_names: List[str],
        filename: str = "tass_apa_table.txt",
    ) -> str:
        """
        Export group comparison results as an APA 7th Edition formatted table.
        Produces a plain-text table suitable for pasting into manuscripts.

        APA table format:
        - Title in italics (indicated by underscores in plain text)
        - Column headers with horizontal rules
        - Means and SDs per group
        - Test statistics, p-values, effect sizes
        - Notes below with significance markers and test descriptions
        """
        path = os.path.join(self.output_dir, filename)

        lines = []
        lines.append("_Table X_")
        lines.append("_Group Comparison Results for Dictionary Category Scores_")
        lines.append("")

        # Determine max widths for alignment
        cat_width = max(
            20,
            max((len(k.split("__")[-1] if "__" in k else k) for k in group_stats), default=20)
        )
        group_col_width = 16

        # Header row
        header_parts = [f"{'Category':<{cat_width}}"]
        for g in group_names:
            header_parts.append(f"{'M (SD) ' + str(g):>{group_col_width}}")
        header_parts.extend([
            f"{'Test Statistic':>20}",
            f"{'p':>10}",
            f"{'Effect':>8}",
            f"{'Size':>10}",
        ])
        header = "  ".join(header_parts)

        rule = "─" * len(header)
        lines.append(rule)
        lines.append(header)
        lines.append(rule)

        # Data rows
        for col_key, gs in sorted(group_stats.items()):
            cat = col_key.split("__")[-1] if "__" in col_key else col_key
            parts = [f"{cat:<{cat_width}}"]

            for g in group_names:
                desc = gs.group_descriptives.get(str(g), {})
                m = desc.get("mean")
                sd = desc.get("std")
                if m is not None and sd is not None:
                    cell = f"{m:.2f} ({sd:.2f})"
                else:
                    cell = "—"
                parts.append(f"{cell:>{group_col_width}}")

            # Test statistic with df in APA format
            stat_str = format_stat_with_df(
                gs.test_name, gs.test_statistic, gs.df_between, gs.df_within
            )

            # p-value in APA format + significance stars
            p_str = format_p_apa(gs.p_value)
            stars = sig_stars(gs.p_value)
            p_display = p_str + stars if stars and stars != "n.s." else p_str

            # Effect size + interpretation
            eff = f"{gs.effect_size:.2f}" if gs.effect_size is not None else "—"
            eff_label = effect_size_label(gs.effect_size, gs.effect_size_name)
            eff_interp = f"[{eff_label}]" if eff_label else ""

            parts.extend([
                f"{stat_str:>20}",
                f"{p_display:>10}",
                f"{eff:>8}",
                f"{eff_interp:>10}",
            ])

            lines.append("  ".join(parts))

        lines.append(rule)

        # Notes
        lines.append("")
        lines.append("_Note._ M = mean; SD = standard deviation.")

        test_names = set(gs.test_name for gs in group_stats.values() if gs.test_name)
        effect_names = set(gs.effect_size_name for gs in group_stats.values() if gs.effect_size_name)

        if test_names:
            lines.append(f"Tests: {', '.join(sorted(test_names))}.")
        if effect_names:
            lines.append(f"Effect sizes: {', '.join(sorted(effect_names))}.")
        lines.append("Effect size interpretation: Cohen's d (< .2 negligible, .2–.5 small, .5–.8 medium, > .8 large);")
        lines.append("  eta-squared (< .01 negligible, .01–.06 small, .06–.14 medium, > .14 large).")

        lines.append("* p < .05. ** p < .01. *** p < .001.")
        lines.append("")
        lines.append(citation_block())

        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))

        return path

    # ------------------------------------------------------------------
    # Reproducibility metadata sidecar
    # ------------------------------------------------------------------

    def export_metadata_sidecar(
        self,
        method_info: Dict[str, Any],
        filename: str = "tass_metadata.json",
    ) -> str:
        """Write a JSON sidecar file alongside exports for reproducibility."""
        import json
        path = os.path.join(self.output_dir, filename)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(method_info, fh, indent=2, default=str)
        return path

    # ------------------------------------------------------------------
    # Chart export
    # ------------------------------------------------------------------

    def export_figure(
        self,
        fig: matplotlib.figure.Figure,
        filename: str,
        dpi: int = 300,
    ) -> List[str]:
        """Export a figure as both PNG and SVG."""
        from core.visualization_engine import VisualizationEngine
        viz = VisualizationEngine()
        paths = []
        for ext in ("png", "svg"):
            fname = filename if filename.endswith(f".{ext}") else f"{os.path.splitext(filename)[0]}.{ext}"
            path = os.path.join(self.output_dir, fname)
            viz.save_figure(fig, path, dpi=dpi)
            paths.append(path)
        return paths

    def export_all_figures(
        self,
        figures: Dict[str, matplotlib.figure.Figure],
        dpi: int = 300,
    ) -> List[str]:
        all_paths = []
        for name, fig in figures.items():
            safe_name = name.replace(" ", "_").replace("/", "-")
            all_paths.extend(self.export_figure(fig, safe_name, dpi=dpi))
        return all_paths


# ------------------------------------------------------------------
# Citation helpers (avoid circular import from app)
# ------------------------------------------------------------------

def _apa():
    try:
        from core.citation import apa_citation
        return apa_citation()
    except Exception:
        return "See TASS documentation for citation."

def _mla():
    try:
        from core.citation import mla_citation
        return mla_citation()
    except Exception:
        return ""

def _chicago():
    try:
        from core.citation import chicago_citation
        return chicago_citation()
    except Exception:
        return ""

def _doi():
    try:
        from core.citation import ZENODO_DOI
        return f"https://doi.org/{ZENODO_DOI}"
    except Exception:
        return ""
