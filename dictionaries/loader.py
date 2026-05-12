"""
Dictionary loader — reads dictionary files and normalizes them to TASS internal format.

Internal format:
{
    "name": str,
    "version": str,
    "citation": str,
    "license": str,
    "scoring": "binary" | "weighted" | "count",
    "categories": {
        "category_name": {word: weight, ...} | [word, ...]
    }
}
"""

from __future__ import annotations
import json
import os
from typing import Dict, Any


class DictionaryLoadError(Exception):
    pass


def load_dictionary(path: str) -> Dict[str, Any]:
    """
    Load a dictionary from a JSON, CSV, or Excel file and validate its structure.
    Returns the normalized internal dict object.

    CSV/Excel format:
        Requires a 'word' column and a 'category' column.
        Optional 'score' column for weighted dictionaries.
        The file name (without extension) becomes the dictionary name.
    """
    if not os.path.exists(path):
        raise DictionaryLoadError(f"Dictionary file not found: {path}")

    ext = os.path.splitext(path)[1].lower()

    if ext in (".csv", ".xlsx", ".xls"):
        data = _load_tabular(path, ext)
    elif ext == ".json":
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise DictionaryLoadError(f"Invalid JSON in {path}: {exc}") from exc
    else:
        raise DictionaryLoadError(
            f"Unsupported file type '{ext}'. Use .json, .csv, or .xlsx."
        )

    return _validate_and_normalize(data, path)


def _load_tabular(path: str, ext: str) -> Dict[str, Any]:
    """Convert a CSV or Excel file to TASS dictionary format.

    Expected columns:
        word      (required) — the dictionary term
        category  (required) — which category the word belongs to
        score     (optional) — numeric weight; if absent, scoring is binary
    """
    import pandas as pd

    try:
        if ext == ".csv":
            df = pd.read_csv(path, encoding="utf-8")
        else:
            df = pd.read_excel(path)
    except Exception as exc:
        raise DictionaryLoadError(f"Could not read {path}: {exc}") from exc

    # Normalize column names to lowercase
    df.columns = [c.strip().lower() for c in df.columns]

    if "word" not in df.columns:
        raise DictionaryLoadError(
            f"Missing required 'word' column in {path}.\n\n"
            "Expected columns: word, category, and optionally score.\n"
            "Example:\n  word,category\n  happy,positive\n  sad,negative"
        )
    if "category" not in df.columns:
        raise DictionaryLoadError(
            f"Missing required 'category' column in {path}.\n\n"
            "Expected columns: word, category, and optionally score.\n"
            "Example:\n  word,category\n  happy,positive\n  sad,negative"
        )

    df = df.dropna(subset=["word", "category"])
    has_scores = "score" in df.columns

    categories: Dict[str, Any] = {}
    for _, row in df.iterrows():
        word = str(row["word"]).strip().lower()
        cat = str(row["category"]).strip()
        if not word or not cat:
            continue

        if has_scores:
            try:
                score = float(row["score"])
            except (ValueError, TypeError):
                score = 1.0
            if cat not in categories:
                categories[cat] = {}
            categories[cat][word] = score
        else:
            if cat not in categories:
                categories[cat] = []
            if word not in categories[cat]:
                categories[cat].append(word)

    if not categories:
        raise DictionaryLoadError(f"No valid word-category pairs found in {path}.")

    name = os.path.splitext(os.path.basename(path))[0].replace("_", " ").replace("-", " ").title()

    return {
        "name": name,
        "version": "1.0",
        "description": f"Imported from {os.path.basename(path)}",
        "citation": "",
        "license": "unknown",
        "scoring": "weighted" if has_scores else "binary",
        "categories": categories,
    }


def _validate_and_normalize(data: Dict[str, Any], path: str) -> Dict[str, Any]:
    required_keys = {"name", "categories"}
    missing = required_keys - set(data.keys())
    if missing:
        raise DictionaryLoadError(
            f"Dictionary at {path} is missing required keys: {missing}"
        )

    if not isinstance(data["categories"], dict):
        raise DictionaryLoadError(
            f"Dictionary 'categories' must be a dict in {path}"
        )

    # Set defaults
    data.setdefault("version", "unknown")
    data.setdefault("citation", "")
    data.setdefault("license", "unknown")
    data.setdefault("scoring", "binary")

    # Normalize: all words lowercase
    for cat_name, word_data in data["categories"].items():
        if isinstance(word_data, dict):
            data["categories"][cat_name] = {w.lower(): v for w, v in word_data.items()}
        elif isinstance(word_data, list):
            data["categories"][cat_name] = [w.lower() for w in word_data]
        else:
            raise DictionaryLoadError(
                f"Category '{cat_name}' in {path} must be a dict (weighted) or list (binary)."
            )

    return data
