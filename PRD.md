# TASS: Text Analysis for Social Scientists
## Product Requirements Document v0.1
**Prepared:** March 2026
**Owner:** SIM DAD LLC
**Status:** Draft

---

## 1. Executive Summary

TASS is a native Windows desktop application that makes professional-grade NLP analysis accessible to social science researchers, humanities scholars, and data journalists who cannot or do not want to write code. It combines dictionary-based text analysis, group-level statistical comparisons, and publication-quality visualizations in a clean, minimal GUI — with no Python, R, or terminal required.

TASS directly challenges LIWC's market dominance by offering:
- Superior large-dataset performance (LIWC notoriously fails above ~10k entries)
- A transparent, open-source dictionary ecosystem (no black-box scoring)
- Multi-level analysis (word, entry, document)
- Built-in group statistical comparisons
- Publication-ready visualizations and auto-generated citations
- Annual pricing of $49/year (~$4/month) vs. LIWC's $89+/year

---

## 2. Product Vision

**Tagline:** Text Analysis for Social Scientists
**Full Name:** TASS
**License:** Source-available (Business Source License or similar — publicly readable on GitHub, not commercially reusable without permission)
**Primary Platform:** Windows 10/11 (64-bit)
**Future Platforms:** Linux (v1.1+), macOS (v2.0+)

---

## 3. Target Users

### Primary Persona: The Non-Coding Researcher
- Social scientist (communication, psychology, political science, sociology, marketing)
- PhD or graduate student level; familiar with research methodology, unfamiliar with NLP code
- Regularly collects text data (surveys, social media, interview transcripts, public statements)
- Needs publishable, citable results with clean exports
- Pain point: LIWC is expensive, opaque, and chokes on large datasets

### Secondary Persona: The Data Journalist
- Works at a news organization or independently
- Needs to analyze statements, articles, or social media at scale
- No coding background; deadline-driven
- Needs clean visual outputs that can go directly into stories or reports

---

## 4. Feature Requirements by Release

---

### v1.0 — Summer Launch (Target: May 31, 2026)

#### 4.1 Data Import
- Supported formats: `.csv`, `.txt`, `.xlsx`
- Batch import: multiple files can be loaded into a single session
- Column mapping wizard:
  - User selects which column contains the text to analyze
  - All other columns are available as grouping or metadata variables
  - Column types auto-detected (text, numeric, categorical); user can override
- Data preview: read-only tabular view of imported data before analysis; no in-app editing
- Row validation: alert user if rows exceed trial limit (500 rows); otherwise no hard cap

#### 4.2 Analysis Engine
- Dictionary-based analysis using all bundled dictionaries (see Section 6)
- Analysis levels:
  1. **Word-level:** which specific words matched each dictionary category (highlighted)
  2. **Entry-level:** score per row (per tweet, per survey response, per paragraph)
  3. **Document-level:** aggregate scores across the full dataset
- Multi-threaded processing: distribute analysis across all available CPU cores via Python `concurrent.futures`
- Real-time progress panel: shows entries processed / total, estimated time remaining, current operation
- Users can select which dictionaries to include before running analysis

#### 4.3 Group Comparisons
- Users define groups by selecting a column and specifying which values represent each group
- Minimum 2 groups; no hard maximum
- Statistics computed per group, per dictionary category:
  - Descriptive: mean, standard deviation, min, max, median
  - Significance: independent-samples t-test (2 groups), one-way ANOVA (3+ groups), Mann-Whitney U (non-parametric option)
  - Effect size: Cohen's d (2 groups), eta-squared (ANOVA)
- Visualizations: box plots and violin plots per category per group (ggplot-style aesthetics)

#### 4.4 Output & Export
- **CSV:** full entry-level scores, one row per text entry, one column per dictionary category
- **Excel (.xlsx):** multi-sheet workbook — Sheet 1: raw scores, Sheet 2: summary statistics, Sheet 3: group comparison results
- **Static visualizations:** exported as high-resolution PNG (300 DPI) and SVG
  - Bar charts: mean category scores (single dataset or per group)
  - Word clouds: top matched words, colored by category
  - Box plots / violin plots: group comparisons per category
  - Heatmaps: category scores across groups or across document segments
- All exports include auto-generated TASS citation block (APA format + Zenodo DOI)

#### 4.5 Visualizations
- All visualizations are static and publication-quality (ggplot-inspired aesthetics: clean axes, minimal gridlines, readable fonts)
- Rendered using Matplotlib + Seaborn
- Word clouds rendered using the `wordcloud` Python library
- Charts displayed inline in the results panel before export
- User can select color palette (at least 3 options: default, colorblind-safe, grayscale)

#### 4.6 Saved Projects
- File format: `.tass` (a ZIP archive with internal structure — see Technical Spec)
- Contents: original imported data + analysis configuration + results + visualization settings + UI state
- Opening a `.tass` file restores the exact session state (active tab, column mappings, results, chart settings)
- Recent projects list shown on home/welcome screen
- Auto-save prompt when closing with unsaved changes

#### 4.7 Help System
- Tooltips on all major UI controls (hover to reveal)
- In-app searchable documentation panel (keyboard shortcut: F1)
- "How to Cite TASS" dialog accessible from Help menu (APA citation + Zenodo DOI auto-populated)
- Link to product website for extended documentation, tutorials, and FAQ

#### 4.8 Error Reporting
- Global exception handler catches all unhandled errors
- On crash or error: dialog prompts user — "An unexpected error occurred. Would you like to send a crash report to help improve TASS?" (Yes / No / Never ask again)
- Report contents: Python traceback, TASS version, OS version, hardware specs (CPU core count, RAM); no user data or text content ever included
- Report sent via SMTP to LLC support email address
- Follows industry standard: Sentry-style format but self-hosted via email for v1 (Sentry integration optional in v1.1)

---

### v1.1 — Fall Kickoff (Target: August 2026)

- **ML Models (bundled, offline):**
  - BERT-based sentiment classification (fine-tuned DistilBERT)
  - LDA topic modeling (scikit-learn, user sets number of topics)
  - Named entity recognition (spaCy en_core_web_sm)
- **Additional export formats:** PDF (formatted analysis report), JSON (full results object)
- **Custom dictionary import:**
  - Formats: TXT (one word per line), CSV (word, category, weight), XLSX, JSON
  - Modes: word/phrase list (default) or regex pattern (opt-in)
  - Validation and preview before import
  - Saved to user's personal dictionary library within the app
- **Interactive dashboards:** Plotly-based charts embedded in an in-app browser panel (WebEngineView); allows hover, filter, zoom
- **Freshdesk integration:** Support ticket button in Help menu (opens Freshdesk widget)
- **Auto-update system:** check GitHub Releases API on startup, background download, user notified on next launch with changelog summary, applies on restart
- **Linux support:** build and test on Ubuntu 22.04 LTS

---

### v2.0 — Post-Sabbatical (Target: Spring 2027+)

- LLM integration hooks (user provides their own API key: Claude, OpenAI, or local Ollama)
  - Auto-summarize analysis results
  - Generate natural-language interpretation of category scores
  - Built on LLM-ready export formats established in v1.0
- Cloud-assisted processing option for very large corpora (>500k entries)
- Spanish NLP: Spanish-language dictionaries + multilingual tokenization
- Additional ML: zero-shot text classification, document similarity, readability scores
- SQL connector: query databases directly (SQLite, PostgreSQL)
- API data connectors: Reddit, news APIs

---

## 5. Non-Functional Requirements

| Requirement | Specification |
|---|---|
| Minimum hardware | 4-core CPU, 8GB RAM, Windows 10/11 64-bit, 3GB free disk |
| Recommended hardware | 6-core CPU, 16GB RAM |
| Dataset performance | 10,000-entry dataset analyzed in <60 seconds on minimum spec |
| Large dataset support | Tested and stable to 500,000 entries via chunked processing |
| Offline operation | All analysis runs 100% locally; internet only for license activation and update checks |
| Installer size | ~1.5–2GB (Python runtime + bundled dictionaries + future ML model weights) |
| Accessibility | High-contrast mode support; full keyboard navigation for all core functions |
| Privacy | No user text data ever sent externally; error reports require explicit user consent |
| Code signing | Windows installer signed with OV code signing certificate (~$200 one-time) to prevent "Unknown Publisher" warnings |

---

## 6. Built-In Dictionary Inventory (v1.0)

> **Policy:** Only dictionaries with verified commercial-use-compatible licenses (MIT, CC-BY, CC-BY-SA, Apache 2.0, or equivalent) are included in TASS. Dictionaries designated "free for research only" are excluded. All bundled dictionaries are included with full attribution per their license terms and documented in the in-app Help panel.

### 6a. Confirmed Commercially-Licensed Dictionaries (Adopt As-Is)

8 third-party dictionaries with verified commercial-use-compatible licenses. No contact or negotiation required.

| Dictionary | Categories Covered | License | Citation |
|---|---|---|---|
| AFINN-165 | Sentiment valence (scored -5 to +5) | MIT | Nielsen (2011) |
| VADER Lexicon | Sentiment valence + intensity (positive, negative, neutral, compound) | MIT | Hutto & Gilbert (2014) |
| Moral Foundations Dictionary 2.0 | Care, Fairness, Loyalty, Authority, Purity (virtue + vice) | CC-BY | Frimer et al. (2019) |
| Brysbaert Concreteness Norms | Concreteness ratings for ~40k English words | CC-BY | Brysbaert et al. (2014) |
| HurtLex | Hurtful/offensive language by category (slurs, profanity, etc.) | CC-BY-SA | Bassignana et al. (2018) |
| WordNet 3.1 | Full English lexicon; part-of-speech categories (noun/verb/adj/adv) | Princeton WordNet License (commercial-compatible) | Fellbaum (1998) |
| NLTK Stopwords | Function words, pronouns, prepositions, articles, conjunctions | Apache 2.0 | NLTK Project |
| SentiWordNet 3.0 | Positive/negative/objective scores per WordNet synset | CC-BY-SA | Baccianella et al. (2010) |

> **Excluded third-party dictionaries:** NRC Emotion Lexicon, Opinion Lexicon (Hu & Liu), Warriner Affective Norms (CC BY-NC-ND — non-commercial restriction), MRC Psycholinguistic Database, General Inquirer, Loughran-McDonald Financial Lexicon, Agency & Communion (Pietraszkiewicz et al.) — all excluded due to non-commercial or research-only licensing. TASS-native equivalents are in development (Section 6b).

### 6b. TASS-Native Dictionaries (Must-Build — In Development)

18 dictionaries built from scratch using documented linguistic frameworks and published measurement scales. Fully owned by SIM DAD LLC, independently citable, and a sustained competitive moat. Organized below by release target, with build priority within each release.

#### Shipping with v1.1 — August 2026 (7 dictionaries)
These are built in parallel with v1.0 software development. Priority is set by (a) filling the most critical gaps left by excluded third-party resources, then (b) unlocking differentiating categories no competitor offers.

| Build Order | Dictionary | Target Categories | Rationale |
|---|---|---|---|
| 1 | TASS Affective Norms | Valence, arousal, dominance ratings for ~40k+ words | Immediate gap: Warriner excluded (non-commercial); affective norms expected in every psycholinguistic toolkit |
| 2 | TASS Discrete Emotions | Anger, fear, joy, sadness, anticipation, trust, surprise, disgust | Highest-demand gap: NRC Emotion Lexicon is the most-cited excluded resource |
| 3 | TASS Psychosocial Process Lexicon | Cognitive processes, social references, biological drives, perceptual processes, temporal orientation | Establishes LIWC feature parity; without this, TASS cannot claim to replace LIWC |
| 4 | TASS Opinion & Stance | Positive/negative evaluative language calibrated for social science text (not product reviews) | Complements v1.0 sentiment dictionaries; distinct from AFINN/VADER in register and domain |
| 5 | TASS Power & Status | Power gain/loss, political arenas, authority, dominance, submission language | Unique offering; no commercial equivalent of Lasswell categories exists |
| 6 | TASS Hedging & Epistemic Stance | Strong/weak modal verbs, approximators, epistemic verbs, evidentials, hedges, boosters | Primary methodological differentiator; no commercial standalone exists |
| 7 | TASS Modal Language | Deontic modals (obligation, permission), epistemic modals (certainty, possibility) | Naturally co-developed with Hedging; efficient to build together |

#### Shipping with v2.0 — Spring 2027 (11 dictionaries)
Built during sabbatical-adjacent period. Mix of completing the LIWC-displacement set and adding domain-specialist resources that expand TASS's addressable research communities.

| Build Order | Dictionary | Target Categories | Primary Audience |
|---|---|---|---|
| 8 | TASS Agency & Communion | Agentic language (competence, assertiveness, autonomy); communal language (warmth, cooperation, affiliation) | Social psychology, gender studies, leadership research |
| 9 | TASS Narrative & Temporal Orientation | Past/future focus, causal reasoning, narrative sequencing markers | Narrative research, computational humanities |
| 10 | TASS Collective Identity & Social Boundaries | In-group/out-group markers, solidarity language, othering vocabulary | Political communication, sociology, group dynamics |
| 11 | TASS Formality & Register | Formal vs. informal register markers | Sociolinguistics, computer-mediated communication |
| 12 | TASS Political & Ideological Language | Populist framing, partisan cues, threat rhetoric, democratic norms vocabulary | Political communication, political science |
| 13 | TASS Health & Illness Communication | Mental health stigma language, health literacy levels, illness narrative framing | Health communication, public health |
| 14 | TASS Deception & Trust Cues | Distancing language, verbal credibility signals, linguistic deception markers | Forensic linguistics, organizational communication |
| 15 | TASS Crisis & Uncertainty Language | Risk framing, ambiguity markers, domain-calibrated epistemic hedging | Risk communication, organizational research |
| 16 | TASS Financial & Economic Sentiment | Optimism, caution, urgency in financial and organizational communication | Organizational communication, economic sociology |
| 17 | TASS Academic & Scientific Register | Hedging in scientific writing, citation language, certainty/uncertainty claims | Science communication, academic writing research |
| 18 | TASS Interpersonal Dominance & Deference | Assertiveness, compliance, face-threatening acts in dyadic interaction | Social psychology, conversation analysis |

**Total library at full build-out:** 8 adopted (v1.0) + 7 TASS-native (v1.1) + 11 TASS-native (v2.0) = **26 dictionaries**

---

## 7. Monetization & Licensing

### Pricing Tiers
| Tier | Price | Seats | Notes |
|---|---|---|---|
| Individual | $49/year | 1 license, 2 machines | Standard researcher license |
| Small Team | $199/year | 5 seats | Lab or small research group |
| Department | $349/year | 10 seats | Departmental use |
| Trial | Free, 14 days | 1 machine | Email required; 500-row limit; full toolset |

### Trial Behavior
- Email address required at trial start (populates Lemon Squeezy mailing list)
- Full toolset available; row limit of 500 entries per analysis run
- On trial expiry: app enters view-only mode — existing projects can be opened and exported, but no new analyses can be run
- Upgrade prompt shown on launch and on any blocked action

### Payment Processing
- **Lemon Squeezy** handles: payment collection, license key generation, global tax/VAT compliance, customer portal, mailing list
- No custom payment backend required
- Lemon Squeezy webhook → Supabase edge function → license record created

### License Enforcement
- Online activation at first use: license key validated against Lemon Squeezy API
- Machine fingerprint (hashed hardware ID) registered in Supabase; max 2 machines per individual license
- After activation: encrypted local license cache; app works offline indefinitely until expiry
- On expiry: app checks Lemon Squeezy on next internet-connected launch; enters view-only if not renewed

### Update Policy
- Background update check on app launch (silent, non-blocking)
- GitHub Releases API used as update source
- If new version found: downloaded in background, user notified on next launch with changelog
- Applied on next restart (no forced restarts)

---

## 8. Citation System

Every TASS export includes the following citation block appended to the file or report:

```
To cite TASS in your research:

[Author Last Name, First Initial]. (2026). TASS: Text Analysis for Social Scientists
(Version 1.0) [Software]. SIM DAD LLC. https://doi.org/[ZENODO_DOI]
```

- Zenodo DOI obtained at v1.0 GitHub Release (free, auto-minted via Zenodo–GitHub integration)
- In-app "How to Cite" dialog (Help menu) shows citation in APA, MLA, and Chicago formats
- Citation includes version number; each major release gets its own Zenodo DOI

---

## 9. Distribution & Support

### Distribution
- Primary: GitHub Releases (versioned `.exe` installer built with Inno Setup)
- Product website: download page, trial signup landing page, documentation
- Future consideration: Microsoft Store (v1.1+)

### Support
- **Freshdesk** (free tier): support email auto-converts to tickets; response tracked
- In-app: "Contact Support" button in Help menu opens email client pre-populated with version info
- Product website: FAQ, documentation, changelog

### Error Reporting
- Opt-in crash reports emailed to LLC support address
- Format: TASS version, OS, CPU/RAM specs, Python traceback (no user content)

---

## 10. Release Roadmap Summary

| Release | Target Date | Key Theme |
|---|---|---|
| v1.0 | May 31, 2026 | Core tool — beats LIWC on performance, openness, and price |
| v1.1 | August 2026 | ML models, custom dictionaries, interactive dashboards, Linux |
| v2.0 | Spring 2027 | LLM integration, cloud processing, Spanish, SQL connectors |
