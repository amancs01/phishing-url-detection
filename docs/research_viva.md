# Research Viva Preparation Guide

## 30-Second Explanation

My project audits phishing URL detection beyond aggregate accuracy. I trained and froze an interpretable Decision Tree on PhiUSIIL using safe URL-only features, then tested it under random, domain-disjoint, and two external dataset settings. The model performed very well inside PhiUSIIL, failed badly on URL-Phish because benign URLs were mostly predicted phishing, and looked strong on full LegitPhish. But LegitPhish subgroup analysis showed the unseen-domain subset was almost all phishing and every sample was predicted phishing, giving high F1 but zero specificity and ROC-AUC 0.5. The main finding is that cross-dataset phishing URL performance is strongly dataset-pair dependent, and aggregate F1 alone can be misleading.

## 2-Minute Explanation

This research began with a Decision Tree phishing URL detector, but the final project is a benchmark audit. I used PhiUSIIL as the source dataset and asked whether its features and results are realistic for a deployed tool that receives only a raw URL string. First, I audited feature provenance and found that many supplied PhiUSIIL features are webpage/content-derived or reference-dependent, so they are not safely reproducible from a pasted URL. I therefore focused on Tier E, a 26-feature URL-only extractor.

The URL-only model performed very strongly inside PhiUSIIL, with phishing F1 0.994992 on a random split and 0.996361 on a registrable-domain-disjoint split. That rejected my expectation that domain-disjoint splitting would reduce performance. Then I froze the model and evaluated it on URL-Phish and LegitPhish without retraining. URL-Phish failed badly: F1 was 0.259245 because 93,481 of 100,000 benign rows were falsely predicted phishing. Diagnostics showed strong class-conditional shift between PhiUSIIL legitimate and URL-Phish benign rows.

LegitPhish full performance looked excellent, with F1 0.995085. But a final overlap and subgroup audit showed 36,935 exact URL overlaps with PhiUSIIL and, more importantly, an unseen-domain subgroup with 62,990 phishing rows and only 388 legitimate rows. The model predicted every unseen-domain row as phishing, so F1 was 0.996930 but specificity was 0 and ROC-AUC was 0.5. The final conclusion is that neither internal performance nor one aggregate external F1 is enough; we need feature provenance, overlap analysis, subgroup composition, and multiple metrics.

## 5-Minute Explanation

The title of my research is *Beyond Aggregate Accuracy: A Feature-Provenance and Cross-Dataset Generalization Audit of PhiUSIIL Phishing URL Detection*. The motivation is that phishing URL datasets often report very high performance, but a deployed URL checker receives only a raw URL string. It cannot safely visit the page, run WHOIS, query DNS, inspect SSL certificates, fetch favicons, or use hidden benchmark features. So the first question was: which PhiUSIIL features are actually reproducible from raw URL text?

I created a feature-provenance taxonomy and found that PhiUSIIL contains directly URL-computable features, reference-dependent URL features, webpage/content-derived features, uncertain features, and non-model fields. The full Tier A benchmark reached perfect performance, but the tree was dominated by `URLSimilarityIndex`, with importance 0.970682. I did not call that leakage; I treated it as a strong engineered benchmark feature that is not reproducible from one submitted URL under my no-contact deployment setting.

Next, I evaluated URL-only feature tiers. The deployment-style Tier E model used 26 local lexical features and an interpretable Decision Tree with fixed hyperparameters. It achieved F1 0.994992 on a random PhiUSIIL split and 0.996361 on a registrable-domain-disjoint split. Since domain-disjoint performance did not drop, simple domain memorization was not supported as the main explanation for strong internal scores.

Then I froze the model and ran external validation. URL-Phish performed poorly: accuracy 0.196509, precision 0.149206, recall 0.987590, F1 0.259245, and ROC-AUC 0.524568. The confusion matrix showed 93,481 benign false positives. Diagnostics showed class-conditional shift: URL-Phish benign rows were very different from PhiUSIIL legitimate rows, and a dominant false-positive leaf used the path `number_of_slashes > 2.5`, which had been a pure phishing leaf in PhiUSIIL.

LegitPhish full performance looked strong: F1 0.995085 and ROC-AUC 0.991929. But the final integrity audit found 36,935 exact URL overlaps with PhiUSIIL. Removing them did not reduce aggregate F1; it was still 0.995272. The bigger issue was subgroup composition. Seen-domain LegitPhish rows were mostly legitimate, but unseen-domain rows were 62,990 phishing and only 388 legitimate. The model predicted every unseen-domain row as phishing. That produced F1 0.996930 but specificity 0, balanced accuracy 0.5, and ROC-AUC 0.5.

So the final answer is nuanced. The model can transfer well in aggregate on one external dataset and fail badly on another. But aggregate F1 can hide subgroup failure under imbalance. My final claim is that near-perfect within-dataset performance, even under domain-disjoint evaluation, is insufficient evidence of robust deployment generalization. External performance varies with dataset construction, class-conditional lexical distributions, domain composition, overlap, and metric choice.

## Viva Questions and Answers

### 1. Why did you use a Decision Tree?

Decision Trees are interpretable, syllabus-appropriate for a Data Mining project, and make failure analysis easier. Their leaf paths and feature thresholds can be inspected directly, which helped explain URL-Phish false positives.

### 2. What is feature provenance?

Feature provenance means identifying where a feature comes from and whether it can be reproduced at inference time. In this project, a feature was deployment-realistic only if it could be computed from the submitted URL string without network or webpage access.

### 3. What is dataset shift?

Dataset shift occurs when the training distribution differs from the evaluation or deployment distribution. In phishing URLs, this can come from different collection sources, time periods, URL normalization policies, label policies, or class prevalence.

### 4. What is covariate shift?

Covariate shift means the feature distribution changes between datasets. Here, examples include changes in path length, slash count, HTTPS usage, and IP-literal prevalence across datasets.

### 5. What is class-conditional shift?

Class-conditional shift means the feature distribution changes within the same label class. For example, PhiUSIIL legitimate URLs and URL-Phish benign URLs differed strongly even though they represent the same semantic class.

### 6. Why was H3 rejected?

H3 predicted that random-split performance would exceed domain-disjoint performance. It was rejected because Tier E phishing F1 was 0.994992 on the random split and 0.996361 on the domain-disjoint split.

### 7. Why did URL-Phish fail?

It failed mainly through benign false positives. The model predicted 93,481 of 100,000 URL-Phish benign rows as phishing. Diagnostics showed that URL-Phish benign rows were lexically different from PhiUSIIL legitimate rows and often routed into phishing leaves.

### 8. Why is LegitPhish F1 misleading?

The full LegitPhish F1 was high, but the unseen-domain subgroup was extremely imbalanced: 62,990 phishing rows and 388 legitimate rows. Since the model predicted every unseen-domain row as phishing, phishing F1 was high while legitimate specificity was zero.

### 9. How can F1 be 99.7% when ROC-AUC is 0.5?

F1 uses the final predicted labels and focuses on the positive class. If almost every row is phishing and the model predicts everything phishing, phishing recall and precision can be high. ROC-AUC measures two-class ranking ability; here the model did not discriminate the tiny legitimate class, so ROC-AUC was 0.5.

### 10. Why is specificity important?

Specificity measures the true negative rate for legitimate URLs. In phishing detection, low specificity means legitimate URLs are falsely flagged, which can make the tool unusable or misleading.

### 11. Why is accuracy bad under imbalance?

Accuracy can be dominated by the majority class. In a highly imbalanced subset, a trivial majority-class predictor can have high accuracy or F1-like behavior while failing the minority class.

### 12. What is domain-disjoint splitting?

Domain-disjoint splitting groups URLs by registrable domain and ensures that a domain group appears in only one split. This tests whether the model generalizes to unseen domains within the same dataset.

### 13. What is a registrable domain?

A registrable domain is the base domain that can be registered under a public suffix, such as `example.com` or `example.co.uk`. Subdomains map back to the same registrable domain.

### 14. Why did you use publicsuffix2?

I used `publicsuffix2` because it provides offline Public Suffix List parsing. That lets the project group domains locally without DNS or network access.

### 15. What is URLSimilarityIndex?

It is a supplied PhiUSIIL engineered feature related to URL similarity. It dominated the full Tier A tree, but its exact reference or formula is not reproducible from one raw URL string in this project.

### 16. Why did you not call URLSimilarityIndex data leakage?

Because high feature importance does not prove leakage. The careful claim is that it is an engineered benchmark feature that strongly separates the supplied dataset and is not deployment-reproducible under the raw-URL-only setting.

### 17. What is the difference between exact URL overlap and domain overlap?

Exact URL overlap means the same URL string appears in both datasets. Domain overlap means the same registrable domain appears, even if the exact URL paths differ. Domain overlap is broader and can include different pages or labels under the same domain.

### 18. Why did removing 36,935 overlapping URLs not reduce LegitPhish F1?

Those overlaps were legitimate-to-legitimate. Removing them left a subset dominated by phishing rows, and the model predicted all or nearly all remaining rows as phishing. That preserved high phishing F1 while collapsing specificity.

### 19. Why is cross-dataset testing not the same as deployment testing?

External datasets are still curated snapshots with their own source policies and biases. Real deployment has evolving threats, user-submitted URLs, adversarial adaptation, and operational consequences.

### 20. What is post-hoc analysis?

Post-hoc analysis happens after the primary result and is used to diagnose or explain it. It should not replace the preregistered primary metric or drive retuning.

### 21. What is a bootstrap confidence interval?

A bootstrap confidence interval estimates metric variability by repeatedly resampling the observed evaluation data and recalculating the metric. It gives an empirical uncertainty interval for the dataset at hand.

### 22. What does a KS statistic measure?

The Kolmogorov-Smirnov statistic measures the maximum difference between two empirical cumulative distributions. A larger KS value indicates stronger distributional difference for that feature.

### 23. Why was phishing label 0 treated as positive?

The dataset convention uses `0 = phishing` and `1 = legitimate`. Metrics were configured so phishing remained the semantic positive class despite being numeric label 0.

### 24. Did you retrain on external data?

No. URL-Phish and LegitPhish were evaluation-only. The model, threshold, feature list, and extractor were frozen.

### 25. Did you contact any phishing URLs?

No. All dataset URLs were treated as strings. The scripts used local parsing only and did not perform HTTP requests, DNS, WHOIS, SSL checks, browser automation, or reputation lookups.

### 26. What is the main contribution?

The contribution is a controlled audit connecting feature provenance, feature reproducibility, benchmark feature dependence, domain-disjoint validation, fixed-model external validation, class-conditional shift, overlap, and subgroup metric interpretation.

### 27. What would you improve in future work?

Future work should test more model families, more external datasets, temporal splits, richer but safe features, calibrated uncertainty, and deployment-like user-submitted URL streams.

### 28. Why not use webpage content?

The safety constraint was no-contact URL analysis. Webpage content may improve performance, but it requires interacting with potentially malicious sites and changes the deployment scenario.

### 29. What is the most important numerical result?

The contrast between URL-Phish and LegitPhish subgroup behavior is most important. URL-Phish F1 was 0.259245 due to benign false positives, while LegitPhish unseen-domain F1 was 0.996930 despite zero specificity because the subset was almost all phishing.

### 30. What is your final conclusion?

Near-perfect within-dataset performance, even under domain-disjoint evaluation, is insufficient evidence of robust cross-dataset phishing detection. External validation must include overlap, class composition, feature shift, and multiple metrics.
