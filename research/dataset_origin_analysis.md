# Post-Hoc Diagnostic Analysis: Dataset-Origin Separability

## Purpose

This post-hoc diagnostic experiment asks whether PhiUSIIL and URL-Phish can be
distinguished using the same frozen Tier E lexical feature representation even
when phishing label is held constant.

The diagnostic labels are dataset-origin labels, not phishing labels:

- Origin label `0`: PhiUSIIL source
- Origin label `1`: URL-Phish source

This experiment does not train, retune, or modify the phishing detector.

## Method

Two independent source-separability experiments were run:

- Benign-only: PhiUSIIL legitimate versus URL-Phish benign
- Phishing-only: PhiUSIIL phishing versus URL-Phish phishing

For each experiment, the larger source class was randomly sampled down to the
smaller source count with `random_state=42`. A shallow
`DecisionTreeClassifier(max_depth=5, random_state=42)` was trained only to
predict dataset origin. This model is a diagnostic instrument, not the phishing
classifier.

The balanced dataset was split with stratification into 70% train and 30% test.
No hyperparameter tuning was performed.

## Results

| Experiment | Balanced rows per source | Origin accuracy | Balanced accuracy | ROC-AUC | Depth | Leaves |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Benign-only origin | 100,000 | 0.967333 | 0.967333 | 0.978597 | 5 | 7 |
| Phishing-only origin | 16,600 | 0.775502 | 0.775502 | 0.853450 | 5 | 31 |

Both experiments show strong dataset-source separability under the same Tier E
features. This supports measurable source/domain shift. It does not prove poor
dataset quality and does not prove concept shift.

## Benign-Origin Top Features

| Rank | Feature | Importance |
| ---: | --- | ---: |
| 1 | `number_of_slashes` | 0.908017 |
| 2 | `uses_https_text` | 0.057767 |
| 3 | `number_of_subdomains` | 0.028058 |
| 4 | `letter_ratio` | 0.004828 |
| 5 | `digit_ratio` | 0.000789 |
| 6 | `special_character_count` | 0.000541 |
| 7 | `domain_length` | 0.000000 |
| 8 | `path_length` | 0.000000 |
| 9 | `number_of_dots` | 0.000000 |
| 10 | `url_length` | 0.000000 |

## Phishing-Origin Top Features

| Rank | Feature | Importance |
| ---: | --- | ---: |
| 1 | `uses_https_text` | 0.537124 |
| 2 | `number_of_subdomains` | 0.106768 |
| 3 | `digit_ratio` | 0.054486 |
| 4 | `domain_length` | 0.054414 |
| 5 | `number_of_digits` | 0.048892 |
| 6 | `number_of_dots` | 0.045578 |
| 7 | `path_length` | 0.043578 |
| 8 | `number_of_hyphens` | 0.039686 |
| 9 | `url_length` | 0.033328 |
| 10 | `letter_ratio` | 0.020797 |

## Interpretation

Benign-only origin classification is extremely accurate, which means
PhiUSIIL legitimate rows and URL-Phish benign rows occupy strongly
dataset-specific regions of Tier E feature space. This is consistent with the
external false-positive collapse: the frozen phishing tree learned internal
benign patterns that do not describe most URL-Phish benign rows.

Phishing-only origin classification is also high, so phishing feature
distributions differ substantially too. However, the external phishing recall
remains high, suggesting that the phishing-side shift did not break the
model's ability to route most external phishing rows into phishing leaves.

Overall, this supports strong class-conditional covariate shift across
datasets, especially in the benign/legitimate class. It does not prove concept
shift because the diagnostic labels describe dataset source, not the phishing
task mapping.

## Safety Statement

All computations used local feature matrices. No URL from PhiUSIIL or
URL-Phish was opened, requested, resolved, pinged, scraped, or contacted.
