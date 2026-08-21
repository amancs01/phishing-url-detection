# Multi-Dataset Generalization Synthesis

## Purpose

This document synthesizes the final empirical evidence for the research-oriented phishing URL detection project. The contribution is a controlled PhiUSIIL feature-provenance and deployment-reproducibility audit combined with fixed-model random, domain-disjoint, and multiple independent external validations.

All external evaluations used the same frozen PhiUSIIL-trained Tier E Decision Tree, the same 26 `FEATURE_NAMES`, the same threshold, and the same local URL-string extractor. No external dataset URL was opened, requested, resolved, or contacted.

## Datasets

| Dataset | Version | DOI/source | Rows used | Phishing | Legitimate/benign |
| --- | ---: | --- | ---: | ---: | ---: |
| PhiUSIIL | UCI dataset 967 | UCI Machine Learning Repository | 235,795 | 100,945 | 134,850 |
| URL-Phish | 2 | 10.17632/65z9twcx3r.2 | 116,600 | 16,600 | 100,000 |
| LegitPhish | 2 | 10.17632/hx4m73v2sf.2 | 101,218 analysis rows from 101,219 raw rows | 63,678 | 37,540 |

LegitPhish contained one row with a missing label, 346 duplicate rows, 346 duplicate URL rows, and zero conflicting-label duplicate URL values. Its label convention already matched the project convention: `0 = phishing`, `1 = legitimate`.

## Feature Provenance

The PhiUSIIL audit separated benchmark features from deployment-reproducible URL-string features. Of 55 audited columns, 20 were directly computable from raw URL text, 3 were URL-derived but reference-dependent, 29 were webpage/content-derived, 1 remained uncertain, and 2 were identifiers or labels.

This matters because a high benchmark score can depend on features unavailable to a model that receives only a URL string. The project therefore emphasized Tier E, the 26-feature deployment extractor, for external validation.

## Tier A Dominance

The full supplied Tier A benchmark achieved perfect random-split test performance, but the fitted tree was dominated by `URLSimilarityIndex`:

| Feature | Importance | Provenance |
| --- | ---: | --- |
| `URLSimilarityIndex` | 0.970682 | URL-derived but reference/definition dependent |
| `IsHTTPS` | 0.027944 | Direct URL text |
| `LineOfCode` | 0.001166 | Webpage/content-derived |
| `NoOfSubDomain` | 0.000209 | Direct URL text |

A one-feature stump on `URLSimilarityIndex` alone reached test F1 0.996055. This does not prove leakage, but it makes the perfect Tier A score inappropriate as a deployment claim.

## URL-Only Performance

Using only supplied direct-reproducible PhiUSIIL URL features, Tier C and the reconstructed Tier D-matched conditions still performed strongly. The research-specific D-matched condition produced random-split phishing F1 0.993460 and ROC-AUC 0.996919. The production-style Tier E extractor produced random-split phishing F1 0.994992 and ROC-AUC 0.997996.

## PhiUSIIL Random Split

| Metric | Tier E random split |
| --- | ---: |
| Accuracy | 0.995731 |
| Phishing precision | 0.999400 |
| Phishing recall | 0.990622 |
| Phishing F1 | 0.994992 |
| ROC-AUC | 0.997996 |
| Confusion matrix | `[[15000, 142], [9, 20219]]` |

## PhiUSIIL Domain-Disjoint Split

The registrable-domain-disjoint Tier E result remained very high:

| Metric | Tier E domain-disjoint |
| --- | ---: |
| Accuracy | 0.996890 |
| Phishing precision | 0.998078 |
| Phishing recall | 0.994651 |
| Phishing F1 | 0.996361 |
| ROC-AUC | 0.998225 |
| Confusion matrix | `[[15061, 81], [29, 20198]]` |

This shows that within-PhiUSIIL domain separation was not enough to expose the larger external-transfer risk.

## External Validation Results

| Metric | PhiUSIIL domain-disjoint | URL-Phish | LegitPhish |
| --- | ---: | ---: | ---: |
| Accuracy | 0.996890 | 0.196509 | 0.993786 |
| Phishing precision | 0.998078 | 0.149206 | 0.990219 |
| Phishing recall | 0.994651 | 0.987590 | 1.000000 |
| Phishing F1 | 0.996361 | 0.259245 | 0.995085 |
| ROC-AUC | 0.998225 | 0.524568 | 0.991929 |
| Balanced accuracy | 0.996890 | 0.526390 | 0.991622 |

URL-Phish was the severe failure case. The model preserved high phishing recall but labeled most benign rows as phishing, yielding the confusion matrix `[[16394, 206], [93481, 6519]]`.

LegitPhish was a strong-transfer case. The model missed no phishing rows in the full matrix and produced the confusion matrix `[[63678, 0], [629, 36911]]`.

## External False Positives

For URL-Phish, the dominant false-positive leaf received 88,986 benign false positives. In PhiUSIIL training that same leaf contained only phishing rows and followed the rule `number_of_slashes > 2.5`. The top three leaves explained 93,448 of 93,481 URL-Phish benign false positives, linking the external failure to lexical routing shift rather than random error.

LegitPhish did not show the same benign collapse. Its full-result false positives were 629 legitimate rows, with specificity 0.983245.

## Class-Conditional Shift

The multi-dataset shift analysis compared each external dataset to the matching PhiUSIIL class using all Tier E features.

| Semantic class | External dataset | Mean KS | Median KS | Max KS | Similarity rank |
| --- | ---: | ---: | ---: | ---: | ---: |
| Legitimate | LegitPhish | 0.004445 | 0.002042 | 0.015956 | 1 |
| Legitimate | URL-Phish | 0.173850 | 0.020020 | 0.889860 | 2 |
| Phishing | URL-Phish | 0.112336 | 0.089140 | 0.426983 | 1 |
| Phishing | LegitPhish | 0.358168 | 0.355834 | 0.764369 | 2 |

LegitPhish is much more similar to PhiUSIIL for legitimate URLs. URL-Phish is more similar to PhiUSIIL for phishing URLs.

Top PhiUSIIL legitimate vs LegitPhish legitimate shifts were small: `path_length` KS 0.015956, `number_of_slashes` KS 0.015956, `special_character_count` KS 0.013928, `url_length` KS 0.011903, and `number_of_letters` KS 0.010920.

Top PhiUSIIL phishing vs LegitPhish phishing shifts were large: `domain_is_ip` KS 0.764369, `number_of_digits` KS 0.734116, `letter_ratio` KS 0.726609, `path_length` KS 0.721652, and `digit_ratio` KS 0.719236.

## Dataset-Origin Separability

Dataset-origin diagnostics used shallow depth-5 decision trees to classify dataset source within a fixed semantic class. They are diagnostics, not phishing models.

| Pair | Semantic class | Origin accuracy | Origin ROC-AUC | Top source-discriminating features |
| --- | --- | ---: | ---: | --- |
| PhiUSIIL vs URL-Phish | benign/legitimate | 0.967333 | 0.978597 | `number_of_slashes`, `uses_https_text`, `number_of_subdomains` |
| PhiUSIIL vs URL-Phish | phishing | 0.775502 | 0.853450 | `uses_https_text`, `number_of_subdomains`, `digit_ratio` |
| PhiUSIIL vs LegitPhish | legitimate | 0.507903 | 0.508291 | `number_of_slashes`, `digit_ratio`, `letter_ratio` |
| PhiUSIIL vs LegitPhish | phishing | 0.952679 | 0.990815 | `domain_is_ip`, `number_of_underscores`, `path_length` |

The URL-Phish failure is therefore consistent with a large benign/legitimate distribution mismatch. LegitPhish has the opposite pattern: legitimate rows are nearly inseparable from PhiUSIIL legitimate rows, while phishing rows are highly separable but still routed as phishing by the frozen model.

## Domain Overlap

URL-Phish had 91,683 registrable domains, of which 7,149 also appeared in PhiUSIIL. Its overlap was 7.798%. Seen-domain F1 was 0.617642; unseen-domain F1 was 0.146542.

LegitPhish had 62,881 registrable domains, of which 36,515 also appeared in PhiUSIIL. Its overlap was 58.070%. Seen-domain rows had phishing F1 0.850959, ROC-AUC 0.997066, and balanced accuracy 0.996757. Unseen-domain rows had phishing F1 0.996930, ROC-AUC 0.500000, and balanced accuracy 0.500000 because this segment contained 62,990 phishing rows and only 388 legitimate rows, all of which were predicted phishing.

Domain overlap is therefore informative but not a complete explanation. Class composition and class-conditional lexical structure still matter.

## Deduplication Sensitivity

URL-Phish exact-URL deduplication changed phishing F1 from 0.259245 to 0.261824 and left the interpretation unchanged.

LegitPhish exact-URL deduplication removed 346 duplicate URL rows, found zero conflicting duplicate URL values, and changed phishing F1 from 0.995085 to 0.996320. The primary full-dataset result remains the reported confirmatory result.

## Hypothesis Outcomes

LP-H1 predicted that LegitPhish phishing F1 would be lower than PhiUSIIL domain-disjoint F1. Supported narrowly: 0.995085 is lower than 0.996361 by 0.001276.

LP-H2 predicted that LegitPhish ROC-AUC would be lower than PhiUSIIL internal ROC-AUC. Supported: 0.991929 is lower than 0.997996.

LP-H3 predicted that if the URL-Phish failure reflected a broader PhiUSIIL transfer problem, LegitPhish would also show a meaningful generalization gap. Not supported in the broad-failure form. URL-Phish was poor, but LegitPhish was strong. The evidence supports dataset-pair-dependent transfer rather than a universal PhiUSIIL-to-external collapse.

LP-H4 predicted class-conditional lexical differences between PhiUSIIL and LegitPhish. Supported, but asymmetrically. Legitimate-class differences were tiny, while phishing-class differences were large.

## Interpretation

The final evidence matches Scenario 2 from the preregistered interpretation matrix: URL-Phish poor, LegitPhish strong. Transfer performance is highly dataset-pair dependent, and the URL-Phish failure cannot be generalized to all external datasets.

The most defensible conclusion is not that PhiUSIIL-trained URL-only models never transfer. It is that very high internal and domain-disjoint benchmark performance is insufficient evidence for external reliability. External performance depends strongly on how the target dataset's class-conditional lexical distributions align with the source benchmark.

## Alternative Explanations

Plausible contributors include dataset construction protocols, time period, source feeds, URL normalization conventions, label policy, benign/legitimate sampling, class prevalence, and differences in how IP-address-heavy or path-heavy phishing URLs were collected. The current analyses demonstrate association and diagnostic mechanism, not causal proof of any one source.

## Threats To Validity

The study used a Decision Tree and a specific URL-only feature extractor. Other models or richer signals may respond differently. Both external validations are dataset validations, not live deployment trials. ROC-AUC can be unstable in extremely imbalanced segments, as seen in the LegitPhish unseen-domain subset. Dataset metadata and local schemas were checked, but original collection pipelines remain partially opaque.

## Implications

Benchmark evaluation should report feature provenance, URL-only reproducibility, domain-disjoint checks, multiple external datasets, class-conditional shift, dataset-origin separability, duplicate sensitivity, and domain-overlap sensitivity before making deployment claims.

The strongest practical result is that a fixed PhiUSIIL Tier E model can transfer very well to one independently curated dataset and very poorly to another. That contrast is itself the central research finding.
