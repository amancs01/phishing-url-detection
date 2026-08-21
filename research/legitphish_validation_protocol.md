# LegitPhish Validation Protocol

## Purpose

This protocol preregisters the second confirmatory external validation for the
frozen PhiUSIIL-trained Tier E phishing URL detector. URL-Phish Version 2
showed a large cross-dataset generalization gap, with high phishing recall but
very low benign specificity. A second external dataset is necessary to test
whether that failure is specific to URL-Phish construction or reflects a
broader transfer problem from PhiUSIIL to independently curated URL datasets.

This is confirmatory external evaluation. It is not a model-improvement step.

## Dataset

The planned dataset is LegitPhish Dataset Version 2 from Mendeley Data.

- Dataset name: LegitPhish Dataset
- Version: 2
- DOI: `10.17632/hx4m73v2sf.2`
- Published: 22 May 2025
- Expected rows: approximately 101,219 URLs
- Expected phishing rows: approximately 63,678
- Expected legitimate rows: approximately 37,540
- Original label convention: `0 = phishing`, `1 = legitimate`

The dataset description reports phishing URLs collected from URLHaus,
PhishTank, and other verified phishing repositories, with legitimate URLs
collected from reputable sources such as Wikipedia and Stack Overflow. This
source structure is a threat to validity and should not be treated as the full
real-internet distribution.

## Raw-URL-Only Rule

The primary evaluation will not use LegitPhish supplied numerical features.
Only the raw URL field may be used to generate this project's existing Tier E
feature representation:

```text
LegitPhish raw URL string
    -> existing extract_url_features()
    -> exact Tier E FEATURE_NAMES order
    -> frozen PhiUSIIL-trained Decision Tree
    -> prediction
```

This keeps training-time and deployment-time feature generation aligned with
the project implementation.

## Frozen Model Contract

The selected phishing detector is the already packaged PhiUSIIL-trained Tier E
Decision Tree. The exact feature list is the existing `FEATURE_NAMES` list:

```text
url_length
domain_length
path_length
query_length
number_of_dots
number_of_hyphens
number_of_underscores
number_of_slashes
number_of_question_marks
number_of_equal_signs
number_of_at_symbols
number_of_ampersands
number_of_percent_symbols
number_of_digits
number_of_letters
digit_ratio
letter_ratio
special_character_count
number_of_subdomains
domain_is_ip
uses_https_text
has_port
number_of_query_parameters
suspicious_keyword_count
has_suspicious_keyword
known_shortener_domain
```

The fixed Decision Tree configuration is:

```text
criterion = entropy
max_depth = 10
min_samples_leaf = 1
min_samples_split = 2
ccp_alpha = 0.0
random_state = 42
```

No retraining, retuning, calibration, threshold adjustment, feature addition,
or extractor modification is allowed after inspecting LegitPhish labels or
results. The validation workflow must not call `model.fit(...)`.

## Metrics

The primary full-dataset evaluation will report:

- Accuracy
- Phishing precision
- Phishing recall
- Phishing F1
- ROC-AUC
- PR-AUC / average precision for phishing
- Balanced accuracy
- Specificity
- False-positive rate
- False-negative rate
- Confusion matrix in project order:

```text
[
  [actual phishing -> predicted phishing,
   actual phishing -> predicted legitimate],

  [actual legitimate -> predicted phishing,
   actual legitimate -> predicted legitimate]
]
```

Phishing is project label `0`. The phishing probability must be selected by
locating class `0` in `model.classes_`, not by assuming a probability-column
index.

## Planned Diagnostics

Duplicate sensitivity will evaluate the same frozen model after exact-URL
deduplication. If identical URLs have conflicting labels, those URL values will
be excluded from the deduplicated sensitivity analysis instead of choosing an
arbitrary label. The full dataset remains the primary result.

Domain-overlap analysis will use the existing offline registrable-domain
extractor to count LegitPhish domains also present in PhiUSIIL and domains
unseen in PhiUSIIL. Metrics will be reported separately for seen-domain and
unseen-domain LegitPhish rows. No DNS, WHOIS, socket, SSL, browser, or webpage
operation is allowed.

Class-conditional feature-shift analysis will compare:

- PhiUSIIL legitimate versus LegitPhish legitimate
- PhiUSIIL phishing versus LegitPhish phishing

The multi-dataset shift analysis will also place LegitPhish beside the already
completed URL-Phish diagnostics.

## Preregistered Hypotheses

LP-H1: LegitPhish phishing F1 will be lower than PhiUSIIL domain-disjoint F1.

LP-H2: LegitPhish ROC-AUC will be lower than PhiUSIIL internal ROC-AUC.

LP-H3: If the URL-Phish failure reflects a broader PhiUSIIL transfer problem
rather than only URL-Phish-specific construction, LegitPhish will also show a
meaningful cross-dataset generalization gap.

LP-H4: Class-conditional lexical feature distributions will differ between
PhiUSIIL and LegitPhish.

These hypotheses are preregistered before model prediction on LegitPhish.

## Safety Constraints

Downloading the official LegitPhish file from Mendeley is allowed. URLs
contained inside LegitPhish must remain local text only.

The workflow must not:

- Request dataset URLs
- Open dataset URLs
- Resolve domains
- Perform DNS lookups
- Run WHOIS
- Use sockets
- Query SSL certificates
- Use browser automation
- Use Selenium or Playwright
- Query reputation services
- Retrieve favicons
- Scrape webpages
- Commit raw URLs or raw datasets

## Threats To Validity

- LegitPhish source families may not represent the full real-internet
  distribution.
- Legitimate and phishing URLs originate from different collection processes.
- Feature definitions supplied by LegitPhish may not match this project's
  extractor, which is why supplied numerical features are excluded.
- Exact duplicate URLs and conflicting labels must be measured rather than
  assumed absent.
- Cross-dataset performance differences may reflect dataset construction,
  source differences, temporal differences, URL normalization, class
  prevalence, covariate shift, class-conditional shift, or concept shift.
- Poor transfer alone does not prove concept shift.
- Strong transfer would not prove real-world security.

The intended contribution is a controlled PhiUSIIL feature-provenance and
deployment-reproducibility audit combined with fixed-model random,
domain-disjoint, and multiple independent external validations.
