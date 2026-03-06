"""
In-memory session state (singleton).
Holds the current DataFrame, analysis config, results, and UI state.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
import pandas as pd


@dataclass
class ColumnMapping:
    text_column: str = ""
    group_column: Optional[str] = None
    metadata_columns: List[str] = field(default_factory=list)


@dataclass
class AnalysisConfig:
    selected_dictionaries: List[str] = field(default_factory=list)
    analysis_levels: List[str] = field(default_factory=lambda: ["word", "entry", "document"])
    groups: Dict[str, List[Any]] = field(default_factory=dict)  # {group_name: [col_value, ...]}
    group_column: Optional[str] = None


@dataclass
class AnalysisResults:
    entry_scores: Optional[pd.DataFrame] = None      # rows=entries, cols=categories
    word_matches: Optional[Dict] = None               # {entry_idx: {category: [words]}}
    document_summary: Optional[pd.DataFrame] = None  # aggregate stats
    group_stats: Optional[Dict] = None               # {category: {group: stats_dict}}


class Session:
    """Singleton session state for the current TASS analysis."""

    _instance: Optional[Session] = None

    def __init__(self):
        self._raw_df: Optional[pd.DataFrame] = None
        self._source_files: List[str] = []
        self.column_mapping: ColumnMapping = ColumnMapping()
        self.analysis_config: AnalysisConfig = AnalysisConfig()
        self.results: AnalysisResults = AnalysisResults()
        self.project_path: Optional[str] = None
        self._saved_state_hash: Optional[int] = None
        self.ui_state: Dict[str, Any] = {
            "active_panel": "home",
            "color_palette": "default",
            "export_path": "",
        }

    @classmethod
    def instance(cls) -> Session:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> Session:
        """Start a fresh session (new analysis)."""
        cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------

    @property
    def raw_df(self) -> Optional[pd.DataFrame]:
        return self._raw_df

    @raw_df.setter
    def raw_df(self, df: Optional[pd.DataFrame]):
        self._raw_df = df

    @property
    def source_files(self) -> List[str]:
        return self._source_files

    def add_source_file(self, path: str):
        if path not in self._source_files:
            self._source_files.append(path)

    def clear_source_files(self):
        self._source_files.clear()

    # ------------------------------------------------------------------
    # Dirty / unsaved change detection
    # ------------------------------------------------------------------

    def mark_saved(self):
        self._saved_state_hash = self._state_hash()

    def has_unsaved_changes(self) -> bool:
        if self._raw_df is None and self.results.entry_scores is None:
            return False
        return self._state_hash() != self._saved_state_hash

    def _state_hash(self) -> int:
        parts = [
            id(self._raw_df),
            id(self.results.entry_scores),
            str(self.column_mapping),
            str(self.analysis_config.selected_dictionaries),
        ]
        return hash(tuple(parts))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def has_data(self) -> bool:
        return self._raw_df is not None and len(self._raw_df) > 0

    @property
    def has_results(self) -> bool:
        return self.results.entry_scores is not None

    @property
    def row_count(self) -> int:
        return len(self._raw_df) if self._raw_df is not None else 0

    def to_dict(self) -> Dict:
        """Serialize session metadata for project save (not the DataFrames)."""
        return {
            "source_files": self._source_files,
            "column_mapping": {
                "text_column": self.column_mapping.text_column,
                "group_column": self.column_mapping.group_column,
                "metadata_columns": self.column_mapping.metadata_columns,
            },
            "analysis_config": {
                "selected_dictionaries": self.analysis_config.selected_dictionaries,
                "analysis_levels": self.analysis_config.analysis_levels,
                "groups": self.analysis_config.groups,
                "group_column": self.analysis_config.group_column,
            },
            "ui_state": self.ui_state,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> Session:
        """Restore session metadata from project load."""
        session = cls.reset()
        session._source_files = data.get("source_files", [])

        cm = data.get("column_mapping", {})
        session.column_mapping.text_column = cm.get("text_column", "")
        session.column_mapping.group_column = cm.get("group_column")
        session.column_mapping.metadata_columns = cm.get("metadata_columns", [])

        ac = data.get("analysis_config", {})
        session.analysis_config.selected_dictionaries = ac.get("selected_dictionaries", [])
        session.analysis_config.analysis_levels = ac.get("analysis_levels", ["word", "entry", "document"])
        session.analysis_config.groups = ac.get("groups", {})
        session.analysis_config.group_column = ac.get("group_column")

        session.ui_state = data.get("ui_state", session.ui_state)
        return session
