"""
QThread workers for async analysis operations.
Keeps the UI responsive during long-running analysis.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
from PySide6.QtCore import QThread, Signal


class AnalysisWorker(QThread):
    """
    Runs the full analysis pipeline in a background thread:
    preprocessing → dictionary matching → statistics.
    """

    progress = Signal(int, int, str)   # (completed, total, message)
    finished = Signal(object, object)  # (entry_scores_df, word_matches_dict)
    error = Signal(str)               # error message

    def __init__(
        self,
        raw_df,
        text_column: str,
        dictionaries: List[Dict],
        analysis_config,
        parent=None,
    ):
        super().__init__(parent)
        self.raw_df = raw_df
        self.text_column = text_column
        self.dictionaries = dictionaries
        self.analysis_config = analysis_config
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            self._run_pipeline()
        except Exception as exc:
            import traceback
            self.error.emit(f"{type(exc).__name__}: {exc}\n\n{traceback.format_exc()}")

    def _run_pipeline(self):
        from core.preprocessor import Preprocessor
        from core.dictionary_engine import DictionaryEngine

        total = len(self.raw_df)

        # Step 1: Preprocessing
        self.progress.emit(0, total, "Tokenizing text...")
        preprocessor = Preprocessor(
            lowercase=True,
            strip_punctuation=True,
            lemmatize=False,
        )
        token_lists = preprocessor.process_series(self.raw_df[self.text_column])

        if self._cancelled:
            return

        # Step 2: Dictionary matching
        self.progress.emit(0, total, "Loading dictionaries...")
        engine = DictionaryEngine(self.dictionaries)
        engine.prepare()

        self.progress.emit(0, total, "Analyzing text...")

        def on_progress(done, n):
            if self._cancelled:
                return
            self.progress.emit(done, n, f"Analyzed {done:,} / {n:,} entries...")

        entry_scores, word_matches = engine.analyze(token_lists, progress_callback=on_progress)

        if self._cancelled:
            return

        self.finished.emit(entry_scores, word_matches)


class StatisticsWorker(QThread):
    """
    Runs group comparison statistics in a background thread.
    """

    finished = Signal(object)  # Dict of GroupStats
    error = Signal(str)

    def __init__(self, scores_df, group_series, nonparametric=False, bonferroni=True, parent=None):
        super().__init__(parent)
        self.scores_df = scores_df
        self.group_series = group_series
        self.nonparametric = nonparametric
        self.bonferroni = bonferroni

    def run(self):
        try:
            from core.statistics_engine import StatisticsEngine
            engine = StatisticsEngine()
            results = engine.group_comparisons(
                self.scores_df,
                self.group_series,
                nonparametric=self.nonparametric,
                bonferroni=self.bonferroni,
            )
            self.finished.emit(results)
        except Exception as exc:
            import traceback
            self.error.emit(f"{type(exc).__name__}: {exc}\n\n{traceback.format_exc()}")
