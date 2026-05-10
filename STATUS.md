---
type: status
status: active
zone: llc
last_modified: 2026-04-15T00:00:00-05:00
tldr: "v1.0 NLP desktop app feature-complete; 250 tests passing; 82K-row dataset validated end-to-end. Warriner VAD + Empath dictionaries shipped. Sign-and-publish gated on YubiKey delivery; T-Lex dictionaries and benchmark corpus are the in-parallel pre-publish work. Hard deadline 2026-05-31."
priority: high
related: [LLC-005-CRYPTO]
next_action_oneline: "Finish T-Lex dictionaries + benchmark corpus in parallel with YubiKey wait so sign + Gumroad publish on arrival is single-day work."
blockers: "YubiKey delivery (cert validated but not issued). Pre-YubiKey work can proceed on v1.0 content."
last_session: 2026-04-15T00:00:00-05:00
last_session_handoff: meta/handoffs/session/2026-04-15-00-00-LLC-BIZ.md
---

# TASS — Status

id: LLC-001
status: active
next_action: 82K dataset validated; progress bar, new dictionaries (Warriner VAD, Empath), and custom dictionary build all confirmed working. Pre-YubiKey prep: finish v1.0 remaining work (T-Lex dictionaries, benchmark corpus) in parallel with the wait. On YubiKey arrival: sign installer, Gumroad publish. Day 5-7 of the LLC rollout. Deadline May 31, 2026.
blockers: YubiKey delivery (cert validated but not issued). Pre-YubiKey work can proceed on v1.0 content.
last_session: 2026-04-15T00:00:00
last_session_handoff: meta/handoffs/session/2026-04-15-00-00-LLC-BIZ.md

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
