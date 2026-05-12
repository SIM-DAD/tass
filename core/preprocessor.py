"""
Text preprocessor — tokenization, lemmatization, cleaning.
All operations return per-entry token lists to feed the dictionary engine.
"""

from __future__ import annotations
import re
import string
from typing import List, Optional
import pandas as pd


class Preprocessor:
    """
    Converts raw text entries into token lists.

    Steps:
    1. Lowercase
    2. Strip punctuation (configurable)
    3. Tokenize (NLTK word_tokenize)
    4. Optional: remove stopwords
    5. Optional: lemmatize (NLTK WordNetLemmatizer)
    """

    def __init__(
        self,
        lowercase: bool = True,
        strip_punctuation: bool = True,
        remove_stopwords: bool = False,
        lemmatize: bool = False,
        min_token_length: int = 1,
    ):
        self.lowercase = lowercase
        self.strip_punctuation = strip_punctuation
        self.remove_stopwords = remove_stopwords
        self.lemmatize = lemmatize
        self.min_token_length = min_token_length

        self._lemmatizer = None
        self._stopwords = None
        self._tokenizer_ready = False

    def _ensure_ready(self):
        if self._tokenizer_ready:
            return
        import nltk
        # Ensure required data
        for (path, pkg) in [
            ("tokenizers/punkt_tab", "punkt_tab"),
            ("tokenizers/punkt", "punkt"),
        ]:
            try:
                nltk.data.find(path)
                break
            except (LookupError, OSError):
                try:
                    nltk.download(pkg, quiet=True)
                    break
                except Exception:
                    continue

        if self.remove_stopwords:
            try:
                from nltk.corpus import stopwords
                self._stopwords = set(stopwords.words("english"))
            except LookupError:
                import nltk
                nltk.download("stopwords", quiet=True)
                from nltk.corpus import stopwords
                self._stopwords = set(stopwords.words("english"))

        if self.lemmatize:
            try:
                from nltk.stem import WordNetLemmatizer
                self._lemmatizer = WordNetLemmatizer()
            except LookupError:
                import nltk
                nltk.download("wordnet", quiet=True)
                from nltk.stem import WordNetLemmatizer
                self._lemmatizer = WordNetLemmatizer()

        self._tokenizer_ready = True

    def tokenize(self, text: str) -> List[str]:
        """Process a single text string into a cleaned token list."""
        self._ensure_ready()

        if not isinstance(text, str):
            text = str(text) if text is not None else ""

        if self.lowercase:
            text = text.lower()

        if self.strip_punctuation:
            text = text.translate(str.maketrans("", "", string.punctuation))
            text = re.sub(r"\s+", " ", text).strip()

        try:
            from nltk import word_tokenize
            tokens = word_tokenize(text)
        except Exception:
            tokens = text.split()

        # Filter by minimum length
        if self.min_token_length > 1:
            tokens = [t for t in tokens if len(t) >= self.min_token_length]

        # Remove stopwords
        if self.remove_stopwords and self._stopwords:
            tokens = [t for t in tokens if t not in self._stopwords]

        # Lemmatize
        if self.lemmatize and self._lemmatizer:
            tokens = [self._lemmatizer.lemmatize(t) for t in tokens]

        return tokens

    @staticmethod
    def generate_ngrams(tokens: List[str], max_n: int) -> List[str]:
        """Generate n-gram strings from a token list.

        Returns the original unigrams plus bigrams, trigrams, etc. up to max_n.
        N-grams are joined with spaces: ["not", "happy"] → "not happy".
        """
        if max_n <= 1:
            return tokens
        ngrams = list(tokens)  # start with unigrams
        for n in range(2, max_n + 1):
            for i in range(len(tokens) - n + 1):
                ngrams.append(" ".join(tokens[i:i + n]))
        return ngrams

    def process_series(
        self,
        series: pd.Series,
        progress_callback=None,
    ) -> List[List[str]]:
        """
        Tokenize every entry in a pandas Series.
        Returns a list of token lists (preserves index order).

        progress_callback: optional (completed, total) callable for progress reporting.
        """
        self._ensure_ready()
        n = len(series)
        result = []
        for i, text in enumerate(series):
            result.append(self.tokenize(text))
            if progress_callback and (i % 500 == 0 or i == n - 1):
                progress_callback(i + 1, n)
        return result

    def process_df(self, df: pd.DataFrame, text_column: str) -> pd.Series:
        """
        Add a '_tokens' column to the DataFrame (returned as a Series).
        """
        return pd.Series(
            self.process_series(df[text_column]),
            index=df.index,
            name="_tokens",
        )
