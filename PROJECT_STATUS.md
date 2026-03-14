# TASS — Project Status
**Updated:** 2026-03-14 (Sprints 5–9 scaffolding complete; bug fixes applied)
**Target Release:** v1.0.0 by May 31, 2026
**Sprint Cadence:** ~1–2 weeks per sprint | 9 sprints total

---

## Sprint Overview

| Sprint | Weeks | Focus | Status | Acceptance Criteria |
|--------|-------|-------|--------|---------------------|
| 0 | Pre-sprint | Core scaffolding: core/, services/, dictionaries/, entry points | ✅ Done | All modules importable; no UI required |
| 1 | 1–2 | PySide6 shell: main window + sidebar nav | ✅ Done | App launches; nav switches between panels |
| 2 | 3–4 | File importer, column mapping wizard, data preview | ✅ Done | User imports CSV and sees data in preview |
| 3 | 5–6 | Dictionary loader UI, preprocessor, dictionary engine (terminal) | ✅ Done | `analyze()` returns scored DataFrame from test script |
| 4 | 7 | Results panel UI, worker threads, progress dialog | ✅ Done | Analysis runs without freezing UI; results in table |
| 5 | 8 | Statistics engine, group comparison panel | ✅ Done | compare_panel.py fully implemented; StatisticsWorker wired |
| 6 | 9 | Visualization engine: bar, word cloud, box plot, heatmap | ✅ Done | All 5 chart types + PNG/SVG export in visualization_panel.py |
| 7 | 10 | Export engine: CSV, Excel, citation | ✅ Done | Multi-sheet Excel + citation block in export_dialog.py |
| 8 | 11 | License system: Supabase + Lemon Squeezy + trial mode | ✅ Done | license.py + supabase_client.py + lemon_squeezy_client.py wired |
| 9 | 12 | Project save/load, help, error reporter, polish, tests | ✅ Done | .tass ZIP round-trip; help_panel.py 14 articles; test suites |

---

## File Completion Checklist

### Entry Points
- [x] `main.py` — QApplication entry point
- [x] `app.py` — App bootstrap, NLTK init, license gate, exception hook

### Core Layer (`core/`)
- [x] `session.py` — Singleton session state
- [x] `importer.py` — CSV/TXT/XLSX ingestion
- [x] `preprocessor.py` — Tokenization, lemmatization pipeline
- [x] `dictionary_engine.py` — Dictionary matching, scoring
- [x] `statistics_engine.py` — Descriptives, t-test, ANOVA, effect sizes
- [x] `visualization_engine.py` — Matplotlib/Seaborn figure generation
- [x] `export_engine.py` — CSV, Excel, PNG/SVG output
- [x] `project.py` — .tass file read/write (ZIP+JSON+parquet)
- [x] `citation.py` — Citation string generation
- [x] `workers.py` — QThread workers (AnalysisWorker, StatisticsWorker)

### Dictionaries (`dictionaries/`)
- [x] `loader.py` — Dictionary file loader + validation
- [x] `registry.py` — Manifest of built-in + user dictionaries
- [x] `builtin/afinn165.json`
- [x] `builtin/vader_lexicon.json`
- [x] `builtin/sentiwordnet.json`
- [x] `builtin/mfd2.json`
- [x] `builtin/brysbaert_concreteness.json`
- [x] `builtin/hurtlex.json`
- [x] `builtin/wordnet_pos.json`
- [x] `builtin/nltk_stopwords.json`

### Services Layer (`services/`)
- [x] `license.py` — Key validation, trial management, machine fingerprint
- [x] `supabase_client.py` — Supabase REST API calls
- [x] `lemon_squeezy_client.py` — Lemon Squeezy API
- [x] `error_reporter.py` — Crash log email
- [x] `updater.py` — GitHub Releases API check

### UI Layer (`ui/`)
- [x] `main_window.py` — Shell: sidebar nav, stacked panels, menus, status bar
- [x] `welcome_screen.py` — Home: recent projects, quick-start actions
- [x] `license_dialog.py` — Trial signup + license key activation
- [x] `import_wizard.py` — Full 3-step wizard ✅ (file picker, column mapping, data preview)
- [x] `data_preview.py` — PandasTableModel + QTableView ✅ (embedded in wizard step 3)
- [x] `analysis_config_panel.py` — Full panel ✅ (dict browser, options, Run Analysis → AnalysisWorker)
- [x] `progress_dialog.py` — Modal progress bar + cancel ✅ (wired to AnalysisWorker in Sprint 3)
- [x] `results_panel.py` — Full 4-tab panel ✅ (Scores, Word Matches, Summary, Groups CTA)
- [x] `visualization_panel.py` — Full 5-chart-type panel ✅ (bar, word cloud, box, violin, heatmap + PNG/SVG export)
- [x] `compare_panel.py` — Full group comparison panel ✅ (StatisticsWorker wired, p-value table with stars)
- [x] `export_dialog.py` — Full export dialog ✅ (CSV/Excel/PNG/SVG with ExportEngine)
- [x] `help_panel.py` — Full help panel ✅ (14 articles, 7 sections, debounced search)
- [x] `cite_dialog.py` — APA/MLA/Chicago copy dialog ✅ functional
- [x] `settings_dialog.py` — Palette + export path preferences ✅ functional

### Assets
- [x] `assets/styles/theme.qss` — Full Qt stylesheet
- [x] `assets/icons/app-icon.svg` — Source icon ✅ (magnifying glass + bar chart + text lines)
- [ ] `assets/icons/tass.ico` — Convert SVG → ICO before PyInstaller build (Sprint 9)
- [ ] `assets/fonts/` — Bundle Inter font (optional; Segoe UI fallback active)

### Build & Distribution
- [ ] `requirements.txt` — (exists; verify versions against installed env)
- [ ] `requirements-dev.txt` — (exists)
- [ ] `tass.spec` — PyInstaller spec (Sprint 9)
- [ ] `installer.iss` — Inno Setup script (Sprint 9)

### Tests (`tests/`)
- [x] `test_importer.py` — 20 tests across import_file, import_files, detect_column_types, suggest_text_column ✅
- [x] `test_preprocessor.py` — 25 tests: tokenize, min_length, stopwords, lemmatize, process_series/df ✅
- [x] `test_dictionary_engine.py` — 25 tests: binary/weighted/count scoring, word_matches, edge cases ✅
- [x] `test_statistics_engine.py` — 35 tests: document_summary, group_comparisons (2+3 groups), per_group_summary, helpers ✅
- [ ] `test_project.py`

---

## Current Status: Integration & End-to-End Verification

All scaffolding is complete (Sprints 0–9). Focus is now on:
1. **Verify end-to-end pipeline** — `python main.py` launches cleanly
2. **Wire import → analysis → results** flow without errors
3. **Populate remaining dictionary stubs** — HurtLex and SentiWordNet need license resolution
4. **Write test_project.py** — round-trip .tass save/load tests
5. **Build Sprint 9 artifacts** — `tass.spec`, `installer.iss`, `assets/icons/tass.ico`

### Bug Fixes Applied (2026-03-14)
- `main_window.py`: `ProjectSerializer` → `ProjectManager` (fixed)
- `welcome_screen.py`: `ProjectSerializer.load()` → `ProjectManager.load()` (fixed)
- `core/project.py`: circular `from app import TASS_VERSION` → inline constant (fixed)
- `core/citation.py`: same circular import (fixed in prior session)
- `services/license.py`: same circular import inside function (fixed)
- `services/error_reporter.py`: same circular import inside function (fixed)
- `core/workers.py`: hardcoded preprocessor opts → now accepts `preprocessor_kwargs` param (fixed)
- `ui/analysis_config_panel.py`: now passes `preprocessor_kwargs` to `AnalysisWorker` (fixed)

---

## Commercial License Audit

> **Status: Requires action before launch on 2 dictionaries. All Python libraries are clear.**

### Python Libraries — All Clear ✅
| Library | License | Commercial Use |
|---------|---------|----------------|
| PySide6 | LGPL 3.0 | ✅ OK — dynamically linked via PyInstaller |
| pandas, numpy, scipy | BSD 3-Clause | ✅ OK |
| matplotlib, seaborn | BSD / PSF | ✅ OK |
| wordcloud | MIT | ✅ OK |
| nltk | Apache 2.0 | ✅ OK |
| openpyxl | MIT | ✅ OK |
| pyarrow | Apache 2.0 | ✅ OK |
| requests, cryptography | Apache 2.0 / BSD | ✅ OK |
| PyInstaller | GPL + bootloader exception | ✅ OK — exception explicitly permits bundling proprietary apps |

### Bundled Dictionaries — Action Required on 2
| Dictionary | License | Status |
|------------|---------|--------|
| AFINN-165 | MIT | ✅ OK |
| VADER Lexicon | MIT | ✅ OK |
| MFD 2.0 | CC-BY 4.0 | ✅ OK — attribution required in UI/docs |
| Brysbaert Concreteness | CC-BY 4.0 | ✅ OK — attribution required |
| WordNet POS | Princeton WordNet License | ✅ OK — permits commercial use with attribution |
| NLTK Stopwords | Apache 2.0 | ✅ OK |
| HurtLex | CC-BY-SA 4.0 | ⚠️ **Share-Alike** — bundling in commercial app is legally gray; get explicit permission or replace |
| SentiWordNet 3.0 | CC-BY-SA 4.0 | ⚠️ **Share-Alike** — same concern as HurtLex |

### Required Actions Before Launch
1. **HurtLex & SentiWordNet**: either (a) obtain written permission from authors for commercial bundling, (b) replace with MIT/CC-BY alternatives, or (c) make them optional downloads (not bundled) so the Share-Alike clause applies only to the data, not the app. Option (c) is the lowest-risk path.
2. **MFD 2.0 & Brysbaert**: add attribution in the About dialog and in all exports that include scores from these dictionaries. Already handled by `citation.py`.
3. **Get legal review** before exceeding ~500 paying users (per original risk register).

---

## Known Issues / Blockers
- HurtLex and SentiWordNet require license resolution before commercial launch (see above)

## Architecture Decisions Locked In
- Python 3.11 + PySide6 6.7 + pandas 2.x (no changes)
- `.tass` format = ZIP(manifest.json + data.parquet + results.parquet + config.json)
- Worker threads: QThread subclasses (AnalysisWorker, StatisticsWorker) in `core/workers.py`
- License backend: Supabase (free tier) + Lemon Squeezy
- Scoring modes: binary (% of tokens), weighted (AFINN-style), count (raw)

---

## Risks to Watch
| Risk | Status |
|------|--------|
| PyInstaller bundle size | Monitor at Sprint 9; exclude unused NLTK corpora |
| SVG → ICO conversion | Needed before Sprint 9 build; use Pillow + cairosvg or Inkscape CLI |
| Dictionary license audit | Complete before launch; legal review at ~500 paying users |
| May 31 deadline | On track; Sprints 1–4 complete on schedule |
| HurtLex / SentiWordNet CC-BY-SA | ⚠️ Resolve before launch — see Commercial License Audit section |
