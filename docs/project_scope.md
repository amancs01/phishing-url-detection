# Project Scope

## Project Title

Phishing URL Detection Using an Optimized Decision Tree Classifier

## Problem Statement

Phishing URLs imitate legitimate websites to trick users into revealing
sensitive information. This project develops a machine-learning system that
classifies a URL as phishing or legitimate by analysing only its textual
structure.

## Main Objective

To design, train, optimize, evaluate, and deploy a Decision Tree classifier
for phishing URL detection using safely extractable URL-text features.

## Specific Objectives

1. Obtain and inspect the UCI PhiUSIIL Phishing URL Dataset.
2. Select features that can be recreated directly from URL text.
3. Clean and preprocess the selected data.
4. Perform exploratory data analysis.
5. Train a baseline Decision Tree classifier.
6. analyse overfitting using training and validation results.
7. Optimize the Decision Tree using hyperparameter tuning.
8. Evaluate the final model using multiple classification metrics.
9. Compare the baseline and optimized Decision Tree models.
10. Build a Streamlit dashboard for safe URL-text prediction.
11. Document the complete workflow in a professional GitHub repository.

## Primary Algorithm

The primary algorithm is the Decision Tree Classifier, which is directly
included in the Data Mining course syllabus.

## Dataset

The project will use the UCI PhiUSIIL Phishing URL Dataset.

Only the URL column and features that can be extracted safely from URL text
will be used for the final model.

## Safe Feature Scope

Examples of permitted features include:

- URL length
- Domain length
- Path length
- Number of dots
- Number of subdomains
- Number of digits
- Number of letters
- Number of hyphens
- Number of special characters
- Presence of an IP address
- Presence of suspicious keywords
- Presence of URL-shortening patterns
- Query-string properties
- HTTPS text in the URL

## Out of Scope

The project will not:

- Open or visit a submitted URL
- Send HTTP requests to submitted websites
- Download webpage content
- Execute JavaScript from websites
- Download files from submitted URLs
- Inspect live SSL certificates
- Perform live WHOIS or DNS lookups
- Claim that predictions are guaranteed security verdicts

## Final Output

The final output will be a Streamlit dashboard that displays:

- Phishing or legitimate prediction
- Prediction confidence
- Risk level
- Extracted URL features
- Model observations
- Model performance information

## Academic Experiments

The project will include:

- Data preprocessing
- Exploratory data analysis
- Baseline classification
- Training, validation, and testing
- Overfitting analysis
- Decision Tree depth comparison
- Hyperparameter tuning
- Model comparison
- Final test evaluation

## Evaluation Metrics

The model will be evaluated using:

- Accuracy
- Precision
- Recall
- F1-score
- Confusion matrix
- ROC-AUC

## Safety Principle

Every submitted URL will be treated as plain text. The application will never
connect to the website represented by that URL.
