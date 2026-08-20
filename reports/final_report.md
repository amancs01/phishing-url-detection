# Phishing URL Detection Using an Optimized Decision Tree Classifier

## Abstract

This project develops a phishing URL detection system using an optimized
Decision Tree classifier. The work is based on the UCI PhiUSIIL Phishing URL
Dataset, which contains 235,795 URL records with binary labels for phishing and
legitimate classes. A central design rule of this project is safety: the final
application must classify a pasted URL using only local URL-text parsing and
must never open, visit, request, resolve, or otherwise contact the submitted
website. The project therefore implements its own URL-text feature extractor
and trains the model only on features that can be reproduced from a raw URL
string. The workflow includes dataset inspection, validation, preprocessing,
exploratory data analysis, stratified train/validation/test splitting,
baseline Decision Tree training, overfitting analysis, hyperparameter tuning,
cost-complexity pruning analysis, optimized model selection, final untouched
test evaluation, model interpretation, and a Streamlit dashboard. The final
optimized Decision Tree achieved 0.9959 test accuracy, 0.9993 phishing
precision, 0.9910 phishing recall, 0.9952 phishing F1-score, and 0.9981
ROC-AUC while using a simpler tree than the unrestricted baseline.

## 1. Introduction

Phishing is a common cyber-security attack where a malicious URL is designed to
look trustworthy and trick users into entering sensitive information. Data
mining techniques can help detect such URLs by learning patterns from labelled
examples.

This project focuses on binary classification of URLs into phishing and
legitimate classes. It uses a Decision Tree because the algorithm is suitable
for an undergraduate Data Mining course and is easier to explain than many
black-box models.

## 2. Problem Statement

The problem is to classify a raw URL string as phishing or legitimate using
machine learning. The final dashboard receives only a pasted URL string, so the
model must use features that can be extracted from that string alone.

## 3. Objectives

### 3.1 Main Objective

To design, optimize, evaluate, and deploy a Decision Tree classifier for
phishing URL detection using safe URL-text features.

### 3.2 Specific Objectives

- Inspect and validate the PhiUSIIL dataset.
- Select only features that can be reproduced from URL text.
- Build a local URL feature extractor.
- Prepare train, validation, and test datasets.
- Train a baseline Decision Tree classifier.
- Study overfitting and model complexity.
- Tune Decision Tree hyperparameters.
- Analyze cost-complexity pruning.
- Evaluate the selected model on the untouched test set.
- Build a Streamlit dashboard for safe prediction.
- Add tests, CI, documentation, and viva preparation material.

## 4. Background

Data mining is the process of discovering useful patterns from data.
Classification is a supervised learning task where a model learns from labelled
examples and predicts a class label for new examples.

In phishing detection, each URL can be described by numerical features. A
classifier can then learn patterns that distinguish phishing URLs from
legitimate URLs.

A Decision Tree makes predictions through a sequence of feature-based splits.
Each internal node applies a condition, and each leaf node gives a final class
prediction.

## 5. Original Internet Project

The project was inspired by the public GitHub project
`npapernot/phishing-detection`, titled "Detecting Phishing Websites Using a
Decision Tree." That project demonstrated phishing detection using a Decision
Tree on a smaller prepared dataset.

## 6. Proposed Extension

This project extends the original idea by using the larger UCI PhiUSIIL
dataset, implementing a custom URL-text feature extractor, enforcing a
non-network safety design, adding preprocessing and validation, conducting EDA,
studying overfitting, tuning and pruning the Decision Tree, evaluating with
multiple metrics, interpreting feature importance, and deploying a Streamlit
dashboard.

## 7. Dataset

Dataset: UCI PhiUSIIL Phishing URL Dataset

| Property | Value |
| --- | ---: |
| Raw rows | 235,795 |
| Raw columns | 55 |
| Target column | `label` |
| Phishing label | `0` |
| Legitimate label | `1` |
| Phishing count | 100,945 |
| Legitimate count | 134,850 |

Validation found 0 missing values, 0 duplicate full rows, and 425 duplicated
URL texts affecting 850 rows.

## 8. Feature Selection

The original dataset contains URL, domain, and webpage/content-derived
features. The final dashboard cannot inspect webpages, redirects, favicons,
forms, SSL certificates, DNS, WHOIS, or page content. Therefore, the final
model uses only features produced by the project extractor from raw URL text.

The final model uses 26 URL-text features, including URL length, domain length,
path length, query length, character counts, ratios, subdomain count,
IP-literal detection, HTTPS text, explicit port, query parameter count,
suspicious keyword count, and known shortener hostname detection.

## 9. Methodology

The project workflow was:

1. Download the UCI PhiUSIIL dataset.
2. Inspect schema and identify the target column.
3. Validate missing values, duplicates, and target labels.
4. Define final URL-only features.
5. Implement safe URL parsing and feature extraction.
6. Convert raw URL strings into a processed modeling dataset.
7. Create a stratified 70/15/15 train, validation, and test split.
8. Train an unrestricted baseline Decision Tree.
9. Analyze overfitting through training and validation results.
10. Compare max-depth values from 1 through 25.
11. Tune hyperparameters with stratified cross-validation.
12. Analyze cost-complexity pruning.
13. Select the optimized model before using the test set.
14. Refit the selected model on train plus validation data.
15. Evaluate once on the untouched test set.
16. Build interpretation artifacts and a Streamlit dashboard.

## 10. Decision Tree Classifier

A Decision Tree has a root node, internal decision nodes, and leaf nodes. The
root node is the first split. Internal nodes split data using conditions such
as a feature being less than or equal to a threshold. Leaf nodes contain final
class predictions.

Decision Trees use impurity measures such as Gini impurity or entropy to choose
useful splits. A lower impurity means a node contains more examples from one
class. Important hyperparameters include `criterion`, `max_depth`,
`min_samples_split`, and `min_samples_leaf`.

Pruning reduces tree complexity. In cost-complexity pruning, `ccp_alpha`
controls the penalty for complexity. Larger values usually produce smaller
trees.

## 11. Overfitting Analysis

The unrestricted baseline had:

- Training accuracy: 0.9962
- Validation accuracy: 0.9953
- Tree depth: 25
- Leaves: 388

The training-validation gap was small, so severe overfitting was not observed
in accuracy terms. However, the unrestricted tree was much deeper than needed.
Depth analysis showed that validation performance improved quickly at shallow
depths and then plateaued, suggesting a simpler tree could be preferred.

Generated figures:

- `reports/figures/tree_depth_accuracy.png`
- `reports/figures/tree_depth_f1.png`

## 12. Hyperparameter Optimization

Grid search used only the training split with stratified 3-fold
cross-validation. The scoring metric was phishing F1-score with `pos_label=0`.

Best parameters:

```text
criterion = entropy
max_depth = 10
min_samples_leaf = 1
min_samples_split = 2
```

Best mean cross-validation phishing F1-score: 0.9948.

Pruning analysis found that `ccp_alpha = 0.0` had the best validation phishing
F1-score among the tested representative alpha values. Light pruning reduced
leaves with almost unchanged validation F1, but it did not improve the selected
score.

## 13. Evaluation Metrics

The project reports:

- Accuracy: proportion of all correct predictions.
- Precision: how many predicted phishing URLs were actually phishing.
- Recall: how many actual phishing URLs were detected.
- F1-score: harmonic mean of phishing precision and recall.
- Confusion matrix: counts of actual versus predicted classes.
- ROC-AUC: ranking quality based on phishing probability.

Although phishing has label `0`, it is treated as the important positive
condition. The code explicitly uses `pos_label=0` and locates the phishing
probability column by checking `model.classes_`.

## 14. Results

| Model | Training Accuracy | Validation Accuracy | Final Test Accuracy | Phishing Precision | Phishing Recall | Phishing F1 | ROC-AUC | Depth | Leaves |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline unrestricted Decision Tree | 0.9962 | 0.9953 | 0.9954 | 0.9985 | 0.9909 | 0.9947 | 0.9968 | 25 | 388 |
| Optimized Decision Tree | 0.9958 | 0.9956 | 0.9959 | 0.9993 | 0.9910 | 0.9952 | 0.9981 | 10 | 69 |

Final optimized model confusion matrix:

```text
                 Predicted Phishing  Predicted Legitimate
Actual Phishing              15006                   136
Actual Legitimate               10                 20218
```

The most concerning error is actual phishing predicted legitimate. This
occurred 136 times on the final test set.

Generated figures include:

- `reports/figures/final_test_confusion_matrix.png`
- `reports/figures/baseline_validation_confusion_matrix.png`
- `reports/figures/pruning_f1.png`
- `reports/figures/pruning_complexity.png`

## 15. Model Interpretation

Top 10 feature importances:

| Feature | Importance |
| --- | ---: |
| `uses_https_text` | 0.532747 |
| `number_of_slashes` | 0.424362 |
| `url_length` | 0.021197 |
| `number_of_dots` | 0.010408 |
| `letter_ratio` | 0.002714 |
| `number_of_digits` | 0.002475 |
| `digit_ratio` | 0.002353 |
| `special_character_count` | 0.001181 |
| `number_of_hyphens` | 0.000900 |
| `number_of_letters` | 0.000590 |

Feature importance does not prove causation. It only explains how this fitted
Decision Tree used the available URL-text features.

Generated interpretation artifacts:

- `results/feature_importance.csv`
- `reports/figures/feature_importance.png`
- `reports/figures/decision_tree_preview.png`

## 16. Dashboard

The Streamlit dashboard accepts a URL as plain text and displays:

- Predicted class
- Confidence
- Phishing probability
- Risk level
- Extracted URL-text features
- Model observations
- Final model metrics
- Limitations and safety notice

The dashboard does not render submitted URLs as clickable links.

## 17. Safety Design

The final application analyses only the URL text and does not visit the
submitted website. It does not use HTTP requests, browser automation, DNS
resolution, WHOIS, SSL inspection, ping, favicon requests, or external
reputation services.

## 18. Limitations

- The model does not inspect webpage content.
- It does not check live domain reputation.
- It does not verify SSL certificates.
- It may not generalize perfectly to new phishing patterns.
- Feature importance does not prove that a feature causes phishing.
- Model output should not be treated as guaranteed security advice.

## 19. Future Work

Possible future improvements include temporal validation, richer lexical
feature research, safe offline reputation datasets, concept drift monitoring,
and comparison with other course-syllabus classifiers.

## 20. Conclusion

The project successfully implements a complete Decision Tree phishing URL
detection workflow using safe URL-text features. The optimized model is simpler
than the unrestricted baseline while achieving slightly better final test
metrics. The completed repository includes scripts, notebooks, metrics,
figures, tests, CI, documentation, a packaged optimized model, and a Streamlit
dashboard.

## References

- UCI Machine Learning Repository: PhiUSIIL Phishing URL Dataset,
  https://archive.ics.uci.edu/dataset/967/phiusiil-phishing-url-dataset
- Dataset DOI: https://doi.org/10.1016/j.cose.2023.103545
- Original inspired project: https://github.com/npapernot/phishing-detection
- scikit-learn Decision Trees:
  https://scikit-learn.org/stable/modules/tree.html
- scikit-learn model evaluation:
  https://scikit-learn.org/stable/modules/model_evaluation.html
- Streamlit documentation: https://docs.streamlit.io/
