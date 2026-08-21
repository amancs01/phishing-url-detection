# Domain Generalization Analysis

## Purpose

This report tests whether the high URL-only PhiUSIIL performance survives a
registrable-domain-disjoint train/validation/test split. It evaluates the
fixed Decision Tree on Tier D-matched and Tier E only, using local feature
matrices and a saved offline split. It does not download, open, resolve, or
contact any URL.

## Registrable Domain Definition

A registrable domain is the effective top-level-domain-plus-one grouping
derived from the URL hostname with the local `publicsuffix2` parser. For
example, subdomains under the same privately registrable parent are assigned to
one group before splitting. IP literals are grouped as stable `ip:<address>`
values, and unparseable values would be grouped under `unknown`.

The parser uses the Public Suffix List bundled with the installed
`publicsuffix2` package. It does not fetch or update suffix data at runtime, so
future PSL snapshots could assign a small number of edge-case hostnames
differently.

## Why This Split Is Stricter Than A Row Split

The earlier benchmark experiment used deterministic row-level train,
validation, and test partitions. That is a standard IID benchmark setting, but
it can be less stringent for URLs because multiple rows can share a
registrable domain or near-duplicate URL patterns across partitions. A model
may then benefit from domain-family regularities that are unavailable when the
entire domain group is withheld.

This is not evidence of leakage by itself. The safer interpretation is that a
row-level split and a registrable-domain-disjoint split answer different
questions. The random split estimates benchmark IID performance; the
domain-disjoint split estimates generalization to registrable domains not seen
during training.

## Method

- Dataset rows: 235,795
- Label convention: `0 = phishing`, `1 = legitimate`
- Phishing precision, recall, and F1 treat class `0` as the positive class
- Total unique registrable domains: 194,036
- Split seed: 42
- Split method: deterministic greedy allocation of whole registrable-domain
  groups to 70/15/15 row and class-count targets
- Test data used for model selection: no
- Evaluated tiers: D-matched and E
- Fixed model: Decision Tree with `criterion='entropy'`, `max_depth=10`,
  `min_samples_leaf=1`, `min_samples_split=2`, `ccp_alpha=0.0`, and
  `random_state=42`
- Confidence intervals: 1,000 percentile bootstrap samples over test
  prediction rows; models are not retrained during bootstrap resampling

## Split Diagnostics

| Split | Rows | Unique registrable domains | Phishing rows | Legitimate rows |
| --- | ---: | ---: | ---: | ---: |
| Train | 165,057 | 154,811 | 70,661 | 94,396 |
| Validation | 35,369 | 19,613 | 15,142 | 20,227 |
| Test | 35,369 | 19,612 | 15,142 | 20,227 |

Registrable-domain overlap counts:

| Intersection | Shared domains |
| --- | ---: |
| Train vs validation | 0 |
| Train vs test | 0 |
| Validation vs test | 0 |

Unknown or unparseable domain-group rows: 0

Duplicate and domain-group diagnostics:

| Diagnostic | Value |
| --- | ---: |
| Exact duplicate raw URL values | 425 |
| Rows with exact duplicate raw URL | 850 |
| Normalized stripped/lower duplicate URL values | 425 |
| Rows with normalized stripped/lower duplicate URL | 850 |
| Domains with multiple URLs | 7,141 |
| Median URLs per domain | 1.0 |

The ten largest registrable-domain groups contain 3,097, 1,559, 1,199, 928,
872, 782, 781, 567, 555, and 494 rows respectively. Each of these largest
groups is entirely phishing in the local dataset. Domain names are intentionally
not written to the committed summary.

## Random Split Baseline

These are the earlier fixed-tree random-split test results for the same
deployment-oriented URL-only tiers.

| Tier | Test accuracy | Phishing recall | Phishing F1 | Depth | Leaves | Confusion matrix |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| D-matched | 0.994430 | 0.988113 | 0.993460 | 10 | 152 | `[[14962, 180], [17, 20211]]` |
| E | 0.995731 | 0.990622 | 0.994992 | 10 | 72 | `[[15000, 142], [9, 20219]]` |

False negatives under the random split were 180 for Tier D-matched and 142 for
Tier E.

## Domain-Disjoint Results

| Tier | Test accuracy | Phishing precision | Phishing recall | Phishing F1 | ROC-AUC | Depth | Leaves | Confusion matrix |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| D-matched | 0.997031 | 0.996107 | 0.996962 | 0.996534 | 0.998897 | 10 | 147 | `[[15096, 46], [59, 20168]]` |
| E | 0.996890 | 0.998078 | 0.994651 | 0.996361 | 0.998225 | 10 | 80 | `[[15061, 81], [29, 20198]]` |

False negatives under the domain-disjoint split were 46 for Tier D-matched and
81 for Tier E.

## Bootstrap Confidence Intervals

| Tier | Metric | Observed | 95% CI |
| --- | --- | ---: | --- |
| D-matched | Accuracy | 0.997031 | [0.996494, 0.997597] |
| D-matched | Phishing recall | 0.996962 | [0.996093, 0.997774] |
| D-matched | Phishing F1 | 0.996534 | [0.995890, 0.997171] |
| E | Accuracy | 0.996890 | [0.996296, 0.997427] |
| E | Phishing recall | 0.994651 | [0.993474, 0.995774] |
| E | Phishing F1 | 0.996361 | [0.995688, 0.997085] |

## Random Versus Domain-Disjoint Gaps

Positive values mean the domain-disjoint result is higher than the earlier
random-split result.

| Tier | Metric | Random split | Domain-disjoint | Gap |
| --- | --- | ---: | ---: | ---: |
| D-matched | Test accuracy | 0.994430 | 0.997031 | +0.260 pp |
| D-matched | Phishing recall | 0.988113 | 0.996962 | +0.885 pp |
| D-matched | Phishing F1 | 0.993460 | 0.996534 | +0.307 pp |
| E | Test accuracy | 0.995731 | 0.996890 | +0.116 pp |
| E | Phishing recall | 0.990622 | 0.994651 | +0.403 pp |
| E | Phishing F1 | 0.994992 | 0.996361 | +0.137 pp |

## Interpretation

The high URL-only performance survives the registrable-domain-disjoint split
in this local PhiUSIIL experiment. More surprisingly, the domain-disjoint
scores are slightly higher than the earlier row-level random-split scores for
both evaluated URL-only tiers. Tier D-matched phishing F1 increased from
0.993460 to 0.996534, while Tier E phishing F1 increased from 0.994992 to
0.996361.

This result argues against a simple explanation that the earlier URL-only
performance was mainly caused by repeated registrable domains crossing the
random split. If domain reuse were the dominant driver, withholding entire
registrable domains would be expected to reduce performance, especially recall.
Instead, phishing false negatives fell from 180 to 46 for Tier D-matched and
from 142 to 81 for Tier E.

The result still does not prove real-world robustness. The split removes
registrable-domain overlap inside PhiUSIIL, but it remains an in-dataset
evaluation with the same collection process, labeling conventions, feature
space, and time period. The strongest scientific conclusion is narrower:
within PhiUSIIL, the tested URL-only feature representations generalize well to
unseen registrable domains under the fixed Decision Tree protocol.

The larger concern raised by the Tier A analysis remains separate. Perfect
Tier A benchmark performance is driven primarily by `URLSimilarityIndex`, a
reference-dependent supplied feature, and also uses the webpage-derived
`LineOfCode`. The domain-disjoint experiment here focuses on D-matched and E,
which are the safer URL-only deployment conditions.

## Practical Conclusion

For a no-contact phishing URL detector, Tier E remains a practical deployment
condition, and Tier D-matched remains the fair reconstruction-oriented
comparison. Both retain very high test F1 and recall when train, validation,
and test are separated by registrable domain.

The surprising finding is that domain-disjoint evaluation did not expose a
generalization collapse. Instead, the stricter split produced modestly better
test metrics, likely because the greedy grouped split created an easier or more
representative held-out domain mix than the earlier random partition. That
possibility is a sampling-design caveat, not a reason to discard the result.

## Safety Statement

All URL handling in this analysis is offline text parsing. No dataset URL was
opened, requested, resolved, pinged, scraped, or otherwise contacted.
