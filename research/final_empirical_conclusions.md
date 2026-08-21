# Final Empirical Conclusions

## Scope

This document freezes the empirical interpretation before manuscript writing. It does not introduce another dataset, retrain a model, retune hyperparameters, recalibrate probabilities, change thresholds, or modify feature definitions.

The final model interpretation concerns the frozen PhiUSIIL-trained Tier E Decision Tree evaluated with the same 26 local URL-string features across internal, domain-disjoint, URL-Phish, and LegitPhish settings.

## 1. Feature Provenance Findings

The PhiUSIIL provenance audit showed that many supplied benchmark columns are not deployment-reproducible from a pasted URL alone. Of 55 audited columns, 20 were directly computable from raw URL text, 3 were URL-derived but reference-dependent, 29 were webpage/content-derived, 1 was uncertain, and 2 were identifiers or labels.

The deployment claim therefore cannot rest on the full supplied benchmark feature set. The safest deployed condition is Tier E, the project extractor's 26 URL-only features.

## 2. Feature Reconstruction Findings

Several apparently simple supplied URL features were computable in principle but did not reproduce PhiUSIIL values exactly under independently tested definitions. `NoOfDegitsInURL` and `DegitRatioInURL` showed high fidelity, while `URLLength`, `NoOfLettersInURL`, `LetterRatioInURL`, and `SpacialCharRatioInURL` showed substantial convention mismatch. This supports the distinction between feature availability and bit-for-bit reproducibility.

## 3. Tier A Perfect Separation

The full supplied Tier A condition reached perfect random-split performance: accuracy, phishing precision, phishing recall, phishing F1, and ROC-AUC were all 1.0. That result is a benchmark finding, not a deployment guarantee.

## 4. URLSimilarityIndex Domination

The Tier A tree was dominated by `URLSimilarityIndex` with importance 0.970682. This feature is URL-derived but reference/definition dependent. A one-feature stump on `URLSimilarityIndex` alone reached test F1 0.996055. The finding does not prove leakage, but it explains why full supplied benchmark performance is not enough for deployment-realistic claims.

## 5. Reproducible URL-Only Performance

The URL-only conditions still performed strongly inside PhiUSIIL. Tier D-matched reached random-split phishing F1 0.993460 and ROC-AUC 0.996919. Tier E reached random-split phishing F1 0.994992 and ROC-AUC 0.997996.

## 6. Random vs Domain-Disjoint Result

The expectation that domain-disjoint evaluation would be lower than random evaluation was not supported. Tier E domain-disjoint phishing F1 was 0.996361, slightly above the Tier E random-split F1 of 0.994992. This means domain overlap inside PhiUSIIL was not the sole explanation for strong internal performance.

## 7. URL-Phish External Result

The frozen Tier E model transferred poorly to URL-Phish Version 2:

| Metric | URL-Phish |
| --- | ---: |
| Accuracy | 0.196509 |
| Phishing precision | 0.149206 |
| Phishing recall | 0.987590 |
| Phishing F1 | 0.259245 |
| ROC-AUC | 0.524568 |
| PR-AUC | 0.148627 |
| Balanced accuracy | 0.526390 |
| Confusion matrix | `[[16394, 206], [93481, 6519]]` |

The model preserved phishing recall but overpredicted phishing for benign rows.

## 8. URL-Phish Failure Mechanism

Post-hoc diagnostics support a class-conditional covariate-shift mechanism. URL-Phish benign rows were lexically far from PhiUSIIL legitimate rows, especially in path/slash structure and HTTPS usage. Leaf routing showed that 88,986 benign false positives entered a leaf that was pure phishing in PhiUSIIL training and whose path was `number_of_slashes > 2.5`.

Dataset-origin diagnostics also showed strong benign/legitimate source separability between PhiUSIIL and URL-Phish: origin AUC 0.978597.

## 9. LegitPhish External Result

The frozen Tier E model transferred strongly to LegitPhish Version 2:

| Metric | LegitPhish full |
| --- | ---: |
| Accuracy | 0.993786 |
| Phishing precision | 0.990219 |
| Phishing recall | 1.000000 |
| Phishing F1 | 0.995085 |
| ROC-AUC | 0.991929 |
| PR-AUC | 0.990573 |
| Balanced accuracy | 0.991622 |
| Specificity | 0.983245 |
| Confusion matrix | `[[63678, 0], [629, 36911]]` |

This contradicts a blanket claim that PhiUSIIL-trained URL-only models cannot generalize to external datasets.

## 10. LegitPhish Overlap Audit

The final integrity audit found substantial exact overlap between PhiUSIIL and LegitPhish:

| Pair | Exact shared URLs | Normalized shared URLs | Shared registrable domains | Exact cross-label conflicts | Normalized cross-label conflicts | Domain cross-label conflicts |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| PhiUSIIL vs URL-Phish | 595 | 595 | 7,149 | 0 | 0 | 97 |
| PhiUSIIL vs LegitPhish | 36,935 | 36,935 | 36,515 | 0 | 0 | 41 |

All exact and normalized PhiUSIIL-LegitPhish URL overlaps were legitimate-to-legitimate. No exact or normalized cross-label conflicts were found.

LegitPhish seen-domain rows were mostly legitimate: 37,840 total rows, 688 phishing, and 37,152 legitimate. LegitPhish unseen-domain rows were extremely phishing-skewed: 63,378 total rows, 62,990 phishing, and 388 legitimate.

## 11. Overlap-Controlled LegitPhish Result

Removing exact URLs present in PhiUSIIL left LegitPhish performance strong by phishing F1 but exposed extreme subset imbalance:

| LegitPhish subset | Rows | Phishing | Legitimate | F1 | Specificity | Balanced accuracy | ROC-AUC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Full primary | 101,218 | 63,678 | 37,540 | 0.995085 | 0.983245 | 0.991622 | 0.991929 |
| Remove exact PhiUSIIL URLs | 64,283 | 63,678 | 605 | 0.995272 | 0.000000 | 0.500000 | 0.500000 |
| Remove normalized PhiUSIIL URLs | 64,283 | 63,678 | 605 | 0.995272 | 0.000000 | 0.500000 | 0.500000 |
| Unseen registrable domains | 63,378 | 62,990 | 388 | 0.996930 | 0.000000 | 0.500000 | 0.500000 |

The previous unseen-domain ROC-AUC of 0.5 was not a single-class fallback. It was a valid two-class calculation on a subset containing both classes, but the model predicted every row as phishing. This makes F1 misleadingly high under heavy phishing prevalence.

## 12. Cross-Dataset Comparison

The strongest final pattern is dataset-pair dependence:

- URL-Phish: low precision, low F1, low ROC-AUC, severe benign false positives.
- LegitPhish full: strong accuracy, F1, ROC-AUC, and specificity.
- LegitPhish overlap-removed/unseen subsets: high phishing F1 remains, but specificity, balanced accuracy, and ROC-AUC collapse because the remaining subsets are overwhelmingly phishing and predicted all phishing.

The exact overlap audit means LegitPhish cannot be described as fully independent of PhiUSIIL at the raw-URL level. The overlap-controlled sensitivity also shows that high phishing F1 alone is not enough; class composition and two-class discrimination metrics must be reported with it.

## 13. Hypothesis Table

| Hypothesis | Outcome | Evidence |
| --- | --- | --- |
| H1: Full supplied PhiUSIIL features outperform independently reproducible raw-URL features. | Supported narrowly | Tier A F1 was 1.0; deployment-style Tier E random F1 was 0.994992 and D-matched F1 was 0.993460. |
| H2: Simple lexical features show high reproduction fidelity. | Partially supported | Digit counts and ratios were high fidelity, but URL length, letter counts, and some ratio conventions did not exactly reproduce supplied values. |
| H3: Random-split performance exceeds domain-disjoint performance. | Not supported | Tier E domain-disjoint F1 0.996361 exceeded random-split F1 0.994992. |
| H4: External-dataset performance is lower than internal random-holdout performance. | Partially supported | URL-Phish was far lower; LegitPhish had lower ROC-AUC and accuracy but similar/slightly higher phishing F1 than internal random. |
| H5: Decision Tree feature-importance rankings change after reference/webpage features are removed. | Supported | Tier A was dominated by `URLSimilarityIndex`, while URL-only conditions necessarily used different lexical feature families. |
| EX-H1: URL-Phish recall is lower than PhiUSIIL domain-disjoint recall. | Supported | URL-Phish recall 0.987590 was below PhiUSIIL domain-disjoint recall 0.994651. |
| EX-H2: URL-Phish F1 is lower than PhiUSIIL domain-disjoint F1. | Supported | URL-Phish F1 0.259245 was far below PhiUSIIL domain-disjoint F1 0.996361. |
| EX-H3: ROC-AUC remains higher than F1 if prevalence shift mainly affects threshold behavior. | Partially supported | URL-Phish ROC-AUC 0.524568 exceeded F1 0.259245, but ROC-AUC was still weak, so the failure was not merely a threshold/prevalence artifact. |
| LP-H1: LegitPhish F1 is lower than PhiUSIIL domain-disjoint F1. | Supported narrowly | LegitPhish F1 0.995085 was below domain-disjoint F1 0.996361 by 0.001276. |
| LP-H2: LegitPhish ROC-AUC is lower than PhiUSIIL internal ROC-AUC. | Supported | LegitPhish ROC-AUC 0.991929 was below Tier E random ROC-AUC 0.997996. |
| LP-H3: If URL-Phish failure is broad, LegitPhish also shows a meaningful generalization gap. | Not supported in broad-failure form | LegitPhish full performance was strong, so URL-Phish failure cannot be generalized to all external datasets. |
| LP-H4: PhiUSIIL and LegitPhish class-conditional lexical distributions differ. | Supported with qualification | Legitimate-class differences were tiny; phishing-class differences were large. |

## 14. Rejected Hypotheses

H3 was rejected because domain-disjoint evaluation did not reduce Tier E performance. LP-H3 was rejected in its broad-failure form because LegitPhish full performance was strong. A simplistic version of H4 is also rejected if interpreted as all external datasets being lower on all metrics.

## 15. Claims Supported By Evidence

The evidence supports these claims:

- Full PhiUSIIL benchmark performance depends heavily on supplied features that are not deployment-reproducible from a raw URL alone.
- A deployment-style URL-only Decision Tree performs very strongly inside PhiUSIIL under both random and registrable-domain-disjoint evaluation.
- URL-Phish exhibits severe cross-dataset degradation for the frozen PhiUSIIL model.
- The URL-Phish degradation is associated with class-conditional lexical shift, especially in benign rows.
- LegitPhish full-dataset transfer is strong, but LegitPhish has substantial exact and domain overlap with PhiUSIIL.
- After removing exact or normalized PhiUSIIL URL overlaps from LegitPhish, high phishing F1 persists but two-class discrimination collapses on the remaining highly phishing-skewed subset.
- Cross-dataset performance is strongly dataset-pair dependent.

## 16. Claims Not Supported By Evidence

The evidence does not support these claims:

- PhiUSIIL-trained URL-only models cannot generalize.
- Domain overlap alone causes high performance.
- URL-Phish is a bad dataset.
- LegitPhish is fully independent of PhiUSIIL at the raw-URL level.
- High phishing F1 alone is sufficient to claim robust external discrimination.
- The study proves feature leakage in PhiUSIIL.
- The study proves real-world deployment security.

## 17. Threats To Validity

The study uses one classifier family and one deployment extractor. External datasets have their own collection policies, time periods, label definitions, URL normalization conventions, and source mixtures. LegitPhish contains substantial exact overlap with PhiUSIIL, especially among legitimate URLs. Some overlap-controlled LegitPhish subsets are extremely imbalanced, so phishing F1 is prevalence-sensitive. Dataset-origin and leaf-routing analyses are diagnostic rather than causal. The conclusions therefore apply to controlled dataset validation, not live production security.

## 18. Final Research Contribution

The final contribution is a controlled audit connecting feature provenance, feature reproducibility, benchmark feature dependence, random evaluation, registrable-domain-disjoint evaluation, multiple fixed-model external validations, class-conditional distribution shift, and external overlap sensitivity.

The evidence-supported high-level conclusion is:

Cross-dataset performance of URL-based phishing classifiers is strongly dataset-pair dependent. Near-perfect within-dataset results, even under domain-disjoint evaluation, are insufficient evidence of robust deployment generalization. External validation must report feature provenance, overlap, class composition, and class-conditional shift alongside conventional metrics.
