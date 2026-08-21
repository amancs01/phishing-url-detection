# Post-Hoc Diagnostic Analysis: External Generalization Failure Mechanism

## Purpose

This document synthesizes the post-hoc diagnostic evidence explaining why the
frozen PhiUSIIL-trained Tier E Decision Tree transfers poorly to URL-Phish
Version 2. It does not change the primary external result, retrain the model,
retune hyperparameters, modify thresholds, or alter feature definitions.

## Primary Evidence

The internal PhiUSIIL random-split Tier E result was very high: phishing F1
0.994992, phishing recall 0.990622, and ROC-AUC 0.997996.

The stricter PhiUSIIL registrable-domain-disjoint Tier E result also remained
very high: phishing F1 0.996361, phishing recall 0.994651, and ROC-AUC
0.998225.

The first external URL-Phish evaluation was sharply different:

| Metric | URL-Phish external |
| --- | ---: |
| Accuracy | 0.196509 |
| Phishing precision | 0.149206 |
| Phishing recall | 0.987590 |
| Phishing F1 | 0.259245 |
| ROC-AUC | 0.524568 |
| PR-AUC | 0.148627 |
| Balanced accuracy | 0.526390 |

The external confusion matrix was:

```text
[[16394, 206],
 [93481, 6519]]
```

The model missed only 206 of 16,600 phishing URLs, but it predicted phishing
for 93,481 of 100,000 benign URLs. It predicted phishing for 94.232% of all
URL-Phish rows, and external benign specificity was only 0.06519.

## Shift Terminology

- Prior or prevalence shift means `P(Y)` differs across datasets.
- Covariate shift means `P(X)` differs across datasets.
- Class-conditional shift means `P(X | Y)` differs across datasets.
- Concept shift means `P(Y | X)` differs across datasets.

The evidence already shows prevalence shift: URL-Phish has 16,600 phishing
rows and 100,000 benign rows. This batch adds strong evidence of
class-conditional covariate shift. It does not prove concept shift.

## Class-Conditional Feature Shift

The strongest feature-shift evidence is in the legitimate/benign class. The
mean top-10 KS statistic was 0.4305 for PhiUSIIL legitimate versus URL-Phish
benign, compared with 0.2076 for PhiUSIIL phishing versus URL-Phish phishing.

Top legitimate/benign shifts:

| Feature | KS statistic | PhiUSIIL legitimate mean | URL-Phish benign mean |
| --- | ---: | ---: | ---: |
| `path_length` | 0.889860 | 0.000000 | 4.604890 |
| `number_of_slashes` | 0.889860 | 2.000000 | 3.148250 |
| `uses_https_text` | 0.649070 | 1.000000 | 0.350930 |
| `special_character_count` | 0.618764 | 5.244865 | 6.670650 |
| `letter_ratio` | 0.420388 | 0.799957 | 0.754285 |

Top phishing/phishing shifts:

| Feature | KS statistic | PhiUSIIL phishing mean | URL-Phish phishing mean |
| --- | ---: | ---: | ---: |
| `uses_https_text` | 0.426983 | 0.487354 | 0.914337 |
| `path_length` | 0.321266 | 8.725256 | 17.153373 |
| `number_of_slashes` | 0.321257 | 3.019208 | 3.617289 |
| `number_of_subdomains` | 0.184028 | 1.156699 | 0.741988 |
| `number_of_dots` | 0.169284 | 2.384695 | 1.927289 |

HTTPS usage differs sharply:

| Comparison | PhiUSIIL proportion HTTPS | URL-Phish proportion HTTPS |
| --- | ---: | ---: |
| Legitimate vs benign | 1.000000 | 0.350930 |
| Phishing vs phishing | 0.487354 | 0.914337 |

Path length also differs strongly:

| Comparison | PhiUSIIL mean | URL-Phish mean | PhiUSIIL median | URL-Phish median |
| --- | ---: | ---: | ---: | ---: |
| Legitimate vs benign | 0.000000 | 4.604890 | 0.000000 | 1.000000 |
| Phishing vs phishing | 8.725256 | 17.153373 | 1.000000 | 6.000000 |

This supports class-conditional covariate shift, especially among benign URLs.

## Leaf-Routing Mechanism

Leaf routing shows how the feature shift translates into false positives. The
dominant false-positive leaf was leaf `136`, which received 88,986 URL-Phish
benign false positives. In PhiUSIIL training, this leaf received 51,406
samples, all phishing. Its complete path is:

```text
number_of_slashes > 2.500000
```

The next largest false-positive leaves were:

| Leaf | Training phishing proportion | External benign false positives | Path |
| ---: | ---: | ---: | --- |
| 136 | 1.000000 | 88,986 | `number_of_slashes > 2.500000` |
| 2 | 1.000000 | 3,056 | `number_of_slashes <= 2.500000 AND uses_https_text <= 0.500000` |
| 5 | 1.000000 | 1,406 | `number_of_slashes <= 2.500000 AND uses_https_text > 0.500000 AND url_length <= 46.500000 AND number_of_dots <= 1.500000` |

The top three leaves account for 93,448 of 93,481 external benign false
positives. This directly connects the benign feature shift to the tree's
internal routing behavior.

## Probability Distributions

The phishing-probability distributions show the same mechanism:

| Group | Mean | Median | q01 | q25 | q75 | q99 | P(prob >= 0.5) | P(prob = 1) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| PhiUSIIL legitimate | 0.006873 | 0.003936 | 0.001169 | 0.003088 | 0.003936 | 0.064618 | 0.000601 | 0.000022 |
| PhiUSIIL phishing | 0.990906 | 1.000000 | 0.712508 | 1.000000 | 1.000000 | 1.000000 | 0.990926 | 0.988410 |
| URL-Phish benign | 0.935245 | 1.000000 | 0.001169 | 1.000000 | 1.000000 | 1.000000 | 0.934810 | 0.934620 |
| URL-Phish phishing | 0.986813 | 1.000000 | 0.064618 | 1.000000 | 1.000000 | 1.000000 | 0.987590 | 0.982892 |

URL-Phish benign rows receive probabilities resembling PhiUSIIL phishing rows,
not PhiUSIIL legitimate rows.

## Dataset-Origin Separability

The dataset-origin experiment held phishing label constant and asked whether
source dataset could still be predicted from Tier E lexical features.

| Experiment | Origin accuracy | ROC-AUC | Top source-discriminating features |
| --- | ---: | ---: | --- |
| Benign-only origin | 0.967333 | 0.978597 | `number_of_slashes`, `uses_https_text`, `number_of_subdomains` |
| Phishing-only origin | 0.775502 | 0.853450 | `uses_https_text`, `number_of_subdomains`, `digit_ratio` |

The benign-only result is very strong. It demonstrates that PhiUSIIL
legitimate URLs and URL-Phish benign URLs are highly separable even before any
phishing decision is considered.

## Deduplication Sensitivity

Exact-URL deduplication found no conflicting duplicate labels. It reduced the
external set from 116,600 rows to 115,231 rows.

Deduplicated metrics stayed close to the primary result:

| Metric | Primary | Deduplicated |
| --- | ---: | ---: |
| Accuracy | 0.196509 | 0.198263 |
| Phishing precision | 0.149206 | 0.150917 |
| Phishing recall | 0.987590 | 0.987583 |
| Phishing F1 | 0.259245 | 0.261824 |
| ROC-AUC | 0.524568 | 0.524726 |
| Balanced accuracy | 0.526390 | 0.526547 |

Duplicates are therefore not the explanation.

## Domain-Overlap Sensitivity

Offline registrable-domain analysis found 91,683 URL-Phish registrable domains.
Of these, 7,149 were also present in PhiUSIIL and 84,534 were unseen in
PhiUSIIL, for 7.798% domain overlap.

| Segment | Rows | Phishing rows | Legitimate rows | F1 | ROC-AUC | Balanced accuracy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Seen in PhiUSIIL | 22,326 | 9,436 | 12,890 | 0.617642 | 0.548833 | 0.549935 |
| Unseen in PhiUSIIL | 94,274 | 7,164 | 87,110 | 0.146542 | 0.519199 | 0.521351 |

Simple domain overlap does not explain the failure. Most external domains are
unseen, and both segments retain the same qualitative overprediction of
phishing.

## Balanced Sensitivity Interpretation

Earlier balanced URL-Phish sensitivity produced mean phishing F1 around 0.6759
while phishing recall remained around 0.9876. This does not mean model
discrimination became good after balancing. Precision and F1 changed partly
because class prevalence changed mathematically. ROC-AUC on the full external
dataset remained only 0.5246, which indicates weak ranking ability under the
external distribution.

## What The Evidence Supports

The evidence supports a class-conditional covariate-shift mechanism. URL-Phish
benign URLs differ strongly from PhiUSIIL legitimate URLs in lexical structure,
especially path/slash structure and HTTPS usage. The frozen tree then routes
most external benign rows into leaves that were pure phishing leaves during
PhiUSIIL training.

This explains why external phishing recall remains high while precision,
accuracy, and benign specificity collapse.

## What The Evidence Does Not Support

The evidence does not prove:

- That URL-Phish is a complete real-internet distribution
- That PhiUSIIL contains confirmed leakage
- That URL-Phish has poor dataset quality
- That temporal drift is the only cause
- That concept shift has been proven
- That threshold changes should replace the pre-registered external result

## Alternative Explanations Still Unresolved

Possible unresolved contributors include dataset construction differences,
source differences, time-period differences, URL normalization differences,
collection-source artifacts, and true changes in the relationship between URL
lexical patterns and phishing labels.

## Research Implications

The central result is now sharper: near-perfect within-PhiUSIIL performance
remained stable under registrable-domain-disjoint testing, but failed to
transfer to independently collected URL-Phish data. Post-hoc diagnostics
indicate that the failure is primarily associated with class-conditional
lexical distribution differences, especially among legitimate/benign URLs,
rather than simple duplicate rows or domain overlap.

This means future work should prioritize multi-source validation and explicit
source-shift analysis before making deployment claims from a single phishing
URL benchmark.

## Safety Statement

All analyses used local feature matrices, anonymous predictions, or offline
registrable-domain extraction. No URL from PhiUSIIL or URL-Phish was opened,
requested, resolved, pinged, scraped, or contacted.
