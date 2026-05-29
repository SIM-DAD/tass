---
type: status
status: active
zone: llc
last_modified: 2026-05-29T14:24:00-05:00
tldr: "Error-reporting catalog gate SHIPPED 2026-05-29: the non-compliant SMTP error_reporter is replaced with the policy-compliant mailto: three-touchpoint flow (report builder + path redactor + local queue + dialogs A/B/C + Settings→Privacy); 10 new tests, full suite 287 green; tass-web privacy.html + eula.html aligned; docs/error-reporting-compliance.md written. This was the last LLC catalog gate. v1.0 PySide6 remains feature-complete (YubiKey cert delivery blocks signing). v2 Tauri at 0.2.5; 0.2.6 punch list still open (U-009 validation workspace, B-010 inferential stats, Report export bundle)."
priority: high
related: [LLC-005-CRYPTO]
next_action_oneline: "Launch TASS, trigger a test exception, and confirm the crash dialog renders and opens the mailto with no network send (the deferred GUI smoke that fully closes error-reporting compliance)."
blockers: "v1.0 release — YubiKey EV cert delivery (validated, not yet issued) blocks signing. error_reporter non-compliance RESOLVED 2026-05-29. v2 0.2.6 punch list (U-009, B-010, Report exports) is ongoing product work, not a launch blocker."
last_session: 2026-05-29T14:24:00-05:00
last_session_handoff: meta/handoffs/session/2026-05-29-14-24-LLC-001.md
---

# TASS — Status

## Tasks
- [ ] Open the file smoke-test-report-2026-05-24-v3-0.2.5.md
- [ ] Navigate to section §8 punch list
- [ ] Identify the three items: U-009 validation workspace, B-010 inferential stats, and Report exports
- [ ] Select the highest-priority item among them for scoping in v2 0.2.6

## Roadmap

### v1.0.0 — Launch (May 31, 2026)
- Clean CSV export (no citation footer breaking R/Excel import)
- Re-import scored TASS data (skip scoring, go to Compare/Visualize)
- Codebook export (JSON/YAML — dictionary categories, scoring mode, preprocessing)

### v1.1 — Interoperability (timing TBD — map to retention window)
- SPSS .sav export (pyreadstat)
- R .rds export (pyreadstat)
- Import from SPSS/Stata (.sav, .dta)
- Reproducibility script export (generate equivalent R or Python code)

### v1.2 — Power Users (timing TBD — map to second press cycle)
- CLI mode (tass score --input data.csv --dict afinn165 --output results.csv)
- Parquet export for large datasets
- LIWC-format dictionary import

**Release strategy:** Ship features on the marketing calendar, not the dev calendar. Each version is a press/outreach opportunity — space for maximum coverage and retention impact.

## Recent Changes
- 2026-05-29 14:24: **error_reporter catalog gate SHIPPED.** Replaced the homegrown SMTP `services/error_reporter.py` (non-compliant with the LLC error-reporting policy) with the policy-compliant manual-submit `mailto:` flow. New `error_reporter.py`: section-4 `CrashReport` builder, `redact_paths()` (strips absolute paths to `<redacted-path>/<file>`), `compose_mailto()` to `support+tass@simdadllc.com`, local queue at `%LOCALAPPDATA%\TASS\crash-queue`. New `ui/crash_dialogs.py`: touchpoints A (first-launch pref) / B (live crash) / C (post-restart) + `QueuedReportsDialog`. `app.py` excepthook routes to `LiveCrashDialog` and queues on silent-close; `_launch` shows A once + C if queued. `ui/settings_dialog.py` Privacy panel (3 booleans + queued-reports manager). `tests/test_error_reporter.py` 10 cases pass; full suite **287 passed, no regressions**. `tass-web/privacy.html` corrected (it falsely claimed "no crash reporting") + `eula.html` §7 clause. Compliance checklist at `docs/error-reporting-compliance.md`. Deferred: manual GUI click-through on a running build; a segfault/hard-kill dumper (documented, Python can't schema a C-level crash). This was the last LLC catalog gate.
- 2026-05-24 22:00: **TASS v2 Tauri smoke-test trilogy (0.2.3 → 0.2.4 → 0.2.5)** completed today; three reports landed in tass/docs/. 0.2.5 is the cleanest: 5 fixes from 0.2.4 punch list (U-003 Run scoring state machine, U-008 navigator on corpus load, M-002 Publisher = "SIM DAD LLC", M-003 URL metadata populated, M-004 multi-Python cache strip), 0 regressions. Analyze view now renders Summary + Group Frequencies tables; Report view renders Methods Text canvas. Still open: U-009 validation workspace, B-010 inferential stats on continuous score columns, Report export bundle. Plus: **peer-review brief** (peer-review-brief.md, 3 code-grounded appendices), **design-followup brief** (design-followup-brief.md, paired-voice critique with owner-invited dissent block on the deep-research-report's Electron/Highcharts/multi-metaphor assumptions). Plus: **SIM DAD LLC-wide error-reporting policy** at llc/policies/error-reporting-policy.md — three-touchpoint manual-submit opt-in, data minimization contract, no third-party processor, per-product compliance checklist. Current TASS services/error_reporter.py SMTP path is now non-compliant; replace with mailto: flow before public release.
- 2026-05-18 06:30: **Soft launch 5/22 CANCELLED; single launch 5/31.** Owner decision in response to LLC-003 Lector slipping 5/18 to at-least 5/22 — the dual-product 5/22 day would have collided. TASS was always doubly-staged (soft 5/22 + hard 5/31); the soft slot is dropped in favor of a single 5/31 launch. Today's TASS Day-0 marketing queued in [content-calendar.md](C:/life-os/llc/launch-2026-05/content-calendar.md) — substantiation publish 06:00 CT, founder LinkedIn 09:00, LLC LinkedIn 09:30, three listservs (AAPORnet + NCA COMMNotes + AEJMC) at 10:00, founder X 10:00, LLC X 10:30, Bluesky personal + LLC at 11:00 + 11:30 — all need pause/cancel. Per content-calendar entries marked "DRAFT PENDING" (~half the slots), those weren't ready so they won't fire; the listserv emails + any Buffer-queued posts WILL fire if not cancelled. Pre-publish work (T-Lex dictionaries + benchmark corpus) timeline relaxes from 4 days to 13 days. Adds an opportunity: run TASS through PERS-011 clean-VM rig before launch (rig caught two Lector Tier-0s last week — TASS should get the same scrutiny).
- 2026-04-15: 82K dataset validated end-to-end — progress bar smooth, no freeze. Warriner VAD and Empath dictionaries confirmed in Analyze panel, scores populated. Custom dictionary built and tested successfully.
- 2026-04-12: Book Plan v3 created — audited v2 against codebase, found and corrected 13 factual mismatches (dictionaries, scoring modes, result panels, effect sizes, exports, missing features). Website audit: rebuilt buy/download/support subpages in light/green design, unified pricing to 4-tier subscription, EULA updated (Gumroad + correct tier names), privacy policy and og:image added.
- 2026-04-12: Final build + installer (168.1 MB). Clean-machine test passed on THINKPAD. 250 tests passing. 6 fixes: citation author (Leith, A. P.), trial 500-row limit at import, comparison table spacing, scatter plot, optional dictionary download UI in Settings. Statistical methods documentation (10 help articles + website Markdown). Textbook brief written. v1.0/1.1/1.2 roadmap defined.
- 2026-04-06: Licensing resolved. E2E smoke test passed. Ready for final build.
- 2026-04-01: Structured output viewer, FDR correction, TF-IDF scoring, DV selector, n-gram support, comprehensive help panel, analysis log, brand color migration to green, emoji-to-SVG sidebar icons — all shipped.
- 2026-04-01: Dunn's test, Levene's test, degrees of freedom, exact p-values, effect size labels, Spearman correlation, APA interpretive notes — all shipped.
- 2026-03-31: Statistical completeness: Tukey HSD, Kruskal-Wallis, CIs, normality checks, correlation matrix, coverage stats, KWIC viewer, scatter plots, APA export.
- 2026-03-31: Sidebar finalization complete. All 9 sprints done.

## Decisions Log
- 2026-04-01: HurtLex + SentiWordNet made optional user downloads (CC-BY-SA 4.0 incompatible with commercial distribution). Lowest-risk licensing path.
- 2026-04-01: Gumroad Membership for distribution — Academic $79/yr, Professional $129/yr, Lab $249/yr, Department $699/yr.
- 2026-04-01: Brand color migrated from blue (#2563EB) to green (#2E7D5E).
- 2026-03-31: Python 3.12 venv (upgraded from 3.11). 250 tests passing.
- 2026-03-31: Test selector wizard kept as optional sidebar helper (not mandatory). Dev plan Q8.
