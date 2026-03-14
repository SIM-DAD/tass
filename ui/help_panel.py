"""
Help Panel — Sprint 9.
Searchable in-app documentation sidebar (F1).
Content is structured as a tree: sections → articles.
Each article is plain text rendered in a QTextBrowser.
"""

from __future__ import annotations
from typing import Dict, List, Tuple

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTreeWidget, QTreeWidgetItem, QTextBrowser,
    QSplitter, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QKeySequence


# ══════════════════════════════════════════════════════════════════════
# Help content
# ══════════════════════════════════════════════════════════════════════

HELP_CONTENT: List[Tuple[str, str, str]] = [
    # (section, article_title, body_html)
    ("Getting Started", "Overview",
     """<h2>TASS — Text Analysis for Social Scientists</h2>
     <p>TASS is a native Windows desktop application for dictionary-based text analysis.
     It is designed for social science researchers, humanities scholars, and data journalists
     who need NLP-powered insights without writing code.</p>
     <h3>Basic Workflow</h3>
     <ol>
       <li><b>Import</b> — Load a CSV, TXT, or XLSX file via File → Import Data</li>
       <li><b>Analyze</b> — Select dictionaries and click Run Analysis</li>
       <li><b>Results</b> — Browse entry-level scores, word matches, and summary statistics</li>
       <li><b>Compare</b> — Define groups and run t-tests / ANOVA</li>
       <li><b>Visualize</b> — Generate publication-quality charts</li>
       <li><b>Export</b> — Save CSV, Excel, or chart files</li>
     </ol>"""),

    ("Getting Started", "System Requirements",
     """<h2>System Requirements</h2>
     <table>
       <tr><th>Component</th><th>Minimum</th><th>Recommended</th></tr>
       <tr><td>OS</td><td>Windows 10 64-bit</td><td>Windows 11</td></tr>
       <tr><td>CPU</td><td>4-core</td><td>6-core or more</td></tr>
       <tr><td>RAM</td><td>8 GB</td><td>16 GB</td></tr>
       <tr><td>Disk</td><td>3 GB free</td><td>5 GB free</td></tr>
     </table>
     <p>TASS runs all analysis locally. Internet is required only for license activation
     and optional update checks.</p>"""),

    ("Importing Data", "Supported File Formats",
     """<h2>Supported File Formats</h2>
     <ul>
       <li><b>CSV</b> — Comma-separated values. UTF-8 and Latin-1 encodings supported.</li>
       <li><b>TXT</b> — Plain text. One document per line, or tab-delimited (auto-detected).</li>
       <li><b>XLSX / XLS</b> — Microsoft Excel. First sheet is loaded by default.</li>
     </ul>
     <h3>Large Datasets</h3>
     <p>TASS is tested and stable with datasets up to 500,000 entries. Analysis uses all
     available CPU cores via multi-threading.</p>"""),

    ("Importing Data", "Column Mapping",
     """<h2>Column Mapping</h2>
     <p>After loading a file, the Import wizard asks you to map columns:</p>
     <ul>
       <li><b>Text column</b> — The column containing the text to analyze (e.g., tweet_text,
       response, body). TASS auto-detects this based on column name and content length.</li>
       <li><b>Group column</b> (optional) — A column whose values define comparison groups
       (e.g., political_party, condition, sentiment_label).</li>
       <li><b>Metadata columns</b> (optional) — Any other columns you want carried through
       to the export (e.g., user_id, date, source).</li>
     </ul>"""),

    ("Analysis", "Dictionary Engine",
     """<h2>Dictionary Engine</h2>
     <p>TASS matches each tokenized text entry against the selected dictionaries and
     returns scores at three levels:</p>
     <ul>
       <li><b>Word-level</b> — Which specific words matched each category</li>
       <li><b>Entry-level</b> — Score per row (per tweet, survey response, etc.)</li>
       <li><b>Document-level</b> — Aggregate statistics across the full dataset</li>
     </ul>
     <h3>Scoring Modes</h3>
     <ul>
       <li><b>Binary</b> — (matched / total tokens) × 100. Range: 0–100.</li>
       <li><b>Weighted</b> — Sum of word weights (e.g., AFINN: −5 to +5).</li>
       <li><b>Count</b> — Raw count of matched words per entry.</li>
     </ul>"""),

    ("Analysis", "Bundled Dictionaries",
     """<h2>Bundled Dictionaries (v1.0)</h2>
     <table>
       <tr><th>Dictionary</th><th>Categories</th><th>License</th></tr>
       <tr><td>AFINN-165</td><td>Sentiment valence (−5 to +5)</td><td>MIT</td></tr>
       <tr><td>VADER Lexicon</td><td>Positive, Negative, Neutral</td><td>MIT</td></tr>
       <tr><td>Moral Foundations 2.0</td><td>Care, Fairness, Loyalty, Authority, Purity</td><td>CC-BY</td></tr>
       <tr><td>Brysbaert Concreteness</td><td>Concreteness ratings</td><td>CC-BY</td></tr>
       <tr><td>HurtLex</td><td>Offensive language categories</td><td>CC-BY-SA</td></tr>
       <tr><td>WordNet POS</td><td>Noun, Verb, Adjective, Adverb</td><td>Princeton</td></tr>
       <tr><td>NLTK Stopwords</td><td>Function words, Pronouns, Prepositions</td><td>Apache 2.0</td></tr>
       <tr><td>SentiWordNet 3.0</td><td>Positive, Negative, Objective</td><td>CC-BY-SA</td></tr>
     </table>"""),

    ("Group Comparisons", "Running Comparisons",
     """<h2>Group Comparisons</h2>
     <p>Navigate to the <b>Compare</b> panel after running an analysis.</p>
     <ol>
       <li>Select the <b>group column</b> from the dropdown (a column in your dataset
       whose values define the groups, e.g., "condition" with values "treatment", "control").</li>
       <li>Choose whether to use <b>non-parametric</b> tests (Mann-Whitney U) for 2-group
       comparisons, or parametric (Welch t-test, the default).</li>
       <li>Toggle <b>Bonferroni correction</b> to control for multiple comparisons
       across dictionary categories.</li>
       <li>Click <b>Run Comparison</b>.</li>
     </ol>"""),

    ("Group Comparisons", "Statistical Tests",
     """<h2>Statistical Tests</h2>
     <ul>
       <li><b>Welch t-test</b> — 2 groups, parametric. Does not assume equal variances.</li>
       <li><b>Mann-Whitney U</b> — 2 groups, non-parametric. Rank-based.</li>
       <li><b>One-way ANOVA</b> — 3 or more groups, parametric.</li>
     </ul>
     <h3>Effect Sizes</h3>
     <ul>
       <li><b>Cohen's d</b> — Standardized mean difference (t-test).</li>
       <li><b>Rank-biserial r</b> — Effect size for Mann-Whitney U.</li>
       <li><b>Eta-squared (η²)</b> — Proportion of variance explained (ANOVA).</li>
     </ul>
     <h3>Significance Levels</h3>
     <p>*** p &lt; .001 &nbsp; ** p &lt; .01 &nbsp; * p &lt; .05 &nbsp; n.s. not significant</p>"""),

    ("Visualizations", "Chart Types",
     """<h2>Chart Types</h2>
     <ul>
       <li><b>Bar Chart</b> — Mean category scores for the entire dataset (top N categories).</li>
       <li><b>Word Cloud</b> — Frequency visualization of matched words across all entries.</li>
       <li><b>Box Plot</b> — Distribution of scores per group for a single category.</li>
       <li><b>Violin Plot</b> — Richer shape of score distribution per group.</li>
       <li><b>Heatmap</b> — Score matrix showing all categories at once (top N).</li>
     </ul>
     <h3>Export Formats</h3>
     <p>All charts can be exported as <b>PNG (300 DPI)</b> for presentations/publications,
     or <b>SVG</b> for vector-quality journal figures.</p>"""),

    ("Export & Citation", "Export Formats",
     """<h2>Export Formats</h2>
     <ul>
       <li><b>CSV</b> — Entry-level scores with optional metadata columns. Includes citation block.</li>
       <li><b>Excel (.xlsx)</b> — Multi-sheet workbook: Raw Scores, Summary Statistics,
       Group Comparisons, Citation.</li>
       <li><b>PNG/SVG</b> — High-resolution chart exports.</li>
     </ul>
     <p>All text-based exports include an auto-generated APA citation block at the bottom.</p>"""),

    ("Export & Citation", "How to Cite TASS",
     """<h2>How to Cite TASS</h2>
     <p>Access the citation dialog via <b>Export → How to Cite TASS…</b> or press
     <b>Help → How to Cite TASS…</b></p>
     <p>TASS exports include the citation block automatically. When you publish research
     using TASS, please include the citation in your methods section referencing the
     software and version used.</p>
     <p>A Zenodo DOI is minted at each major release for stable, archival citation.</p>"""),

    ("Projects", "Saving & Loading",
     """<h2>Project Files (.tass)</h2>
     <p>TASS saves your full session as a <code>.tass</code> file — a ZIP archive containing:</p>
     <ul>
       <li>Your original data (compressed with Parquet)</li>
       <li>All analysis results</li>
       <li>Analysis configuration (which dictionaries, group settings)</li>
       <li>UI state (active tab, color palette)</li>
     </ul>
     <p>Opening a <code>.tass</code> file restores the exact session state, including results.
     You do not need to re-run analysis after loading a project.</p>"""),

    ("License & Trial", "Trial Mode",
     """<h2>Trial Mode</h2>
     <p>The TASS trial is free for 14 days and includes the full toolset with one limitation:</p>
     <ul>
       <li><b>Row limit:</b> 500 entries per analysis run.</li>
     </ul>
     <p>After the trial expires, the app enters <b>view-only mode</b> — you can open and
     export existing <code>.tass</code> projects but cannot run new analyses.</p>
     <h3>Starting a Trial</h3>
     <p>On first launch, enter your email address to start the trial.
     Your email is added to the TASS mailing list for release announcements.</p>"""),

    ("License & Trial", "Activating a License",
     """<h2>Activating a License</h2>
     <p>After purchasing at the TASS website:</p>
     <ol>
       <li>Open <b>Help → License / Activate…</b></li>
       <li>Enter your Lemon Squeezy license key</li>
       <li>Click <b>Activate</b></li>
     </ol>
     <p>Activation requires an internet connection the first time.
     After activation, TASS works fully offline until your license expires.</p>
     <h3>Machine Limits</h3>
     <p>Individual licenses allow 2 machines simultaneously.
     Team licenses allow 5 or 10 seats depending on tier.</p>"""),
]


# ══════════════════════════════════════════════════════════════════════
# Help Panel
# ══════════════════════════════════════════════════════════════════════

class HelpPanel(QWidget):
    """
    Searchable help panel.
    Left: tree of sections/articles + search box.
    Right: QTextBrowser rendering the selected article.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_content_index()
        self._build_ui()
        self._populate_tree()
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self._do_search)

    def _build_content_index(self):
        """Build lookup dict: (section, title) -> body_html."""
        self._content: Dict[Tuple[str, str], str] = {}
        self._sections: Dict[str, List[str]] = {}

        for section, title, body in HELP_CONTENT:
            self._content[(section, title)] = body
            self._sections.setdefault(section, []).append(title)

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # ── Left pane: search + tree ──────────────────────────────────
        left = QWidget()
        left.setMinimumWidth(220)
        left.setMaximumWidth(300)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(8, 12, 4, 8)
        left_layout.setSpacing(8)

        # Search
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search help…")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(lambda _: self._search_timer.start())
        left_layout.addWidget(self._search)

        # Tree
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setFont(QFont("Segoe UI", 9))
        self._tree.setIndentation(12)
        self._tree.itemClicked.connect(self._on_item_clicked)
        self._tree.setStyleSheet(
            "QTreeWidget { border: none; background-color: #F9FAFB; }"
            "QTreeWidget::item { padding: 4px 2px; }"
            "QTreeWidget::item:selected { background-color: #DBEAFE; color: #1D4ED8; }"
        )
        left_layout.addWidget(self._tree, 1)

        splitter.addWidget(left)

        # ── Right pane: article browser ───────────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Article toolbar
        art_bar = QFrame()
        art_bar.setFixedHeight(40)
        art_bar.setStyleSheet(
            "background-color: #F9FAFB; border-bottom: 1px solid #E5E7EB;"
        )
        art_bar_layout = QHBoxLayout(art_bar)
        art_bar_layout.setContentsMargins(16, 0, 16, 0)

        self._article_title = QLabel("Select a topic from the list")
        self._article_title.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self._article_title.setStyleSheet("color: #374151;")
        art_bar_layout.addWidget(self._article_title)
        art_bar_layout.addStretch()

        right_layout.addWidget(art_bar)

        self._browser = QTextBrowser()
        self._browser.setOpenLinks(True)
        self._browser.setOpenExternalLinks(True)
        self._browser.setStyleSheet(
            "QTextBrowser { border: none; font-family: 'Segoe UI'; font-size: 10pt; "
            "background-color: #FFFFFF; padding: 8px; }"
        )
        self._browser.document().setDefaultStyleSheet(
            "h2 { color: #111827; font-size: 14pt; margin-bottom: 6px; }"
            "h3 { color: #374151; font-size: 11pt; margin-top: 16px; }"
            "p  { color: #374151; line-height: 1.6; }"
            "li { color: #374151; line-height: 1.8; }"
            "table { border-collapse: collapse; width: 100%; margin: 8px 0; }"
            "th { background-color: #F3F4F6; padding: 6px 12px; text-align: left; "
            "     border: 1px solid #E5E7EB; }"
            "td { padding: 6px 12px; border: 1px solid #E5E7EB; }"
            "code { background-color: #F3F4F6; padding: 2px 4px; "
            "       font-family: Consolas, monospace; font-size: 9pt; }"
        )
        right_layout.addWidget(self._browser, 1)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

    def _populate_tree(self, filter_text: str = ""):
        self._tree.clear()
        ft = filter_text.lower()

        for section, articles in self._sections.items():
            matching = [
                title for title in articles
                if not ft or ft in title.lower() or ft in self._content[(section, title)].lower()
            ]
            if not matching:
                continue

            section_item = QTreeWidgetItem([section])
            section_item.setFont(0, QFont("Segoe UI", 9, QFont.Bold))
            section_item.setForeground(0, Qt.darkGray)
            section_item.setFlags(section_item.flags() & ~Qt.ItemIsSelectable)
            self._tree.addTopLevelItem(section_item)

            for title in matching:
                art_item = QTreeWidgetItem([title])
                art_item.setData(0, Qt.UserRole, (section, title))
                section_item.addChild(art_item)

        self._tree.expandAll()

        # Auto-select first article
        if self._tree.topLevelItemCount() > 0:
            first_section = self._tree.topLevelItem(0)
            if first_section.childCount() > 0:
                first_art = first_section.child(0)
                self._tree.setCurrentItem(first_art)
                self._on_item_clicked(first_art, 0)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        key = item.data(0, Qt.UserRole)
        if key is None:
            return
        section, title = key
        body = self._content.get((section, title), "")
        self._browser.setHtml(body)
        self._article_title.setText(f"{section}  ›  {title}")

    def _do_search(self):
        self._populate_tree(self._search.text().strip())

    # Allow F1 to focus the search box
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F1:
            self._search.setFocus()
            self._search.selectAll()
        else:
            super().keyPressEvent(event)
