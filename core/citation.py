"""
Citation generator for TASS exports.
Produces APA, MLA, and Chicago formatted citations.
"""

from __future__ import annotations
from app import TASS_VERSION

ZENODO_DOI = "10.5281/zenodo.PENDING"  # Updated at v1.0 release
AUTHOR_LAST = "TBD"
AUTHOR_FIRST = "TBD"
YEAR = "2026"
SOFTWARE_TITLE = "TASS: Text Analysis for Social Scientists"
PUBLISHER = "SIM DAD LLC"


def apa_citation() -> str:
    return (
        f"{AUTHOR_LAST}, {AUTHOR_FIRST}. ({YEAR}). {SOFTWARE_TITLE} "
        f"(Version {TASS_VERSION}) [Software]. {PUBLISHER}. "
        f"https://doi.org/{ZENODO_DOI}"
    )


def mla_citation() -> str:
    return (
        f"{AUTHOR_LAST}, {AUTHOR_FIRST}. {SOFTWARE_TITLE}. "
        f"Version {TASS_VERSION}, {PUBLISHER}, {YEAR}, "
        f"https://doi.org/{ZENODO_DOI}."
    )


def chicago_citation() -> str:
    return (
        f"{AUTHOR_LAST}, {AUTHOR_FIRST}. {SOFTWARE_TITLE}. "
        f"Version {TASS_VERSION}. {PUBLISHER}, {YEAR}. "
        f"https://doi.org/{ZENODO_DOI}."
    )


def citation_block() -> str:
    """Full block appended to every TASS export."""
    return (
        "\n\n"
        "--- TASS Citation ---\n"
        "If you use TASS in your research, please cite it:\n\n"
        f"APA:\n{apa_citation()}\n\n"
        f"DOI: https://doi.org/{ZENODO_DOI}\n"
        "---------------------\n"
    )


def all_formats() -> dict:
    return {
        "APA": apa_citation(),
        "MLA": mla_citation(),
        "Chicago": chicago_citation(),
        "DOI": f"https://doi.org/{ZENODO_DOI}",
    }
