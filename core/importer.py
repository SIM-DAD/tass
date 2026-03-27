"""
File importer — reads CSV, TXT, and XLSX into pandas DataFrames.
Handles column type detection and basic validation.
"""

from __future__ import annotations
import os
from typing import List, Tuple, Optional
import pandas as pd


SUPPORTED_EXTENSIONS = {".csv", ".txt", ".xlsx", ".xls"}


class ImportError(Exception):
    pass


class ColumnInfo:
    def __init__(self, name: str, dtype: str, sample_values: list):
        self.name = name
        self.dtype = dtype          # "text", "numeric", "categorical", "datetime"
        self.sample_values = sample_values

    def __repr__(self):
        return f"ColumnInfo(name={self.name!r}, dtype={self.dtype!r})"


def import_file(path: str, **kwargs) -> pd.DataFrame:
    """
    Load a single file into a DataFrame.
    Raises ImportError on unsupported format or parse failure.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ImportError(
            f"Unsupported file format: {ext!r}. "
            f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    try:
        if ext == ".csv":
            df = _read_csv(path, **kwargs)
        elif ext == ".txt":
            df = _read_txt(path, **kwargs)
        elif ext in (".xlsx", ".xls"):
            df = _read_excel(path, **kwargs)
        else:
            raise ImportError(f"Unhandled extension: {ext}")
    except ImportError:
        raise
    except Exception as exc:
        raise ImportError(f"Failed to read {os.path.basename(path)}: {exc}") from exc

    if df.empty:
        raise ImportError(f"File appears to be empty: {os.path.basename(path)}")

    return df


def import_files(paths: List[str], **kwargs) -> pd.DataFrame:
    """
    Load and concatenate multiple files.
    Adds a 'source_file' column with the originating filename.
    """
    frames = []
    for path in paths:
        df = import_file(path, **kwargs)
        df.insert(0, "_source_file", os.path.basename(path))
        frames.append(df)

    if not frames:
        raise ImportError("No files were loaded.")

    combined = pd.concat(frames, ignore_index=True)
    return combined


def detect_column_types(df: pd.DataFrame) -> List[ColumnInfo]:
    """Infer column semantics for the column mapping wizard."""
    infos = []
    for col in df.columns:
        series = df[col].dropna()
        dtype = _infer_dtype(series)
        sample = series.head(3).tolist()
        infos.append(ColumnInfo(name=col, dtype=dtype, sample_values=sample))
    return infos


def suggest_text_column(df: pd.DataFrame, infos: List[ColumnInfo]) -> Optional[str]:
    """
    Heuristically suggest the best text column:
    1. Column named 'text', 'content', 'body', 'message', 'tweet', etc.
    2. Longest average string length among 'text' columns.
    """
    priority_names = {"text", "content", "body", "message", "tweet", "post",
                      "comment", "response", "answer", "description", "review"}

    text_cols = [i for i in infos if i.dtype == "text"]
    if not text_cols:
        return None

    # Check priority names first
    for info in text_cols:
        if info.name.lower() in priority_names:
            return info.name

    # Fall back to longest average length
    def avg_len(col_name):
        return df[col_name].dropna().astype(str).str.len().mean()

    return max(text_cols, key=lambda i: avg_len(i.name)).name


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------

def _read_csv(path: str, **kwargs) -> pd.DataFrame:
    # Try UTF-8 first, fall back to latin-1
    try:
        return pd.read_csv(path, encoding="utf-8", **kwargs)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="latin-1", **kwargs)


def _read_txt(path: str, **kwargs) -> pd.DataFrame:
    """
    Plain text files: one document per line → single 'text' column.
    If the file looks tab-delimited, treat it like a TSV.
    """
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        first_line = fh.readline()

    if "\t" in first_line:
        try:
            return pd.read_csv(path, sep="\t", encoding="utf-8", **kwargs)
        except Exception:
            pass

    # One document per line
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        lines = [line.rstrip("\n") for line in fh if line.strip()]
    return pd.DataFrame({"text": lines})


def _read_excel(path: str, **kwargs) -> pd.DataFrame:
    return pd.read_excel(path, **kwargs)


def _infer_dtype(series: pd.Series) -> str:
    if series.empty:
        return "text"

    # Try numeric
    try:
        pd.to_numeric(series)
        return "numeric"
    except (ValueError, TypeError):
        pass

    # Try datetime
    try:
        pd.to_datetime(series, infer_datetime_format=True)
        return "datetime"
    except Exception:
        pass

    # Text vs categorical: if unique ratio < 10% and fewer than 50 unique, it's categorical
    n_unique = series.nunique()
    n_total = len(series)
    str_series = series.astype(str)
    avg_len = str_series.str.len().mean()

    if n_unique < 50 and n_total > 0 and (n_unique / n_total) < 0.1:
        return "categorical"

    if avg_len < 15 and n_unique < 200:
        return "categorical"

    return "text"
