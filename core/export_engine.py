"""
Export engine — writes analysis results to CSV, Excel (multi-sheet), and chart files.
Appends citation block to text-based exports.
"""

from __future__ import annotations
import os
from typing import Optional, List, Dict, Any
import pandas as pd
import matplotlib.figure

from core.citation import citation_block


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

            # Sheet 4: Citation
            citation_df = pd.DataFrame({
                "Format": ["APA", "MLA", "Chicago", "DOI"],
                "Citation": [
                    _apa(), _mla(), _chicago(), _doi()
                ],
            })
            citation_df.to_excel(writer, sheet_name="Citation", index=False)

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
