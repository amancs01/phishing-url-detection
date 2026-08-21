# External Generalization Analysis

## Purpose

This section reports the first true external validation of the selected
PhiUSIIL-trained phishing URL detector. The experiment evaluates the packaged
Tier E deployment model on URL-Phish Version 2 using raw URL strings only. It
does not train, retune, change thresholds, or alter feature definitions with
URL-Phish data.

The correct interpretation is a cross-dataset generalization gap. URL-Phish
does not represent the full real internet distribution, and performance on it
should not be described as proof of real-world security.

## Dataset

URL-Phish: A Feature-Engineered Dataset for Phishing Detection was obtained
from the official Mendeley Data Version 2 release.

- DOI: `10.17632/65z9twcx3r.2`
- Version: 2
- Published: 9 March 2026
- File used: `Dataset.csv`
- Actual rows loaded: 116,600
- URL column: `url`
- Label column: `label`
- URL-Phish labels: `0 = benign`, `1 = phishing`
- Project labels after normalization: `0 = phishing`, `1 = legitimate`

The official dataset description states that benign URLs were collected from
trusted or curated sources including educational, governmental, and top-ranked
domains, with the benign subset obtained from Research Organization Registry
data. Phishing URLs were obtained from PhishTank between November 2024 and
September 2025. This source structure is important because the external task is
not simply a random sample from all live web traffic.

## Dataset Diagnostics

| Diagnostic | Value |
| --- | ---: |
| Total rows | 116,600 |
| URL-Phish benign label `0` | 100,000 |
| URL-Phish phishing label `1` | 16,600 |
| Project legitimate label `1` after normalization | 100,000 |
| Project phishing label `0` after normalization | 16,600 |
| URL missing rows | 0 |
| Label missing rows | 0 |
| Rows with any source missing value | 14 |
| Rows with any generated matrix missing value | 0 |
| Duplicate full rows | 1,369 |
| Duplicate URL rows | 1,369 |

The 14 source rows with missing values are missing URL-Phish supplied metadata,
not raw URL or label values. Since the main experiment ignores supplied
URL-Phish numerical and metadata features, these rows remain evaluable after
local feature extraction.

## Methodology

Only the URL-Phish raw URL string was used to generate features. The workflow
was:

```text
URL-Phish raw URL string
    -> existing extract_url_features()
    -> existing Tier E FEATURE_NAMES order
    -> existing PhiUSIIL-trained Decision Tree
    -> prediction
```

The URL-Phish supplied numerical features were not used. This keeps the
external validation aligned with the project's deployment-time feature
implementation.

The selected model was the already packaged PhiUSIIL Tier E Decision Tree with
these fixed hyperparameters:

```text
criterion = entropy
max_depth = 10
min_samples_leaf = 1
min_samples_split = 2
ccp_alpha = 0.0
random_state = 42
```

The external workflow contains no model-training step and does not call
`model.fit(...)`.

## Internal Reference Results

| Evaluation | Accuracy | Phishing precision | Phishing recall | Phishing F1 | ROC-AUC | Missed phishing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| PhiUSIIL random split, Tier E | 0.995731 | 0.999400 | 0.990622 | 0.994992 | 0.997996 | 142 |
| PhiUSIIL domain-disjoint, Tier E | 0.996890 | 0.998078 | 0.994651 | 0.996361 | 0.998225 | 81 |

Domain-disjoint evaluation did not reduce Tier E performance inside PhiUSIIL.
That made external validation especially important.

## Full URL-Phish External Results

| Metric | Value |
| --- | ---: |
| Accuracy | 0.196509 |
| Phishing precision | 0.149206 |
| Phishing recall | 0.987590 |
| Phishing F1 | 0.259245 |
| ROC-AUC | 0.524568 |
| PR-AUC / average precision | 0.148627 |
| Balanced accuracy | 0.526390 |

The confusion matrix uses the project order:

```text
[
  [actual phishing -> predicted phishing,
   actual phishing -> predicted legitimate],

  [actual legitimate -> predicted phishing,
   actual legitimate -> predicted legitimate]
]
```

Observed matrix:

```text
[[16394, 206],
 [93481, 6519]]
```

The model missed 206 of 16,600 phishing URLs, a missed-phishing rate of
1.241%. The larger failure mode was false positives: 93,481 of 100,000 benign
URLs were predicted phishing. This produced high phishing recall but very low
precision, F1, accuracy, and balanced accuracy.

## Absolute External Gaps

Gaps below compare URL-Phish full external results against the PhiUSIIL
domain-disjoint Tier E result. Negative values mean external performance is
lower.

| Metric | PhiUSIIL domain-disjoint | URL-Phish external | External gap |
| --- | ---: | ---: | ---: |
| Accuracy | 0.996890 | 0.196509 | -80.038 pp |
| Phishing precision | 0.998078 | 0.149206 | -84.887 pp |
| Phishing recall | 0.994651 | 0.987590 | -0.706 pp |
| Phishing F1 | 0.996361 | 0.259245 | -73.712 pp |
| ROC-AUC | 0.998225 | 0.524568 | -47.366 pp |

The cross-dataset gap is therefore not a missed-phishing collapse. It is mainly
a benign-class rejection collapse, with the model assigning phishing to most
URL-Phish benign rows.

## Bootstrap Confidence Intervals

Bootstrap intervals use 1,000 percentile resamples over anonymous external
prediction rows. Models are not retrained during bootstrap.

| Metric | Observed | 95% CI |
| --- | ---: | --- |
| Accuracy | 0.196509 | [0.194125, 0.198774] |
| Phishing precision | 0.149206 | [0.147029, 0.151493] |
| Phishing recall | 0.987590 | [0.985797, 0.989192] |
| Phishing F1 | 0.259245 | [0.256205, 0.262624] |
| ROC-AUC | 0.524568 | [0.523294, 0.525719] |

## Balanced Prevalence Sensitivity

The full external dataset contains 16,600 phishing rows and 100,000 benign
rows. To separate prevalence effects from feature/generalization effects, a
secondary sensitivity analysis retained all phishing rows and sampled an equal
number of benign rows with seeds 42 through 46. The model was not retrained.

| Analysis | Accuracy | Phishing precision | Phishing recall | Phishing F1 | ROC-AUC | PR-AUC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Full external | 0.196509 | 0.149206 | 0.987590 | 0.259245 | 0.524568 | 0.148627 |
| Balanced mean | 0.526380 | 0.513722 | 0.987590 | 0.675871 | 0.524569 | 0.512589 |
| Balanced std | 0.000961 | 0.000514 | 0.000000 | 0.000445 | 0.001008 | 0.000531 |
| Balanced min | 0.525181 | 0.513082 | 0.987590 | 0.675317 | 0.523305 | 0.511924 |
| Balanced max | 0.527470 | 0.514305 | 0.987590 | 0.676376 | 0.525688 | 0.513178 |

As expected, phishing recall is unchanged because every balanced sample keeps
all phishing rows. Precision and F1 rise sharply under balanced prevalence,
showing that class prevalence strongly affects the threshold-dependent metrics.
However, balanced accuracy and ROC-AUC remain near 0.5, so prevalence alone
does not explain the poor external separability.

## Feature Distribution Shift Diagnostics

A separate aggregate diagnostic compared PhiUSIIL Tier E feature distributions
against URL-Phish Tier E features generated by the project extractor. KS
statistics are descriptive shift indicators only; they do not prove causation.

| Rank | Feature | KS statistic | PhiUSIIL mean | URL-Phish mean | External - internal mean |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `path_length` | 0.637865 | 3.735325 | 6.391381 | +2.656056 |
| 2 | `number_of_slashes` | 0.637860 | 2.436328 | 3.215026 | +0.778698 |
| 3 | `special_character_count` | 0.405310 | 6.275048 | 7.001707 | +0.726658 |
| 4 | `uses_https_text` | 0.349393 | 0.780534 | 0.431141 | -0.349393 |
| 5 | `letter_ratio` | 0.296025 | 0.777389 | 0.752510 | -0.024880 |
| 6 | `domain_length` | 0.246026 | 21.468899 | 17.405369 | -4.063530 |

The largest shifts involve path/slash structure, special-character counts, and
HTTPS text usage. These shifts are consistent with a model trained on PhiUSIIL
URL-text patterns overfiring on URL-Phish benign rows, but the experiment does
not identify a single cause.

## Hypothesis Outcomes

EX-H1: External phishing recall will be lower than PhiUSIIL domain-disjoint
recall.

Supported. PhiUSIIL domain-disjoint Tier E recall was 0.994651, while
URL-Phish recall was 0.987590, a decrease of 0.706 percentage points.

EX-H2: External phishing F1 will be lower than PhiUSIIL domain-disjoint F1.

Supported. PhiUSIIL domain-disjoint Tier E F1 was 0.996361, while URL-Phish F1
was 0.259245, a decrease of 73.712 percentage points.

EX-H3: ROC-AUC will remain higher than threshold-dependent F1 if prevalence
shift mainly affects calibration or decision-threshold behavior.

Directionally supported but scientifically weak. ROC-AUC was higher than F1
on the full external dataset, 0.524568 versus 0.259245. However, ROC-AUC was
only slightly above random ranking, and balanced sensitivity still produced
ROC-AUC near 0.5. The result suggests threshold and prevalence effects matter,
but it does not support a simple story that prevalence shift is the main
problem.

## Scientific Interpretation

The external validation changes the research story substantially. Internal
PhiUSIIL experiments showed excellent URL-only performance, including
domain-disjoint F1 of 0.996361. On URL-Phish, the same fixed Tier E model
retained high phishing recall but classified most benign URLs as phishing.

This means the model is sensitive enough to catch nearly all external phishing
examples, but it fails to reject URL-Phish benign examples under the fixed
PhiUSIIL-trained decision boundary. In deployment terms, that would produce an
unusable false-positive burden even though missed phishing is low.

The appropriate conclusion is not that the model is useless, nor that
PhiUSIIL contained proven leakage. The appropriate conclusion is that high
in-dataset and domain-disjoint PhiUSIIL scores did not transfer cleanly across
datasets. The observed behavior is a cross-dataset generalization gap.

Possible contributors include dataset construction differences, source
differences, temporal differences, lexical-distribution differences, class
prevalence, and URL normalization differences. The current experiment does not
isolate these causes.

## Threats To Validity

- URL-Phish benign and phishing samples come from different source families.
- URL-Phish is not a complete real-internet distribution.
- URL-Phish includes supplied feature engineering, but the main experiment uses
  only raw URL strings and ignores those supplied features.
- The external CSV contains duplicate rows despite the dataset description
  stating unique URLs.
- The PhiUSIIL model was trained on one dataset and tested on another with
  different collection timing and source construction.
- High phishing recall could partly reflect broad overprediction of phishing.
- Low external precision does not by itself identify whether the cause is
  temporal drift, dataset construction, feature shift, prevalence, or URL
  normalization.
- Feature-shift diagnostics are descriptive, not causal.

## Safety Statement

All URL handling in this external validation is offline text parsing. The only
network activity was downloading the official dataset file from Mendeley Data.
No URL contained inside URL-Phish was opened, requested, resolved, pinged,
scraped, or otherwise contacted.
