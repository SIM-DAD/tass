"""
Project manager — read/write .tass project files.
.tass is a ZIP archive containing:
  manifest.json, data.parquet, results.parquet,
  analysis_config.json, session_state.json,
  visualizations/chart_config.json
"""

from __future__ import annotations
import json
import os
import io
import zipfile
import datetime
from typing import Optional

import pandas as pd

from app import TASS_VERSION


class ProjectManager:
    """Static helpers for saving and loading .tass project files."""

    @staticmethod
    def save(path: str) -> None:
        from core.session import Session
        session = Session.instance()

        manifest = {
            "tass_version": TASS_VERSION,
            "created_at": datetime.datetime.utcnow().isoformat() + "Z",
            "modified_at": datetime.datetime.utcnow().isoformat() + "Z",
            "text_column": session.column_mapping.text_column,
            "group_column": session.column_mapping.group_column,
            "metadata_columns": session.column_mapping.metadata_columns,
            "row_count": session.row_count,
            "dictionaries_used": session.analysis_config.selected_dictionaries,
        }

        analysis_config = session.analysis_config.__dict__.copy()
        session_state = session.ui_state.copy()

        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
            zf.writestr("analysis_config.json", json.dumps(analysis_config, indent=2))
            zf.writestr("session_state.json", json.dumps(session_state, indent=2))

            # Save raw DataFrame
            if session.raw_df is not None:
                buf = io.BytesIO()
                session.raw_df.to_parquet(buf, index=True)
                zf.writestr("data.parquet", buf.getvalue())

            # Save results DataFrame
            if session.results.entry_scores is not None:
                buf = io.BytesIO()
                session.results.entry_scores.to_parquet(buf, index=True)
                zf.writestr("results.parquet", buf.getvalue())

            # Chart config placeholder
            chart_config = {"palette": session.ui_state.get("color_palette", "default")}
            zf.writestr("visualizations/chart_config.json", json.dumps(chart_config, indent=2))

        session.project_path = path
        session.mark_saved()

    @staticmethod
    def load(path: str) -> None:
        from core.session import Session, AnalysisResults

        with zipfile.ZipFile(path, "r") as zf:
            names = zf.namelist()

            manifest = json.loads(zf.read("manifest.json"))
            analysis_config_data = json.loads(zf.read("analysis_config.json"))
            session_state_data = json.loads(zf.read("session_state.json"))

            raw_df: Optional[pd.DataFrame] = None
            if "data.parquet" in names:
                buf = io.BytesIO(zf.read("data.parquet"))
                raw_df = pd.read_parquet(buf)

            results_df: Optional[pd.DataFrame] = None
            if "results.parquet" in names:
                buf = io.BytesIO(zf.read("results.parquet"))
                results_df = pd.read_parquet(buf)

        # Rebuild session
        session = Session.reset()
        session.column_mapping.text_column = manifest.get("text_column", "")
        session.column_mapping.group_column = manifest.get("group_column")
        session.column_mapping.metadata_columns = manifest.get("metadata_columns", [])

        from core.session import AnalysisConfig
        ac = AnalysisConfig()
        ac.selected_dictionaries = analysis_config_data.get("selected_dictionaries", [])
        ac.analysis_levels = analysis_config_data.get("analysis_levels", ["word", "entry", "document"])
        ac.groups = analysis_config_data.get("groups", {})
        ac.group_column = analysis_config_data.get("group_column")
        session.analysis_config = ac

        session.ui_state.update(session_state_data)
        session.raw_df = raw_df
        session.results = AnalysisResults(entry_scores=results_df)
        session.project_path = path
        session.mark_saved()
