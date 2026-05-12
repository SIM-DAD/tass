# TASS — Statistical Methods

> **Version 1.0.0** | Last updated: April 2026
>
> TASS implements standard statistical methods from peer-reviewed literature using established open-source libraries. **No custom or proprietary statistical algorithms are used.** Every test, effect size, and correction traces directly to SciPy, NumPy, pandas, or NLTK.

---

## Core Libraries

| Library | Min Version | Role |
|---------|-------------|------|
| SciPy | >= 1.11 | Hypothesis tests, effect sizes, confidence intervals, regression |
| NumPy | >= 1.24 | Descriptive statistics, array operations |
| pandas | >= 2.0 | Data handling, correlation matrices |
| NLTK | >= 3.8 | Tokenization, stopwords, lemmatization |
| matplotlib / seaborn | >= 3.7 / >= 0.12 | Visualization |

---

## Text Scoring

TASS scores text entries by matching tokens against dictionary word lists.

### Binary (Percentage) Scoring

```
score = (matched_tokens / total_tokens) × 100
```

The proportion of tokens matching a dictionary category, expressed as a percentage. This is the default and most interpretable mode for social science applications.

### Count Scoring

```
score = count(matched_tokens)
```

Raw count of dictionary matches per entry.

### Weighted Scoring

```
score = Σ weight(token) for all matched tokens
```

Sum of pre-assigned weights from the dictionary (e.g., AFINN sentiment values).

### TF-IDF Scoring

```
score = Σ TF(t) × IDF(t)
```

Where:
- **TF(t)** = count(t) / n_tokens — term frequency within the entry
- **IDF(t)** = ln(N / (1 + DF(t))) — inverse document frequency with add-one smoothing

IDF weighting down-weights terms that appear in many entries. The natural logarithm and add-one smoothing are standard choices (Salton & Buckley, 1988).

### N-gram Matching

When dictionaries contain multi-word phrases (e.g., "climate change"), TASS generates n-grams up to the maximum phrase length in the dictionary. Unigrams consumed by a matched n-gram are suppressed to prevent double-counting.

---

## Text Preprocessing

All preprocessing steps are configurable per analysis:

| Step | Default | Implementation |
|------|---------|---------------|
| Lowercasing | On | Python `str.lower()` |
| Punctuation removal | On | `str.translate()` with `string.punctuation` |
| Whitespace normalization | On | Regex `\s+` → single space |
| Tokenization | On | `nltk.word_tokenize()` (Penn Treebank tokenizer) |
| Stopword removal | Off | NLTK English stopword list (179 words) |
| Lemmatization | Off | `nltk.WordNetLemmatizer` (WordNet 3.1) |
| Minimum token length | 1 | Tokens shorter than threshold are discarded |

Stopword removal and lemmatization are off by default because many dictionary-based analyses rely on exact word forms.

---

## Descriptive Statistics

| Statistic | Implementation | Notes |
|-----------|---------------|-------|
| Mean (M) | `numpy.mean()` | Arithmetic mean |
| Standard deviation (SD) | `numpy.std(ddof=1)` | Sample SD with Bessel's correction (N−1) |
| Standard error (SE) | `scipy.stats.sem()` | SE = SD / √N |
| Median | `numpy.median()` | |
| Min / Max | `numpy.min()`, `numpy.max()` | |
| 95% Confidence interval | `scipy.stats.t.ppf()` | t-distribution with df = N−1. Requires N ≥ 2. |

---

## Hypothesis Tests

### Two-Group Comparisons

| Test | Implementation | When Used |
|------|---------------|-----------|
| Welch's t-test | `scipy.stats.ttest_ind(equal_var=False)` | Default for 2 groups |
| Mann-Whitney U | `scipy.stats.mannwhitneyu(alternative="two-sided")` | Non-parametric option (user-selected) |

Welch's t-test is the default because it is robust to unequal variances and unequal sample sizes, which are common in social science datasets (Delacre et al., 2017).

### Multi-Group Comparisons (3+ groups)

| Test | Implementation | When Used |
|------|---------------|-----------|
| One-way ANOVA | `scipy.stats.f_oneway()` | Default for 3+ groups |
| Kruskal-Wallis H | `scipy.stats.kruskal()` | Non-parametric option (user-selected) |

### Post-Hoc Pairwise Comparisons

Post-hoc tests run automatically when the omnibus test is significant (p < α):

| After... | Post-Hoc Test | Implementation |
|----------|--------------|---------------|
| Significant ANOVA | Tukey HSD | `scipy.stats.tukey_hsd()` |
| Significant Kruskal-Wallis | Dunn's test | Pairwise Mann-Whitney U with Bonferroni correction |

If `tukey_hsd` is unavailable (SciPy < 1.8), TASS falls back to pairwise t-tests with Bonferroni correction.

---

## Assumption Checks

TASS automatically tests assumptions before running group comparisons:

### Normality: Shapiro-Wilk Test

`scipy.stats.shapiro()` — run per group, per category.

- p ≥ .05 → normality assumed
- p < .05 → normality violated (W statistic and p-value reported)
- Requires N ≥ 3 per group

### Equal Variance: Levene's Test

`scipy.stats.levene()` — run across all groups, per category.

- p ≥ .05 → equal variances assumed
- p < .05 → unequal variances (F statistic and p-value reported)
- Requires ≥ 2 groups with N ≥ 2 each

TASS reports assumption violations but does not automatically switch tests. The user selects parametric or non-parametric tests, keeping the researcher in control of analytical decisions.

---

## Effect Sizes

| Test | Effect Size | Formula | Benchmarks |
|------|------------|---------|------------|
| Welch's t-test | Cohen's d | d = (M₁ − M₂) / SD_pooled | Small: 0.2, Medium: 0.5, Large: 0.8 |
| Mann-Whitney U | Rank-biserial r | r = 1 − (2U / n₁n₂) | Small: 0.1, Medium: 0.3, Large: 0.5 |
| One-way ANOVA | η² (eta-squared) | η² = SS_between / SS_total | Small: .01, Medium: .06, Large: .14 |
| Kruskal-Wallis H | η²_H | η²_H = (H − k + 1) / (N − k) | Same benchmarks as η² |

The pooled standard deviation for Cohen's d uses the sample variance formula (ddof=1), consistent with Bessel's correction.

η²_H for Kruskal-Wallis follows the formula from Tomczak & Tomczak (2014), which adjusts for the number of groups (k) and total sample size (N).

---

## Multiple Comparison Corrections

### Bonferroni Correction (Default)

```
α_adj = α / m
```

Where m = number of categories tested. Controls the **family-wise error rate** (FWER). Conservative but reliable.

### Benjamini-Hochberg FDR (Optional)

1. Rank all p-values in ascending order (p_(1) ≤ p_(2) ≤ ... ≤ p_(m))
2. For each rank i: p_adj = p_(i) × m / i
3. Enforce monotonicity: p_adj(i) = min(p_adj(i), p_adj(i+1))
4. Cap at 1.0

Controls the **false discovery rate** (FDR). Less conservative than Bonferroni; appropriate when exploring many categories simultaneously (Benjamini & Hochberg, 1995).

### Post-Hoc Corrections

Post-hoc pairwise comparisons use Bonferroni correction: `p_adj = min(p × n_pairs, 1.0)`

---

## Correlation Analysis

| Method | Implementation | When to Use |
|--------|---------------|-------------|
| Pearson r | `scipy.stats.pearsonr()` | Linear relationships, interval/ratio data |
| Spearman ρ | `scipy.stats.spearmanr()` | Monotonic relationships, ordinal data |

Correlation matrices are computed via `pandas.DataFrame.corr()`. Individual p-values are computed via the SciPy functions above, requiring N ≥ 3.

The scatter plot visualization includes an OLS regression line computed via `scipy.stats.linregress()`, which reports the Pearson r and p-value on the chart.

---

## Default Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Significance threshold (α) | 0.05 | Standard in social science research |
| Confidence level | 95% | Corresponds to α = .05 |
| Multiple comparisons | Bonferroni (default) | Family-wise error control |
| Variance assumption | Welch's (unequal) | More robust for social science data |
| Standard deviation | Sample (ddof=1) | Bessel's correction |
| Min N for normality test | 3 | Shapiro-Wilk requirement |
| Min N for correlation | 3 | Minimum for meaningful computation |
| TF-IDF smoothing | Add-one (1) | Standard IDF smoothing |

---

## References

### Statistical Methods

- Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate: A practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society: Series B*, 57(1), 289–300.
- Cohen, J. (1988). *Statistical power analysis for the behavioral sciences* (2nd ed.). Lawrence Erlbaum.
- Delacre, M., Lakens, D., & Leys, C. (2017). Why psychologists should by default use Welch's t-test instead of Student's t-test. *International Review of Social Psychology*, 30(1), 92–101.
- Dunn, O. J. (1964). Multiple comparisons using rank sums. *Technometrics*, 6(3), 241–252.
- Kruskal, W. H., & Wallis, W. A. (1952). Use of ranks in one-criterion variance analysis. *Journal of the American Statistical Association*, 47(260), 583–621.
- Levene, H. (1960). Robust tests for equality of variances. In I. Olkin (Ed.), *Contributions to probability and statistics* (pp. 278–292). Stanford University Press.
- Salton, G., & Buckley, C. (1988). Term-weighting approaches in automatic text retrieval. *Information Processing & Management*, 24(5), 513–523.
- Shapiro, S. S., & Wilk, M. B. (1965). An analysis of variance test for normality (complete samples). *Biometrika*, 52(3–4), 591–611.
- Tomczak, M., & Tomczak, E. (2014). The need to report effect size estimates revisited. *Trends in Sport Sciences*, 21(1), 19–25.
- Tukey, J. W. (1949). Comparing individual means in the analysis of variance. *Biometrics*, 5(2), 99–114.
- Welch, B. L. (1947). The generalization of Student's problem when several different population variances are involved. *Biometrika*, 34(1–2), 28–35.

### Software Libraries

- Virtanen, P., et al. (2020). SciPy 1.0: Fundamental algorithms for scientific computing in Python. *Nature Methods*, 17, 261–272.
- Harris, C. R., et al. (2020). Array programming with NumPy. *Nature*, 585, 357–362.
- Bird, S., Klein, E., & Loper, E. (2009). *Natural language processing with Python*. O'Reilly Media.
- McKinney, W. (2010). Data structures for statistical computing in Python. *Proceedings of the 9th Python in Science Conference*, 56–61.
