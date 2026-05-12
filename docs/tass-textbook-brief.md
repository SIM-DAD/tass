# TASS Companion Textbook — Project Brief

**Prepared by:** Alex P. Leith
**Date:** April 12, 2026
**For:** Editorial assistants — use this to scope and outline a companion textbook for TASS

---

## What is TASS?

TASS (Text Analysis for Social Scientists) is a no-code Windows desktop application for dictionary-based text analysis. It replaces the workflow of exporting text to LIWC/Diction, running stats in SPSS, and building charts in Excel — doing all three in a single application with no programming required.

**Target users:** Social science researchers, graduate students, journalists, and communication professionals who work with open-ended text data (survey responses, social media posts, interview transcripts, news articles) but have no Python/R background.

**Publisher:** SIM DAD LLC
**Pricing:** Subscription via Gumroad — Academic ($79/yr), Professional ($129/yr), Lab ($249/yr), Department ($699/yr). 30-day free trial with 500-row limit.
**Website:** usetass.app

---

## What TASS Does (Feature Set)

### Import
- CSV, XLSX, XLS, TXT file import
- Drag-and-drop or file browser
- Column mapping wizard (text column, group variable, metadata columns)
- Data preview with row/column counts

### Analyze
- Dictionary-based text scoring against built-in and user-imported word lists
- Four scoring modes: binary (percentage), count, weighted, TF-IDF
- N-gram matching (multi-word phrases like "climate change")
- Configurable preprocessing: tokenization, stopword removal, lemmatization

### Built-in Dictionaries
- **AFINN-165** — sentiment (positive/negative valence scores)
- **VADER Lexicon** — sentiment (positive, negative, compound)
- **Moral Foundations Dictionary 2.0** — care, fairness, loyalty, authority, sanctity (virtue/vice)
- **Concreteness Ratings** — word concreteness on a 1-5 scale
- **WordNet POS Categories** — noun, verb, adjective, adverb classification
- **NLTK Function Words** — pronouns, prepositions, articles, conjunctions
- **Optional downloads (CC-BY-SA):** HurtLex (offensive language), SentiWordNet (synset sentiment)

### Compare
- Between-subjects group comparisons on any scored category
- Welch's t-test (2 groups) or one-way ANOVA (3+ groups) — parametric
- Mann-Whitney U (2 groups) or Kruskal-Wallis H (3+ groups) — non-parametric
- Automatic assumption checks: Shapiro-Wilk normality, Levene's equal variance
- Post-hoc tests: Tukey HSD (after ANOVA), Dunn's test (after Kruskal-Wallis)
- Effect sizes: Cohen's d, eta-squared, rank-biserial correlation
- Multiple comparison correction: Bonferroni (default), Benjamini-Hochberg FDR
- Full APA-formatted output with interpretive notes

### Visualize
- Bar chart (mean category scores)
- Word cloud (matched word frequencies)
- Box plot (score distributions by group)
- Violin plot (richer distributions)
- Scatter plot (correlation between two categories, with regression line)
- Heatmap (score matrix across categories)
- Export as PNG or SVG

### Export
- Results to Excel (.xlsx) or CSV
- APA-formatted tables
- Citation dialog (APA, MLA, Chicago — pre-formatted)

### Results Panels
- Entry-level score table (every row scored across all dictionaries)
- Word matches (which words matched which categories per entry)
- Correlation matrix (Pearson or Spearman across all categories)
- Coverage statistics (what percentage of entries had matches)
- KWIC concordance (keyword in context — see matched words in surrounding text)
- Analysis log (reproducibility record of every analysis run)

---

## Statistical Foundation

Every statistical method in TASS comes from established, peer-reviewed open-source libraries. No proprietary or custom algorithms. Full documentation is in the app (Help > Statistical Methods) and at usetass.app/methods.

**Core libraries:** SciPy, NumPy, pandas, NLTK, matplotlib, seaborn

**Key references the textbook should cite:**
- Welch (1947) — t-test without equal variance assumption
- Shapiro & Wilk (1965) — normality testing
- Cohen (1988) — effect size benchmarks
- Benjamini & Hochberg (1995) — false discovery rate
- Salton & Buckley (1988) — TF-IDF
- Delacre et al. (2017) — why Welch's t-test should be the default

The full reference list (11 methods papers + 4 software citations) is available in `docs/statistical-methods.md`.

---

## Textbook Vision

### Format
- **Name-your-own-price** via Gumroad (companion to the software, not a separate revenue stream)
- **Primary goal:** Lower the barrier to adoption. Researchers who read the book should feel confident purchasing and using TASS.
- **Secondary goal:** Serve as a standalone methods resource for dictionary-based text analysis, even for readers who don't use TASS.

### Suggested Structure

**Part I — Foundations**
1. What is dictionary-based text analysis? (vs. topic modeling, ML classifiers, manual coding)
2. When to use it: research questions suited to dictionary methods
3. Preparing text data: formats, cleaning, what "preprocessing" means and when it matters
4. Dictionaries: what they are, how they're built, how to evaluate them

**Part II — Working with TASS**
5. Installation and first launch
6. Importing data: CSV/XLSX workflows, column mapping, common pitfalls
7. Choosing and configuring dictionaries
8. Scoring modes: percentage vs. count vs. weighted vs. TF-IDF — when to use each
9. Reading your results: entry scores, word matches, coverage, KWIC

**Part III — Statistical Analysis**
10. Descriptive statistics and confidence intervals — what they tell you
11. Group comparisons: t-tests, ANOVA, and their non-parametric alternatives
12. Assumption checking: normality, equal variance, what to do when assumptions fail
13. Effect sizes: why p-values aren't enough
14. Multiple comparisons: the problem, Bonferroni, FDR, and when each matters
15. Correlations and scatter plots

**Part IV — From Analysis to Publication**
16. Exporting results: APA tables, charts, reproducibility logs
17. Writing a methods section that references TASS
18. Visualizations: choosing the right chart, publication-ready formatting
19. Common mistakes and how to avoid them

**Part V — Advanced Topics**
20. Building custom dictionaries
21. Multi-dictionary analysis strategies
22. Working with large datasets
23. Integrating TASS results with R or SPSS for advanced modeling

### Appendices
- A: Complete list of built-in dictionaries with category definitions
- B: Statistical methods reference (mirrors the in-app documentation)
- C: Sample datasets and walk-through exercises
- D: Glossary of terms

---

## Audience Notes

- **Primary:** Graduate students in communication, sociology, psychology, political science who are taking methods courses. They have SPSS exposure but not R/Python.
- **Secondary:** Faculty adopting TASS for courses (the textbook becomes the course packet supplement).
- **Tertiary:** Journalists and nonprofit researchers doing content analysis.

The tone should be accessible but not patronizing. Assume the reader understands what a p-value is but may not remember when to use Kruskal-Wallis vs. ANOVA.

---

## Assets Available

- Full statistical methods documentation: `docs/statistical-methods.md`
- Capability document: `TASS-CAPABILITIES.md`
- Screenshot-ready app (v1.0.0 built and tested)
- Sample datasets used in testing (Spotify playlist corpus — 500 entries, genre groups, sentiment scores)
- In-app help content (28 articles across 6 sections)

---

## Next Steps for Assistants

1. Review this brief and the statistical methods doc
2. Draft a detailed chapter outline (working titles + 2-3 bullet points per chapter)
3. Identify which chapters need original sample datasets or exercises
4. Flag any gaps — topics the textbook should cover that aren't in the current feature set
5. Propose a timeline for first draft (target: alongside TASS launch, or shortly after)
