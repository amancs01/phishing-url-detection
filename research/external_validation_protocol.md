# External Validation Protocol

## Purpose

This protocol pre-registers the first true external validation experiment for
the phishing URL detection project. Previous experiments evaluated PhiUSIIL
under random and registrable-domain-disjoint splits. Those results were useful
for internal validity, but they do not answer whether the selected no-contact
URL feature extractor generalizes to a different dataset with a different
collection process.

The external dataset is evaluation data only. It will not be used for training,
retuning, threshold selection, feature-definition changes, or model selection.

## External Dataset

The planned external dataset is URL-Phish: A Feature-Engineered Dataset for
Phishing Detection, Mendeley Data Version 2.

- Official source: https://data.mendeley.com/datasets/65z9twcx3r/2
- DOI: `10.17632/65z9twcx3r.2`
- Version: 2
- Published: 9 March 2026
- Expected rows: 116,600 unique URLs
- Expected benign rows: 100,000
- Expected phishing rows: 16,600
- License: CC BY 4.0

The dataset description states that benign samples were collected from trusted
or curated sources including educational, governmental, and top-ranked domains,
with the benign subset obtained from the Research Organization Registry data.
The phishing samples were obtained from PhishTank between November 2024 and
September 2025.

This collection structure is a threat to validity. URL-Phish should not be
treated as the full real internet distribution.

## Label Semantics

URL-Phish and this project use opposite label conventions.

| Source | Phishing label | Legitimate/benign label |
| --- | ---: | ---: |
| URL-Phish | 1 | 0 |
| This project | 0 | 1 |

The external pipeline must normalize URL-Phish labels into the project
convention before evaluation:

- URL-Phish label `1` maps to project label `0`
- URL-Phish label `0` maps to project label `1`

All phishing metrics will treat project label `0` as the positive semantic
class.

## Feature Policy

The main experiment will not use URL-Phish supplied numerical feature columns.
Only the raw URL string is allowed as input to the existing project feature
extractor.

The external feature-generation flow is:

```text
URL-Phish raw URL string
    -> existing extract_url_features()
    -> existing Tier E FEATURE_NAMES order
    -> existing PhiUSIIL-trained Decision Tree
    -> prediction
```

This keeps training-time and deployment-time feature generation aligned with
the project implementation, rather than mixing URL-Phish feature definitions
with PhiUSIIL-trained model expectations.

## Fixed Model

The selected deployment model is the Tier E deployment-extended Decision Tree.
The fixed Decision Tree configuration is:

```text
criterion = entropy
max_depth = 10
min_samples_leaf = 1
min_samples_split = 2
ccp_alpha = 0.0
random_state = 42
```

No external training is allowed. The external validation workflow must not call
`model.fit(...)`.

No external retuning is allowed. Hyperparameters, thresholds, and feature
definitions must not be changed after seeing URL-Phish labels or predictions.

## Primary Metrics

The primary external metrics are:

- Accuracy
- Phishing precision
- Phishing recall
- Phishing F1
- ROC-AUC
- Balanced accuracy
- PR-AUC / average precision for phishing
- Confusion matrix in the explicit project order:

```text
[
  [actual phishing -> predicted phishing,
   actual phishing -> predicted legitimate],

  [actual legitimate -> predicted phishing,
   actual legitimate -> predicted legitimate]
]
```

The number of actual phishing URLs predicted legitimate is the primary missed
phishing count.

## Class Imbalance And Sensitivity Analysis

URL-Phish Version 2 is expected to be imbalanced, with approximately 16,600
phishing URLs and 100,000 benign URLs. Precision and F1 depend on prevalence,
so the external experiment will include a sensitivity analysis.

The primary analysis uses the full external dataset. A secondary balanced
prevalence analysis will retain all external phishing samples and repeatedly
sample an equal number of legitimate samples with predetermined seeds:

```text
42, 43, 44, 45, 46
```

The balanced analysis will not retrain the model. Because all phishing samples
are retained, phishing recall should match the full external phishing recall.
If it does not, the implementation must be investigated before interpretation.

Bootstrap 95% confidence intervals will be calculated for the full external
dataset for accuracy, phishing precision, phishing recall, phishing F1, and
ROC-AUC.

## Pre-Registered Hypotheses

EX-H1: External phishing recall will be lower than PhiUSIIL
domain-disjoint recall.

EX-H2: External phishing F1 will be lower than PhiUSIIL domain-disjoint F1.

EX-H3: ROC-AUC will remain higher than the threshold-dependent F1 if
prevalence shift mainly affects calibration or decision-threshold behavior.

These are hypotheses only and must not drive model changes.

## Safety Restrictions

Downloading the official dataset file from Mendeley is allowed. URLs contained
inside the dataset must remain plain text only.

The experiment must not:

- Open dataset URLs
- Make HTTP requests to dataset URLs
- Resolve domains
- Perform DNS lookups
- Run WHOIS
- Use sockets
- Inspect SSL certificates
- Ping hosts
- Use browser automation
- Use Selenium or Playwright
- Scrape webpages
- Query reputation services
- Retrieve favicons

Raw external URLs must not be committed. Committed artifacts may include only
compact metadata, metrics, anonymous row indices, normalized labels,
predictions, and probabilities.

## Threats To Validity

- URL-Phish benign and phishing classes come from different source families.
- URL-Phish does not represent the complete real internet distribution.
- Collection timing differs from PhiUSIIL.
- URL normalization and preprocessing may differ across datasets.
- Lexical distributions may differ because URL-Phish benign rows come from
  trusted or curated sources while phishing rows come from PhishTank.
- Class prevalence differs from the internal PhiUSIIL splits.
- High external accuracy would not prove real-world security.
- Low external performance would not by itself identify a single cause such as
  temporal drift.

The preferred interpretation term is cross-dataset generalization gap unless a
specific cause is demonstrated.
