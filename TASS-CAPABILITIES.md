# TASS — Text Analysis for Social Scientists

## Comprehensive Capability & Design Document

**Version:** 1.0.0 (pre-release)
**Author:** Alex P. Leith / SIM DAD LLC
**Date:** 2026-03-31
**Purpose:** Expert review prior to final implementation and launch

---

## 1. Product Overview

TASS is a no-code Windows desktop application for dictionary-based text analysis. It scores text data against curated word dictionaries, computes per-entry and per-document statistics, and provides inferential group comparisons — all with publication-ready exports. The target users are social scientists, journalists, and domain experts who work with open-ended text data (survey responses, tweets, interview transcripts, news articles) but have no programming background.

**Core philosophy:** Replace the LIWC/Diction workflow of "paste text into a tool, get a score" with a modern, visual, statistically complete desktop application that doesn't require SPSS, R, or Python.

**Platform:** Windows 10/11 (macOS planned). PySide6 (Qt 6) GUI. Python 3.11 runtime.
**Licensing:** Gumroad — Individual $49.99 / Team 5 $199.99 / Team 10 $349.99. 14-day free trial (500-row limit). 30-day money-back guarantee.
**Distribution:** Signed installer (Inno Setup + EV code signing), GitHub Releases.

---

## 2. Application Architecture

### 2.1 Navigation Model

The application uses a **sidebar + panel** pattern with 7 main screens:

| # | Panel | Purpose |
|---|-------|---------|
| 1 | **Home** | Welcome screen, recent projects, quick-start guide |
| 2 | **Import** | 3-step data import wizard (file → columns → preview) |
| 3 | **Analyze** | Dictionary selection, preprocessing options, run analysis |
| 4 | **Results** | 7-tab results explorer (Scores, Word Matches, Summary, Correlations, Coverage, KWIC, Groups) |
| 5 | **Visualize** | Chart generation (bar, box, violin, heatmap, word cloud, scatter) |
| 6 | **Compare** | Group comparison statistics (t-tests, ANOVA, post-hoc) |
| 7 | **Help** | In-app documentation tree |

**Additional dialogs:** Settings, License/Activate, Export, Citation, Progress.

The sidebar is fixed-width (100px), dark (#1A2332), with icon+label buttons. The active panel is highlighted in blue (#2563EB). A settings gear button sits at the bottom. The status bar shows license state (color-coded: green = licensed, orange = trial, red = expired/not activated).

### 2.2 Menu Bar

| Menu | Items |
|------|-------|
| **File** | New Analysis (Ctrl+N), Open Project (Ctrl+O), Save (Ctrl+S), Save As (Ctrl+Shift+S), Import Data (Ctrl+I), Exit (Ctrl+Q) |
| **Analysis** | Run Analysis (Ctrl+R) |
| **Export** | Export Results (Ctrl+E), How to Cite TASS |
| **Help** | Help (F1), License / Activate, End User License Agreement, About TASS |

### 2.3 Project Files

TASS projects are saved as `.tass` files — ZIP archives containing:

- `manifest.json` — metadata (version, timestamps, column mappings, row count, dictionaries used)
- `data.parquet` — raw imported DataFrame
- `results.parquet` — entry-level scores
- `analysis_config.json` — dictionary selection and preprocessing settings
- `session_state.json` — UI state (active panel, palette, export path)
- `visualizations/chart_config.json` — palette preferences

### 2.4 Concurrency

- **AnalysisWorker** (QThread) — preprocessing + dictionary matching with progress updates
- **StatisticsWorker** (QThread) — group comparisons (fast, no progress needed)
- **DictionaryEngine** — multi-threaded scoring via ThreadPoolExecutor (CPU-count workers)
- All heavy computation is non-blocking; a modal progress dialog prevents user interaction during analysis

---

## 3. Data Import

### 3.1 Supported Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| CSV | .csv | UTF-8, fallback to latin-1. Standard pandas read_csv |
| Tab-delimited text | .txt | Auto-detects tab delimiter; else treats as one document per line |
| Excel | .xlsx, .xls | Standard pandas read_excel |

### 3.2 Import Wizard (3 Steps)

**Step 1 — File Selection**
- Drag-and-drop zone or file browser dialog
- Multiple files supported (concatenated with `_source_file` column)
- Progress dots: ●○○

**Step 2 — Column Mapping**
- **Text column (required)** — dropdown populated from all columns, auto-suggests based on column name heuristics (checks for: text, content, body, message, tweet, post, comment, response, answer, description, review) and average string length
- **Group column (optional)** — dropdown showing categorical columns (unique count < 50 and unique ratio < 10%). Enables group comparison features
- **Metadata columns (optional)** — checkbox list for columns to carry through to exports without analyzing (IDs, dates, URLs)
- Column type detection: numeric, datetime, categorical, or text — determined automatically via pandas type inference + heuristics

**Step 3 — Preview & Confirm**
- Summary banner: row count, column count
- Mapping display: text column, group column, metadata columns
- Sortable preview table (first 2,000 rows displayed; all rows included in analysis)
- Truncation notice if >2,000 rows
- Confirm button navigates to Analyze panel

---

## 4. Dictionary Engine

### 4.1 Scoring Pipeline

1. **Preprocessing** — tokenize text column into word lists
2. **Dictionary preparation** — build lookup sets for all selected categories
3. **Per-entry scoring** — match tokens against dictionaries, compute scores
4. **Aggregation** — document-level summary statistics

### 4.2 Preprocessing Options

| Option | Default | Description |
|--------|---------|-------------|
| Lowercase | On | Convert all text to lowercase before matching |
| Strip punctuation | On | Remove punctuation and normalize whitespace |
| Remove stopwords | Off | Remove NLTK English stopwords before matching |
| Lemmatize | Off | Reduce words to base form (e.g., "running" → "run") via NLTK WordNetLemmatizer |
| Min token length | 1 | Filter out tokens shorter than N characters |

Tokenization uses NLTK `word_tokenize()` with automatic fallback to `.split()` if NLTK data is unavailable.

### 4.3 Scoring Modes

Each dictionary declares a scoring mode:

| Mode | Formula | Use case |
|------|---------|----------|
| **Binary** | `(matched_count / total_tokens) × 100` | Percentage of text matching a category (e.g., LIWC-style) |
| **Count** | `len(matched_tokens)` | Raw frequency (e.g., count of moral foundations words) |
| **Weighted** | `Σ weight(word) for matched words` | Sum of pre-assigned weights (e.g., AFINN sentiment valence) |

### 4.4 Built-In Dictionaries

| Dictionary | Categories | Scoring | License | Default |
|------------|-----------|---------|---------|---------|
| **AFINN-165** (Nielsen 2011) | sentiment (valence -5 to +5) | Weighted | MIT | Yes |
| **VADER Lexicon** (Hutto & Gilbert 2014) | positive, negative, neutral, compound | Weighted | MIT | Yes |
| **Moral Foundations Dictionary 2.0** (Frimer et al. 2019) | 10 categories (5 foundations × virtue/vice) | Binary | CC-BY | Yes |
| **Brysbaert Concreteness Norms** (Brysbaert et al. 2014) | concreteness (1=abstract to 5=concrete) | Weighted | CC-BY | No |
| **WordNet POS Categories** (Fellbaum 1998) | noun, verb, adjective, adverb | Binary | Princeton | No |
| **NLTK Stopwords / Function Words** | function_words, pronouns, prepositions | Binary | Apache 2.0 | No |

Two additional dictionaries (HurtLex, SentiWordNet) were removed due to CC-BY-SA 4.0 Share-Alike licensing incompatibility with commercial distribution.

### 4.5 Custom Dictionaries

Users can import custom dictionaries in JSON format:

```json
{
  "name": "My Dictionary",
  "version": "1.0",
  "citation": "Author (Year)",
  "license": "MIT",
  "scoring": "binary",
  "categories": {
    "positive": ["happy", "joy", "love"],
    "negative": ["sad", "anger", "fear"]
  }
}
```

Weighted dictionaries use `{word: weight}` objects instead of arrays. Custom dictionaries are assigned IDs in the format `user__{dict_name_lower}` and persist in the registry.

### 4.6 Category Column Naming

All scored columns follow the pattern `{DictName}__{category}` (e.g., `AFINN-165__sentiment`, `MFD2__care.virtue`). This ensures unique column names across dictionaries.

---

## 5. Results Display

After analysis, results are shown in a 7-tab panel.

### 5.1 Scores Tab

Sortable table of entry-level scores. One row per text entry. Columns: text column (if available) + all category score columns. Values displayed to 4 decimal places. Capped at 5,000 rows for display (all rows retained in session). CSV export button.

### 5.2 Word Matches Tab

Two-pane split (1:3 ratio). Left pane: scrollable entry list with 80-character text previews. Right pane: full text with matched words highlighted in category-specific colors (8-color rotating palette). Hovering over a highlighted word shows a tooltip listing all matching categories. Category legend displayed above the text.

### 5.3 Summary Tab

Document-level aggregate statistics in a sortable table. Columns: category, mean, SD, min, max, median, count. One row per dictionary category. CSV export button.

### 5.4 Correlations Tab

Pearson correlation matrix between all category score columns. Cells display `r` values to 3 decimal places with significance stars:
- `*` p < .05
- `**` p < .01
- `***` p < .001

Diagonal cells show "—". CSV export button. P-values are computed pairwise using `scipy.stats.pearsonr()`.

### 5.5 Coverage Tab

Dictionary coverage statistics per category. Columns: category, entries matched, entries total, entry coverage %, total matches, mean matches per entry. Shows what percentage of the corpus each category touches. CSV export button.

### 5.6 KWIC Tab (Keyword in Context)

Standard concordance display. Each matched word is shown with 6 words of left context and 6 words of right context, in the format:

```
Entry | Category | Left Context           | KEYWORD | Right Context
  42  | care     | the government should   | protect | vulnerable citizens from
```

Category filter dropdown (default: "All categories"). Sortable by all columns. CSV export button.

### 5.7 Groups Tab

CTA stub that displays the current group column (if set) and a button to navigate to the Compare panel. Updates dynamically when a group column is assigned.

---

## 6. Group Comparison Statistics

The Compare panel runs inferential statistics comparing dictionary scores across groups defined by a categorical column.

### 6.1 Configuration Controls

- **Group column selector** — dropdown of all categorical/text columns
- **Non-parametric checkbox** — when checked, uses Mann-Whitney U (2 groups) or Kruskal-Wallis (3+ groups) instead of Welch t-test / ANOVA
- **Bonferroni correction checkbox** — when checked (default), adjusts alpha = 0.05 / number of categories

### 6.2 Statistical Tests

| Condition | Parametric Test | Nonparametric Test |
|-----------|----------------|-------------------|
| 2 groups | Welch t-test (unequal variance) | Mann-Whitney U |
| 3+ groups | One-way ANOVA | Kruskal-Wallis |

### 6.3 Effect Sizes

| Test | Effect Size | Interpretation |
|------|-------------|----------------|
| Welch t-test | Cohen's d | |
| Mann-Whitney U | Rank-biserial r | |
| One-way ANOVA | Eta-squared (η²) | |
| Kruskal-Wallis | Eta-squared (H) | Approximation from H statistic |

### 6.4 Assumption Checks

- **Shapiro-Wilk normality test** — computed per group per category. Results displayed in a "Normality" column: "OK" (all groups pass, green) or "Violated (N)" (red, with tooltip listing non-normal groups). Requires n ≥ 3 per group.
- **95% confidence intervals** — computed per group mean using t-distribution. Displayed in a "95% CI" column with tooltip showing `[lower, upper]` per group.

### 6.5 Post-Hoc Tests

When the omnibus test (ANOVA or Kruskal-Wallis) is significant, post-hoc pairwise comparisons are automatically computed:

- **Tukey HSD** — via `scipy.stats.tukey_hsd()` (scipy ≥ 1.8). Fallback: pairwise t-tests with Bonferroni adjustment.
- Results displayed in a yellow info section below the results table, showing each pairwise comparison with p-value and significance marker.

### 6.6 Results Table Columns

1. Category
2. Per-group: M (SD) — one column per group
3. Test name
4. Test statistic
5. p-value (green background if p < .05, yellow if p ≥ .05)
6. Significance marker (*** / ** / * / n.s.)
7. Effect size value
8. Effect size type
9. 95% CI (per group, in tooltip)
10. Normality (Shapiro-Wilk summary)

### 6.7 Current Statistical Gaps (Identified via Reference Book Audit)

The following gaps were identified through review of Zaidi (SPSS), Cronk (SPSS), Oh (SPSS Basics), Lane (NLP in Action), and Pillai (ML/DL in NLP):

**HIGH priority (pre-release):**

1. **Dunn's test for Kruskal-Wallis post-hoc** — Tukey HSD is currently used after Kruskal-Wallis, which is methodologically incorrect (Tukey assumes normality). Dunn's test with Bonferroni correction is the standard nonparametric post-hoc.

2. **Levene's test for homogeneity of variance** — All three SPSS textbooks treat this as a mandatory assumption check for t-tests and ANOVA. TASS uses Welch's t-test (robust to unequal variances), but social scientists expect to see Levene's test result in output.

3. **Degrees of freedom in APA output** — APA requires `t(df) = X.XX` and `F(df₁, df₂) = X.XX`. Currently omitted from APA table export.

4. **Exact p-value formatting** — APA 7th prefers `p = .006` (exact, no leading zero) over `p < .01` (threshold). Use `p < .001` only when truly below .001.

5. **Effect size interpretation labels** — Standard labels: Cohen's d (< .2 small, .2–.8 medium, > .8 large); η² (< .01 small, .01–.25 moderate, > .25 large). Should appear in APA output and the Compare panel.

6. **N-gram dictionary support** — Unigram-only matching misses negation ("not happy" scored as two separate words). The NLP references flag this as the single biggest limitation of bag-of-words dictionary analysis. Supporting bigram and trigram dictionary entries would dramatically improve scoring accuracy.

**MEDIUM priority (v1.x):**

7. **Paired-samples t-test** — for pre/post designs comparing two measurements from the same participants.
8. **Factorial (two-way) ANOVA** — test main effects of two grouping variables plus their interaction.
9. **Spearman rho correlation** — already supported in the engine (`method="spearman"`), but not exposed in the Correlations tab UI.
10. **FDR (Benjamini-Hochberg) correction** — less conservative alternative to Bonferroni for many comparisons.
11. **TF-IDF normalization** — optional weighting to account for term informativeness across the corpus.
12. **Variable role assignment UI step** — explicit declaration of measurement levels (nominal, ordinal, scale) per column, matching SPSS's Variable View concept.
13. **Test selector wizard** — guided UI that asks "How many groups?" and "Is your data normally distributed?" to recommend the appropriate test.
14. **Structured output viewer** — results as discrete blocks (descriptives → assumption checks → test results → post-hoc) rather than a single table.

**LOW priority (future):**

15. Chi-square tests, single-sample t-test, ANCOVA/MANOVA.
16. Linear/multiple regression.
17. Wilcoxon signed-rank and Friedman tests.
18. Post-hoc test selection (Tukey vs. Bonferroni vs. Scheffé).
19. Concordance plot (showing where in a document hits occur).

---

## 7. Visualizations

### 7.1 Chart Types

| Chart | Input | Description |
|-------|-------|-------------|
| **Bar chart** | Summary DataFrame | Horizontal bars of top N categories by mean score |
| **Grouped bar chart** | Per-group summary | Groups on Y-axis, colored bars per category |
| **Box plot** | Scores + groups | Distribution of one category across groups |
| **Violin plot** | Scores + groups | Density distribution alternative to box plot |
| **Heatmap** | Summary or per-group | Category × group score intensity grid (YlOrRd) |
| **Word cloud** | Word matches | Frequency-proportional word cloud |
| **Scatter plot** | Two categories | Category vs. category with regression line, r, and p-value; optional group coloring |

### 7.2 Visualization Panel Layout

Left sidebar (200px): chart type radio buttons, category dropdown, palette selector.
Right content: toolbar (render/export buttons) + Matplotlib canvas (FigureCanvasQTAgg).

### 7.3 Palettes

- **Default** — Seaborn Set2
- **Colorblind-safe** — Seaborn colorblind palette
- **Grayscale** — reverse grays

### 7.4 Export

- **PNG** — 300 DPI, publication quality
- **SVG** — vector, editable in Illustrator/Inkscape

---

## 8. Export System

### 8.1 Export Formats

| Format | Contents |
|--------|----------|
| **CSV** | Entry-level scores + metadata columns. Citation block appended |
| **Excel (.xlsx)** | 4 sheets: Raw Scores, Summary Statistics, Group Comparisons, Citation (APA/MLA/Chicago/DOI) |
| **APA table (.txt)** | Plain-text APA 7th Edition formatted table: M (SD) per group, test statistics, p-values, effect sizes, significance markers, notes |
| **PNG / SVG** | Individual chart exports |

### 8.2 Export Dialog

Modal dialog with checkboxes for output formats (CSV, Excel, PNG, SVG), directory browser, and progress bar. All text-based exports include a citation block.

### 8.3 Citation Block

Automatically appended to every TASS export:

```
--- TASS Citation ---
If you use TASS in your research, please cite it:

APA:
Leith, Alex. (2026). TASS: Text Analysis for Social Scientists (Version 1.0.0) [Software]. SIM DAD LLC. https://doi.org/10.5281/zenodo.PENDING

DOI: https://doi.org/10.5281/zenodo.PENDING
---------------------
```

Available in APA, MLA, and Chicago formats via the Citation dialog (Help menu or Export menu → How to Cite TASS). Each format has a "Copy to Clipboard" button.

---

## 9. Licensing & Trial

### 9.1 Pricing Tiers

| Tier | Price | Devices |
|------|-------|---------|
| Individual | $49.99 | 1 |
| Team 5 | $199.99 | 5 |
| Team 10 | $349.99 | 10 |

### 9.2 Trial Mode

- 14-day free trial, local-only (no account creation required beyond email)
- Trial limited to 500 rows per analysis
- After expiry: view-only mode (can view existing results, cannot run new analyses)

### 9.3 License Verification

- **Platform:** Gumroad License API (`POST /v2/licenses/verify`)
- **Activation:** `increment_uses_count=true` on first activation per machine. Device count enforced client-side via Gumroad `uses` field + `variants` field for tier detection
- **Validation:** `increment_uses_count=false` on subsequent launches
- **Grace period:** 14 days offline before license re-validation required
- **Revocation:** automatic via `purchase.refunded` or `purchase.chargebacked` fields
- **Machine fingerprint:** SHA-256 hash of Windows MachineGuid (registry) or macOS IOPlatformUUID (ioreg)
- **Cache location:** `platformdirs.user_config_dir("TASS") / license.json`

### 9.4 License Dialog

Two-tab modal: "Free Trial" (email entry → start trial) and "License Key" (paste key → activate). Shows license status in the main window status bar. "Don't have a license?" link opens the product website.

---

## 10. User Interaction Design

### 10.1 Workflow Sequence

The primary workflow is linear:

```
Home → Import → Analyze → Results → (Visualize / Compare / Export)
```

Each step in the sidebar highlights as the user progresses. Navigation is non-destructive — users can jump back to any panel at any time. The session state (data, results, group stats) persists throughout.

### 10.2 Import Wizard

The 3-step wizard uses progress dots (●○○ / ●●○ / ●●●) and Back/Next navigation. Each step validates before allowing progression: Step 1 requires file selection, Step 2 requires text column assignment, Step 3 requires confirmation.

Auto-detection reduces friction: text column is auto-suggested, column types are inferred, and the preview table is sortable. Users can override all auto-detections.

### 10.3 Dictionary Selection

Dictionaries are presented as cards (not a raw list), each showing:
- Checkbox (toggle)
- Dictionary name + license badge (color-coded: MIT=green, CC-BY=blue)
- Citation
- Description
- Category preview tags

"Select All" / "Deselect All" buttons for quick selection. Custom dictionary import via "+ Import Custom Dictionary" button at the bottom (opens file dialog for JSON files).

### 10.4 Analysis Execution

The "Run Analysis" button is a large, prominent green button (48px height). When clicked:
1. Input validation: data loaded? At least one dictionary selected? Trial row limit OK?
2. Build preprocessor configuration from UI options
3. Launch AnalysisWorker in background thread
4. Modal progress dialog with percentage bar and status text ("Tokenizing text…", "Matching dictionaries…")
5. On completion: auto-navigate to Results panel
6. On error: error dialog with traceback

### 10.5 Results Navigation

Seven tabs, accessible by clicking. Each tab independently populates from session state. Tabs are labeled without emoji in the tab bar (Scores, Word Matches, Summary, Correlations, Coverage, KWIC, Groups). The top status bar provides a consistent "✓ Analysis complete" summary with a link to re-configure.

### 10.6 Group Comparison Flow

1. User navigates to Compare panel (via sidebar or Groups tab CTA)
2. Selects group column from dropdown
3. Toggles non-parametric / Bonferroni options
4. Clicks "Run Comparison"
5. Indeterminate progress bar animates
6. Results table appears with color-coded p-values and significance markers
7. Post-hoc section appears below table (if 3+ groups and omnibus significant)
8. CSV export available via status bar button

### 10.7 Visualization Flow

1. Select chart type (radio buttons)
2. Select category (dropdown, populated from analysis results)
3. Select palette (dropdown)
4. Click "Render Chart"
5. Matplotlib figure renders inline
6. Export PNG / Export SVG buttons

### 10.8 Export Flow

1. File → Export Results (or Ctrl+E)
2. Modal dialog: check desired formats, browse to output directory
3. Click Export → progress bar
4. Success dialog with file paths

---

## 11. Design System

### 11.1 Colors

| Token | Value | Usage |
|-------|-------|-------|
| Primary action | #2563EB (blue) | Navigation highlight, action buttons, links |
| Success / run | #16A34A (green) | Analysis execution, success states |
| Sidebar background | #1A2332 (dark navy) | Fixed sidebar |
| Panel backgrounds | #F9FAFB, #FFFFFF | Content areas |
| Info panels | #EFF6FF (light blue) | Status bars, info boxes |
| Success tint | #D1FAE5 / #DCFCE7 (green) | Significant p-values, success states |
| Warning tint | #FEF9C3 (yellow) | Non-significant p-values |
| Post-hoc section | #FFFBEB (amber) | Post-hoc results background |
| Error / violation | #DC2626 (red) | Normality violations |
| Muted text | #6B7280, #9CA3AF (gray) | Secondary text, empty states |
| Borders | #E5E7EB (light gray) | Separator lines, panel borders |

### 11.2 Typography

| Role | Specification |
|------|---------------|
| Primary font | Segoe UI (system default, sans-serif fallback) |
| Monospace | Courier New (license keys) |
| Small text | 8pt |
| Default text | 9pt |
| Body text | 10pt |
| Section headers | 12pt |
| Panel titles | 14–16pt |
| Button text | 9–12pt, bold for primary actions |

### 11.3 Component Patterns

- **Primary buttons:** blue (#2563EB) fill, white text, 6–8px border-radius, 8–20px padding
- **Success buttons:** green (#16A34A) fill, white text
- **Secondary buttons:** transparent background, colored border, colored text
- **Checkboxes:** standard Qt checkboxes with 9pt labels
- **Dropdowns:** QComboBox, 160px minimum width
- **Tables:** alternating row colors, single-row selection, sortable columns, interactive column resize
- **Cards:** white background, 1px gray border, 4–8px border-radius, hover highlight
- **Progress bars:** 4–6px height, blue chunk on gray background
- **Empty states:** centered gray text (10pt), instructional, with numbered steps

### 11.4 Window

- **Title:** "TASS — Text Analysis for Social Scientists"
- **Minimum size:** 1024 × 700 px
- **Default size:** 1280 × 800 px
- **Window geometry:** persisted to QSettings between sessions

---

## 12. Data Model

### 12.1 Session State (Singleton)

```
Session
├── raw_df: pandas.DataFrame          # Original imported data
├── column_mapping
│   ├── text_column: str              # Column containing text to analyze
│   ├── group_column: Optional[str]   # Column defining groups
│   └── metadata_columns: List[str]   # Passthrough columns for export
├── analysis_config
│   ├── selected_dictionaries: List[str]  # Dictionary IDs
│   ├── analysis_levels: List[str]        # ["word", "entry", "document"]
│   ├── groups: Dict[str, List]           # Group inclusion filter
│   └── group_column: Optional[str]       # Redundant with column_mapping
├── results
│   ├── entry_scores: pandas.DataFrame    # Rows=entries, cols=categories
│   ├── word_matches: Dict                # {entry_idx: {category: [words]}}
│   ├── document_summary: pandas.DataFrame
│   └── group_stats: Dict                 # {category: GroupStats}
├── project_path: Optional[str]
└── ui_state: Dict                        # Active panel, palette, export path
```

### 12.2 Category Score Columns

All score columns follow the naming convention `{DictName}__{category}`. For example:
- `AFINN-165__sentiment`
- `MFD2__care.virtue`
- `MFD2__fairness.vice`
- `user__my_custom__positive`

### 12.3 GroupStats Object

```
GroupStats
├── category: str
├── group_descriptives: {group: {mean, std, min, max, median, n}}
├── test_name: str                     # "Welch t-test", "Mann-Whitney U", etc.
├── test_statistic: float
├── p_value: float
├── effect_size: float
├── effect_size_name: str              # "Cohen's d", "eta-squared", etc.
├── significant: bool
├── confidence_intervals: {group: (lower, upper)}
├── normality: {group: (W, p, is_normal)}
└── posthoc: [(group_a, group_b, p_value, significant), ...]
```

---

## 13. Dependencies

### 13.1 Core

| Package | Version | Purpose |
|---------|---------|---------|
| Python | 3.11 | Runtime |
| PySide6 | 6.7.3 | GUI framework (Qt 6) |
| pandas | 2.1.4 | DataFrame operations |
| numpy | 1.26.4 | Numerical computation |
| scipy | 1.11.4 | Statistical tests |
| matplotlib | 3.8.3 | Chart rendering |
| seaborn | 0.13.2 | Statistical chart styling |
| wordcloud | 1.9.3 | Word cloud generation |
| NLTK | 3.8.1 | Tokenization, lemmatization, stopwords |
| openpyxl | 3.1.2 | Excel file writing |
| platformdirs | 4.0+ | Cross-platform config directories |

### 13.2 Build & Distribution

| Tool | Purpose |
|------|---------|
| PyInstaller 6.5.0 | Executable bundling |
| Inno Setup | Windows installer |
| EV code signing cert (ssl.com) | SmartScreen trust |

### 13.3 Planned Upgrades (Cross-Platform Migration)

- Python 3.11 → 3.12
- PySide6 6.7.3 → 6.11.0
- PyInstaller 6.5.0 → 6.19.0
- Add: desktop-notifier ≥ 6.2.0
- Remove: python-dotenv, requests (no longer needed)

---

## 14. Testing

- 134 tests passing (as of 2026-03-14)
- Test suite covers: dictionary engine, statistics engine, preprocessor, importer, session management
- Test runner: pytest
- CI: planned GitHub Actions (windows-latest + macos-14 matrix)

---

## 15. Open Questions for Expert Review

1. **Dunn's test implementation** — Should TASS use `scipy.stats.kruskal` + manual Dunn's pairwise comparisons, or integrate `scikit-posthocs` (adds a dependency)?

2. **N-gram dictionary format** — How should bigram/trigram dictionary entries be specified in JSON? Options: space-separated strings (`"not happy"`) vs. array notation (`["not", "happy"]`). How should n-gram matching interact with the preprocessing pipeline?

3. **Levene's test display** — Should Levene's result appear as a column in the Compare table, as a separate assumption-check section, or as a tooltip/warning?

4. **Effect size labels in UI** — Should "small/medium/large" labels appear inline in the results table (adding a column), in tooltips, or only in the APA export?

5. **Spearman correlation toggle** — Should the Correlations tab have a Pearson/Spearman toggle, or should it automatically choose based on normality test results?

6. **FDR vs. Bonferroni** — Should both be offered as radio buttons in the Compare panel, or should FDR replace Bonferroni as the default?

7. **Variable role assignment** — Is a dedicated "Variable View" step (à la SPSS) warranted, or does the current import wizard with auto-detection suffice for the target audience?

8. **Test selector wizard** — Would a guided "which test should I use?" dialog add value, or would it patronize the target audience (social scientists who have taken statistics courses)?

9. **Paired-samples t-test** — How common is pre/post text analysis in the target audience's workflows? Is this a v1.0 requirement or a v1.1 feature?

10. **TF-IDF normalization** — Should this be a preprocessing option (applied before dictionary matching) or a separate scoring mode alongside binary/count/weighted?

---

*This document is intended for expert review. It describes the current state of TASS as of 2026-03-31, including features implemented during this session that have not yet been tested end-to-end.*
