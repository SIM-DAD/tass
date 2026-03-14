"""
Tests for core/project.py — .tass project round-trip (save + load).

Run with:  pytest tests/test_project.py -v
"""

import os
import sys
import json
import tempfile
import zipfile

import pytest
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.project import ProjectManager, TASS_VERSION
from core.session import Session, AnalysisConfig, AnalysisResults, ColumnMapping


# ══════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════

def _make_session(
    text_col: str = "text",
    group_col: str = "group",
    dicts: list | None = None,
    with_results: bool = False,
) -> Session:
    """Reset the singleton and populate it with test data."""
    session = Session.reset()

    session.raw_df = pd.DataFrame({
        text_col: ["Hello world", "Goodbye world", "Test entry"],
        group_col: ["A", "B", "A"],
        "meta": [1, 2, 3],
    })
    session.column_mapping.text_column = text_col
    session.column_mapping.group_column = group_col
    session.column_mapping.metadata_columns = ["meta"]

    session.analysis_config.selected_dictionaries = dicts or ["afinn165"]
    session.analysis_config.analysis_levels = ["word", "entry"]
    session.analysis_config.group_column = group_col
    session.analysis_config.groups = {"A": ["A"], "B": ["B"]}

    if with_results:
        session.results = AnalysisResults(
            entry_scores=pd.DataFrame({
                "afinn165__sentiment": [1.0, -2.0, 0.0],
            })
        )

    session.ui_state["color_palette"] = "viridis"
    return session


# ══════════════════════════════════════════════════════════════════════
# ZIP structure
# ══════════════════════════════════════════════════════════════════════

class TestZipStructure:

    def test_creates_valid_zip(self, tmp_path):
        _make_session()
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        assert zipfile.is_zipfile(path)

    def test_manifest_present(self, tmp_path):
        _make_session()
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        with zipfile.ZipFile(path) as zf:
            assert "manifest.json" in zf.namelist()

    def test_analysis_config_present(self, tmp_path):
        _make_session()
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        with zipfile.ZipFile(path) as zf:
            assert "analysis_config.json" in zf.namelist()

    def test_session_state_present(self, tmp_path):
        _make_session()
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        with zipfile.ZipFile(path) as zf:
            assert "session_state.json" in zf.namelist()

    def test_data_parquet_present(self, tmp_path):
        _make_session()
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        with zipfile.ZipFile(path) as zf:
            assert "data.parquet" in zf.namelist()

    def test_chart_config_present(self, tmp_path):
        _make_session()
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        with zipfile.ZipFile(path) as zf:
            assert "visualizations/chart_config.json" in zf.namelist()

    def test_results_parquet_present_when_results_exist(self, tmp_path):
        _make_session(with_results=True)
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        with zipfile.ZipFile(path) as zf:
            assert "results.parquet" in zf.namelist()

    def test_results_parquet_absent_when_no_results(self, tmp_path):
        _make_session(with_results=False)
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        with zipfile.ZipFile(path) as zf:
            assert "results.parquet" not in zf.namelist()


# ══════════════════════════════════════════════════════════════════════
# Manifest content
# ══════════════════════════════════════════════════════════════════════

class TestManifest:

    def _load_manifest(self, path: str) -> dict:
        with zipfile.ZipFile(path) as zf:
            return json.loads(zf.read("manifest.json"))

    def test_tass_version_field(self, tmp_path):
        _make_session()
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        manifest = self._load_manifest(path)
        assert manifest["tass_version"] == TASS_VERSION

    def test_text_column_field(self, tmp_path):
        _make_session(text_col="body")
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        manifest = self._load_manifest(path)
        assert manifest["text_column"] == "body"

    def test_group_column_field(self, tmp_path):
        _make_session(group_col="condition")
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        manifest = self._load_manifest(path)
        assert manifest["group_column"] == "condition"

    def test_row_count_field(self, tmp_path):
        _make_session()
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        manifest = self._load_manifest(path)
        assert manifest["row_count"] == 3

    def test_dictionaries_used_field(self, tmp_path):
        _make_session(dicts=["afinn165", "vader_lexicon"])
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        manifest = self._load_manifest(path)
        assert manifest["dictionaries_used"] == ["afinn165", "vader_lexicon"]

    def test_created_at_is_iso_string(self, tmp_path):
        _make_session()
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        manifest = self._load_manifest(path)
        assert isinstance(manifest["created_at"], str)
        assert "T" in manifest["created_at"]  # ISO format


# ══════════════════════════════════════════════════════════════════════
# Round-trip: column mapping
# ══════════════════════════════════════════════════════════════════════

class TestRoundTripColumnMapping:

    def test_text_column_restored(self, tmp_path):
        _make_session(text_col="content")
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        ProjectManager.load(path)
        assert Session.instance().column_mapping.text_column == "content"

    def test_group_column_restored(self, tmp_path):
        _make_session(group_col="category")
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        ProjectManager.load(path)
        assert Session.instance().column_mapping.group_column == "category"

    def test_metadata_columns_restored(self, tmp_path):
        _make_session()
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        ProjectManager.load(path)
        assert "meta" in Session.instance().column_mapping.metadata_columns


# ══════════════════════════════════════════════════════════════════════
# Round-trip: analysis config
# ══════════════════════════════════════════════════════════════════════

class TestRoundTripAnalysisConfig:

    def test_selected_dictionaries_restored(self, tmp_path):
        _make_session(dicts=["afinn165", "mfd2"])
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        ProjectManager.load(path)
        assert Session.instance().analysis_config.selected_dictionaries == ["afinn165", "mfd2"]

    def test_analysis_levels_restored(self, tmp_path):
        _make_session()
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        ProjectManager.load(path)
        assert "word" in Session.instance().analysis_config.analysis_levels
        assert "entry" in Session.instance().analysis_config.analysis_levels

    def test_groups_restored(self, tmp_path):
        _make_session()
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        ProjectManager.load(path)
        groups = Session.instance().analysis_config.groups
        assert "A" in groups
        assert "B" in groups

    def test_group_column_restored(self, tmp_path):
        _make_session(group_col="grp")
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        ProjectManager.load(path)
        assert Session.instance().analysis_config.group_column == "grp"


# ══════════════════════════════════════════════════════════════════════
# Round-trip: DataFrames
# ══════════════════════════════════════════════════════════════════════

class TestRoundTripDataFrames:

    def test_raw_df_shape_preserved(self, tmp_path):
        _make_session()
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        ProjectManager.load(path)
        df = Session.instance().raw_df
        assert df is not None
        assert df.shape == (3, 3)

    def test_raw_df_text_column_intact(self, tmp_path):
        _make_session(text_col="text")
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        ProjectManager.load(path)
        df = Session.instance().raw_df
        assert "text" in df.columns
        assert df["text"].iloc[0] == "Hello world"

    def test_results_df_restored_when_present(self, tmp_path):
        _make_session(with_results=True)
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        ProjectManager.load(path)
        results = Session.instance().results.entry_scores
        assert results is not None
        assert "afinn165__sentiment" in results.columns

    def test_results_none_when_not_saved(self, tmp_path):
        _make_session(with_results=False)
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        ProjectManager.load(path)
        assert Session.instance().results.entry_scores is None


# ══════════════════════════════════════════════════════════════════════
# Round-trip: UI state
# ══════════════════════════════════════════════════════════════════════

class TestRoundTripUIState:

    def test_color_palette_restored(self, tmp_path):
        _make_session()
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        ProjectManager.load(path)
        assert Session.instance().ui_state.get("color_palette") == "viridis"


# ══════════════════════════════════════════════════════════════════════
# Project path and dirty tracking
# ══════════════════════════════════════════════════════════════════════

class TestProjectPathAndDirty:

    def test_project_path_set_after_save(self, tmp_path):
        _make_session()
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        assert Session.instance().project_path == path

    def test_not_dirty_after_save(self, tmp_path):
        _make_session()
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        assert not Session.instance().has_unsaved_changes()

    def test_project_path_set_after_load(self, tmp_path):
        _make_session()
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        ProjectManager.load(path)
        assert Session.instance().project_path == path

    def test_not_dirty_after_load(self, tmp_path):
        _make_session()
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        ProjectManager.load(path)
        assert not Session.instance().has_unsaved_changes()


# ══════════════════════════════════════════════════════════════════════
# Edge cases
# ══════════════════════════════════════════════════════════════════════

class TestEdgeCases:

    def test_load_nonexistent_file_raises(self, tmp_path):
        with pytest.raises(Exception):
            ProjectManager.load(str(tmp_path / "nonexistent.tass"))

    def test_load_invalid_zip_raises(self, tmp_path):
        bad_path = str(tmp_path / "bad.tass")
        with open(bad_path, "w") as f:
            f.write("not a zip file")
        with pytest.raises(Exception):
            ProjectManager.load(bad_path)

    def test_save_with_no_raw_df(self, tmp_path):
        """Save should succeed even without data loaded."""
        session = Session.reset()
        session.column_mapping.text_column = ""
        session.analysis_config.selected_dictionaries = []
        path = str(tmp_path / "empty.tass")
        ProjectManager.save(path)
        assert os.path.exists(path)
        assert zipfile.is_zipfile(path)

    def test_tass_extension_not_required(self, tmp_path):
        """ProjectManager doesn't enforce file extension."""
        _make_session()
        path = str(tmp_path / "myproject.zip")
        ProjectManager.save(path)
        ProjectManager.load(path)
        assert Session.instance().raw_df is not None

    def test_multiple_save_overwrites_cleanly(self, tmp_path):
        """Saving to same path twice produces a valid file."""
        _make_session()
        path = str(tmp_path / "test.tass")
        ProjectManager.save(path)
        _make_session(text_col="body")
        ProjectManager.save(path)
        ProjectManager.load(path)
        assert Session.instance().column_mapping.text_column == "body"

    def test_round_trip_large_dataframe(self, tmp_path):
        """DataFrames with many rows should survive round-trip."""
        import numpy as np
        session = Session.reset()
        n = 1000
        session.raw_df = pd.DataFrame({
            "text": [f"Entry {i}" for i in range(n)],
            "group": np.where(np.arange(n) % 2 == 0, "A", "B"),
        })
        session.column_mapping.text_column = "text"
        session.column_mapping.group_column = "group"
        session.analysis_config.selected_dictionaries = ["afinn165"]
        path = str(tmp_path / "large.tass")
        ProjectManager.save(path)
        ProjectManager.load(path)
        assert len(Session.instance().raw_df) == n

    def test_unicode_text_survives_round_trip(self, tmp_path):
        """Non-ASCII text should be preserved through parquet serialization."""
        session = Session.reset()
        session.raw_df = pd.DataFrame({
            "text": ["Héllo wörld", "日本語テキスト", "émoji 🎉"],
            "group": ["A", "B", "A"],
        })
        session.column_mapping.text_column = "text"
        session.analysis_config.selected_dictionaries = []
        path = str(tmp_path / "unicode.tass")
        ProjectManager.save(path)
        ProjectManager.load(path)
        texts = Session.instance().raw_df["text"].tolist()
        assert "Héllo wörld" in texts
        assert "日本語テキスト" in texts
