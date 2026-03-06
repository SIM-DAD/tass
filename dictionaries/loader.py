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
    Load a dictionary from a JSON file and validate its structure.
    Returns the normalized internal dict object.
    """
    if not os.path.exists(path):
        raise DictionaryLoadError(f"Dictionary file not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        raise DictionaryLoadError(f"Invalid JSON in {path}: {exc}") from exc

    return _validate_and_normalize(data, path)


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
