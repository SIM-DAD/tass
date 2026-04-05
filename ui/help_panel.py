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
     <p>TASS is a desktop application for dictionary-based text analysis.
     It is designed for social science researchers, humanities scholars, and data journalists
     who need NLP-powered insights without writing code.</p>
     <h3>Basic Workflow</h3>
     <ol>
       <li><b>Import</b> — Load a CSV, TXT, or XLSX file via File → Import Data</li>
       <li><b>Analyze</b> — Select dictionaries, choose a scoring mode, and click Run Analysis</li>
       <li><b>Results</b> — Browse entry-level scores, word matches, correlations, coverage, and KWIC concordance</li>
       <li><b>Compare</b> — Select dependent variables and a grouping factor, then run t-tests / ANOVA</li>
       <li><b>Visualize</b> — Generate publication-quality charts (bar, box, violin, heatmap, word cloud, scatter)</li>
       <li><b>Export</b> — Save CSV, Excel, APA tables, or chart files</li>
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
     <p>Select the scoring mode in the <b>Scoring Mode</b> dropdown on the Analyze panel:</p>
     <ul>
       <li><b>Dictionary default</b> — Uses each dictionary's built-in scoring:
         <ul>
           <li><i>Binary (%)</i> — (matched / total tokens) × 100</li>
           <li><i>Weighted</i> — Sum of numeric word weights (e.g., AFINN: −5 to +5)</li>
           <li><i>Count</i> — Raw count of matched tokens</li>
         </ul>
       </li>
       <li><b>Count (raw frequency)</b> — Overrides all dictionaries: returns raw match count per category</li>
       <li><b>TF-IDF</b> — Term Frequency × Inverse Document Frequency. Weights rare matches higher
       than common ones. TF = count/tokens, IDF = log(N/(1+DF)). Best for identifying
       distinctive vocabulary across documents.</li>
     </ul>
     <h3>N-gram (Multi-Word) Support</h3>
     <p>Dictionaries can include multi-word entries like <code>"not happy"</code> or
     <code>"on the other hand"</code>. TASS automatically:</p>
     <ul>
       <li>Detects multi-word entries in dictionaries</li>
       <li>Generates bigrams/trigrams from your text</li>
       <li>Suppresses constituent unigrams from double-counting — if "not happy" matches,
       "happy" alone will <i>not</i> also count as a match in other categories</li>
     </ul>"""),

    ("Analysis", "Preprocessing Options",
     """<h2>Preprocessing Options</h2>
     <p>Preprocessing options are configured on the <b>Analyze</b> panel before running analysis:</p>
     <ul>
       <li><b>Lemmatize tokens</b> — Reduces words to base form (e.g., "running" → "run",
       "better" → "good"). Slower but can improve match recall for dictionaries
       that only list base forms. Uses NLTK WordNet lemmatizer.</li>
       <li><b>Remove stopwords</b> — Strips common function words ("the", "is", "and")
       before dictionary matching. Only useful for dictionaries that do not
       include stopwords in their word lists.</li>
       <li><b>Min token length</b> — Filters out tokens shorter than N characters.
       Default is 1 (keep all tokens). Setting to 2 or 3 removes single-character
       tokens that may be punctuation artifacts.</li>
     </ul>
     <p>All text is lowercased and punctuation is stripped before tokenization.</p>"""),

    ("Analysis", "Bundled Dictionaries",
     """<h2>Bundled Dictionaries (v1.0)</h2>
     <table>
       <tr><th>Dictionary</th><th>Categories</th><th>Scoring</th><th>License</th></tr>
       <tr><td>AFINN-165</td><td>Sentiment valence (−5 to +5)</td><td>Weighted</td><td>MIT</td></tr>
       <tr><td>VADER Lexicon</td><td>Sentiment (−4 to +4)</td><td>Weighted</td><td>MIT</td></tr>
       <tr><td>Moral Foundations 2.0</td><td>Care, Fairness, Loyalty, Authority, Purity (virtue + vice)</td><td>Binary</td><td>CC-BY</td></tr>
       <tr><td>Brysbaert Concreteness</td><td>Concreteness ratings (1.0–5.0)</td><td>Weighted</td><td>CC-BY</td></tr>
       <tr><td>WordNet POS</td><td>Noun, Verb, Adjective</td><td>Binary</td><td>Princeton WN License</td></tr>
       <tr><td>NLTK Stopwords</td><td>Function words, Pronouns, Prepositions</td><td>Binary</td><td>Apache 2.0</td></tr>
     </table>
     <p>You can also import custom dictionaries in JSON format via the
     <b>+ Import Custom Dictionary…</b> button on the Analyze panel.</p>"""),

    ("Group Comparisons", "Running Comparisons",
     """<h2>Group Comparisons</h2>
     <p>Navigate to the <b>Compare</b> panel after running an analysis.</p>
     <ol>
       <li>Select the <b>Between-Subjects Factor</b> — the column whose values define your
       groups (e.g., "condition" with values "treatment" / "control").</li>
       <li>Check the <b>Dependent Variable(s)</b> you want to compare. Only checked
       variables are analyzed — this prevents unwanted tests and improves performance
       on large datasets.</li>
       <li>Choose your <b>options</b>:
         <ul>
           <li><i>Non-parametric tests</i> — Use Mann-Whitney U / Kruskal-Wallis instead
           of Welch t-test / ANOVA</li>
           <li><i>Correction</i> — Bonferroni (default), FDR (Benjamini-Hochberg), or None</li>
         </ul>
       </li>
       <li>Click <b>Run Comparison</b>.</li>
     </ol>
     <h3>Structured Output</h3>
     <p>Results are displayed in 5 collapsible sections:</p>
     <ol>
       <li><b>Descriptive Statistics</b> — Group means, SDs, sample sizes, 95% confidence intervals</li>
       <li><b>Assumption Checks</b> — Shapiro-Wilk normality test + Levene's test for equal variances</li>
       <li><b>Inferential Test Results</b> — Test statistic with degrees of freedom, p-value, effect size + interpretation</li>
       <li><b>Post-Hoc Comparisons</b> — Pairwise results (Tukey HSD for parametric, Dunn's test for non-parametric)</li>
       <li><b>Interpretive Notes</b> — Auto-generated APA-style result sentences ready for manuscripts</li>
     </ol>"""),

    ("Group Comparisons", "Statistical Tests",
     """<h2>Statistical Tests</h2>
     <h3>Inferential Tests</h3>
     <table>
       <tr><th>Test</th><th>Groups</th><th>Type</th><th>Output</th></tr>
       <tr><td>Welch t-test</td><td>2</td><td>Parametric</td><td>t(df) = X.XX</td></tr>
       <tr><td>Mann-Whitney U</td><td>2</td><td>Non-parametric</td><td>U = X.XX</td></tr>
       <tr><td>One-way ANOVA</td><td>3+</td><td>Parametric</td><td>F(df₁, df₂) = X.XX</td></tr>
       <tr><td>Kruskal-Wallis</td><td>3+</td><td>Non-parametric</td><td>H(df) = X.XX</td></tr>
     </table>
     <h3>Post-Hoc Tests</h3>
     <ul>
       <li><b>Tukey HSD</b> — Used after significant ANOVA. Controls family-wise error rate.</li>
       <li><b>Dunn's test</b> — Used after significant Kruskal-Wallis. Pairwise Mann-Whitney U with Bonferroni correction. The correct nonparametric post-hoc.</li>
     </ul>
     <h3>Assumption Checks</h3>
     <ul>
       <li><b>Shapiro-Wilk</b> — Tests normality per group. Violation (p &lt; .05) suggests non-parametric tests may be more appropriate.</li>
       <li><b>Levene's test</b> — Tests homogeneity of variance across groups. Violation suggests unequal variances (Welch t-test already handles this).</li>
     </ul>
     <h3>Effect Sizes</h3>
     <table>
       <tr><th>Metric</th><th>Test</th><th>Negligible</th><th>Small</th><th>Medium</th><th>Large</th></tr>
       <tr><td>Cohen's d</td><td>t-test</td><td>&lt; 0.2</td><td>0.2–0.5</td><td>0.5–0.8</td><td>&gt; 0.8</td></tr>
       <tr><td>η² (eta-squared)</td><td>ANOVA</td><td>&lt; .01</td><td>.01–.06</td><td>.06–.14</td><td>&gt; .14</td></tr>
       <tr><td>r (rank-biserial)</td><td>Mann-Whitney</td><td>&lt; 0.1</td><td>0.1–0.3</td><td>0.3–0.5</td><td>&gt; 0.5</td></tr>
     </table>
     <h3>Multiple Comparison Corrections</h3>
     <ul>
       <li><b>Bonferroni</b> — Divides alpha by number of tests. Conservative: controls family-wise error rate. May miss real effects when testing many variables.</li>
       <li><b>FDR (Benjamini-Hochberg)</b> — Controls false discovery rate. More powerful than Bonferroni: allows more detections at the cost of slightly higher false positive rate. Recommended when testing many variables simultaneously.</li>
       <li><b>None</b> — No correction. Each test uses α = .05 independently. Increases risk of false positives.</li>
     </ul>
     <h3>P-Value Formatting (APA 7th Edition)</h3>
     <p>All p-values follow APA 7th Ed. conventions: no leading zero (.006, not 0.006),
     three decimal places, and <code>p &lt; .001</code> only when truly below .001.</p>
     <p>*** p &lt; .001 &nbsp; ** p &lt; .01 &nbsp; * p &lt; .05 &nbsp; n.s. not significant</p>"""),

    ("Results", "Results Tabs",
     """<h2>Results Panel Tabs</h2>
     <p>After running an analysis, the Results panel shows multiple tabs:</p>
     <ul>
       <li><b>Scores</b> — Entry-level scores table. Sortable by any column. Shows the
       numerical score for each dictionary category across every row in your data.</li>
       <li><b>Word Matches</b> — Interactive highlighting: select a category and entry
       to see exactly which words matched.</li>
       <li><b>Summary</b> — Document-level aggregate statistics: mean, SD, min, max,
       median, and count for each category across the entire dataset.</li>
       <li><b>Correlations</b> — Pairwise correlation matrix between all category scores.
       Toggle between Pearson (linear) and Spearman (rank-order) using the Method dropdown.
       Stars indicate significance: * p &lt; .05, ** p &lt; .01, *** p &lt; .001.</li>
       <li><b>Coverage</b> — Dictionary coverage statistics per category: entries matched,
       total entries, coverage percentage, total matches, mean matches per entry.</li>
       <li><b>KWIC</b> — Keyword-In-Context concordance viewer. Shows matched words
       with left and right context. Filter by category. Export to CSV.</li>
     </ul>"""),

    ("Results", "Correlations",
     """<h2>Correlation Matrix</h2>
     <p>The Correlations tab computes pairwise correlations between all dictionary category scores.</p>
     <h3>Methods</h3>
     <ul>
       <li><b>Pearson r</b> — Measures linear association. Assumes normality and
       interval-level data. The default for most dictionary score analyses.</li>
       <li><b>Spearman r<sub>s</sub></b> — Rank-order correlation. Non-parametric alternative.
       Use when data are ordinal, non-normal, or you suspect non-linear relationships.</li>
     </ul>
     <p>Switch methods using the <b>Method</b> dropdown in the Correlations tab header.
     The matrix re-computes immediately when you change the method.</p>"""),

    ("Visualizations", "Chart Types",
     """<h2>Chart Types</h2>
     <ul>
       <li><b>Bar Chart</b> — Mean category scores for the entire dataset (top N categories).</li>
       <li><b>Word Cloud</b> — Frequency visualization of matched words across all entries.</li>
       <li><b>Box Plot</b> — Distribution of scores per group for a single category. Requires a group column.</li>
       <li><b>Violin Plot</b> — Richer shape of score distribution per group. Combines box plot with kernel density.</li>
       <li><b>Heatmap</b> — Score matrix showing all categories at once (top N).</li>
       <li><b>Scatter Plot</b> — Two-category scatter with regression line and r/p annotation.</li>
     </ul>
     <h3>Color Palettes</h3>
     <ul>
       <li><b>Default</b> — ColorBrewer-based palette for general use.</li>
       <li><b>Colorblind-safe</b> — Viridis palette, distinguishable by all viewers.</li>
       <li><b>Grayscale</b> — For journals that require black-and-white figures.</li>
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
     <p>The TASS trial is free for <b>30 days</b> and includes the full toolset with one limitation:</p>
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
     <p>After purchasing a subscription at <b>usetass.app</b>:</p>
     <ol>
       <li>Open <b>Help → License / Activate…</b></li>
       <li>Enter your Gumroad license key (from your purchase receipt email)</li>
       <li>Click <b>Activate</b></li>
     </ol>
     <p>Activation requires an internet connection the first time.
     After activation, TASS works offline with periodic re-verification.</p>
     <h3>Subscription Tiers</h3>
     <table>
       <tr><th>Tier</th><th>Price</th><th>Seats</th><th>Audience</th></tr>
       <tr><td>Academic</td><td>$79/yr</td><td>2</td><td>Students, faculty, staff</td></tr>
       <tr><td>Professional</td><td>$129/yr</td><td>2</td><td>Journalists, consultants, nonprofits</td></tr>
       <tr><td>Lab</td><td>$249/yr</td><td>10</td><td>Research labs</td></tr>
       <tr><td>Department</td><td>$699/yr</td><td>50</td><td>Academic departments</td></tr>
     </table>"""),

    ("Keyboard Shortcuts", "Shortcuts",
     """<h2>Keyboard Shortcuts</h2>
     <table>
       <tr><th>Shortcut</th><th>Action</th></tr>
       <tr><td>Ctrl+N</td><td>New Analysis</td></tr>
       <tr><td>Ctrl+O</td><td>Open Project</td></tr>
       <tr><td>Ctrl+S</td><td>Save Project</td></tr>
       <tr><td>Ctrl+I</td><td>Import Data</td></tr>
       <tr><td>Ctrl+R</td><td>Run Analysis</td></tr>
       <tr><td>Ctrl+E</td><td>Export Results</td></tr>
       <tr><td>F1</td><td>Help</td></tr>
     </table>"""),
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
            "QTreeWidget::item:selected { background-color: #D1FAE5; color: #256B4E; }"
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
