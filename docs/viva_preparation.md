# Viva Preparation Guide

## Fundamentals

### What is data mining?

Data mining is the process of finding useful patterns, relationships, and
knowledge from data.

### What is classification?

Classification is supervised learning where the model predicts a discrete
class label.

### Why is this a classification problem?

The target has two classes: phishing and legitimate.

### Why Decision Tree?

A Decision Tree is part of the Data Mining syllabus, works well for tabular
features, and is easier to explain because it uses feature-based rules.

### What is supervised learning?

Supervised learning trains a model using examples that already have labels.

## Dataset

### Why PhiUSIIL?

It is a newer and larger phishing URL dataset from the UCI Machine Learning
Repository.

### How many rows?

The raw dataset has 235,795 rows.

### What are the labels?

`0 = phishing` and `1 = legitimate`.

### Why not use all 54 original features?

Some original features depend on webpage content, redirects, forms, images,
or page resources. The dashboard receives only a pasted URL, so the final model
uses only features our code can extract safely from URL text.

## Features

### What is lexical URL analysis?

Lexical URL analysis studies the characters and structure of the URL string,
such as length, dots, slashes, digits, query parameters, and keywords.

### How are features extracted safely?

The project uses local string parsing through standard-library tools. It does
not open, request, resolve, ping, or scrape the URL.

### Why must training and dashboard extraction match?

If training uses features that the dashboard cannot recreate, dashboard
predictions would be inconsistent with training.

### Why is HTTPS text not proof of safety?

`uses_https_text` only means the URL string uses the HTTPS scheme. It does not
verify certificates or prove the website is safe.

### What is `domain_is_ip`?

It checks whether the hostname text is an IPv4 or IPv6 literal using local
text parsing. It does not resolve domain names.

## Decision Tree

### How does a Decision Tree choose splits?

It tests feature thresholds and chooses splits that reduce class impurity.

### Gini versus entropy

Both measure impurity. Gini is commonly used by default, while entropy is
based on information gain. The tuned model selected entropy.

### What is `max_depth`?

It limits how many split levels the tree can grow.

### What are leaves?

Leaves are final nodes where the model outputs a class prediction.

### What is pruning?

Pruning reduces unnecessary branches to make the tree simpler.

### What is `ccp_alpha`?

`ccp_alpha` controls cost-complexity pruning. Larger values penalize complex
trees more strongly.

## Overfitting

### What is overfitting?

Overfitting happens when a model learns training-specific patterns that do not
generalize well.

### How did we observe it?

The unrestricted baseline had depth 25 and 388 leaves. Its training and
validation accuracies were both high, but depth analysis showed similar
validation performance could be achieved with a simpler tree.

### Why compare training and validation scores?

Training score shows how well the model fits learned data. Validation score
shows how well it performs on held-out development data.

## Validation

### Why train/validation/test?

Training fits the model, validation supports model selection, and test gives
the final untouched evaluation.

### Why stratified splitting?

Stratification preserves the phishing and legitimate class proportions in
each split.

### Why keep the test set untouched?

Using the test set during model selection would make final performance
unreliable.

### What is cross-validation?

Cross-validation divides training data into folds so different subsets are
used for training and validation during tuning.

### Why GridSearchCV?

It gives a simple, reproducible way to compare Decision Tree hyperparameter
combinations.

## Metrics

### Accuracy

The proportion of all predictions that are correct.

### Precision

For phishing, precision means how many URLs predicted as phishing were truly
phishing.

### Recall

For phishing, recall means how many actual phishing URLs were detected.

### F1

F1-score balances phishing precision and phishing recall.

### ROC-AUC

ROC-AUC measures how well the model ranks phishing above legitimate using
phishing probability.

### Confusion Matrix

The confusion matrix compares actual classes with predicted classes. The most
concerning error is actual phishing predicted legitimate.

## Results

| Model | Test Accuracy | Phishing Precision | Phishing Recall | Phishing F1 | ROC-AUC | Depth | Leaves |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 0.9954 | 0.9985 | 0.9909 | 0.9947 | 0.9968 | 25 | 388 |
| Optimized | 0.9959 | 0.9993 | 0.9910 | 0.9952 | 0.9981 | 10 | 69 |

Final optimized confusion matrix:

```text
                 Predicted Phishing  Predicted Legitimate
Actual Phishing              15006                   136
Actual Legitimate               10                 20218
```

## Dashboard

### What happens when a URL is entered?

The URL is parsed as local text, converted into 26 features, passed to the
optimized Decision Tree, and displayed with prediction outputs.

### Does the project open the website?

No. It analyses only the URL text.

### How is confidence calculated?

Confidence is the probability assigned to the predicted class.

### How is risk level calculated?

Risk level uses phishing probability:

- Low: less than 0.35
- Moderate: 0.35 to less than 0.65
- High: 0.65 to less than 0.85
- Very High: 0.85 or above

These thresholds are UI interpretation thresholds, not optimized academic
decision thresholds.

### What are model observations?

They are neutral notes about URL-text properties, such as long URL length,
many subdomains, IP-literal hostname, keywords, query parameters, or explicit
ports.

## Limitations

Likely examiner questions:

- Does the model prove a URL is malicious? No.
- Does it inspect webpage content? No.
- Does it check domain reputation? No.
- Can attackers adapt? Yes.
- Can dataset patterns become outdated? Yes.

## Original Versus Our Project

The original project demonstrated Decision Tree phishing detection on a smaller
prepared dataset. This project extends that idea with the PhiUSIIL dataset, a
custom URL-text extractor, safe non-network prediction, validation, EDA,
tuning, pruning, final evaluation, interpretation, tests, CI, and a Streamlit
dashboard.

## Short Explanations

### 30-Second Explanation

My project detects phishing URLs using an optimized Decision Tree classifier.
It uses the UCI PhiUSIIL dataset, extracts 26 safe URL-text features, trains
and tunes the model, evaluates it on an untouched test set, and provides a
Streamlit dashboard. The dashboard never opens the submitted URL.

### 2-Minute Explanation

This project is a Data Mining classification system for phishing URL detection.
The raw dataset is PhiUSIIL from UCI, with 235,795 records and labels where
0 means phishing and 1 means legitimate. Because the final dashboard only gets
a URL entered by the user, I did not use webpage-dependent features. Instead,
I built my own URL-text feature extractor with 26 lexical and structural
features. I split the processed dataset into train, validation, and test sets.
I trained a baseline Decision Tree, studied overfitting, compared tree depths,
used GridSearchCV with phishing F1-score, analyzed pruning, selected the final
optimized Decision Tree, and evaluated it once on the untouched test set. The
optimized model is much simpler than the baseline and achieved 0.9959 final
test accuracy with phishing F1-score 0.9952. The project also includes feature
importance, a Streamlit dashboard, tests, GitHub Actions, and documentation.

### 5-Minute Structured Outline

1. Introduce phishing and why URL classification matters.
2. Explain the PhiUSIIL dataset and labels.
3. Explain the safety rule: URL text only, no website contact.
4. Describe the 26 URL-text features.
5. Explain the train/validation/test split.
6. Describe the baseline Decision Tree.
7. Discuss overfitting, depth analysis, tuning, and pruning.
8. Present optimized model results and confusion matrix.
9. Explain feature importance and dashboard outputs.
10. Conclude with limitations and future work.
