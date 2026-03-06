"""
Dictionary engine — matches tokenized text against loaded dictionaries.
Produces entry-level scored DataFrames and word-match indexes.
Multi-threaded via concurrent.futures.
"""

from __future__ import annotations
import os
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import numpy as np


class DictionaryEngine:
    """
    Core scoring engine.

    Usage:
        engine = DictionaryEngine(dictionaries)
        results_df, word_matches = engine.analyze(token_lists)
    """

    def __init__(self, dictionaries: List[Dict[str, Any]], max_workers: Optional[int] = None):
        """
        Args:
            dictionaries: list of normalized dict objects (from DictionaryLoader).
            max_workers: thread count. Defaults to CPU count.
        """
        self.dictionaries = dictionaries
        self.max_workers = max_workers or os.cpu_count() or 4
        self._prepared = False
        self._category_specs: List[Dict] = []
        self._category_columns: List[str] = []

    def prepare(self):
        """Pre-compute lookup sets for every category across all dictionaries."""
        self._category_specs = []
        self._category_columns = []

        for d in self.dictionaries:
            dict_name = d["name"]
            scoring = d.get("scoring", "binary")
            for cat_name, word_data in d.get("categories", {}).items():
                col = f"{dict_name}__{cat_name}"
                self._category_columns.append(col)

                if isinstance(word_data, dict):
                    # weighted scoring: {word: score}
                    word_set = {w.lower() for w in word_data}
                    word_weights = {w.lower(): v for w, v in word_data.items()}
                    self._category_specs.append({
                        "col": col,
                        "scoring": "weighted",
                        "word_set": word_set,
                        "word_weights": word_weights,
                    })
                else:
                    # binary / count: list of words
                    word_set = {w.lower() for w in word_data}
                    self._category_specs.append({
                        "col": col,
                        "scoring": scoring,
                        "word_set": word_set,
                        "word_weights": {},
                    })

        self._prepared = True

    def analyze(
        self,
        token_lists: List[List[str]],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> tuple[pd.DataFrame, Dict[int, Dict[str, List[str]]]]:
        """
        Run dictionary matching across all entries.

        Returns:
            entry_scores: DataFrame (rows=entries, cols=categories)
            word_matches: {entry_idx: {category_col: [matched_words]}}
        """
        if not self._prepared:
            self.prepare()

        n = len(token_lists)
        specs = self._category_specs
        cols = self._category_columns

        scores_list = [None] * n
        matches_list = [None] * n

        def process_entry(idx: int, tokens: List[str]):
            row_scores = {}
            row_matches = {}
            token_set = set(tokens)
            n_tokens = len(tokens) or 1

            for spec in specs:
                col = spec["col"]
                word_set = spec["word_set"]
                scoring_mode = spec["scoring"]

                matched = [t for t in tokens if t in word_set]
                row_matches[col] = matched

                if scoring_mode == "weighted":
                    weights = spec["word_weights"]
                    score = sum(weights.get(w, 0) for w in matched)
                elif scoring_mode == "count":
                    score = len(matched)
                else:  # binary (percentage)
                    score = (len(matched) / n_tokens) * 100.0

                row_scores[col] = score

            return idx, row_scores, row_matches

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(process_entry, i, tokens): i
                for i, tokens in enumerate(token_lists)
            }
            completed = 0
            for future in as_completed(futures):
                idx, row_scores, row_matches = future.result()
                scores_list[idx] = row_scores
                matches_list[idx] = row_matches
                completed += 1
                if progress_callback:
                    progress_callback(completed, n)

        entry_scores = pd.DataFrame(scores_list, columns=cols)
        word_matches = {i: m for i, m in enumerate(matches_list)}

        return entry_scores, word_matches

    @property
    def category_columns(self) -> List[str]:
        if not self._prepared:
            self.prepare()
        return list(self._category_columns)
