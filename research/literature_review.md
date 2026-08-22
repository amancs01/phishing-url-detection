# Literature Review

## Scope

This review supports the paper titled **Beyond Aggregate Accuracy: A Feature-Provenance and Cross-Dataset Generalization Audit of PhiUSIIL Phishing URL Detection**. It focuses on phishing URL classification, interpretable lexical features, feature provenance, dataset shift, grouped evaluation, cross-dataset overlap, and metric interpretation under imbalance.

The review is conservative. It does not claim that this project is the first phishing detection study, the first dataset-shift study, or the first domain-disjoint evaluation. The gap is narrower: this work combines a PhiUSIIL feature-provenance and reconstruction audit with a fixed interpretable classifier evaluated under random, registrable-domain-disjoint, and multiple external-dataset conditions, followed by overlap and subgroup composition analysis.

## Phishing URL Classification

Phishing URL classification is commonly framed as a supervised binary classification problem: a URL or website instance is represented by features and assigned to phishing or legitimate/benign classes. Earlier lexical approaches argued that URL strings can provide useful signals without requiring webpage downloads. Blum et al. demonstrated lexical-feature phishing URL detection using online learning, emphasizing fast adaptation to new threats without relying only on reactive blacklists [1]. Later studies extended lexical, host, webpage, and content-derived features, often comparing classical learners, ensembles, and neural models.

Benchmarking work in phishing detection has also warned that feature categories differ in deployment availability. Mohammad et al.'s security-needs benchmarking discussion distinguishes URL, network, script, and website feature families and gives examples such as URL length, ports, WHOIS-like network features, and webpage/script-derived indicators [2]. This distinction matters because a system that receives only a submitted URL string cannot reproduce webpage or reputation features without contacting the destination or querying external services.

## Lexical URL Features

Lexical URL features remain attractive because they are inexpensive, privacy-preserving relative to page fetching, and usable before interacting with a potentially malicious host. Common lexical signals include URL length, domain length, character ratios, digit counts, special characters, query parameters, suspicious tokens, subdomain counts, HTTPS text, and IP-literal hostnames. Gupta et al. reported high performance with a small set of lexical URL features and several machine-learning classifiers, illustrating the long-standing appeal of lightweight URL-only detection [3]. Ahmed and Jameel similarly focused on malicious URL detection with lexical features and Decision Tree-based feature selection, motivated by speed and practicality [4].

The limitation is that lexical models can learn dataset-specific source patterns. A curated benign collection and a phishing feed may differ in URL length, path structure, HTTPS prevalence, subdomain usage, or IP literals for reasons related to collection process rather than phishing semantics alone. This project therefore treats lexical features as deployment-feasible but not automatically deployment-robust.

## Decision Trees and Interpretability

Decision Trees are a natural fit for a university Data Mining project because they are transparent, fast at inference time, and directly interpretable as feature-threshold rules. Recent PhiUSIIL-oriented educational comparisons describe Decision Trees as interpretable classifiers that recursively split samples into increasingly pure subsets and can expose how URL and webpage features influence phishing decisions [5]. The interpretability advantage is important in this project because false-positive leaf routing can be inspected after external failure.

However, interpretability does not guarantee generalization. A shallow tree can still learn a dataset artifact if a supplied feature nearly separates the benchmark. Conversely, a Decision Tree's explicit leaf paths make this risk easier to audit than in many opaque models.

## PhiUSIIL and Feature Engineering

The PhiUSIIL Phishing URL Dataset is a large UCI benchmark with 235,795 instances, 134,850 legitimate URLs, and 100,945 phishing URLs. UCI records the label convention as `1 = legitimate` and `0 = phishing` and states that features were extracted from webpage source code and URL information; it also identifies `CharContinuationRate`, `URLTitleMatchScore`, `URLCharProb`, and `TLDLegitimateProb` as derived from existing features [6]. The associated Computers & Security paper is listed as *PhiUSIIL: A diverse security profile empowered phishing URL detection framework based on similarity index and incremental learning*, DOI `10.1016/j.cose.2023.103545` [7].

These dataset facts motivate feature-provenance auditing. PhiUSIIL is not simply a raw lexical URL dataset; it includes URL-derived, webpage/content-derived, and reference-dependent engineered features. This project's Tier A result showed that the full supplied benchmark condition was dominated by `URLSimilarityIndex`, a highly discriminative engineered feature whose reference or formula is not reproducible from a single submitted URL string in this repository.

## URL-Phish and LegitPhish External Datasets

URL-Phish is described in Data in Brief as a feature-engineered dataset of benign and phishing URLs for machine learning and large language model evaluation. The article reports 100,000 benign URLs and 11,660 phishing URLs in the Data in Brief abstract, while the repository version used in this project contained 116,600 rows with 100,000 benign and 16,600 phishing rows after local inspection [8]. The dataset preserves raw URL/domain/TLD strings and engineered lexical/structural features. In this project, its supplied features were not used; only raw URL text was parsed into the frozen PhiUSIIL Tier E feature representation.

LegitPhish is also described in Data in Brief as a large annotated URL dataset with 101,219 labelled URLs, including 63,678 phishing and 37,540 legitimate entries. Its abstract states that phishing URLs were collected from threat intelligence feeds such as URLHaus and PhishTank, while legitimate URLs were sourced from high-authority sources such as Wikipedia and other reputable sources [9]. The local repository inspection found one missing-label row, resulting in 101,218 analysis rows. As with URL-Phish, this project ignored supplied LegitPhish numerical features for primary validation and used only raw URL text.

## Cross-Dataset Generalization and Dataset Shift

Dataset shift is the broad problem in which training data and deployment or evaluation data are drawn from different populations. Quiñonero-Candela et al.'s *Dataset Shift in Machine Learning* frames this as a central machine-learning concern when the distribution used for model building differs from the distribution used for prediction [10]. In phishing detection, shift can arise from collection source, time period, threat feed, benign-source policy, normalization, label policy, or class prevalence.

This project distinguishes several related ideas:

- Prior or prevalence shift: class proportions differ across datasets.
- Covariate shift: feature distributions differ across datasets.
- Class-conditional shift: feature distributions differ within the same semantic class.
- Concept shift: the relationship between features and labels changes.

The evidence in this repository supports class-conditional covariate shift for URL-Phish, especially between PhiUSIIL legitimate URLs and URL-Phish benign URLs. It does not prove concept shift.

## Domain- and Group-Disjoint Evaluation

Random train/test splits can overestimate performance when related examples appear in multiple partitions. Grouped validation addresses this by ensuring that the same group does not appear in both training and testing. Scikit-learn's GroupKFold documentation states that each group appears in exactly one test fold, and its cross-validation guide notes that grouped data can break the independent-and-identically-distributed assumption when samples within groups are dependent [11,12].

This project adapts that principle to registrable domains: URLs sharing a registrable domain are allocated together so the model is evaluated on domains not seen during training. This is stricter than random splitting, but it is still not equivalent to deployment. A domain-disjoint split within one dataset can preserve source-specific collection artifacts.

## Dataset Leakage, Overlap, and Independence

Phishing URL datasets can overlap at multiple levels. Exact URL overlap means the same URL string appears in two datasets. Normalized URL overlap may capture case or whitespace variants. Registrable-domain overlap means datasets share base domains even when exact URLs differ. These are not equivalent: domain overlap is broader and can include legitimate and phishing URLs under the same registrable domain.

The final integrity audit found that LegitPhish had 36,935 exact URL overlaps with PhiUSIIL, all legitimate-to-legitimate at the exact and normalized levels. URL-Phish had only 595 exact overlaps with PhiUSIIL. This supports careful language: LegitPhish is externally sourced but not fully independent at the raw-URL level. At the same time, exact-overlap removal did not materially reduce aggregate LegitPhish phishing F1, so exact duplication alone does not explain its high aggregate F1.

## Interpretability and Failure Analysis

Interpretable models are useful not only for explaining correct decisions, but also for diagnosing failures. In this project, URL-Phish failure was traced to false-positive leaf routing: most benign false positives entered leaves that were pure or near-pure phishing leaves during PhiUSIIL training. That made the failure mechanism concrete: the external benign distribution resembled PhiUSIIL phishing routing patterns under the learned tree.

This complements dataset-origin diagnostics. A shallow origin classifier can show whether source dataset remains predictable even after holding semantic class fixed. In this project, PhiUSIIL legitimate versus URL-Phish benign origin AUC was 0.978597, while PhiUSIIL legitimate versus LegitPhish legitimate origin AUC was 0.508291. The contrast helps explain why URL-Phish and LegitPhish produced such different aggregate results.

## Evaluation Under Class Imbalance

Class imbalance can make aggregate metrics misleading. Scikit-learn's model-evaluation documentation defines balanced accuracy as the macro-average of class recalls and notes that it avoids inflated performance estimates on imbalanced datasets [13]. Average precision summarizes precision-recall behavior over thresholds and is often more informative than accuracy when positive-class prevalence is low or unstable [14]. ROC metrics are useful for ranking, but they require both classes and can reveal a model that assigns identical or non-discriminating scores across classes.

The final LegitPhish subgroup result illustrates this issue sharply. After removing seen domains, the unseen-domain subset contained 62,990 phishing rows and only 388 legitimate rows. The model predicted every row as phishing. Phishing F1 was therefore 0.996930, but specificity was 0.000000, balanced accuracy was 0.500000, and ROC-AUC was 0.500000. This demonstrates why F1 alone cannot establish useful two-class discrimination.

## Related-Work Comparison

| Study/source | Dataset(s) | Features | Model | Evaluation protocol | Cross-dataset evaluation? | Main limitation/relevance to this work |
| --- | --- | --- | --- | --- | --- | --- |
| Blum et al. (2010) [1] | Phishing URL data from operational sources | Lexical/content URL features | Online learning/confidence-weighted classification | Dynamic URL classification | Not the focus | Establishes lexical URL detection as practical and fast, but predates current curated benchmark-overlap concerns. |
| Mohammad et al. (2020) [2] | Phishing detection literature benchmark review | URL, network, script, website features | Multiple families reviewed | Benchmarking and security-needs analysis | Discusses evaluation needs broadly | Supports feature-category reasoning; this project applies provenance auditing to PhiUSIIL specifically. |
| Gupta et al. (2021) [3] | ISCXURL-2016 | Nine lexical URL features | Classical ML classifiers | Within-dataset model comparison | Limited | Shows high lexical-feature performance is possible; this project asks whether such performance transfers across datasets. |
| Ahmed and Jameel (2022) [4] | Malicious URL dataset | Lexical features selected with Decision Tree | DT-based feature selection plus MLP | Within-dataset evaluation | No | Relevant to lightweight lexical design, less focused on provenance and external overlap. |
| Prasad and Chandra / PhiUSIIL [6,7] | PhiUSIIL | URL, webpage, similarity, and derived engineered features | Similarity/incremental framework | Benchmark dataset and associated framework | Not framed as this project's fixed-model external audit | Provides the primary benchmark; this project audits which features are deployment-reproducible. |
| URL-Phish Data in Brief [8] | URL-Phish | Raw URL/domain/TLD plus engineered lexical/structural features | Baseline ML/LLM evaluation | Dataset paper with benchmark baselines | Dataset intended for evaluation | This project uses URL-Phish as a fixed-model external test and finds severe false-positive transfer failure. |
| LegitPhish Data in Brief [9] | LegitPhish | Raw URL plus 17 structural/lexical features | Dataset resource | Dataset paper with verified labels | Dataset intended for benchmarking | This project finds strong aggregate transfer but substantial PhiUSIIL URL/domain overlap and a skewed unseen-domain subgroup. |
| Scikit-learn GroupKFold docs [11,12] | General grouped ML data | Group labels | Cross-validation splitter | Non-overlapping groups across folds | Not phishing-specific | Motivates registrable-domain-disjoint evaluation, while this project shows domain-disjoint internal success is not sufficient for external robustness. |
| Dataset Shift in Machine Learning [10] | General ML | Distributional framing | Theory and methods | Shift taxonomy | General | Provides conceptual language for covariate, prior, and class-conditional shift. |

## Final Literature Gap

Prior work supports lexical phishing URL detection, interpretable Decision Trees, feature engineering, and external datasets. The narrower gap addressed here is the combination of:

- PhiUSIIL feature-provenance classification.
- Independent reconstruction/fidelity auditing for URL-derived features.
- Tiered comparison of full benchmark, supplied URL-oriented, directly reproducible, reconstructed, and deployment-extended features.
- Fixed Decision Tree evaluation under random and registrable-domain-disjoint splits.
- Fixed-model external validation on URL-Phish and LegitPhish.
- Post-hoc class-conditional shift, leaf-routing, dataset-origin, overlap, and subgroup composition analysis.

The project therefore contributes a controlled audit of how benchmark feature availability and dataset-pair composition affect apparent generalization, without claiming first-ever novelty.

## References

[1] A. Blum, B. Wardman, T. Solorio, and G. Warner, "Lexical feature based phishing URL detection using online learning," AISec 2010. https://doi.org/10.1145/1866423.1866434

[2] R. M. Mohammad, F. Thabtah, and L. McCluskey, "An In-Depth Benchmarking and Evaluation of Phishing Detection Research for Security Needs," IEEE Access, 2020. https://doi.org/10.1109/ACCESS.2020.2969780

[3] B. B. Gupta, K. Yadav, I. Razzak, K. Psannis, A. Castiglione, and X. Chang, "A novel approach for phishing URLs detection using lexical based machine learning in a real-time environment," Computer Communications, 2021. https://doi.org/10.1016/j.comcom.2021.04.023

[4] W. F. Ahmed and N. G. M. Jameel, "Malicious URL Detection Using Decision Tree-based Lexical Features Selection and Multilayer Perceptron Model," UHD Journal of Science and Technology, 2022. https://doi.org/10.21928/uhdjst.v6n2y2022.pp105-116

[5] "Phishing URL Classification in Cybersecurity Education: A Comparative Study of RF, SVM, DT, and LR," Information, 2026. https://www.mdpi.com/2078-2489/17/5/401

[6] A. Prasad and S. Chandra, "PhiUSIIL Phishing URL (Website)," UCI Machine Learning Repository, 2024. https://archive.ics.uci.edu/dataset/967/phiusiil+phishing+url+dataset

[7] A. Prasad and S. Chandra, "PhiUSIIL: A diverse security profile empowered phishing URL detection framework based on similarity index and incremental learning," Computers & Security, 2024. https://doi.org/10.1016/J.COSE.2023.103545

[8] "A feature-engineered dataset of benign and phishing URLs for machine learning and large language models evaluation," Data in Brief, 2025. https://doi.org/10.1016/j.dib.2025.112162

[9] "LegitPhish: A large-scale annotated dataset for URL-based phishing detection," Data in Brief, 2025. https://doi.org/10.1016/j.dib.2025.111972

[10] J. Quiñonero-Candela, M. Sugiyama, A. Schwaighofer, and N. D. Lawrence, eds., *Dataset Shift in Machine Learning*, MIT Press, 2009. https://doi.org/10.7551/mitpress/9780262170055.001.0001

[11] Scikit-learn developers, "GroupKFold." https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html

[12] Scikit-learn developers, "Cross-validation iterators for grouped data." https://scikit-learn.org/stable/modules/cross_validation.html

[13] Scikit-learn developers, "Metrics and scoring: balanced accuracy." https://scikit-learn.org/stable/modules/model_evaluation.html

[14] Scikit-learn developers, "average_precision_score." https://sklearn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html
