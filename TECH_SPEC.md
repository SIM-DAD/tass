# TASS: Text Analysis for Social Scientists
## Technical Specification v0.1
**Prepared:** March 2026
**Owner:** SIM DAD LLC
**Status:** Draft

---

## 1. Architecture Overview

TASS is a layered native desktop application. The GUI layer never directly calls analysis logic — all heavy work runs in background threads via Qt's worker thread model, keeping the UI responsive during long operations.

```
┌──────────────────────────────────────────────────────────┐
│                        GUI Layer                          │
│             PySide6 (Qt 6) — Windows Desktop              │
│   MainWindow | Wizards | Panels | Dialogs | Charts        │
├──────────────────────────────────────────────────────────┤
│                   Application Layer                       │
│   ProjectManager | SessionState | AnalysisOrchestrator   │
│   ExportManager | LicenseGate | CitationGenerator        │
├──────────────────────────────────────────────────────────┤
│                    Analysis Layer                         │
│   Preprocessor | DictionaryEngine | StatisticsEngine     │
│   VisualizationEngine | (MLEngine — v1.1)                │
├──────────────────────────────────────────────────────────┤
│                      Data Layer                           │
│   FileImporter | DictionaryLoader | ResultsCache         │
│   ProjectSerializer (.tass format)                       │
├──────────────────────────────────────────────────────────┤
│                    Services Layer                         │
│   LicenseService | ErrorReporter | UpdateChecker         │
│   SupabaseClient | LemonSqueezyClient                    │
└──────────────────────────────────────────────────────────┘
```

---

## 2. Technology Stack

| Component | Technology | Version | Rationale |
|---|---|---|---|
| Language | Python | 3.11.x | NLP ecosystem; best AI tooling support |
| GUI Framework | PySide6 (Qt 6) | 6.7.x | Native Windows rendering; LGPL license; mature |
| Bundler | PyInstaller | 6.x | Single-folder EXE output; well-maintained |
| Installer Builder | Inno Setup | 6.x | Free; standard Windows installer; code-sign friendly |
| Data Handling | pandas | 2.x | DataFrame manipulation; CSV/Excel I/O |
| Excel I/O | openpyxl | 3.x | Multi-sheet Excel write |
| Statistics | SciPy + NumPy | 1.11+ / 1.26+ | t-tests, ANOVA, Mann-Whitney, effect sizes |
| Visualizations | Matplotlib + Seaborn | 3.8+ / 0.13+ | ggplot-style static charts; high-res export |
| Word Clouds | wordcloud | 1.9+ | Standard, customizable |
| NLP Tokenization | NLTK | 3.8+ | Tokenization, lemmatization, stopwords |
| Project Files | stdlib zipfile + JSON | — | .tass format (ZIP bundle) |
| Compressed Data | pyarrow (parquet) | 14.x | Efficient storage of DataFrames inside .tass |
| License Backend | Supabase | free tier | PostgreSQL; license + trial records |
| Payment | Lemon Squeezy | — | Payment + key generation + mailing list |
| Error Reporting | smtplib (stdlib) | — | Crash log email; zero cost |
| Code Signing | Sectigo/DigiCert OV | — | ~$200/year; eliminates Unknown Publisher warning |
| Update Source | GitHub Releases API | — | v1.1; free; version-controlled |

**v1.1 additions:**

| Component | Technology | Notes |
|---|---|---|
| Transformer ML | HuggingFace transformers + DistilBERT | Bundled model weights (~250MB) |
| Topic Modeling | scikit-learn (LDA) | Pure Python; no extra runtime |
| NER | spaCy en_core_web_sm | Bundled model (~12MB) |
| Interactive charts | Plotly + PySide6 WebEngineView | In-app browser for dashboards |
| Support | Freshdesk widget | Web widget embedded in Help panel |

---

## 3. Repository Structure

```
tass/
├── main.py                         # Entry point; launches QApplication
├── app.py                          # App init, license gate, global exception hook
│
├── ui/                             # All PySide6 UI modules
│   ├── main_window.py              # Shell: sidebar nav, central widget switcher
│   ├── welcome_screen.py           # Home screen: recent projects, trial/license status
│   ├── import_wizard.py            # Step-by-step: file select → column mapping → preview
│   ├── data_preview.py             # Read-only QTableView of imported DataFrame
│   ├── analysis_config_panel.py    # Dictionary selection, analysis level checkboxes
│   ├── progress_dialog.py          # Modal: progress bar, live status text, cancel button
│   ├── results_panel.py            # Tabbed: Scores | Word Matches | Summary | Groups
│   ├── visualization_panel.py      # Chart display area; export button
│   ├── compare_panel.py            # Group definition UI + comparison results table
│   ├── export_dialog.py            # Format checkboxes, output directory picker
│   ├── license_dialog.py           # Trial signup (email) + license key activation
│   ├── help_panel.py               # Searchable docs sidebar (F1)
│   ├── cite_dialog.py              # "How to Cite TASS" — APA/MLA/Chicago formats
│   └── settings_dialog.py          # Preferences: color palette, default export path, etc.
│
├── core/                           # Business logic; no Qt imports here
│   ├── session.py                  # In-memory session state (singleton)
│   ├── project.py                  # .tass project read/write (serialize/deserialize)
│   ├── importer.py                 # CSV/TXT/XLSX ingestion, validation, column detection
│   ├── preprocessor.py             # Tokenization, lemmatization, cleaning pipeline
│   ├── dictionary_engine.py        # Dictionary matching; produces scored DataFrame
│   ├── statistics_engine.py        # Descriptives, t-test, ANOVA, effect sizes
│   ├── visualization_engine.py     # Chart generation (returns matplotlib figures)
│   ├── export_engine.py            # Writes CSV, Excel, PNG, SVG to disk
│   ├── citation.py                 # Generates citation strings; appends to exports
│   └── workers.py                  # QThread subclasses for async analysis operations
│
├── dictionaries/
│   ├── loader.py                   # Load + validate a dictionary file into standard format
│   ├── registry.py                 # Manifest of all available dictionaries (built-in + user)
│   └── builtin/                    # Bundled dictionary data files
│       ├── afinn165.json
│       ├── vader_lexicon.json
│       ├── sentiwordnet.json
│       ├── mfd2.json
│       ├── brysbaert_concreteness.json
│       ├── hurtlex.json
│       ├── wordnet_pos.json
│       └── nltk_stopwords.json
│       # EXCLUDED (research-only or NC license): nrc_emotion, opinion_lexicon,
│       #   warriner_affective (CC BY-NC-ND), loughran_mcdonald, mrc_psycholinguistic
│       # 18 TASS-native dictionaries added progressively in v1.1 and v2.0 (see PRD §6b)
│
├── services/
│   ├── license.py                  # Key validation, trial management, machine fingerprint
│   ├── supabase_client.py          # Supabase REST API calls (license + trial records)
│   ├── lemon_squeezy_client.py     # LS API: validate key, get subscription status
│   ├── error_reporter.py           # Global exception capture; opt-in email send
│   └── updater.py                  # GitHub Releases API check (v1.1)
│
├── assets/
│   ├── icons/                      # App icon (tass.ico), toolbar icons
│   ├── fonts/                      # Bundled font (Inter or similar clean sans-serif)
│   └── styles/
│       └── theme.qss               # Qt stylesheet — minimal, clean, accessible
│
├── tests/
│   ├── test_importer.py
│   ├── test_preprocessor.py
│   ├── test_dictionary_engine.py
│   ├── test_statistics_engine.py
│   └── test_project.py
│
├── build/                          # PyInstaller output (gitignored)
├── dist/                           # Inno Setup installer output (gitignored)
├── requirements.txt
├── requirements-dev.txt
├── tass.spec                       # PyInstaller spec file
└── installer.iss                   # Inno Setup installer script
```

---

## 4. Core Data Flow

```
1. IMPORT
   User selects file(s)
   → importer.py reads file → pandas DataFrame
   → Column types auto-detected
   → Data preview shown (read-only QTableView)
   → User maps: text column, optional group column, metadata columns
   → session.py stores DataFrame + column mapping

2. CONFIGURE
   User selects dictionaries from registry
   User selects analysis levels (word / entry / document)
   User optionally defines groups (column + value mapping)
   → session.py stores analysis config

3. ANALYZE (runs in QThread worker — UI stays responsive)
   preprocessor.py:
     → Tokenize each text entry (NLTK word_tokenize)
     → Lowercase, strip punctuation
     → Optional lemmatization (NLTK WordNetLemmatizer)
     → Store token list per entry

   dictionary_engine.py (multi-threaded via concurrent.futures):
     → For each dictionary × each entry:
         → Match tokens against dictionary word list
         → Record: matched words, category, score
     → Produce: entry-level scores DataFrame (rows=entries, cols=categories)
     → Produce: word-match index (entry_id → {category: [matched_words]})

   statistics_engine.py:
     → Document-level: aggregate means across all entries
     → If groups defined: compute per-group stats + significance tests

   → Results stored in session.py
   → Progress dialog updated via Qt signals throughout

4. VIEW
   Results panel displays:
     → Scores tab: sortable table of entry-level scores
     → Word matches tab: click an entry to see highlighted matches per category
     → Summary tab: document-level aggregates
     → Groups tab: comparison tables + inline charts

5. VISUALIZE
   visualization_engine.py:
     → Generates matplotlib figures from session results
     → Applies TASS theme (ggplot-inspired, configurable palette)
     → Renders to in-app canvas (FigureCanvasQTAgg)
   User selects export format (PNG 300dpi / SVG)

6. EXPORT
   export_engine.py:
     → CSV: entry-level scores + metadata columns
     → Excel: multi-sheet (raw scores / summary / group comparisons)
     → Charts: PNG/SVG files per chart type
   citation.py appends citation block to all text-based exports

7. SAVE PROJECT
   project.py bundles into .tass (ZIP):
     → manifest.json (TASS version, created date, column mapping)
     → data.parquet (original DataFrame, compressed)
     → results.parquet (scored DataFrame)
     → analysis_config.json (dictionaries, levels, group config)
     → session_state.json (active tab, scroll positions, viz settings)
     → visualizations/chart_config.json (chart customizations)
```

---

## 5. Dictionary Engine Design

All dictionaries are normalized to a standard internal format on load:

```json
{
  "name": "AFINN-165",
  "version": "2011",
  "citation": "Nielsen (2011)",
  "license": "MIT",
  "categories": {
    "sentiment": {
      "abandon": -2, "abhor": -3, "admire": 3, "adore": 3, "affection": 3
    }
  },
  "scoring": "weighted"
}
```

**Scoring modes:**
- `binary`: word present = 1, absent = 0; entry score = (matched / total tokens) * 100
- `weighted`: word has a numeric weight (e.g., AFINN: -5 to +5); entry score = sum of weights
- `count`: raw count of matched words per entry

**Entry-level score formula (binary):**
```
score(entry, category) = (matched_token_count / total_token_count) * 100
```

**Word-level output:**
For each entry, store a mapping of `{category: [list of matched words]}`. This powers the word-match highlighting view in the Results panel.

**Multi-threading:**
```python
from concurrent.futures import ThreadPoolExecutor

def analyze_entry(entry_tokens, dictionaries):
    results = {}
    for dict_name, dict_data in dictionaries.items():
        for category, word_list in dict_data['categories'].items():
            matches = [t for t in entry_tokens if t in word_list_set]
            results[f"{dict_name}_{category}"] = score(matches, entry_tokens)
    return results

with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
    futures = [executor.submit(analyze_entry, tokens, dicts) for tokens in all_tokens]
    results = [f.result() for f in futures]
```

---

## 6. .tass Project File Format

```
myproject.tass  (renamed ZIP archive)
├── manifest.json           # Metadata
├── data.parquet            # Original imported data (pandas → parquet, compressed)
├── results.parquet         # Entry-level scored DataFrame
├── analysis_config.json    # Which dictionaries, levels, group definitions
├── session_state.json      # UI state (active tab, scroll position, palette choice)
└── visualizations/
    ├── chart_config.json   # Chart customization settings
    └── cache/              # Optional: cached PNG thumbnails for fast reload
```

**manifest.json example:**
```json
{
  "tass_version": "1.0.0",
  "created_at": "2026-05-15T14:23:00Z",
  "modified_at": "2026-05-15T16:45:00Z",
  "text_column": "tweet_text",
  "group_column": "political_party",
  "metadata_columns": ["user_id", "date", "retweet_count"],
  "row_count": 8432,
  "dictionaries_used": ["afinn165", "vader_lexicon", "mfd2"]
}
```

---

## 7. Supabase Database Schema

```sql
-- License keys (created by Lemon Squeezy webhook on purchase)
CREATE TABLE licenses (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  key            TEXT UNIQUE NOT NULL,
  tier           TEXT NOT NULL CHECK (tier IN ('individual', 'team_5', 'team_10')),
  seats          INTEGER NOT NULL DEFAULT 1,
  customer_email TEXT,
  activated_at   TIMESTAMPTZ,
  expires_at     TIMESTAMPTZ NOT NULL,
  created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- Machine activations (max 2 per individual license)
CREATE TABLE activations (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  license_id          UUID REFERENCES licenses(id) ON DELETE CASCADE,
  machine_fingerprint TEXT NOT NULL,
  tass_version        TEXT,
  os_info             TEXT,
  activated_at        TIMESTAMPTZ DEFAULT NOW(),
  last_seen_at        TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(license_id, machine_fingerprint)
);

-- Trial registrations
CREATE TABLE trials (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email       TEXT UNIQUE NOT NULL,
  trial_key   TEXT UNIQUE NOT NULL DEFAULT gen_random_uuid()::TEXT,
  started_at  TIMESTAMPTZ DEFAULT NOW(),
  expires_at  TIMESTAMPTZ NOT NULL,  -- started_at + 14 days
  converted   BOOLEAN DEFAULT FALSE,
  converted_at TIMESTAMPTZ
);
```

**Machine fingerprint:** SHA-256 hash of (CPU ID + disk serial + MAC address). Never stored in plain text on user machine; used only for activation count enforcement.

---

## 8. License System Flow

```
App launch
  → Read encrypted local license cache (AES-256, key derived from machine fingerprint)
  → If valid + not expired → proceed (fully offline)
  → If missing or expired → show LicenseDialog

Trial flow
  → User enters email
  → POST to Supabase edge function: /create-trial
  → Trial record created; 14-day key returned
  → Key stored in local cache
  → Row limit (500) enforced in analysis_config_panel.py before analysis starts

Trial expiry
  → App enters view-only mode
  → Existing .tass projects: open + export allowed
  → New analysis runs: blocked; upgrade dialog shown
  → Banner shown on every screen during view-only

License activation
  → User enters Lemon Squeezy license key
  → App calls LS API to validate key + check expiry
  → On success:
      → POST to Supabase /activate: register machine fingerprint
      → If seats exceeded: show "max devices reached" with deactivation option
      → Encrypted local cache written with key + expiry + tier
  → Activation succeeds once; works offline thereafter until expiry

License renewal
  → On internet-connected launch when within 14 days of expiry: prompt to renew
  → On expiry: re-validate online; enter view-only if not renewed
```

---

## 9. Statistics Engine Reference

All statistics use SciPy. Results are stored in the session and exported.

| Statistic | Function | Condition |
|---|---|---|
| Mean, SD, Min, Max, Median | `numpy` | Always computed |
| Independent t-test | `scipy.stats.ttest_ind` | Exactly 2 groups |
| Mann-Whitney U | `scipy.stats.mannwhitneyu` | Exactly 2 groups (non-parametric option) |
| One-way ANOVA | `scipy.stats.f_oneway` | 3+ groups |
| Cohen's d | Computed manually: `(m1-m2)/pooled_sd` | 2 groups |
| Eta-squared | `SS_between / SS_total` | ANOVA |
| p-value display | Report exact p; flag p<.05, p<.01, p<.001 | All tests |

Multiple comparison correction (Bonferroni) is applied when comparing across all dictionary categories simultaneously. User can toggle this in settings.

---

## 10. Visualization Engine Reference

All charts use Matplotlib + Seaborn. Color palettes are swappable via theme settings.

| Chart Type | Library | Use Case |
|---|---|---|
| Bar chart (horizontal) | Seaborn `barplot` | Category mean scores, single dataset or per group |
| Word cloud | `wordcloud` | Top matched words, colored by category |
| Box plot | Seaborn `boxplot` | Group distributions per category |
| Violin plot | Seaborn `violinplot` | Group distributions (richer shape) |
| Heatmap | Seaborn `heatmap` | Category scores across groups or document segments |
| Scatter plot | Matplotlib | Correlation between two categories (optional) |

**Export settings:**
- PNG: 300 DPI minimum (publication quality)
- SVG: vector format for journal submission or presentation use
- Figure dimensions: default 10×6 inches (configurable in settings)

**TASS theme (QSS-aligned):**
- Font: Inter (bundled) or system sans-serif fallback
- Background: white (`#FFFFFF`)
- Axis lines: light gray (`#CCCCCC`)
- Default palette (accessible): follows ColorBrewer qualitative sets
- Colorblind-safe palette: `viridis` / `cividis` sequential; `colorblind` categorical
- Grayscale palette: for B&W journal requirements

---

## 11. Build & Distribution

### Development Environment Setup
```bash
# Python 3.11 (use pyenv or python.org installer)
python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run app
python main.py
```

### PyInstaller Build
```bash
# One-time: generate spec file
pyinstaller --onedir --windowed --name TASS \
  --icon assets/icons/tass.ico \
  --add-data "dictionaries/builtin;dictionaries/builtin" \
  --add-data "assets;assets" \
  main.py

# Subsequent builds using spec
pyinstaller tass.spec
```

### Code Signing (Windows)
```bash
# After obtaining OV cert from Sectigo/DigiCert (~$200/year)
signtool sign \
  /n "SIM DAD LLC" \
  /t http://timestamp.digicert.com \
  /fd sha256 \
  dist/TASS/TASS.exe

# Sign the installer too (after building with Inno Setup)
signtool sign /n "SIM DAD LLC" /t http://timestamp.digicert.com /fd sha256 TASS_Setup_v1.0.0.exe
```

### Inno Setup Installer
Key Inno Setup configuration sections (`installer.iss`):
```
[Setup]
AppName=TASS
AppVersion=1.0.0
AppPublisher=SIM DAD LLC
DefaultDirName={autopf}\TASS
DefaultGroupName=TASS
OutputBaseFilename=TASS_Setup_v1.0.0
Compression=lzma2/ultra64
SignTool=standard

[Files]
Source: "dist\TASS\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{autoprograms}\TASS"; Filename: "{app}\TASS.exe"
Name: "{autodesktop}\TASS"; Filename: "{app}\TASS.exe"

[Registry]
; Register .tass file extension
Root: HKCR; Subkey: ".tass"; ValueData: "TASSProject"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "TASSProject\shell\open\command"; ValueData: """{app}\TASS.exe"" ""%1"""
```

### GitHub Release Process
```
1. Merge all changes to main branch
2. Tag: git tag v1.0.0 && git push origin v1.0.0
3. Create GitHub Release from tag
   - Upload: TASS_Setup_v1.0.0.exe (signed installer)
   - Write changelog in release notes
4. Zenodo auto-mints DOI from GitHub Release (connected once in Zenodo settings)
5. Update citation.py with new Zenodo DOI
6. Update product website download link
```

---

## 12. Sprint Plan: v1.0 (12 Weeks to May 31, 2026)

| Sprint | Weeks | Focus | Acceptance Criteria |
|---|---|---|---|
| 1 | 1–2 | Project scaffolding, PySide6 shell, main window + sidebar nav | App launches; nav switches between empty panels |
| 2 | 3–4 | File importer, column mapping wizard, data preview | User imports a CSV and sees data in preview table |
| 3 | 5–6 | Dictionary loader, preprocessor, dictionary engine (terminal only) | `analyze()` called from test script returns scored DataFrame |
| 4 | 7 | Results panel UI, worker threads, progress dialog | Analysis runs without freezing UI; results displayed in table |
| 5 | 8 | Statistics engine, group comparison panel | Group stats computed and displayed; t-test/ANOVA results shown |
| 6 | 9 | Visualization engine: bar charts, word clouds, box plots, heatmaps | All chart types render in-app and export to PNG/SVG |
| 7 | 10 | Export engine: CSV, Excel, citation appended | Export produces correct multi-sheet Excel; citation block present |
| 8 | 11 | License system: Supabase + Lemon Squeezy + trial mode | Trial starts with email; license key activates; view-only on expiry |
| 9 | 12 | Project save/load (.tass), help tooltips, error reporter, polish, testing | Round-trip project save/load verified; error report sends email |

---

## 13. requirements.txt (v1.0)

```
PySide6==6.7.3
pandas==2.1.4
numpy==1.26.4
scipy==1.11.4
matplotlib==3.8.3
seaborn==0.13.2
wordcloud==1.9.3
nltk==3.8.1
openpyxl==3.1.2
pyarrow==14.0.2
requests==2.31.0
cryptography==42.0.5
pyinstaller==6.5.0
```

```
# requirements-dev.txt
pytest==8.1.1
pytest-qt==4.4.0
black==24.3.0
ruff==0.3.4
```

---

## 14. Key Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Dictionary commercial use licensing | Medium | High | Audit each dictionary before launch; substitute or seek permission as needed; consult a lawyer before exceeding ~500 paying users |
| PyInstaller bundle size exceeds 2GB | Low | Medium | Profile bundle; exclude unused NLTK corpora; use `--exclude-module` flags |
| Multi-threading instability on Windows | Low | Medium | Thorough testing with `ProcessPoolExecutor` fallback if ThreadPool causes GIL issues |
| Supabase free tier limits hit | Low | Low | 500MB DB limit; 50k MAU limit; well within early-growth range; upgrade plan is $25/month |
| PySide6 licensing misunderstanding | Low | High | PySide6 uses LGPL — compatible with commercial proprietary apps if linked dynamically (default PyInstaller behavior) |
| May 31 deadline slip | Medium | Medium | Sprint 9 (polish/testing) is the natural cut point; ship Sprint 1–8 deliverables as v1.0 if needed; defer polish to v1.0.1 |
