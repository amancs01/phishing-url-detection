# Dataset and Source Project

## Dataset Used

This project uses the PhiUSIIL Phishing URL Dataset from the UCI Machine
Learning Repository.

### Dataset summary

- Dataset name: PhiUSIIL Phishing URL (Website)
- UCI dataset ID: 967
- Total records: 235,795
- Legitimate URLs: 134,850
- Phishing URLs: 100,945
- Total listed features: 54
- Missing values: No
- Task type: Binary classification
- Label 0: Phishing
- Label 1: Legitimate

### Official dataset reference

Prasad, A., and Chandra, S. (2024). PhiUSIIL Phishing URL (Website)
[Dataset]. UCI Machine Learning Repository.

Dataset page:

https://archive.ics.uci.edu/dataset/967/phiusiil-phishing-url-dataset

Associated DOI:

https://doi.org/10.1016/j.cose.2023.103545

## Dataset Licence

The PhiUSIIL dataset is distributed under the Creative Commons Attribution
4.0 International licence, also known as CC BY 4.0.

The dataset may be shared and adapted as long as appropriate credit is given
to its creators.

The dataset licence applies to the dataset. It is separate from the software
licence that will later be added to this GitHub repository.

## Feature Selection Policy

The complete dataset contains features extracted from both URL text and
webpage content.

This project will not blindly use all available columns.

The final model will use only features that:

1. Can be recreated from the URL string.
2. Do not require opening the website.
3. Do not require an HTTP request.
4. Do not require downloading webpage content.
5. Can be calculated consistently during both training and dashboard use.

The exact selected feature list will be determined after inspecting and
validating the dataset schema.

## Original Internet Project

The project is inspired by the following public GitHub tutorial:

Repository:

https://github.com/npapernot/phishing-detection

Repository title:

Detecting Phishing Websites Using a Decision Tree

### Original project summary

The original project:

- Uses a Decision Tree classifier.
- Uses a smaller phishing website dataset.
- Contains 2,456 website records.
- Uses 30 prepared attributes.
- Uses 2,000 records for training.
- Uses 456 records for testing.
- Reports approximately 90.6 percent testing accuracy.
- Runs primarily as a Python command-line tutorial.

## How This Implementation Extends It

Our implementation will retain the main academic idea of phishing
classification with a Decision Tree while extending it through:

- The newer and larger PhiUSIIL dataset
- Safe URL-text-only feature extraction
- Explicit data cleaning and validation
- Exploratory data analysis
- Stratified training, validation, and testing
- Baseline model development
- Overfitting analysis
- Decision Tree depth comparison
- Hyperparameter tuning
- Accuracy, precision, recall, F1-score, confusion matrix, and ROC-AUC
- Baseline-versus-optimized model comparison
- Feature importance and model observations
- Automated tests
- Saved model artifacts
- A Streamlit prediction dashboard
- Complete documentation and deployment instructions

## Reproduction Statement

This repository is an independent academic reproduction and extension of the
general approach demonstrated by the original project.

The original repository is used as inspiration and reference. Its source code
will not be copied and presented as original work. The implementation,
experiments, feature-extraction pipeline, dashboard, tests, visualizations,
and documentation in this repository will be developed independently.

## Safety Statement

No submitted URL will be opened, visited, requested, downloaded from, or
connected to. URLs will be processed only as plain text.
