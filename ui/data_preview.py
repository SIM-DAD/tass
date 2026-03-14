"""
Data Preview — read-only QTableView of imported DataFrame.
Sprint 2.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableView
from PySide6.QtCore import Qt, QAbstractTableModel
import pandas as pd


class PandasTableModel(QAbstractTableModel):
    """Thin adapter to display a pandas DataFrame in a QTableView."""

    def __init__(self, df: pd.DataFrame, parent=None):
        super().__init__(parent)
        self._df = df

    def rowCount(self, parent=None):
        return len(self._df)

    def columnCount(self, parent=None):
        return len(self._df.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            val = self._df.iloc[index.row(), index.column()]
            return str(val) if pd.notna(val) else ""
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._df.columns[section])
            return str(section + 1)
        return None


class DataPreviewPanel(QWidget):
    """Displays the imported DataFrame. Embedded in the import wizard flow."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        self._info_lbl = QLabel("No data imported yet.")
        self._info_lbl.setStyleSheet("color: #888888;")
        layout.addWidget(self._info_lbl)

        self._table = QTableView()
        self._table.setAlternatingRowColors(True)
        self._table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self._table)

    def load_dataframe(self, df: pd.DataFrame):
        row_count = len(df)
        col_count = len(df.columns)
        self._info_lbl.setText(f"{row_count:,} rows × {col_count} columns")
        model = PandasTableModel(df)
        self._table.setModel(model)
