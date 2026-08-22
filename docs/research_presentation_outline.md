# Research Presentation Outline

## Slide 1: Title

Key bullets:
- Beyond Aggregate Accuracy
- Feature-provenance and cross-dataset audit of PhiUSIIL phishing URL detection
- Interpretable Decision Tree, URL-only deployment setting
- [Student Name], [University], [Course]

Figure/table to show:
- Title slide with a simple workflow: benchmark -> audit -> external validation -> conclusions.

Speaker explanation:
- Introduce the project as a Data Mining research audit, not just a classifier build. Emphasize that the goal is to understand when high phishing URL metrics are trustworthy.

## Slide 2: Problem

Key bullets:
- Phishing URL detection is often reported with high benchmark accuracy.
- Benchmarks may include features unavailable to a real raw-URL tool.
- Random splits can hide dataset-specific patterns.
- External datasets may differ in source, prevalence, and lexical structure.

Figure/table to show:
- Small diagram contrasting benchmark table features with a real pasted URL.

Speaker explanation:
- Explain that a dashboard receiving a URL string cannot safely contact the site or fetch hidden information, so benchmark features must be audited.

## Slide 3: Why 99% Accuracy May Be Misleading

Key bullets:
- Accuracy can be inflated by class balance or easy benchmark features.
- F1 can be misleading under extreme subgroup prevalence.
- A model can have high phishing recall but poor legitimate specificity.
- External validation must include confusion matrices and subgroup metrics.

Figure/table to show:
- LegitPhish unseen-domain row: F1 `0.996930`, specificity `0.000000`, ROC-AUC `0.500000`.

Speaker explanation:
- Use the unseen-domain example early: the model predicted every row phishing, which looked excellent by phishing F1 because the subset was almost all phishing.

## Slide 4: Research Questions

Key bullets:
- Which PhiUSIIL features are deployable from raw URL text?
- How faithful are reconstructed URL features?
- Does URL-only performance survive benchmark feature removal?
- Does domain-disjoint evaluation reveal weakness?
- How does the frozen model transfer to URL-Phish and LegitPhish?

Figure/table to show:
- Research question list mapped to experiment stages.

Speaker explanation:
- Frame the project as a controlled audit. The same model family is kept fixed to reduce confounding.

## Slide 5: Dataset Overview

Key bullets:
- PhiUSIIL: `235,795` rows; `100,945` phishing; `134,850` legitimate.
- URL-Phish: `116,600` rows; `16,600` phishing; `100,000` benign.
- LegitPhish: `101,218` analysis rows; `63,678` phishing; `37,540` legitimate.
- Labels normalized to `0 = phishing`, `1 = legitimate`.

Figure/table to show:
- Dataset count table.

Speaker explanation:
- Point out that external datasets are evaluation-only. They are never used for training or tuning.

## Slide 6: Feature Provenance

Key bullets:
- PhiUSIIL includes URL, webpage/content, derived, and reference-dependent features.
- Only raw-URL-computable features are deployment-realistic.
- Audit result: 20 direct URL features, 3 reference-dependent, 29 webpage/content, 1 uncertain, 2 non-model.
- Tier E uses 26 safe local URL-text features.

Figure/table to show:
- Feature-provenance count table or pie chart.

Speaker explanation:
- Explain feature provenance as asking where a feature comes from and whether it can be computed safely at inference time.

## Slide 7: Methodology

Key bullets:
- Decision Tree classifier kept fixed and interpretable.
- Fixed Tier E hyperparameters: entropy, max depth 10, random state 42.
- Random split and registrable-domain-disjoint split.
- Frozen external validation on URL-Phish and LegitPhish.
- Post-hoc shift, origin, leaf-routing, overlap, and subgroup analyses.

Figure/table to show:
- End-to-end pipeline diagram.

Speaker explanation:
- Emphasize no retraining on external data, no threshold tuning, and no feature changes after results.

## Slide 8: Internal and Domain Results

Key bullets:
- Tier E random F1 `0.994992`, recall `0.990622`.
- Tier E domain-disjoint F1 `0.996361`, recall `0.994651`.
- H3 was not supported: domain-disjoint did not reduce performance.
- Simple domain memorization is not supported as the main explanation.

Figure/table to show:
- Random vs domain-disjoint metric table or bar chart.

Speaker explanation:
- This result is surprising because stricter domain splitting often lowers performance. Here it did not, so the later external failures need another explanation.

## Slide 9: Full Benchmark Feature Dependence

Key bullets:
- Tier A accuracy and F1 were `1.000000`.
- Tree depth was 4 with 5 leaves.
- Root feature: `URLSimilarityIndex`.
- `URLSimilarityIndex` importance: `0.970682`.
- Stump F1 using `URLSimilarityIndex`: `0.996055`.

Figure/table to show:
- Tier A tree root or feature-importance table.

Speaker explanation:
- Be careful: do not call this leakage. Say it shows strong dependence on an engineered feature that is not reproducible from a single raw URL in this project.

## Slide 10: URL-Phish Result

Key bullets:
- Accuracy `0.196509`.
- Precision `0.149206`; recall `0.987590`; F1 `0.259245`.
- ROC-AUC `0.524568`; balanced accuracy `0.526390`.
- Confusion matrix `[[16394, 206], [93481, 6519]]`.
- Most benign URLs were predicted phishing.

Figure/table to show:
- URL-Phish confusion matrix heatmap.

Speaker explanation:
- The model was sensitive to phishing but not specific to legitimate URLs. It caught almost all phishing but treated benign URL-Phish rows as phishing.

## Slide 11: Why URL-Phish Failed

Key bullets:
- PhiUSIIL legitimate vs URL-Phish benign distributions shifted strongly.
- Top shifts: path length, slash count, HTTPS text, special characters.
- Dominant false-positive leaf: `number_of_slashes > 2.5`.
- That leaf had 88,986 URL-Phish benign false positives.
- Dataset-origin AUC for legitimate/benign: `0.978597`.

Figure/table to show:
- Benign feature-shift plot or false-positive leaf-routing table.

Speaker explanation:
- Connect feature shift to tree behavior. The model learned that high slash count meant phishing inside PhiUSIIL, but URL-Phish benign rows often looked like that.

## Slide 12: LegitPhish Aggregate Result

Key bullets:
- Accuracy `0.993786`.
- Precision `0.990219`; recall `1.000000`; F1 `0.995085`.
- ROC-AUC `0.991929`; specificity `0.983245`.
- Confusion matrix `[[63678, 0], [629, 36911]]`.
- Exact overlap with PhiUSIIL: `36,935` URLs.

Figure/table to show:
- LegitPhish full confusion matrix and overlap count.

Speaker explanation:
- At first glance this looks like excellent transfer. Then transition to the overlap and subgroup caution.

## Slide 13: LegitPhish Subgroup Trap

Key bullets:
- Seen-domain: `37,840` rows; `688` phishing; `37,152` legitimate.
- Unseen-domain: `63,378` rows; `62,990` phishing; `388` legitimate.
- Every unseen-domain sample was predicted phishing.
- Unseen-domain F1 `0.996930`, but specificity `0.000000`.
- Balanced accuracy and ROC-AUC both `0.500000`.

Figure/table to show:
- Seen/unseen composition table plus unseen-domain metric row.

Speaker explanation:
- This is the most important slide. Explain that high F1 is caused by class composition and all-phishing predictions. The model did not discriminate the legitimate minority.

## Slide 14: Main Research Finding and Limitations

Key bullets:
- Cross-dataset performance is strongly dataset-pair dependent.
- Domain-disjoint internal success did not guarantee external robustness.
- URL-Phish failed through benign false positives.
- LegitPhish full looked strong, but subgroup metrics were more nuanced.
- Limitations: one model family, three datasets, post-hoc diagnostics, dataset snapshots.

Figure/table to show:
- Three-dataset metric comparison.

Speaker explanation:
- Avoid overclaiming. The point is not that Decision Trees cannot generalize or that a dataset is flawed; it is that evaluation must be richer than aggregate accuracy or F1.

## Slide 15: Conclusion

Key bullets:
- Audit features before making deployment claims.
- Use domain-disjoint and external validation.
- Check overlap and class-conditional shift.
- Report specificity, balanced accuracy, ROC-AUC, and confusion matrices.
- Final claim: near-perfect benchmark results are insufficient evidence of robust deployment generalization.

Figure/table to show:
- Final checklist for robust phishing URL evaluation.

Speaker explanation:
- Close with the practical lesson: robust claims need feature provenance, fixed-model external validation, overlap analysis, and honest metric interpretation.
