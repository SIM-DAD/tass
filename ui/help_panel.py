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
     """<h2>Bundled Dictionaries</h2>
     <table>
       <tr><th>Dictionary</th><th>Categories</th><th>Scoring</th><th>License</th></tr>
       <tr><td>AFINN-165</td><td>Sentiment valence (−5 to +5)</td><td>Weighted</td><td>MIT</td></tr>
       <tr><td>VADER Lexicon</td><td>Sentiment (−4 to +4)</td><td>Weighted</td><td>MIT</td></tr>
       <tr><td>Moral Foundations 2.0</td><td>Care, Fairness, Loyalty, Authority, Purity (virtue + vice)</td><td>Binary</td><td>CC-BY</td></tr>
       <tr><td>Brysbaert Concreteness</td><td>Concreteness ratings (1.0–5.0)</td><td>Weighted</td><td>CC-BY</td></tr>
       <tr><td>WordNet POS (Full)</td><td>Noun, Verb, Adjective, Adverb (147K lemmas)</td><td>Binary</td><td>Princeton WN License</td></tr>
       <tr><td>WordNet POS (Curated)</td><td>Noun, Verb, Adjective, Adverb (510 common words)</td><td>Binary</td><td>Princeton WN License</td></tr>
       <tr><td>Warriner VAD Norms</td><td>Valence, Arousal, Dominance (1–9 scale)</td><td>Weighted</td><td>CC-BY</td></tr>
       <tr><td>Empath</td><td>194 topic categories (affect, cognition, social, content)</td><td>Binary</td><td>MIT</td></tr>
       <tr><td>NLTK Stopwords</td><td>Function words, Pronouns, Prepositions</td><td>Binary</td><td>Apache 2.0</td></tr>
     </table>

     <h3>Optional Download Dictionaries</h3>
     <p>These dictionaries are not bundled due to licensing. Download them from the original
     source and import via <b>File → Import Dictionary</b>.</p>
     <table>
       <tr><th>Dictionary</th><th>Categories</th><th>License</th><th>Source</th></tr>
       <tr><td>NRC EmoLex</td><td>8 emotions + positive/negative</td><td>Free for research</td><td>saifmohammad.com</td></tr>
       <tr><td>HurtLex</td><td>Hurtful language categories</td><td>CC-BY-SA</td><td>github.com/valeriobasile/hurtlex</td></tr>
       <tr><td>SentiWordNet 3.0</td><td>Positive/negative/objective per synset</td><td>CC-BY-SA</td><td>github.com/aesuli/SentiWordNet</td></tr>
     </table>

     <p>You can also import your own custom dictionaries. See the
     <b>Custom Dictionary Format</b> topic below.</p>"""),

    ("Analysis", "Custom Dictionary Format",
     """<h2>Custom Dictionary Format</h2>
     <p>TASS accepts custom dictionaries as <b>CSV</b>, <b>Excel (.xlsx)</b>, or <b>JSON</b> files.
     CSV/Excel is the easiest option for most researchers.</p>

     <h3>CSV / Excel Format (recommended)</h3>
     <p>Create a spreadsheet with these columns:</p>
     <table>
       <tr><th>Column</th><th>Required</th><th>Description</th></tr>
       <tr><td><code>word</code></td><td>Yes</td><td>The dictionary term</td></tr>
       <tr><td><code>category</code></td><td>Yes</td><td>Which category the word belongs to</td></tr>
       <tr><td><code>score</code></td><td>No</td><td>Numeric weight (if omitted, scoring is binary)</td></tr>
     </table>

     <p><b>Binary example</b> (word membership):</p>
     <pre style="background-color: #1E293B; color: #E2E8F0; padding: 12px; border-radius: 6px; font-size: 9pt;">
word,category
happy,positive
joyful,positive
sad,negative
angry,negative</pre>

     <p><b>Weighted example</b> (numeric scores):</p>
     <pre style="background-color: #1E293B; color: #E2E8F0; padding: 12px; border-radius: 6px; font-size: 9pt;">
word,category,score
happy,positive_affect,3.5
joyful,positive_affect,4.2
sad,negative_affect,-2.7
angry,negative_affect,-3.1</pre>

     <p>Save as .csv or .xlsx and import via the <b>+ Import Custom Dictionary</b> button
     on the Analyze panel. The file name becomes the dictionary name.</p>

     <hr/>

     <h3>JSON Format (advanced)</h3>
     <p>For users who prefer structured data files, TASS also accepts JSON.
     Two scoring types are supported:</p>

     <h3>Binary (word membership)</h3>
     <p>Each category is a list of words. TASS counts matches and reports the
     percentage of tokens that match each category.</p>
     <pre style="background-color: #1E293B; color: #E2E8F0; padding: 12px; border-radius: 6px; font-size: 9pt;">
{
  "name": "My Custom Dictionary",
  "version": "1.0",
  "description": "What this dictionary measures.",
  "citation": "Author (Year). Title. Journal.",
  "license": "CC-BY",
  "scoring": "binary",
  "categories": {
    "category_a": ["word1", "word2", "multi word phrase"],
    "category_b": ["word3", "word4", "word5"]
  }
}</pre>

     <h3>Weighted (numeric scores per word)</h3>
     <p>Each category is a dictionary mapping words to numeric scores.
     TASS sums the scores for all matched words in each text entry.</p>
     <pre style="background-color: #1E293B; color: #E2E8F0; padding: 12px; border-radius: 6px; font-size: 9pt;">
{
  "name": "My Weighted Dictionary",
  "version": "1.0",
  "description": "A dictionary with numeric scores.",
  "citation": "Author (Year). Title. Journal.",
  "license": "CC-BY",
  "scoring": "weighted",
  "categories": {
    "positive": {"happy": 3.5, "joyful": 4.2},
    "negative": {"sad": -2.7, "angry": -3.1}
  }
}</pre>

     <h3>Required fields</h3>
     <table>
       <tr><th>Field</th><th>Required</th><th>Description</th></tr>
       <tr><td><code>name</code></td><td>Yes</td><td>Display name in the Analyze panel</td></tr>
       <tr><td><code>categories</code></td><td>Yes</td><td>Dict of category names → word lists or word-score dicts</td></tr>
       <tr><td><code>version</code></td><td>No</td><td>Version string (default: "unknown")</td></tr>
       <tr><td><code>citation</code></td><td>No</td><td>How to cite this dictionary</td></tr>
       <tr><td><code>license</code></td><td>No</td><td>License under which the dictionary is shared</td></tr>
       <tr><td><code>scoring</code></td><td>No</td><td>"binary" (default), "weighted", or "count"</td></tr>
       <tr><td><code>description</code></td><td>No</td><td>Brief description of the dictionary</td></tr>
     </table>

     <h3>Tips</h3>
     <ul>
       <li>All words are lowercased automatically — you don't need to pre-process.</li>
       <li>Multi-word phrases (e.g., "climate change") are supported. TASS matches
       bigrams and trigrams before unigrams, so phrase matches take priority.</li>
       <li>You can mix binary and weighted categories in the same dictionary —
       TASS detects the type per category based on whether the data is a list or a dict.</li>
       <li>Template files are included at <code>dictionaries/templates/</code> in the
       TASS installation folder.</li>
     </ul>"""),

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

    # ── Statistical Methods ────────────────────────────────────────

    ("Statistical Methods", "Overview",
     """<h2>Statistical Methods — Overview</h2>
     <p>TASS implements standard statistical methods from peer-reviewed literature using
     established open-source libraries. <b>No custom or proprietary statistical algorithms
     are used.</b> Every test, effect size, and correction method traces directly to
     <code>scipy.stats</code>, <code>NumPy</code>, <code>pandas</code>, or <code>NLTK</code>.</p>
     <p>This transparency is by design: researchers can verify, reproduce, and cite the
     exact implementations TASS relies on.</p>
     <h3>Core Libraries</h3>
     <table>
       <tr><th>Library</th><th>Version</th><th>Role</th></tr>
       <tr><td>SciPy</td><td>&ge; 1.11</td><td>Hypothesis tests, effect sizes, confidence intervals, regression</td></tr>
       <tr><td>NumPy</td><td>&ge; 1.24</td><td>Descriptive statistics, array operations</td></tr>
       <tr><td>pandas</td><td>&ge; 2.0</td><td>Data handling, correlation matrices</td></tr>
       <tr><td>NLTK</td><td>&ge; 3.8</td><td>Tokenization, stopwords, lemmatization</td></tr>
       <tr><td>matplotlib / seaborn</td><td>&ge; 3.7 / &ge; 0.12</td><td>Visualization</td></tr>
     </table>
     <h3>Default Parameters</h3>
     <table>
       <tr><th>Parameter</th><th>Value</th><th>Rationale</th></tr>
       <tr><td>Significance threshold (&alpha;)</td><td>0.05</td><td>Standard in social science research</td></tr>
       <tr><td>Confidence level</td><td>95%</td><td>Corresponds to &alpha; = .05</td></tr>
       <tr><td>Multiple comparisons</td><td>Bonferroni (default), BH-FDR (optional)</td><td>Family-wise error control</td></tr>
       <tr><td>Variance assumption</td><td>Welch's (unequal variances)</td><td>More robust default for social science data</td></tr>
     </table>"""),

    ("Statistical Methods", "Text Scoring",
     """<h2>Text Scoring Methods</h2>
     <p>TASS scores text entries by matching tokens against dictionary word lists. Three
     scoring modes are available:</p>
     <h3>Binary (Percentage) Scoring</h3>
     <p><code>score = (matched_tokens / total_tokens) &times; 100</code></p>
     <p>The proportion of tokens matching a dictionary category, expressed as a percentage.
     This is the default and most interpretable mode for social science applications.</p>
     <h3>Count Scoring</h3>
     <p><code>score = count(matched_tokens)</code></p>
     <p>Raw count of dictionary matches per entry. Useful when document length normalization
     is handled externally.</p>
     <h3>Weighted Scoring</h3>
     <p><code>score = &sum; weight(token)</code> for all matched tokens</p>
     <p>Sum of pre-assigned weights from the dictionary (e.g., AFINN sentiment values).
     Used when dictionaries provide continuous values rather than binary membership.</p>
     <h3>TF-IDF Scoring</h3>
     <p><code>score = &sum; TF(t) &times; IDF(t)</code></p>
     <p>Where:</p>
     <ul>
       <li><b>TF(t)</b> = count(t) / n_tokens &mdash; term frequency within the entry</li>
       <li><b>IDF(t)</b> = ln(N / (1 + DF(t))) &mdash; inverse document frequency with add-one smoothing</li>
     </ul>
     <p>IDF weighting down-weights terms that appear in many entries (common words contribute
     less), following Salton &amp; Buckley (1988). The natural logarithm and add-one smoothing
     are standard choices.</p>
     <h3>N-gram Matching</h3>
     <p>When dictionaries contain multi-word phrases (e.g., "climate change"), TASS generates
     n-grams up to the maximum phrase length in the dictionary. Unigrams consumed by a matched
     n-gram are suppressed to prevent double-counting.</p>"""),

    ("Statistical Methods", "Preprocessing",
     """<h2>Text Preprocessing Pipeline</h2>
     <p>Text preprocessing is configurable per analysis. Each step is optional:</p>
     <table>
       <tr><th>Step</th><th>Default</th><th>Implementation</th></tr>
       <tr><td>Lowercasing</td><td>On</td><td>Python <code>str.lower()</code></td></tr>
       <tr><td>Punctuation removal</td><td>On</td><td><code>str.translate()</code> with <code>string.punctuation</code></td></tr>
       <tr><td>Whitespace normalization</td><td>On</td><td>Regex <code>\\s+</code> &rarr; single space</td></tr>
       <tr><td>Tokenization</td><td>On</td><td><code>nltk.word_tokenize()</code> (Penn Treebank tokenizer)</td></tr>
       <tr><td>Stopword removal</td><td>Off</td><td>NLTK English stopword list (179 words)</td></tr>
       <tr><td>Lemmatization</td><td>Off</td><td><code>nltk.WordNetLemmatizer</code> (WordNet 3.1)</td></tr>
       <tr><td>Minimum token length</td><td>1</td><td>Tokens shorter than threshold are discarded</td></tr>
     </table>
     <p><b>Note:</b> Stopword removal and lemmatization are off by default because many
     dictionary-based analyses rely on exact word forms. Enable these when your dictionaries
     use lemmatized forms or when function words should be excluded.</p>"""),

    ("Statistical Methods", "Descriptive Statistics",
     """<h2>Descriptive Statistics</h2>
     <p>For each category score, TASS computes:</p>
     <table>
       <tr><th>Statistic</th><th>Implementation</th><th>Notes</th></tr>
       <tr><td>Mean (M)</td><td><code>numpy.mean()</code></td><td>Arithmetic mean</td></tr>
       <tr><td>Standard deviation (SD)</td><td><code>numpy.std(ddof=1)</code></td><td>Sample SD with Bessel's correction (N&minus;1)</td></tr>
       <tr><td>Standard error (SE)</td><td><code>scipy.stats.sem()</code></td><td>SE = SD / &radic;N</td></tr>
       <tr><td>Median</td><td><code>numpy.median()</code></td><td></td></tr>
       <tr><td>Min / Max</td><td><code>numpy.min()</code>, <code>numpy.max()</code></td><td></td></tr>
       <tr><td>95% Confidence interval</td><td><code>scipy.stats.t.ppf()</code></td><td>t-distribution with df = N&minus;1. Requires N &ge; 2.</td></tr>
     </table>"""),

    ("Statistical Methods", "Hypothesis Tests",
     """<h2>Hypothesis Tests</h2>
     <h3>Two-Group Comparisons</h3>
     <table>
       <tr><th>Test</th><th>Implementation</th><th>When Used</th></tr>
       <tr><td>Welch's t-test</td><td><code>scipy.stats.ttest_ind(equal_var=False)</code></td><td>Default for 2 groups (does not assume equal variances)</td></tr>
       <tr><td>Mann-Whitney U</td><td><code>scipy.stats.mannwhitneyu(alternative="two-sided")</code></td><td>Non-parametric option (user-selected)</td></tr>
     </table>
     <p>Welch's t-test is the default because it is robust to unequal variances and unequal
     sample sizes, which are common in social science datasets (Delacre et al., 2017).</p>
     <h3>Multi-Group Comparisons (3+ groups)</h3>
     <table>
       <tr><th>Test</th><th>Implementation</th><th>When Used</th></tr>
       <tr><td>One-way ANOVA</td><td><code>scipy.stats.f_oneway()</code></td><td>Default for 3+ groups</td></tr>
       <tr><td>Kruskal-Wallis H</td><td><code>scipy.stats.kruskal()</code></td><td>Non-parametric option (user-selected)</td></tr>
     </table>
     <h3>Post-Hoc Pairwise Comparisons</h3>
     <p>Post-hoc tests run automatically when the omnibus test is significant (p &lt; &alpha;):</p>
     <table>
       <tr><th>After...</th><th>Post-Hoc Test</th><th>Implementation</th></tr>
       <tr><td>Significant ANOVA</td><td>Tukey HSD</td><td><code>scipy.stats.tukey_hsd()</code></td></tr>
       <tr><td>Significant Kruskal-Wallis</td><td>Dunn's test</td><td>Pairwise Mann-Whitney U with Bonferroni correction</td></tr>
     </table>
     <p>If <code>tukey_hsd</code> is unavailable (SciPy &lt; 1.8), TASS falls back to
     pairwise t-tests with Bonferroni correction.</p>"""),

    ("Statistical Methods", "Assumption Checks",
     """<h2>Assumption Checks</h2>
     <p>TASS automatically tests assumptions before running group comparisons:</p>
     <h3>Normality: Shapiro-Wilk Test</h3>
     <p><code>scipy.stats.shapiro()</code> &mdash; run per group, per category.</p>
     <ul>
       <li>p &ge; .05 &rarr; normality assumed (green)</li>
       <li>p &lt; .05 &rarr; normality violated (red, with W statistic and p-value shown)</li>
       <li>Requires N &ge; 3 per group</li>
     </ul>
     <h3>Equal Variance: Levene's Test</h3>
     <p><code>scipy.stats.levene()</code> &mdash; run across all groups, per category.</p>
     <ul>
       <li>p &ge; .05 &rarr; equal variances assumed (green)</li>
       <li>p &lt; .05 &rarr; unequal variances (red, with F statistic and p-value shown)</li>
       <li>Requires &ge; 2 groups with N &ge; 2 each</li>
     </ul>
     <p><b>Note:</b> TASS reports assumption violations but does not automatically switch
     tests. The user selects parametric or non-parametric tests via the Options panel.
     This keeps the researcher in control of analytical decisions.</p>"""),

    ("Statistical Methods", "Effect Sizes",
     """<h2>Effect Sizes</h2>
     <p>TASS reports an effect size for every hypothesis test:</p>
     <table>
       <tr><th>Test</th><th>Effect Size</th><th>Formula</th><th>Interpretation</th></tr>
       <tr><td>Welch's t-test</td><td>Cohen's d</td><td>d = (M<sub>1</sub> &minus; M<sub>2</sub>) / SD<sub>pooled</sub></td><td>Small: 0.2, Medium: 0.5, Large: 0.8</td></tr>
       <tr><td>Mann-Whitney U</td><td>Rank-biserial r</td><td>r = 1 &minus; (2U / n<sub>1</sub>n<sub>2</sub>)</td><td>Small: 0.1, Medium: 0.3, Large: 0.5</td></tr>
       <tr><td>One-way ANOVA</td><td>&eta;&sup2; (eta-squared)</td><td>&eta;&sup2; = SS<sub>between</sub> / SS<sub>total</sub></td><td>Small: .01, Medium: .06, Large: .14</td></tr>
       <tr><td>Kruskal-Wallis H</td><td>&eta;&sup2;<sub>H</sub></td><td>&eta;&sup2;<sub>H</sub> = (H &minus; k + 1) / (N &minus; k)</td><td>Same benchmarks as &eta;&sup2;</td></tr>
     </table>
     <p>The pooled standard deviation for Cohen's d uses the sample variance formula
     (ddof=1), consistent with Bessel's correction.</p>
     <p>&eta;&sup2;<sub>H</sub> for Kruskal-Wallis follows the formula from
     Tomczak &amp; Tomczak (2014), which adjusts for the number of groups (k) and
     total sample size (N).</p>"""),

    ("Statistical Methods", "Multiple Comparison Corrections",
     """<h2>Multiple Comparison Corrections</h2>
     <p>When testing multiple dictionary categories simultaneously, TASS adjusts significance
     thresholds to control for inflated Type I error:</p>
     <h3>Bonferroni Correction (Default)</h3>
     <p><code>&alpha;<sub>adj</sub> = &alpha; / m</code></p>
     <p>Where m = number of categories tested. Controls the <b>family-wise error rate</b>
     (FWER). Conservative but reliable.</p>
     <h3>Benjamini-Hochberg FDR (Optional)</h3>
     <p>Procedure:</p>
     <ol>
       <li>Rank all p-values in ascending order (p<sub>(1)</sub> &le; p<sub>(2)</sub> &le; ... &le; p<sub>(m)</sub>)</li>
       <li>For each rank i: p<sub>adj</sub> = p<sub>(i)</sub> &times; m / i</li>
       <li>Enforce monotonicity: p<sub>adj(i)</sub> = min(p<sub>adj(i)</sub>, p<sub>adj(i+1)</sub>)</li>
       <li>Cap at 1.0</li>
     </ol>
     <p>Controls the <b>false discovery rate</b> (FDR). Less conservative than Bonferroni;
     appropriate when exploring many categories simultaneously (Benjamini &amp; Hochberg, 1995).</p>
     <h3>Post-Hoc Corrections</h3>
     <p>Post-hoc pairwise comparisons use Bonferroni correction:
     <code>p<sub>adj</sub> = min(p &times; n_pairs, 1.0)</code></p>"""),

    ("Statistical Methods", "Correlation Analysis",
     """<h2>Correlation Analysis</h2>
     <table>
       <tr><th>Method</th><th>Implementation</th><th>When to Use</th></tr>
       <tr><td>Pearson r</td><td><code>scipy.stats.pearsonr()</code></td><td>Linear relationships, interval/ratio data</td></tr>
       <tr><td>Spearman &rho;</td><td><code>scipy.stats.spearmanr()</code></td><td>Monotonic relationships, ordinal data</td></tr>
     </table>
     <p>Correlation matrices are computed via <code>pandas.DataFrame.corr()</code>.
     Individual p-values for each pair are computed via the SciPy functions above,
     requiring N &ge; 3 data points.</p>
     <p>The scatter plot visualization includes an OLS regression line computed via
     <code>scipy.stats.linregress()</code>, which reports the Pearson r and p-value
     on the chart.</p>"""),

    ("Statistical Methods", "References",
     """<h2>References</h2>
     <p>The following works describe the statistical methods implemented in TASS:</p>
     <ul>
       <li>Benjamini, Y., &amp; Hochberg, Y. (1995). Controlling the false discovery rate:
       A practical and powerful approach to multiple testing. <i>Journal of the Royal Statistical
       Society: Series B</i>, 57(1), 289&ndash;300.</li>
       <li>Cohen, J. (1988). <i>Statistical power analysis for the behavioral sciences</i>
       (2nd ed.). Lawrence Erlbaum.</li>
       <li>Delacre, M., Lakens, D., &amp; Leys, C. (2017). Why psychologists should by default
       use Welch's t-test instead of Student's t-test. <i>International Review of Social
       Psychology</i>, 30(1), 92&ndash;101.</li>
       <li>Dunn, O. J. (1964). Multiple comparisons using rank sums. <i>Technometrics</i>,
       6(3), 241&ndash;252.</li>
       <li>Kruskal, W. H., &amp; Wallis, W. A. (1952). Use of ranks in one-criterion variance
       analysis. <i>Journal of the American Statistical Association</i>, 47(260), 583&ndash;621.</li>
       <li>Levene, H. (1960). Robust tests for equality of variances. In I. Olkin (Ed.),
       <i>Contributions to probability and statistics</i> (pp. 278&ndash;292). Stanford University Press.</li>
       <li>Salton, G., &amp; Buckley, C. (1988). Term-weighting approaches in automatic text
       retrieval. <i>Information Processing &amp; Management</i>, 24(5), 513&ndash;523.</li>
       <li>Shapiro, S. S., &amp; Wilk, M. B. (1965). An analysis of variance test for normality
       (complete samples). <i>Biometrika</i>, 52(3&ndash;4), 591&ndash;611.</li>
       <li>Tomczak, M., &amp; Tomczak, E. (2014). The need to report effect size estimates
       revisited. <i>Trends in Sport Sciences</i>, 21(1), 19&ndash;25.</li>
       <li>Tukey, J. W. (1949). Comparing individual means in the analysis of variance.
       <i>Biometrics</i>, 5(2), 99&ndash;114.</li>
       <li>Welch, B. L. (1947). The generalization of Student's problem when several different
       population variances are involved. <i>Biometrika</i>, 34(1&ndash;2), 28&ndash;35.</li>
     </ul>
     <h3>Software Libraries</h3>
     <ul>
       <li>Virtanen, P., et al. (2020). SciPy 1.0: Fundamental algorithms for scientific
       computing in Python. <i>Nature Methods</i>, 17, 261&ndash;272.</li>
       <li>Harris, C. R., et al. (2020). Array programming with NumPy. <i>Nature</i>,
       585, 357&ndash;362.</li>
       <li>Bird, S., Klein, E., &amp; Loper, E. (2009). <i>Natural language processing with
       Python</i>. O'Reilly Media.</li>
       <li>McKinney, W. (2010). Data structures for statistical computing in Python.
       <i>Proceedings of the 9th Python in Science Conference</i>, 56&ndash;61.</li>
     </ul>"""),

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
