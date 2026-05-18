---
type: status
status: active
zone: llc
last_modified: 2026-05-18T06:30:00-05:00
tldr: "v1.0 NLP desktop app feature-complete; 250 tests passing; 82K-row dataset validated end-to-end. Warriner VAD + Empath dictionaries shipped. Sign-and-publish gated on YubiKey delivery; T-Lex dictionaries and benchmark corpus are the in-parallel pre-publish work. **Soft launch 5/22 CANCELLED 2026-05-18 06:30 — pushed to 5/31 to clear the LLC-003 Lector 5/22 slip collision** (owner decision). Single launch 5/31 (was hard launch). Both 5/22 collisions resolved."
priority: high
related: [LLC-005-CRYPTO]
next_action_oneline: "Run TASS installer through PERS-011 clean-VM rig (same rig that caught two Lector Tier-0s) before the 5/31 launch — verify cleanly on a baseline Win11."
blockers: "YubiKey delivery (cert validated but not issued). Pre-YubiKey work can proceed on v1.0 content. Soft launch 5/22 cancelled; single launch 5/31."
last_session: 2026-05-18T06:30:00-05:00
last_session_handoff: meta/handoffs/session/2026-05-18-06-09-LLC-003.md
---

# TASS — Status

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
