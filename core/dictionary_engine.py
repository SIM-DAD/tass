"""
Dictionary engine — matches tokenized text against loaded dictionaries.
Produces entry-level scored DataFrames and word-match indexes.
Supports unigram, n-gram (bigram/trigram), and TF-IDF scoring.
Multi-threaded via concurrent.futures.
"""

from __future__ import annotations
import math
import os
from typing import List, Dict, Any, Optional, Callable, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import numpy as np

from core.preprocessor import Preprocessor


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
        self._max_ngram: int = 1  # max n-gram size across all dictionaries

    def prepare(self):
        """Pre-compute lookup sets for every category across all dictionaries."""
        self._category_specs = []
        self._category_columns = []
        self._max_ngram = 1

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
                    cat_scoring = "weighted"
                else:
                    # binary / count: list of words
                    word_set = {w.lower() for w in word_data}
                    word_weights = {}
                    cat_scoring = scoring

                # Detect n-grams: entries containing spaces are multi-word
                ngram_entries: Set[str] = set()
                for w in word_set:
                    n = len(w.split())
                    if n > 1:
                        ngram_entries.add(w)
                        self._max_ngram = max(self._max_ngram, n)

                self._category_specs.append({
                    "col": col,
                    "scoring": cat_scoring,
                    "word_set": word_set,
                    "word_weights": word_weights,
                    "ngram_entries": ngram_entries,  # multi-word entries for suppression
                })

        self._prepared = True

    def analyze(
        self,
        token_lists: List[List[str]],
        scoring_override: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> tuple[pd.DataFrame, Dict[int, Dict[str, List[str]]]]:
        """
        Run dictionary matching across all entries.

        Args:
            token_lists: per-entry unigram token lists from Preprocessor
            scoring_override: if "tfidf", use TF-IDF scoring for all categories
            progress_callback: (completed, total) progress reporter

        Returns:
            entry_scores: DataFrame (rows=entries, cols=categories)
            word_matches: {entry_idx: {category_col: [matched_words]}}
        """
        if not self._prepared:
            self.prepare()

        n = len(token_lists)
        specs = self._category_specs
        cols = self._category_columns
        max_ng = self._max_ngram
        use_tfidf = scoring_override == "tfidf"
        use_count = scoring_override == "count"

        # Pre-generate n-gram token lists if any dictionary needs them
        if max_ng > 1:
            ngram_token_lists = [
                Preprocessor.generate_ngrams(tokens, max_ng)
                for tokens in token_lists
            ]
        else:
            ngram_token_lists = token_lists

        # Pre-compute IDF if TF-IDF mode requested
        idf: Dict[str, float] = {}
        if use_tfidf:
            idf = self._compute_idf(token_lists, ngram_token_lists)

        scores_list = [None] * n
        matches_list = [None] * n

        def process_entry(idx: int, unigrams: List[str], all_tokens: List[str]):
            row_scores = {}
            row_matches = {}
            n_tokens = len(unigrams) or 1

            # Pass 1: find all n-gram matches across ALL categories to build
            # a global suppression set. When "not happy" matches anywhere,
            # "not" and "happy" are suppressed as unigram matches everywhere.
            suppressed_unigrams: set = set()
            if max_ng > 1:
                for spec in specs:
                    for t in all_tokens:
                        if " " in t and t in spec["word_set"]:
                            for part in t.split():
                                suppressed_unigrams.add(part)

            # Pass 2: score each category
            for spec in specs:
                col = spec["col"]
                word_set = spec["word_set"]
                scoring_mode = spec["scoring"]

                # Match against full token list (unigrams + n-grams)
                matched = [t for t in all_tokens if t in word_set]

                # Apply n-gram suppression: remove unigrams consumed by n-grams
                if suppressed_unigrams and matched:
                    matched = [m for m in matched
                               if " " in m or m not in suppressed_unigrams]

                row_matches[col] = matched

                if use_tfidf:
                    from collections import Counter
                    tf_counts = Counter(matched)
                    score = sum(
                        (count / n_tokens) * idf.get(w, 0.0)
                        for w, count in tf_counts.items()
                    )
                elif use_count:
                    score = len(matched)
                elif scoring_mode == "weighted":
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
                executor.submit(process_entry, i, token_lists[i], ngram_token_lists[i]): i
                for i in range(n)
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

    def _compute_idf(
        self,
        unigram_lists: List[List[str]],
        ngram_lists: List[List[str]],
    ) -> Dict[str, float]:
        """Compute inverse document frequency for all dictionary terms.

        IDF(t) = log(N / DF(t)) where DF(t) = number of documents containing t.
        Uses add-one smoothing: log(N / (1 + DF(t))) to avoid division by zero.
        """
        # Collect all dictionary terms
        all_terms: set = set()
        for spec in self._category_specs:
            all_terms.update(spec["word_set"])

        n_docs = len(unigram_lists)
        if n_docs == 0:
            return {}

        # Count document frequency for each term
        df_counts: Dict[str, int] = {t: 0 for t in all_terms}
        for tokens in ngram_lists:
            doc_tokens = set(tokens)
            for t in all_terms:
                if t in doc_tokens:
                    df_counts[t] += 1

        # Compute IDF with add-one smoothing
        return {
            t: math.log(n_docs / (1 + df))
            for t, df in df_counts.items()
        }

    @property
    def category_columns(self) -> List[str]:
        if not self._prepared:
            self.prepare()
        return list(self._category_columns)
