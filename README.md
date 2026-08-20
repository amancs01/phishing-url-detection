# Phishing URL Detection Using an Optimized Decision Tree Classifier

## Overview

This repository contains a university Data Mining project that classifies URLs
as phishing or legitimate using an optimized `DecisionTreeClassifier`.

The final application analyses only URL text. It does not open, visit, request,
download from, resolve, ping, or otherwise connect to submitted websites.

## Problem Statement

Phishing URLs are designed to imitate legitimate websites and trick users into
sharing sensitive information. This project treats phishing detection as a
binary classification problem: given a URL string, predict whether it is
phishing or legitimate.

## Project Objective

The main objective is to design, optimize, evaluate, and deploy a Decision Tree
classifier for phishing URL detection using safely extractable URL-text
features.

Specific objectives include dataset inspection, URL-only feature extraction,
preprocessing, exploratory analysis, stratified validation, overfitting
analysis, hyperparameter tuning, pruning analysis, final test evaluation, model
interpretation, testing, CI, and a Streamlit dashboard.

## Original Internet Project

This work is inspired by the public GitHub tutorial
`npapernot/phishing-detection`, titled "Detecting Phishing Websites Using a
Decision Tree." The original project demonstrated phishing website
classification with a Decision Tree on a smaller prepared dataset.

## How This Project Extends The Original

This project keeps the academic idea of Decision Tree classification and
extends it through:

- Newer and larger UCI PhiUSIIL dataset
- Custom URL-text feature extractor
- Safe non-network prediction workflow
- Data inspection and validation
- Exploratory data analysis notebooks
- Stratified train/validation/test split
- Baseline Decision Tree experiment
- Overfitting and depth analysis
- Hyperparameter tuning using phishing F1-score
- Cost-complexity pruning analysis
- Baseline versus optimized comparison
- Final untouched-test evaluation
- Feature importance and model interpretation
- Streamlit dashboard
- Pytest tests and GitHub Actions CI

This is an academic reproduction and extension, not a claim of research
novelty.

## Dataset

Dataset: UCI PhiUSIIL Phishing URL Dataset

- Records: 235,795
- Columns in raw local CSV: 55
- Label column: `label`
- `0 = phishing`: 100,945 records
- `1 = legitimate`: 134,850 records
- Licence: Creative Commons Attribution 4.0 International, for the dataset

Reference:

Prasad, A., and Chandra, S. (2024). PhiUSIIL Phishing URL (Website)
[Dataset]. UCI Machine Learning Repository.

## Safety Design

The prediction workflow is:

```text
submitted URL text
-> local string parsing
-> numerical URL-text features
-> optimized Decision Tree
-> prediction
```

The dashboard and prediction code never connect to the submitted URL. HTTPS is
treated only as text in the URL string and is not interpreted as proof of
website safety.

## Methodology

```text
Dataset
-> inspection
-> validation
-> URL-only feature extraction
-> processed modeling dataset
-> stratified train/validation/test split
-> baseline Decision Tree
-> overfitting analysis
-> depth comparison
-> hyperparameter tuning
-> pruning analysis
-> optimized model selection
-> final untouched-test evaluation
-> Streamlit dashboard
```

## Selected Features

The final URL-text features are:

`url_length`, `domain_length`, `path_length`, `query_length`,
`number_of_dots`, `number_of_hyphens`, `number_of_underscores`,
`number_of_slashes`, `number_of_question_marks`, `number_of_equal_signs`,
`number_of_at_symbols`, `number_of_ampersands`,
`number_of_percent_symbols`, `number_of_digits`, `number_of_letters`,
`digit_ratio`, `letter_ratio`, `special_character_count`,
`number_of_subdomains`, `domain_is_ip`, `uses_https_text`, `has_port`,
`number_of_query_parameters`, `suspicious_keyword_count`,
`has_suspicious_keyword`, and `known_shortener_domain`.

These features describe URL length, domain/path/query structure, character
counts, ratios, subdomains, IP-literal hostnames, HTTPS text, ports, query
parameters, suspicious keywords, and known shortener hostname text.

## Model Evaluation

Phishing is treated as the important positive condition for precision, recall,
and F1-score, even though its label value is `0`.

| Model | Training Accuracy | Validation Accuracy | Final Test Accuracy | Phishing Precision | Phishing Recall | Phishing F1 | ROC-AUC | Depth | Leaves |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline unrestricted Decision Tree | 0.9962 | 0.9953 | 0.9954 | 0.9985 | 0.9909 | 0.9947 | 0.9968 | 25 | 388 |
| Optimized Decision Tree | 0.9958 | 0.9956 | 0.9959 | 0.9993 | 0.9910 | 0.9952 | 0.9981 | 10 | 69 |

The optimized model is much simpler while performing slightly better on the
final test metrics.

## Confusion Matrix

Final optimized model test confusion matrix:

```text
                 Predicted Phishing  Predicted Legitimate
Actual Phishing              15006                   136
Actual Legitimate               10                 20218
```

The most important error for security is actual phishing predicted legitimate.
This occurred 136 times on the final test set.

## Feature Importance

Top feature importances from the optimized Decision Tree:

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

Feature importance describes how the fitted tree used features. It does not
prove causation.

## Dashboard

The Streamlit dashboard provides:

- URL text input
- Prediction: Phishing or Legitimate
- Confidence
- Phishing probability
- Risk level
- Extracted feature table
- Model observations
- Final model metrics
- Limitations and safety notice

Run it with:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Project Structure

```text
phishing-url-detection/
|-- .github/workflows/tests.yml
|-- app.py
|-- data/
|   |-- processed/.gitkeep
|   `-- raw/.gitkeep
|-- docs/
|   |-- dataset_and_sources.md
|   |-- dataset_schema.md
|   |-- project_scope.md
|   `-- url_feature_selection.md
|-- models/
|   |-- model_metadata.json
|   `-- optimized_decision_tree.joblib
|-- notebooks/
|   |-- 01_dataset_exploration.ipynb
|   |-- 02_url_feature_analysis.ipynb
|   |-- 03_baseline_model.ipynb
|   |-- 04_tree_depth_analysis.ipynb
|   |-- 05_pruning_analysis.ipynb
|   |-- 06_model_comparison.ipynb
|   `-- 07_model_interpretation.ipynb
|-- reports/figures/
|-- results/
|-- src/
|-- tests/
|-- .gitignore
|-- README.md
`-- requirements.txt
```

Raw and processed full datasets are intentionally ignored.

## Installation

```powershell
git clone https://github.com/amancs01/phishing-url-detection.git
cd phishing-url-detection
python -m venv .venv
```

Normal PowerShell activation:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell activation is blocked, use the interpreter directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

## Reproduce Model Development

The full workflow can be reproduced with the project scripts:

```powershell
.\.venv\Scripts\python.exe -m src.download_data
.\.venv\Scripts\python.exe -m src.inspect_data
.\.venv\Scripts\python.exe -m src.validate_data
.\.venv\Scripts\python.exe -m src.prepare_data
.\.venv\Scripts\python.exe -m src.split_data
.\.venv\Scripts\python.exe -m src.train_baseline
.\.venv\Scripts\python.exe -m src.tune_model
.\.venv\Scripts\python.exe -m src.analyze_pruning
.\.venv\Scripts\python.exe -m src.select_model
.\.venv\Scripts\python.exe -m src.evaluate_final
.\.venv\Scripts\python.exe -m src.model_interpretation
```

The final dashboard can run from the packaged optimized model already included
in `models/optimized_decision_tree.joblib`.

## Limitations

- The model analyses URL text only.
- It does not inspect webpage content, reputation lists, DNS, WHOIS, or SSL
  certificates.
- Predictions are model outputs, not guaranteed security verdicts.
- New phishing patterns may differ from the training dataset.
- Some URL features can be dataset-specific and may shift over time.

## Future Work

- Temporal validation on newer phishing data
- Additional safe lexical URL features
- Safe offline reputation datasets
- Concept drift monitoring
- Comparison with other course-syllabus classifiers
- Clearer per-prediction explanation methods

## Ethical And Safety Note

This project is for academic learning. It should not be used as the only basis
for real-world security decisions. Suspicious URLs should be handled according
to trusted security policies and tools.

## References

- UCI Machine Learning Repository: PhiUSIIL Phishing URL Dataset,
  https://archive.ics.uci.edu/dataset/967/phiusiil-phishing-url-dataset
- Dataset DOI: https://doi.org/10.1016/j.cose.2023.103545
- Original inspired project: https://github.com/npapernot/phishing-detection
- scikit-learn Decision Trees:
  https://scikit-learn.org/stable/modules/tree.html
- Streamlit documentation: https://docs.streamlit.io/

## Licence

The software code in this repository is licensed under the repository software
licence. The PhiUSIIL dataset remains under its own CC BY 4.0 dataset licence.
