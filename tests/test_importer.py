"""
Tests for core/importer.py

Run with:  pytest tests/test_importer.py -v
"""

import io
import os
import textwrap
import tempfile

import pandas as pd
import pytest

# Ensure project root is on the path when running from tests/ directly
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.importer import (
    import_file,
    import_files,
    detect_column_types,
    suggest_text_column,
    ImportError,
    SUPPORTED_EXTENSIONS,
)


# ══════════════════════════════════════════════════════════════════════
# Fixtures / helpers
# ══════════════════════════════════════════════════════════════════════

def _write_tmp(content: str, suffix: str, encoding: str = "utf-8") -> str:
    """Write content to a temp file and return its path."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "w", encoding=encoding) as fh:
        fh.write(content)
    return path


@pytest.fixture
def simple_csv(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text(
        "text,category,score\n"
        "I love this product,positive,5\n"
        "This is terrible,negative,1\n"
        "It is okay I guess,neutral,3\n",
        encoding="utf-8",
    )
    return str(path)


@pytest.fixture
def simple_txt(tmp_path):
    path = tmp_path / "docs.txt"
    path.write_text(
        "First document here.\nSecond document here.\nThird document here.\n",
        encoding="utf-8",
    )
    return str(path)


@pytest.fixture
def tsv_txt(tmp_path):
    path = tmp_path / "data.txt"
    path.write_text(
        "text\tgroup\n"
        "Hello world\tA\n"
        "Goodbye world\tB\n",
        encoding="utf-8",
    )
    return str(path)


@pytest.fixture
def simple_excel(tmp_path):
    path = tmp_path / "data.xlsx"
    df = pd.DataFrame({
        "response": ["Strongly agree", "Disagree", "Neutral"],
        "condition": ["treatment", "control", "control"],
        "id": [1, 2, 3],
    })
    df.to_excel(str(path), index=False)
    return str(path)


@pytest.fixture
def latin1_csv(tmp_path):
    path = tmp_path / "latin.csv"
    path.write_bytes(
        "text,score\n"
        "caf\xe9 au lait,3\n"
        "na\xefve statement,2\n".encode("latin-1")
    )
    return str(path)


# ══════════════════════════════════════════════════════════════════════
# import_file — basic format support
# ══════════════════════════════════════════════════════════════════════

class TestImportFile:

    def test_csv_returns_dataframe(self, simple_csv):
        df = import_file(simple_csv)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "text" in df.columns

    def test_csv_correct_values(self, simple_csv):
        df = import_file(simple_csv)
        assert df["text"].iloc[0] == "I love this product"
        assert df["score"].iloc[2] == 3

    def test_txt_one_doc_per_line(self, simple_txt):
        df = import_file(simple_txt)
        assert "text" in df.columns
        assert len(df) == 3
        assert df["text"].iloc[0] == "First document here."

    def test_txt_tsv_detected(self, tsv_txt):
        df = import_file(tsv_txt)
        assert "text" in df.columns
        assert "group" in df.columns
        assert len(df) == 2

    def test_xlsx_import(self, simple_excel):
        df = import_file(simple_excel)
        assert len(df) == 3
        assert "response" in df.columns
        assert "condition" in df.columns

    def test_latin1_fallback(self, latin1_csv):
        # Should not raise despite non-UTF-8 encoding
        df = import_file(latin1_csv)
        assert len(df) == 2

    def test_unsupported_extension_raises(self, tmp_path):
        path = tmp_path / "data.json"
        path.write_text('{"a": 1}')
        with pytest.raises(ImportError, match="Unsupported file format"):
            import_file(str(path))

    def test_empty_file_raises(self, tmp_path):
        path = tmp_path / "empty.csv"
        path.write_text("")
        with pytest.raises(ImportError, match="empty"):
            import_file(str(path))

    def test_nonexistent_file_raises(self):
        with pytest.raises((ImportError, Exception)):
            import_file("/nonexistent/path/data.csv")


# ══════════════════════════════════════════════════════════════════════
# import_files — multi-file concatenation
# ══════════════════════════════════════════════════════════════════════

class TestImportFiles:

    def test_multiple_csv_concatenated(self, tmp_path):
        for i in range(3):
            (tmp_path / f"part{i}.csv").write_text(
                f"text,score\nDoc {i} content here,{i}\n", encoding="utf-8"
            )
        paths = [str(tmp_path / f"part{i}.csv") for i in range(3)]
        df = import_files(paths)
        assert len(df) == 3
        assert "_source_file" in df.columns

    def test_source_file_column_contains_basename(self, simple_csv, simple_txt):
        # Both files have a 'text' column; txt produces text col automatically
        df = import_files([simple_csv])
        assert df["_source_file"].iloc[0] == os.path.basename(simple_csv)

    def test_empty_list_raises(self):
        with pytest.raises(ImportError, match="No files"):
            import_files([])


# ══════════════════════════════════════════════════════════════════════
# detect_column_types
# ══════════════════════════════════════════════════════════════════════

class TestDetectColumnTypes:

    def _make_df(self):
        return pd.DataFrame({
            "long_text": [
                "This is a fairly long piece of text that describes something",
                "Another sentence that is quite long and detailed in nature",
                "A third entry that has enough words to be considered textual",
            ],
            "category": ["A", "B", "A"],
            "score": [1.5, 2.0, 3.5],
        })

    def test_returns_one_info_per_column(self):
        df = self._make_df()
        infos = detect_column_types(df)
        assert len(infos) == len(df.columns)

    def test_numeric_column_detected(self):
        df = self._make_df()
        infos = detect_column_types(df)
        score_info = next(i for i in infos if i.name == "score")
        assert score_info.dtype == "numeric"

    def test_categorical_column_detected(self):
        df = self._make_df()
        infos = detect_column_types(df)
        cat_info = next(i for i in infos if i.name == "category")
        assert cat_info.dtype == "categorical"

    def test_text_column_detected(self):
        df = self._make_df()
        infos = detect_column_types(df)
        text_info = next(i for i in infos if i.name == "long_text")
        assert text_info.dtype == "text"

    def test_sample_values_populated(self):
        df = self._make_df()
        infos = detect_column_types(df)
        for info in infos:
            assert isinstance(info.sample_values, list)
            assert len(info.sample_values) <= 3


# ══════════════════════════════════════════════════════════════════════
# suggest_text_column
# ══════════════════════════════════════════════════════════════════════

class TestSuggestTextColumn:

    def test_priority_name_wins(self):
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "text": ["Alpha beta gamma delta epsilon", "Zeta eta theta iota kappa", "Lambda mu nu xi omicron"],
            "label": ["pos", "neg", "neu"],
        })
        infos = detect_column_types(df)
        result = suggest_text_column(df, infos)
        assert result == "text"

    def test_longest_column_chosen_when_no_priority_name(self):
        df = pd.DataFrame({
            "col_a": ["short", "brief", "tiny"],
            "col_b": [
                "This is a much longer text entry with many words and detail",
                "Another considerably long sentence with numerous descriptive words",
                "Yet another extended textual entry for testing column length heuristics",
            ],
        })
        infos = detect_column_types(df)
        result = suggest_text_column(df, infos)
        assert result == "col_b"

    def test_returns_none_when_no_text_columns(self):
        df = pd.DataFrame({
            "score": [1, 2, 3],
            "count": [10, 20, 30],
        })
        infos = detect_column_types(df)
        result = suggest_text_column(df, infos)
        assert result is None

    def test_tweet_name_recognized(self):
        df = pd.DataFrame({
            "tweet": ["Hello world this is a tweet text body", "Another tweet text body here"],
            "user_id": [1, 2],
        })
        infos = detect_column_types(df)
        result = suggest_text_column(df, infos)
        assert result == "tweet"


# ══════════════════════════════════════════════════════════════════════
# supported extensions
# ══════════════════════════════════════════════════════════════════════

class TestSupportedExtensions:

    def test_all_required_formats_supported(self):
        for ext in (".csv", ".txt", ".xlsx", ".xls"):
            assert ext in SUPPORTED_EXTENSIONS
