"""
Dictionary registry — manifest of all available dictionaries (built-in + user-imported).
Provides a central API for listing and loading dictionaries.
"""

from __future__ import annotations
import os
from typing import List, Dict, Any, Optional
from dictionaries.loader import load_dictionary, DictionaryLoadError

BUILTIN_DIR = os.path.join(os.path.dirname(__file__), "builtin")

# Metadata for built-in dictionaries (display info; data is in the JSON files)
BUILTIN_MANIFEST = [
    {
        "id": "afinn165",
        "file": "afinn165.json",
        "display_name": "AFINN-165",
        "description": "Sentiment valence scores for 3,382 words (-5 to +5).",
        "license": "MIT",
        "citation": "Nielsen (2011)",
        "categories_preview": ["sentiment"],
        "enabled_by_default": True,
    },
    {
        "id": "vader_lexicon",
        "file": "vader_lexicon.json",
        "display_name": "VADER Lexicon",
        "description": "Sentiment valence + intensity (positive, negative, neutral, compound).",
        "license": "MIT",
        "citation": "Hutto & Gilbert (2014)",
        "categories_preview": ["positive", "negative", "neutral"],
        "enabled_by_default": True,
    },
    {
        "id": "mfd2",
        "file": "mfd2.json",
        "display_name": "Moral Foundations Dictionary 2.0",
        "description": "Care, Fairness, Loyalty, Authority, Purity (virtue + vice).",
        "license": "CC-BY",
        "citation": "Frimer et al. (2019)",
        "categories_preview": ["care.virtue", "care.vice", "fairness.virtue",
                               "fairness.vice", "loyalty.virtue", "loyalty.vice",
                               "authority.virtue", "authority.vice",
                               "purity.virtue", "purity.vice"],
        "enabled_by_default": True,
    },
    {
        "id": "brysbaert_concreteness",
        "file": "brysbaert_concreteness.json",
        "display_name": "Brysbaert Concreteness Norms",
        "description": "Concreteness ratings for ~40k English words (1=abstract, 5=concrete).",
        "license": "CC-BY",
        "citation": "Brysbaert et al. (2014)",
        "categories_preview": ["concreteness"],
        "enabled_by_default": False,
    },
    {
        "id": "hurtlex",
        "file": "hurtlex.json",
        "display_name": "HurtLex",
        "description": "Hurtful/offensive language categorized by type (slurs, profanity, etc.).",
        "license": "CC-BY-SA",
        "citation": "Bassignana et al. (2018)",
        "categories_preview": ["slurs", "profanity", "derogatory"],
        "enabled_by_default": False,
    },
    {
        "id": "wordnet_pos",
        "file": "wordnet_pos.json",
        "display_name": "WordNet POS Categories",
        "description": "Part-of-speech category membership from WordNet 3.1.",
        "license": "Princeton WordNet License",
        "citation": "Fellbaum (1998)",
        "categories_preview": ["noun", "verb", "adjective", "adverb"],
        "enabled_by_default": False,
    },
    {
        "id": "nltk_stopwords",
        "file": "nltk_stopwords.json",
        "display_name": "NLTK Stopwords / Function Words",
        "description": "Pronouns, prepositions, articles, conjunctions, and other function words.",
        "license": "Apache 2.0",
        "citation": "NLTK Project",
        "categories_preview": ["function_words", "pronouns", "prepositions"],
        "enabled_by_default": False,
    },
    {
        "id": "sentiwordnet",
        "file": "sentiwordnet.json",
        "display_name": "SentiWordNet 3.0",
        "description": "Positive/negative/objective scores per WordNet synset.",
        "license": "CC-BY-SA",
        "citation": "Baccianella et al. (2010)",
        "categories_preview": ["positive", "negative", "objective"],
        "enabled_by_default": False,
    },
]


class DictionaryRegistry:
    """Central registry for all available dictionaries."""

    def __init__(self):
        self._builtin: List[Dict[str, Any]] = list(BUILTIN_MANIFEST)
        self._user: List[Dict[str, Any]] = []
        self._cache: Dict[str, Dict] = {}

    def all_entries(self) -> List[Dict[str, Any]]:
        return self._builtin + self._user

    def get_entry(self, dict_id: str) -> Optional[Dict[str, Any]]:
        for entry in self.all_entries():
            if entry["id"] == dict_id:
                return entry
        return None

    def load(self, dict_id: str) -> Dict[str, Any]:
        """Load and cache a dictionary by its ID."""
        if dict_id in self._cache:
            return self._cache[dict_id]

        entry = self.get_entry(dict_id)
        if entry is None:
            raise DictionaryLoadError(f"Unknown dictionary ID: {dict_id!r}")

        if "path" in entry:
            path = entry["path"]  # user dictionary with explicit path
        else:
            path = os.path.join(BUILTIN_DIR, entry["file"])

        data = load_dictionary(path)
        self._cache[dict_id] = data
        return data

    def load_multiple(self, dict_ids: List[str]) -> List[Dict[str, Any]]:
        return [self.load(did) for did in dict_ids]

    def default_selection(self) -> List[str]:
        return [e["id"] for e in self._builtin if e.get("enabled_by_default")]

    def register_user_dictionary(self, path: str, dict_id: Optional[str] = None) -> str:
        """Register a user-supplied dictionary file. Returns its assigned ID."""
        data = load_dictionary(path)
        assigned_id = dict_id or f"user__{data['name'].lower().replace(' ', '_')}"
        entry = {
            "id": assigned_id,
            "path": path,
            "display_name": data["name"],
            "description": f"User dictionary: {data.get('citation', '')}",
            "license": data.get("license", "unknown"),
            "citation": data.get("citation", ""),
            "categories_preview": list(data.get("categories", {}).keys())[:5],
            "enabled_by_default": True,
        }
        # Remove existing entry with same ID if present
        self._user = [u for u in self._user if u["id"] != assigned_id]
        self._user.append(entry)
        self._cache[assigned_id] = data
        return assigned_id


# Module-level singleton
_registry: Optional[DictionaryRegistry] = None


def get_registry() -> DictionaryRegistry:
    global _registry
    if _registry is None:
        _registry = DictionaryRegistry()
    return _registry
