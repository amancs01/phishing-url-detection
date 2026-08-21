# Tier A Tree Analysis

## Purpose

This report investigates why the full supplied Tier A benchmark condition
achieved perfect random-split test performance with a depth-4, 5-leaf
Decision Tree. It does not claim data leakage; it documents the fitted
tree, the features it used, and their provenance.

## Fixed Configuration

```text
criterion = entropy
max_depth = 10
min_samples_leaf = 1
min_samples_split = 2
ccp_alpha = 0.0
random_state = 42
```

## Root And Used Features

Root feature: `URLSimilarityIndex`

| Feature | Importance | Provenance | Directly deployable | Reference dependent | Webpage dependent |
| --- | ---: | --- | --- | --- | --- |
| `URLSimilarityIndex` | 0.970682 | C URL-derived but external/reference/unavailable stats | False | True | False |
| `IsHTTPS` | 0.027944 | B directly computable raw URL text | True | False | False |
| `LineOfCode` | 0.001166 | D webpage/content-derived | False | False | True |
| `NoOfSubDomain` | 0.000209 | B directly computable raw URL text | True | False | False |

## Human-Readable Tree Rules

```text
|--- URLSimilarityIndex <= 98.502224
|   |--- class: 0
|--- URLSimilarityIndex >  98.502224
|   |--- IsHTTPS <= 0.500000
|   |   |--- class: 0
|   |--- IsHTTPS >  0.500000
|   |   |--- LineOfCode <= 67.500000
|   |   |   |--- class: 0
|   |   |--- LineOfCode >  67.500000
|   |   |   |--- NoOfSubDomain <= 0.500000
|   |   |   |   |--- class: 0
|   |   |   |--- NoOfSubDomain >  0.500000
|   |   |   |   |--- class: 1

```

## Top 10 Feature Importances

| Rank | Feature | Importance |
| ---: | --- | ---: |
| 1 | `URLSimilarityIndex` | 0.970682 |
| 2 | `IsHTTPS` | 0.027944 |
| 3 | `LineOfCode` | 0.001166 |
| 4 | `NoOfSubDomain` | 0.000209 |
| 5 | `Bank` | 0.000000 |
| 6 | `CharContinuationRate` | 0.000000 |
| 7 | `Crypto` | 0.000000 |
| 8 | `DegitRatioInURL` | 0.000000 |
| 9 | `DomainLength` | 0.000000 |
| 10 | `DomainTitleMatchScore` | 0.000000 |

## Decision-Stump Diagnostics

Each stump uses only one tree-used feature. These are diagnostics, not
model-selection results.

| Feature | Threshold | Validation accuracy | Validation F1 | Test accuracy | Test F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `URLSimilarityIndex` | 98.502224 | 0.996268 | 0.995622 | 0.996636 | 0.996055 |
| `IsHTTPS` | 0.500000 | 0.789561 | 0.674139 | 0.791575 | 0.678247 |
| `LineOfCode` | 202.500000 | 0.956431 | 0.947983 | 0.954227 | 0.945291 |
| `NoOfSubDomain` | 0.500000 | 0.632560 | 0.248265 | 0.630308 | 0.240121 |

## Interpretation

The perfect Tier A separation is primarily driven by `URLSimilarityIndex`, a URL-oriented feature classified as reference-dependent or definition-dependent rather than directly deployable. The fitted tree also uses `LineOfCode`, a webpage/content-derived feature, plus `IsHTTPS` and `NoOfSubDomain`, which are URL-text features. This supports a cautious interpretation: the random-split Tier A benchmark contains extremely discriminative supplied features, including at least one feature unavailable to a raw-URL-only deployment setting. This is not by itself proof of data leakage.

## Safety Statement

This analysis uses local feature matrices and saved split assignments.
No URL is opened, requested, resolved, pinged, or contacted.
