# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for TASS — Text Analysis for Social Scientists
# Build with:  pyinstaller tass.spec
#
# Prerequisites:
#   pip install pyinstaller==6.5.0
#   assets/icons/tass_icon.ico must exist (created in Illustrator)
#
# Output: dist/TASS/TASS.exe (onedir bundle)

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(SPECPATH)

# ── Collect NLTK data (only the corpora TASS actually needs) ──────────────
nltk_datas = []
try:
    import nltk
    for _nltk_base in nltk.data.path:
        _nltk_base = Path(_nltk_base)
        for corpus in ("stopwords", "wordnet", "averaged_perceptron_tagger", "omw-1.4"):
            corpus_path = _nltk_base / "corpora" / corpus
            if corpus_path.exists():
                nltk_datas.append((str(corpus_path), f"nltk_data/corpora/{corpus}"))
        tokenizer_path = _nltk_base / "tokenizers"
        if tokenizer_path.exists():
            nltk_datas.append((str(tokenizer_path), "nltk_data/tokenizers"))
    # deduplicate (keep first found for each dest path)
    nltk_datas = list({d[1]: d for d in nltk_datas}.values())
    print(f"[tass.spec] Bundling {len(nltk_datas)} NLTK data directories.")
except ImportError:
    print("[tass.spec] WARNING: nltk not found; NLTK data will not be bundled.")
    print("  Run: pip install nltk && python -c \"import nltk; nltk.download('stopwords')\" etc.")

# ── Application data files ─────────────────────────────────────────────────
# NOTE: hurtlex.json and sentiwordnet.json are intentionally absent from
# dictionaries/builtin/. Both are CC-BY-SA 4.0 (Share-Alike), which is
# incompatible with commercial distribution. They are optional user downloads
# — see dictionaries/registry.py (optional_download entries) for details.
app_datas = [
    (str(ROOT / "dictionaries" / "builtin"), "dictionaries/builtin"),
    (str(ROOT / "assets"), "assets"),
]

# ── Hidden imports ─────────────────────────────────────────────────────────
hidden_imports = [
    # PySide6 modules not always auto-detected
    "PySide6.QtSvg",
    "PySide6.QtSvgWidgets",
    "PySide6.QtPrintSupport",
    # matplotlib Qt backend
    "matplotlib.backends.backend_qtagg",
    "matplotlib.backends.backend_svg",
    "matplotlib.backends.backend_agg",
    # scipy stats
    "scipy.stats",
    "scipy.stats._stats_py",
    "scipy._lib.messagestream",
    # NLTK tokenizers + taggers
    "nltk.tokenize",
    "nltk.stem",
    "nltk.stem.wordnet",
    "nltk.corpus",
    # pyarrow parquet engine
    "pyarrow.pandas_compat",
    "pyarrow._parquet",
    # wordcloud
    "wordcloud",
    # openpyxl
    "openpyxl",
    "openpyxl.styles",
    "openpyxl.utils",
    # cryptography
    "cryptography.hazmat.primitives",
    "cryptography.hazmat.backends",
    # requests
    "requests.adapters",
    "requests.packages",
    # TASS internal modules
    "core.session",
    "core.importer",
    "core.preprocessor",
    "core.dictionary_engine",
    "core.statistics_engine",
    "core.visualization_engine",
    "core.export_engine",
    "core.project",
    "core.citation",
    "core.workers",
    "dictionaries.loader",
    "dictionaries.registry",
    "services.license",
    "services.error_reporter",
    "services.supabase_client",
    "services.lemon_squeezy_client",
    "services.updater",
    "ui.main_window",
    "ui.welcome_screen",
    "ui.import_wizard",
    "ui.data_preview",
    "ui.analysis_config_panel",
    "ui.progress_dialog",
    "ui.results_panel",
    "ui.visualization_panel",
    "ui.compare_panel",
    "ui.export_dialog",
    "ui.help_panel",
    "ui.license_dialog",
    "ui.cite_dialog",
    "ui.settings_dialog",
]

# ── Analysis ───────────────────────────────────────────────────────────────
a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=app_datas + nltk_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Keep the bundle lean — exclude unused large packages
        "tkinter",
        "wx",
        "gtk",
        "IPython",
        "jupyter",
        "notebook",
        "sphinx",
        "docutils",
        "test",
        "pytest",
        "setuptools",
        "pip",
        # Large NLTK corpora not needed
        "nltk.corpus.brown",
        "nltk.corpus.gutenberg",
        "nltk.corpus.reuters",
        "nltk.corpus.inaugural",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# ── Strip debug symbols from binaries ─────────────────────────────────────
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# ── Executable ────────────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TASS",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,          # Windows: strip=True can break binaries
    upx=True,             # compress with UPX if available
    console=False,        # no console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "assets" / "icons" / "tass_icon.ico"),
    version=str(ROOT / "assets" / "version_info.txt"),
)

# ── One-directory bundle ───────────────────────────────────────────────────
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[
        # UPX can corrupt some Qt DLLs — exclude them
        "Qt6Core.dll",
        "Qt6Gui.dll",
        "Qt6Widgets.dll",
        "Qt6Svg.dll",
        "Qt6PrintSupport.dll",
    ],
    name="TASS",
)
