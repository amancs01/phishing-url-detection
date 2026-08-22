# Draft Paper Sections

## 3. Materials and Methods

### 3.1 Datasets

This study used three phishing URL datasets. PhiUSIIL was the source benchmark and training dataset for all fitted models. URL-Phish and LegitPhish were external evaluation datasets only. No external dataset was used for training, tuning, calibration, feature selection, threshold selection, or model replacement.

PhiUSIIL contained 235,795 labelled URLs: 100,945 phishing URLs and 134,850 legitimate URLs. Its native label convention is consistent with this project's convention: numeric label `0` denotes phishing and numeric label `1` denotes legitimate. PhiUSIIL includes raw URL text and a large set of supplied engineered features derived from URL information, webpage/source-code information, similarity scores, and other derived quantities.

URL-Phish Version 2 was used as the first independent external dataset. The local inspected file contained 116,600 rows, with 16,600 phishing URLs and 100,000 benign URLs after mapping its source labels into the project convention. URL-Phish source label `1` was mapped to project label `0` for phishing, and URL-Phish source label `0` was mapped to project label `1` for legitimate/benign.

LegitPhish Version 2 was used as the second external dataset. The local inspected file contained 101,219 raw rows. One row had a missing label, leaving 101,218 analysis rows: 63,678 phishing and 37,540 legitimate. LegitPhish already used the project convention, with `0 = phishing` and `1 = legitimate`.

### 3.2 Safety and URL-Only Extraction

All URL strings were treated as inert text. The workflow did not open, request, resolve, ping, scrape, render, or otherwise contact any URL contained in any dataset. No DNS, WHOIS, SSL, browser automation, reputation lookup, or webpage download was performed.

The deployment-style feature extractor computed only local URL-string properties. The Tier E feature list contained 26 features: URL length, domain length, path length, query length, character counts, character ratios, query-parameter count, subdomain count, IP-literal indicator, HTTPS text indicator, explicit-port indicator, suspicious-keyword count, suspicious-keyword indicator, and known-shortener-domain indicator.

### 3.3 Feature Provenance Taxonomy

PhiUSIIL supplied columns were audited before the main research experiments. Each column was assigned to one of five categories:

- Identifier, label, or non-model column.
- Directly computable raw URL-text feature.
- URL-derived but reference-dependent or definition-dependent feature.
- Webpage/content-derived feature.
- Uncertain feature requiring further verification.

The purpose of the taxonomy was to distinguish benchmark features from features that a deployed URL-only detector could reproduce safely from a submitted URL string.

### 3.4 Feature Fidelity Audit

For supplied PhiUSIIL features classified as directly URL-computable in principle, independent reconstruction candidates were compared against the supplied dataset values. The audit measured exact match percentage, mean absolute error, median absolute error, and Pearson correlation where meaningful. This tested whether a concept that is available from URL text was also reproducible under the repository's local parsing conventions.

### 3.5 Feature Tiers

Five feature tiers were defined:

- Tier A: full usable numerical PhiUSIIL benchmark features.
- Tier B: supplied URL-oriented PhiUSIIL features, including reference-dependent URL-derived attributes.
- Tier C: supplied features defensibly computable from raw URL text.
- Tier D-matched: independently reconstructed versions of Tier C concepts where a semantic mapping was possible.
- Tier E: the project's deployment-extended 26-feature URL-only extractor.

The external experiments used Tier E only.

### 3.6 Classifier and Fixed Hyperparameters

The classifier family was `DecisionTreeClassifier`. Keeping one interpretable classifier family fixed reduced confounding between feature availability and model choice. The selected frozen Tier E model used:

```text
criterion = entropy
max_depth = 10
min_samples_leaf = 1
min_samples_split = 2
ccp_alpha = 0.0
random_state = 42
```

Phishing was the semantic positive class for precision, recall, F1, PR-AUC, and ROC-AUC, even though its numeric label was `0`. Probability-based metrics selected the probability column corresponding to class `0` by inspecting `model.classes_`.

### 3.7 Train/Validation/Test Protocol

For internal random-split experiments, PhiUSIIL was split into training, validation, and test partitions using fixed random seeds and stratification. Test data were not used for model selection after evaluation. Tier comparisons used the same split assignments so that performance differences reflected feature tiers rather than row sampling differences.

### 3.8 Registrable-Domain-Disjoint Protocol

A stricter PhiUSIIL evaluation grouped URLs by offline registrable-domain keys. Whole domain groups were allocated to train, validation, and test partitions, preventing the same registrable domain from appearing in multiple splits. Registrable domains were extracted using the local bundled `publicsuffix2` parser. This was an offline string-parsing operation and did not contact domains.

### 3.9 External-Validation Freeze

The selected PhiUSIIL-trained Tier E Decision Tree was frozen before external validation. URL-Phish and LegitPhish were processed by applying the existing `extract_url_features()` function to raw URL strings, arranging columns in the exact `FEATURE_NAMES` order, and passing the resulting matrix to the same frozen model. No external `.fit()`, retuning, recalibration, threshold adjustment, feature addition, or extractor modification was allowed.

### 3.10 Bootstrap Intervals

Bootstrap confidence intervals were computed for selected internal and external results using fixed bootstrap seeds. These intervals summarized metric uncertainty for the observed datasets. They were not used for model selection.

### 3.11 Class-Conditional Shift Analysis

Class-conditional feature-shift diagnostics compared feature distributions within semantic classes. For each Tier E feature, the analysis calculated class-specific means, medians, quantiles, Kolmogorov-Smirnov statistics, KS p-values, and binary-feature prevalence differences. Comparisons included PhiUSIIL legitimate vs URL-Phish benign, PhiUSIIL legitimate vs LegitPhish legitimate, PhiUSIIL phishing vs URL-Phish phishing, and PhiUSIIL phishing vs LegitPhish phishing.

### 3.12 Dataset-Origin Diagnostic Trees

Dataset-origin diagnostics trained shallow depth-5 Decision Trees to classify source dataset while holding semantic class fixed. These post-hoc trees were not phishing detectors. They were used to quantify whether, for example, PhiUSIIL legitimate and URL-Phish benign rows remained separable by Tier E lexical features even after labels were matched.

### 3.13 Overlap Analysis

The final integrity audit compared PhiUSIIL against URL-Phish and LegitPhish using local strings only. It measured exact stripped URL overlap, stripped-lower normalized URL overlap, registrable-domain overlap, class-conditional same-label overlap, and cross-label conflicts. It also evaluated overlap-controlled external subsets without replacing the primary external results.

### 3.14 Evaluation Metrics

The main metrics were accuracy, phishing precision, phishing recall, phishing F1, ROC-AUC, PR-AUC, balanced accuracy, specificity, and confusion matrices. Confusion matrices were reported in the order:

```text
[[actual phishing predicted phishing, actual phishing predicted legitimate],
 [actual legitimate predicted phishing, actual legitimate predicted legitimate]]
```

For any subset with only one observed class, two-class metrics such as ROC-AUC and balanced accuracy were to be marked undefined rather than assigned a numeric fallback. In the final LegitPhish unseen-domain subset, both classes were present, so ROC-AUC and balanced accuracy were mathematically defined.

## 4. Results

### 4.1 Feature Provenance and Fidelity

The feature-provenance audit found that PhiUSIIL contains a mixture of deployment-reproducible and non-deployment-reproducible columns. Of 55 audited columns, 20 were directly computable from raw URL text, 3 were URL-derived but reference-dependent, 29 were webpage/content-derived, 1 was uncertain, and 2 were identifiers or labels.

The fidelity audit showed that URL-computable in principle did not always mean bit-for-bit reproducible. Digit-count features showed high reconstruction fidelity, while URL length, letter-count, and some ratio features depended on undocumented preprocessing or counting conventions. This motivated separating supplied feature tiers from independently reconstructed and deployment-style features.

### 4.2 Full-Benchmark Feature Dependence

The full supplied Tier A benchmark condition achieved perfect test performance: accuracy 1.000000, phishing F1 1.000000, tree depth 4, and 5 leaves. This result was strongly concentrated in one engineered feature. The root feature was `URLSimilarityIndex`, with feature importance 0.970682. A decision stump using `URLSimilarityIndex` alone reached phishing F1 0.996055.

This finding was treated as feature dependence, not as proof of leakage. The feature is highly discriminative but not reproducible from a single submitted URL string under the repository's safe deployment assumptions.

### 4.3 Reproducible URL-Only Performance

The deployment-style Tier E random-split model performed strongly inside PhiUSIIL. Its phishing F1 was 0.994992 and phishing recall was 0.990622. The reconstructed D-matched condition also performed strongly, with phishing F1 0.993460 and ROC-AUC 0.996919. These results show that removing benchmark-only supplied features did not destroy internal PhiUSIIL performance.

### 4.4 Domain-Disjoint Performance

The Tier E registrable-domain-disjoint result was also high: phishing F1 0.996361 and phishing recall 0.994651. Hypothesis H3, which predicted lower domain-disjoint performance than random-split performance, was not supported. Domain-disjoint evaluation did not expose a major within-PhiUSIIL generalization drop.

### 4.5 URL-Phish External Validation

URL-Phish produced a severe external generalization failure:

| Metric | URL-Phish |
| --- | ---: |
| Accuracy | 0.196509 |
| Phishing precision | 0.149206 |
| Phishing recall | 0.987590 |
| Phishing F1 | 0.259245 |
| ROC-AUC | 0.524568 |
| Balanced accuracy | 0.526390 |
| Confusion matrix | `[[16394, 206], [93481, 6519]]` |

The model missed only 206 phishing URLs but falsely classified 93,481 of 100,000 benign URLs as phishing.

### 4.6 URL-Phish Failure Diagnostics

Class-conditional shift analysis showed that PhiUSIIL legitimate URLs and URL-Phish benign URLs differed strongly. The top legitimate/benign shifts included `path_length` and `number_of_slashes` with KS 0.889860, `uses_https_text` with KS 0.649070, and `special_character_count` with KS 0.618764.

False-positive leaf routing linked this shift to model behavior. The dominant false-positive leaf received 88,986 URL-Phish benign false positives and corresponded to the path `number_of_slashes > 2.5`; in PhiUSIIL training, that leaf contained only phishing rows.

Dataset-origin diagnostics supported the same interpretation. A shallow origin tree distinguished PhiUSIIL legitimate from URL-Phish benign rows with ROC-AUC 0.978597.

### 4.7 LegitPhish External Validation

The full LegitPhish external validation looked strong in aggregate:

| Metric | LegitPhish full |
| --- | ---: |
| Accuracy | 0.993786 |
| Phishing precision | 0.990219 |
| Phishing recall | 1.000000 |
| Phishing F1 | 0.995085 |
| ROC-AUC | 0.991929 |
| Balanced accuracy | 0.991622 |
| Specificity | 0.983245 |
| Confusion matrix | `[[63678, 0], [629, 36911]]` |

The model predicted every phishing row correctly and falsely classified 629 legitimate rows as phishing.

### 4.8 Cross-Dataset Overlap Audit

The final integrity audit found different overlap profiles for the two external datasets:

| Pair | Exact shared URLs | Normalized shared URLs | Shared registrable domains | Exact cross-label conflicts |
| --- | ---: | ---: | ---: | ---: |
| PhiUSIIL vs URL-Phish | 595 | 595 | 7,149 | 0 |
| PhiUSIIL vs LegitPhish | 36,935 | 36,935 | 36,515 | 0 |

Removing exact PhiUSIIL URL overlaps from URL-Phish did not change the qualitative result. URL-Phish F1 remained 0.259247 and ROC-AUC was 0.521688.

Removing exact or normalized PhiUSIIL URL overlaps from LegitPhish did not reduce aggregate phishing F1. The exact-overlap-removed and normalized-overlap-removed LegitPhish subsets both had F1 0.995272. Exact duplication therefore did not explain the aggregate LegitPhish F1, although the resulting subset composition changed substantially.

### 4.9 LegitPhish Subgroup Composition

The LegitPhish domain-overlap analysis produced a critical subgroup finding:

| Subset | Rows | Phishing | Legitimate | Phishing proportion |
| --- | ---: | ---: | ---: | ---: |
| Seen-domain | 37,840 | 688 | 37,152 | 0.018182 |
| Unseen-domain | 63,378 | 62,990 | 388 | 0.993878 |

For the unseen-domain subset, phishing F1 was 0.996930, but specificity was 0.000000, balanced accuracy was 0.500000, and ROC-AUC was 0.500000. The model predicted every unseen-domain sample as phishing.

Thus the high unseen-domain F1 did not indicate useful two-class discrimination. It resulted from extreme class composition: the subset was overwhelmingly phishing, so an all-phishing prediction achieved very high phishing recall and F1 while completely failing on the legitimate minority class.

### 4.10 Hypothesis Outcomes

| Hypothesis | Outcome | Summary evidence |
| --- | --- | --- |
| H1 | Supported narrowly | Tier A F1 1.000000 exceeded Tier E random F1 0.994992. |
| H2 | Partially supported | Some lexical features reconstructed well; others depended on undocumented conventions. |
| H3 | Not supported | Tier E domain-disjoint F1 0.996361 exceeded random F1 0.994992. |
| H4 | Partially supported | URL-Phish was much lower; LegitPhish full remained strong. |
| H5 | Supported | Removing reference/webpage features changed feature-dependence patterns. |
| EX-H1 | Supported | URL-Phish recall 0.987590 was below PhiUSIIL domain-disjoint recall 0.994651. |
| EX-H2 | Supported | URL-Phish F1 0.259245 was far below PhiUSIIL domain-disjoint F1 0.996361. |
| EX-H3 | Partially supported | URL-Phish ROC-AUC exceeded F1 but remained weak at 0.524568. |
| LP-H1 | Supported narrowly | LegitPhish F1 0.995085 was slightly below domain-disjoint F1 0.996361. |
| LP-H2 | Supported | LegitPhish ROC-AUC 0.991929 was below Tier E random ROC-AUC 0.997996. |
| LP-H3 | Not supported in broad-failure form | LegitPhish full performance was strong, unlike URL-Phish. |
| LP-H4 | Supported with qualification | LegitPhish legitimate rows were close to PhiUSIIL legitimate rows, but phishing rows differed strongly. |
