# Beyond Aggregate Accuracy: A Feature-Provenance and Cross-Dataset Generalization Audit of PhiUSIIL Phishing URL Detection

**Author:** [Student Name]  
**Affiliation:** [University / Department]  
**Course:** [Course Name / Data Mining]  
**Supervisor:** [Supervisor Name]

## Abstract

High reported accuracy on phishing URL benchmarks can obscure whether a detector is deployable from raw URL text and whether it generalizes beyond its source dataset. This study audits the PhiUSIIL phishing URL benchmark through feature provenance, feature reconstruction, interpretable Decision Tree evaluation, registrable-domain-disjoint testing, and two fixed-model external validations. The full supplied PhiUSIIL benchmark reached perfect test performance, but the fitted tree was dominated by `URLSimilarityIndex` with importance 0.970682, a feature not reproducible from a single submitted URL under the safe deployment assumptions used here. A reproducible URL-only Decision Tree still achieved strong internal performance, with phishing F1 0.994992 on a random split and 0.996361 on a registrable-domain-disjoint split. External results diverged sharply. On URL-Phish, phishing F1 fell to 0.259245 and ROC-AUC to 0.524568, mainly because 93,481 of 100,000 benign URLs were falsely classified as phishing. Aggregate LegitPhish performance remained strong, with phishing F1 0.995085 and ROC-AUC 0.991929, but subgroup analysis showed that the unseen-domain subset was overwhelmingly phishing, containing 62,990 phishing rows and 388 legitimate rows. Every unseen-domain sample was predicted phishing, producing F1 0.996930 but specificity 0.000000, balanced accuracy 0.500000, and ROC-AUC 0.500000. These findings show that aggregate F1 alone can misrepresent external generalization. Near-perfect within-dataset performance, even under domain-disjoint evaluation, is insufficient evidence of robust cross-dataset phishing detection.

**Keywords:** phishing URL detection, PhiUSIIL, feature provenance, dataset shift, cross-dataset validation, Decision Tree, class imbalance

## 1. Introduction

Phishing remains a persistent cybersecurity problem because deceptive URLs can be created, modified, and distributed quickly. Machine-learning classifiers trained on phishing URL datasets are attractive because they can make rapid decisions from lexical and structural indicators. Many benchmark datasets report very high classification performance, but high aggregate accuracy does not necessarily mean that a model is deployable or robust across independently collected datasets.

Two issues motivate this work. First, phishing URL benchmarks may contain supplied engineered features that are not reproducible from a raw URL alone. A deployed dashboard that receives only a pasted URL cannot safely compute webpage-content features, external reputation scores, similarity indexes requiring hidden references, WHOIS values, DNS-derived attributes, or SSL indicators without contacting the destination or querying outside systems. Second, a model that performs well within one dataset may fail under a different collection process, label policy, time period, benign-source distribution, or phishing-feed distribution.

This paper studies these issues using the PhiUSIIL phishing URL dataset as the source benchmark. The project keeps an interpretable Decision Tree classifier fixed so that performance differences can be attributed primarily to feature availability and evaluation protocol rather than model-family changes. The study asks how much performance survives when features are restricted to URL-only values, whether a registrable-domain-disjoint split reveals hidden weakness, and how the same frozen model behaves on URL-Phish and LegitPhish external datasets.

The core result is not simply that one external dataset failed and another succeeded. URL-Phish produced severe false positives, while full LegitPhish performance looked excellent. However, LegitPhish contained 36,935 exact URLs also found in PhiUSIIL, and its unseen-domain subset was so phishing-skewed that all-phishing predictions achieved high F1 while failing every legitimate unseen-domain row. The final conclusion is therefore cautious: external phishing URL performance is strongly dataset-pair dependent, and aggregate metrics must be interpreted alongside feature provenance, overlap, class composition, and class-conditional shift.

## 2. Related Work

Phishing URL detection has long used lexical and structural URL features. Blum et al. showed that lexical URL information can support fast online phishing detection without waiting for webpage inspection or blacklist updates [1]. Later work continued to show strong within-dataset performance using lightweight lexical features and conventional classifiers [2]. These studies motivate URL-only detection as a practical setting, especially when visiting a suspicious URL is unsafe.

Feature engineering remains central in phishing detection. Benchmarking work by Mohammad et al. emphasized that phishing features may come from URL text, network information, scripts, website content, and other sources [3]. This distinction is important because features differ in deployment availability. A feature that is valid inside a prepared benchmark table may be unavailable in a no-contact raw-URL dashboard.

PhiUSIIL is a large benchmark dataset for phishing URL detection. The UCI repository lists 235,795 instances and identifies the classes as legitimate and phishing [4]. The associated PhiUSIIL paper describes a diverse security profile and similarity-index-based framework [5]. The dataset includes URL-derived, webpage/content-derived, similarity-based, and derived engineered features. This paper therefore treats PhiUSIIL not only as a classification benchmark but also as a feature-provenance case study.

URL-Phish and LegitPhish are recent external URL datasets. URL-Phish is described as a feature-engineered dataset of benign and phishing URLs for machine-learning and language-model evaluation [6]. LegitPhish is described as a large annotated dataset for URL-based phishing detection, with phishing URLs collected from threat repositories and legitimate URLs from reputable sources [7]. Both datasets contain raw URL fields and supplied numerical features. This study uses only raw URL strings from those datasets for external validation.

The broader machine-learning problem is dataset shift. Dataset shift occurs when training and evaluation or deployment data come from different distributions [8]. In phishing URL classification, possible sources include time, source feed, benign collection policy, phishing repository policy, label definitions, normalization, prevalence, and overlap. Grouped evaluation can reduce some forms of leakage or dependence. Scikit-learn's grouped cross-validation documentation emphasizes that samples from the same group should not appear in both training and test folds when group dependence exists [9,10]. This project applies that principle by grouping URLs by offline registrable domain.

Evaluation under imbalance is also central. Balanced accuracy macro-averages class recalls and can reveal failures hidden by prevalence [11]. Precision-recall metrics are often useful when positive-class prevalence differs across datasets [12]. This paper shows why even phishing F1 can be misleading when an external subset is overwhelmingly phishing and the model predicts every sample as phishing.

## 3. Materials and Methods

### 3.1 Datasets

PhiUSIIL was the source benchmark and training dataset. It contained 235,795 rows: 100,945 phishing and 134,850 legitimate. URL-Phish Version 2 was the first external dataset, with 116,600 locally inspected rows after label normalization: 16,600 phishing and 100,000 benign. LegitPhish Version 2 was the second external dataset. The local raw file had 101,219 rows; one row had a missing label, leaving 101,218 analysis rows: 63,678 phishing and 37,540 legitimate.

The project convention treated phishing as numeric label `0` and legitimate/benign as numeric label `1`. Phishing was the semantic positive class for precision, recall, F1, PR-AUC, and ROC-AUC even though its numeric label was `0`.

### 3.2 Safe URL-Only Extraction

All URLs were treated as plain strings. The workflow did not open, request, resolve, ping, scrape, render, or otherwise contact dataset URLs. The deployment-style extractor computed local lexical and structural features only, including length, domain length, path length, query length, character counts, character ratios, subdomain count, query-parameter count, HTTPS text indicator, IP-literal indicator, explicit-port indicator, suspicious-keyword features, and shortener-domain indicator.

### 3.3 Provenance and Fidelity Audit

PhiUSIIL columns were classified into provenance categories: identifier/label/non-model, directly computable raw URL text, URL-derived but reference-dependent, webpage/content-derived, and uncertain. Directly URL-computable features were then reconstructed using local parsing candidates and compared against supplied PhiUSIIL values using exact-match percentage, mean absolute error, median absolute error, and correlation where meaningful.

### 3.4 Feature Tiers

Five feature tiers were evaluated. Tier A used full usable numerical PhiUSIIL benchmark features. Tier B used supplied URL-oriented features, including reference-dependent URL-derived attributes. Tier C used supplied features defensibly computable from raw URL text. Tier D-matched used independently reconstructed versions of Tier C concepts. Tier E used the project's deployment-extended 26-feature URL-only extractor. All external validation used Tier E.

### 3.5 Classifier and Validation Protocols

The classifier was `DecisionTreeClassifier`. The frozen Tier E model used criterion `entropy`, maximum depth 10, minimum samples per leaf 1, minimum samples split 2, `ccp_alpha = 0.0`, and random state 42. Internal experiments used fixed train/validation/test partitions. A registrable-domain-disjoint evaluation grouped URLs by offline registrable-domain keys extracted with `publicsuffix2`; whole domain groups were assigned to partitions so that no registrable domain crossed split boundaries.

External validation froze the selected PhiUSIIL-trained Tier E model. URL-Phish and LegitPhish raw URL strings were transformed with the same extractor and feature order. No external `.fit()`, retuning, recalibration, threshold change, or feature modification was allowed.

### 3.6 Diagnostics

Post-hoc diagnostics included class-conditional KS feature-shift analysis, shallow dataset-origin Decision Trees, false-positive leaf routing, duplicate sensitivity, domain-overlap sensitivity, exact and normalized URL-overlap audits, and overlap-controlled external subset validation. These analyses were diagnostic and did not replace the primary external results.

## 4. Results

### 4.1 Feature Provenance and Fidelity

Of 55 audited PhiUSIIL columns, 20 were directly computable from raw URL text, 3 were URL-derived but reference-dependent, 29 were webpage/content-derived, 1 was uncertain, and 2 were identifiers or labels. Fidelity results showed that some URL concepts were reproducible while others depended on undocumented counting or normalization conventions. Digit counts and digit ratios showed high fidelity, but URL length, letter counts, and some ratio features did not exactly match supplied values under local reconstruction candidates.

### 4.2 Full-Benchmark Feature Dependence

The full supplied Tier A benchmark achieved accuracy 1.000000 and phishing F1 1.000000 with a depth-4 tree containing 5 leaves. The root feature was `URLSimilarityIndex`, whose importance was 0.970682. A decision stump using `URLSimilarityIndex` alone reached phishing F1 0.996055. This was interpreted as strong benchmark feature dependence, not as proof of data leakage.

### 4.3 URL-Only and Domain-Disjoint Performance

The Tier E URL-only model achieved phishing F1 0.994992 and phishing recall 0.990622 on the random PhiUSIIL split. Under registrable-domain-disjoint evaluation, Tier E achieved phishing F1 0.996361 and recall 0.994651. The hypothesis that domain-disjoint performance would be lower than random-split performance was not supported.

### 4.4 URL-Phish External Validation

URL-Phish showed severe transfer degradation. Accuracy was 0.196509, phishing precision 0.149206, recall 0.987590, F1 0.259245, ROC-AUC 0.524568, and balanced accuracy 0.526390. The confusion matrix was `[[16394, 206], [93481, 6519]]`. Thus, 93,481 of 100,000 benign URLs were falsely predicted as phishing.

Class-conditional diagnostics showed large shifts between PhiUSIIL legitimate URLs and URL-Phish benign URLs. The dominant false-positive leaf contained 88,986 URL-Phish benign false positives and corresponded to `number_of_slashes > 2.5`; in PhiUSIIL training this leaf contained only phishing rows. A shallow dataset-origin tree separated PhiUSIIL legitimate from URL-Phish benign with ROC-AUC 0.978597.

### 4.5 LegitPhish External Validation

Full LegitPhish evaluation looked strong: accuracy 0.993786, phishing precision 0.990219, recall 1.000000, F1 0.995085, ROC-AUC 0.991929, balanced accuracy 0.991622, and specificity 0.983245. The confusion matrix was `[[63678, 0], [629, 36911]]`.

The overlap audit found 36,935 exact URL overlaps and 36,935 normalized URL overlaps between PhiUSIIL and LegitPhish. Removing exact or normalized overlapping URLs did not reduce aggregate phishing F1; both overlap-controlled subsets had F1 0.995272. Exact URL duplication therefore did not explain aggregate LegitPhish F1.

### 4.6 LegitPhish Subgroup Composition

Domain-overlap subgroup analysis changed the interpretation. The seen-domain subset contained 37,840 rows: 688 phishing and 37,152 legitimate. The unseen-domain subset contained 63,378 rows: 62,990 phishing and 388 legitimate. For unseen domains, the model predicted every sample as phishing. This produced phishing F1 0.996930, but specificity 0.000000, balanced accuracy 0.500000, and ROC-AUC 0.500000.

The unseen-domain F1 therefore did not indicate useful discrimination. It reflected extreme class composition plus all-phishing predictions. This is the central cautionary example in the study: a high positive-class F1 can coexist with total failure on the minority legitimate class.

### 4.7 Hypothesis Outcomes

H1 was supported narrowly because Tier A outperformed URL-only conditions by small margins. H2 was partially supported because some lexical features reproduced well and others did not. H3 was not supported because domain-disjoint performance did not decline. H4 was partially supported because URL-Phish was far lower than internal performance, whereas full LegitPhish remained strong. H5 was supported because feature-importance patterns changed after non-deployment features were removed.

For URL-Phish, EX-H1 and EX-H2 were supported, while EX-H3 was partially supported because ROC-AUC exceeded F1 but remained weak. For LegitPhish, LP-H1 and LP-H2 were supported narrowly, LP-H3 was not supported in broad-failure form, and LP-H4 was supported with qualification because legitimate-class differences were tiny while phishing-class differences were large.

## 5. Discussion

The results show that full PhiUSIIL benchmark performance is highly dependent on engineered `URLSimilarityIndex`. Removing benchmark-only features still left remarkably high internal URL-only performance, and registrable-domain-disjoint testing did not reduce that performance. Therefore simple domain memorization within PhiUSIIL is not supported as the main explanation for strong internal scores.

The external datasets told a more complicated story. URL-Phish transfer failed mainly through false positives on its benign distribution. PhiUSIIL legitimate and URL-Phish benign source distributions were highly separable, and leaf routing showed that many external benign rows entered phishing leaves learned from PhiUSIIL. This is evidence of dataset-pair-specific class-conditional shift, not proof that URL-Phish is flawed.

LegitPhish aggregate transfer looked excellent. However, class composition and overlap strongly structured its subgroups. Exact URL overlap removal did not materially change aggregate LegitPhish F1, so exact duplication alone does not explain the aggregate result. Yet the unseen-domain subset was overwhelmingly phishing and predicted entirely as phishing, making high F1 misleading. Specificity, balanced accuracy, and ROC-AUC were necessary to reveal the failure to discriminate the small legitimate minority.

The final practical lesson is that neither one successful nor one failed external benchmark should be treated as definitive evidence of deployment robustness. Cross-dataset phishing URL performance depends on dataset construction, class-conditional lexical distributions, domain composition, overlap, and metric choice.

## 6. Threats to Validity

This study used one primary classifier family, an interpretable Decision Tree. Other models may respond differently to the same shift. The Tier E extractor is deployment-safe but still hand-engineered, and other URL-only feature sets could change results. Some PhiUSIIL supplied feature definitions were ambiguous, so reconstruction conclusions depend on tested local parsing candidates.

The external datasets have their own collection biases and represent snapshots from different time periods. Domain overlap is not the same as exact URL overlap, and domain-level conflicts can arise from mixed benign and phishing URLs under the same registrable domain. Label-source quality and source-policy differences remain partially opaque. The public suffix parser uses the installed bundled list, which may differ from future versions. Diagnostic analyses such as leaf routing, KS statistics, and dataset-origin trees were post-hoc. Finally, cross-dataset validation on three datasets is stronger than a single benchmark but is not equivalent to live production deployment.

## 7. Practical Demonstration

The repository includes a Streamlit dashboard as an implementation output. The dashboard accepts a submitted URL string, extracts local lexical features, and displays a model prediction with explanatory observations. It does not send a network request to the submitted URL. The dashboard is a useful demonstration of safe raw-URL-only inference, but it is not treated as the primary research contribution.

## 8. Conclusion

This study audited PhiUSIIL phishing URL detection from benchmark features to deployment-style external validation. The full supplied benchmark achieved perfect performance, but depended heavily on `URLSimilarityIndex`. URL-only features preserved very high internal and domain-disjoint performance. External validation then revealed dataset-pair dependence: URL-Phish failed severely through benign false positives, while LegitPhish appeared strong in aggregate but contained substantial overlap and a highly skewed unseen-domain subgroup where all samples were predicted phishing.

Near-perfect within-dataset performance, even when confirmed using registrable-domain-disjoint evaluation, is insufficient evidence of robust cross-dataset phishing detection. External performance can vary dramatically with dataset construction, class-conditional lexical distributions, domain composition, overlap, and evaluation metric choice.

## References

[1] A. Blum, B. Wardman, T. Solorio, and G. Warner, "Lexical feature based phishing URL detection using online learning," AISec 2010. https://doi.org/10.1145/1866423.1866434

[2] B. B. Gupta, K. Yadav, I. Razzak, K. Psannis, A. Castiglione, and X. Chang, "A novel approach for phishing URLs detection using lexical based machine learning in a real-time environment," Computer Communications, 2021. https://doi.org/10.1016/j.comcom.2021.04.023

[3] R. M. Mohammad, F. Thabtah, and L. McCluskey, "An In-Depth Benchmarking and Evaluation of Phishing Detection Research for Security Needs," IEEE Access, 2020. https://doi.org/10.1109/ACCESS.2020.2969780

[4] A. Prasad and S. Chandra, "PhiUSIIL Phishing URL (Website)," UCI Machine Learning Repository, 2024. https://archive.ics.uci.edu/dataset/967/phiusiil+phishing+url+dataset

[5] A. Prasad and S. Chandra, "PhiUSIIL: A diverse security profile empowered phishing URL detection framework based on similarity index and incremental learning," Computers & Security, 2024. https://doi.org/10.1016/J.COSE.2023.103545

[6] "A feature-engineered dataset of benign and phishing URLs for machine learning and large language models evaluation," Data in Brief, 2025. https://doi.org/10.1016/j.dib.2025.112162

[7] "LegitPhish: A large-scale annotated dataset for URL-based phishing detection," Data in Brief, 2025. https://doi.org/10.1016/j.dib.2025.111972

[8] J. Quiñonero-Candela, M. Sugiyama, A. Schwaighofer, and N. D. Lawrence, eds., *Dataset Shift in Machine Learning*, MIT Press, 2009. https://doi.org/10.7551/mitpress/9780262170055.001.0001

[9] Scikit-learn developers, "GroupKFold." https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html

[10] Scikit-learn developers, "Cross-validation iterators for grouped data." https://scikit-learn.org/stable/modules/cross_validation.html

[11] Scikit-learn developers, "Metrics and scoring: balanced accuracy." https://scikit-learn.org/stable/modules/model_evaluation.html

[12] Scikit-learn developers, "average_precision_score." https://sklearn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html
