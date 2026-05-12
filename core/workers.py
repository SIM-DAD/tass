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
        preprocessor_kwargs: Optional[Dict[str, Any]] = None,
        scoring_override: Optional[str] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.raw_df = raw_df
        self.text_column = text_column
        self.dictionaries = dictionaries
        self.analysis_config = analysis_config
        self.preprocessor_kwargs = preprocessor_kwargs or {}
        self.scoring_override = scoring_override
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
        from core.analysis_log import AnalysisLog

        alog = AnalysisLog.instance()
        total = len(self.raw_df)

        # Step 1: Preprocessing
        self.progress.emit(0, total, "Tokenizing text...")
        preprocessor_opts = {
            "lowercase": True,
            "strip_punctuation": True,
            **self.preprocessor_kwargs,
        }
        preprocessor = Preprocessor(**preprocessor_opts)

        def on_preprocess_progress(done, n):
            if self._cancelled:
                return
            self.progress.emit(done, n, f"Tokenizing {done:,} / {n:,} entries...")

        token_lists = preprocessor.process_series(
            self.raw_df[self.text_column],
            progress_callback=on_preprocess_progress,
        )

        alog.log_section("Analysis Run")
        alog.log(f"Text column: {self.text_column}")
        alog.log(f"Entries: {total:,}")
        alog.log(f"Preprocessing: lemmatize={preprocessor_opts.get('lemmatize', False)}, "
                 f"stopwords={preprocessor_opts.get('remove_stopwords', False)}, "
                 f"min_length={preprocessor_opts.get('min_token_length', 1)}")
        dict_names = [d.get("name", "?") for d in self.dictionaries]
        alog.log(f"Dictionaries: {', '.join(dict_names)}")
        if self.scoring_override:
            alog.log(f"Scoring override: {self.scoring_override}")

        if self._cancelled:
            return

        # Step 2: Dictionary matching
        self.progress.emit(0, total, "Loading dictionaries...")
        engine = DictionaryEngine(self.dictionaries)
        engine.prepare()

        if engine._max_ngram > 1:
            alog.log(f"N-gram matching enabled (max n={engine._max_ngram})")

        self.progress.emit(0, total, "Analyzing text...")

        _last_report = [0]

        def on_progress(done, n):
            if self._cancelled:
                return
            if done - _last_report[0] >= 500 or done == n:
                _last_report[0] = done
                self.progress.emit(done, n, f"Analyzed {done:,} / {n:,} entries...")

        entry_scores, word_matches = engine.analyze(
            token_lists,
            scoring_override=self.scoring_override,
            progress_callback=on_progress,
        )

        alog.log(f"Analysis complete: {len(entry_scores.columns)} category scores computed")

        if self._cancelled:
            return

        self.finished.emit(entry_scores, word_matches)


class StatisticsWorker(QThread):
    """
    Runs group comparison statistics in a background thread.
    """

    finished = Signal(object)  # Dict of GroupStats
    error = Signal(str)

    def __init__(self, scores_df, group_series, nonparametric=False,
                 bonferroni=True, correction="bonferroni", parent=None):
        super().__init__(parent)
        self.scores_df = scores_df
        self.group_series = group_series
        self.nonparametric = nonparametric
        self.correction = correction

    def run(self):
        try:
            from core.statistics_engine import StatisticsEngine
            from core.analysis_log import AnalysisLog

            alog = AnalysisLog.instance()
            groups = sorted(str(v) for v in self.group_series.dropna().unique())
            n_dvs = len(self.scores_df.columns)
            alog.log_section("Group Comparison")
            alog.log(f"Groups ({len(groups)}): {', '.join(groups)}")
            alog.log(f"Dependent variables ({n_dvs}): {', '.join(self.scores_df.columns[:5])}"
                     + (f"... +{n_dvs - 5} more" if n_dvs > 5 else ""))
            alog.log(f"Non-parametric: {self.nonparametric}")
            alog.log(f"Correction: {self.correction}")

            engine = StatisticsEngine()
            results = engine.group_comparisons(
                self.scores_df,
                self.group_series,
                nonparametric=self.nonparametric,
                correction=self.correction,
            )

            n_sig = sum(1 for gs in results.values() if gs.significant)
            alog.log(f"Comparison complete: {n_sig}/{len(results)} significant")
            self.finished.emit(results)
        except Exception as exc:
            import traceback
            self.error.emit(f"{type(exc).__name__}: {exc}\n\n{traceback.format_exc()}")
