# Research Protocol

## Research Title

From Benchmark to Deployment: A Feature-Provenance and Generalization Audit of
PhiUSIIL Phishing URL Detection Using Interpretable Decision Trees

## Motivation

The completed project already implements a safe deployment-oriented phishing
URL detector using an optimized `DecisionTreeClassifier`. The next research
step is to ask whether high benchmark performance still holds when features
are restricted to values that can be independently reproduced from a raw URL at
inference time.

Many phishing benchmark datasets contain precomputed features. Some are simple
URL-text properties, while others may depend on webpage content, reference
statistics, similarity methods, or collection-time context. A deployed
dashboard that receives only a pasted URL cannot safely recreate webpage or
network-dependent features. This research protocol therefore studies feature
provenance and deployment realism.

## Central Research Question

How much of the apparent performance of a Decision Tree on the PhiUSIIL
benchmark survives when the classifier is restricted to features that can be
independently reproduced from a raw URL at inference time?

## Research Questions

### RQ1

Which PhiUSIIL features can be independently reconstructed from a raw URL
without webpage access, network queries, hidden reference corpora, or
unavailable external information?

### RQ2

For features that are directly reproducible, how closely do independently
recalculated values match the values supplied in PhiUSIIL?

### RQ3

How does Decision Tree performance change as non-reproducible feature groups
are progressively removed?

### RQ4

How does the deployment-realistic URL-only model perform under a
registrable-domain-disjoint evaluation rather than only a random split?

### RQ5

How well does the same model generalize to an independent external raw-URL
dataset without retraining?

### RQ6

How stable are Decision Tree feature-importance rankings across benchmark and
deployment-realistic feature conditions?

## Hypotheses

### H1

The full supplied PhiUSIIL feature set will outperform the independently
reproducible raw-URL feature set.

### H2

Simple lexical features such as URL length and character counts will show high
reproduction fidelity.

### H3

Random-split performance will exceed registrable-domain-disjoint performance.

### H4

External-dataset performance will be lower than internal random-holdout
performance.

### H5

Decision Tree feature-importance rankings will change after
reference-dependent and webpage-dependent features are removed.

These are hypotheses only. The experiments must report actual findings even
when they reject these expectations.

## Why Decision Tree Is Kept Fixed

The classifier family remains `DecisionTreeClassifier` throughout the research
study. Keeping the model family fixed reduces confounding: observed performance
changes can be interpreted mainly as the result of feature availability,
feature provenance, and validation protocol changes rather than as differences
between unrelated algorithms.

This also keeps the study aligned with the original university project and the
Data Mining syllabus.

## Experimental Variables

Controlled factors:

- Same primary classifier family: `DecisionTreeClassifier`
- Same label semantics: `0 = phishing`, `1 = legitimate`
- Phishing treated as the positive condition for precision, recall, F1, and
  ROC-AUC
- Same safety rule: URLs are plain text only

Independent variables:

- Feature tier and provenance
- Random split versus domain-disjoint split
- Internal PhiUSIIL evaluation versus external raw-URL evaluation

Dependent variables:

- Accuracy
- Phishing precision
- Phishing recall
- Phishing F1-score
- ROC-AUC
- Confusion matrix counts
- Tree depth
- Number of leaves
- Feature-importance ranking stability

## Metrics

The main classification metrics are:

- Accuracy
- Phishing precision, using `pos_label=0`
- Phishing recall, using `pos_label=0`
- Phishing F1-score, using `pos_label=0`
- ROC-AUC based on the probability column corresponding to class `0`
- Confusion matrix ordered as Phishing and Legitimate

Model complexity metrics:

- Decision Tree depth
- Number of leaves

Feature-fidelity metrics:

- Exact match percentage for integer and boolean features
- Mean absolute error for continuous features
- Median absolute error for continuous features
- Pearson correlation where meaningful

## Safety Restrictions

Dataset and submitted URLs must never be opened, visited, requested,
downloaded from, resolved, pinged, scraped, or otherwise contacted.

Forbidden operations on dataset/submitted URLs include:

- HTTP requests
- `requests`
- `urllib.request`
- Selenium
- Playwright
- Browser automation
- Socket or DNS resolution
- WHOIS
- SSL querying
- Ping
- Webpage downloads
- Favicon requests
- External reputation APIs

Allowed operations:

- `urllib.parse` for local string parsing
- `ipaddress` for checking whether hostname text is an IP literal

## Planned Feature Tiers

Exact tier membership will be decided after the provenance audit.

### Tier A: Full Usable Numerical PhiUSIIL Benchmark Features

This tier represents the broad benchmark setting using supplied numerical
PhiUSIIL features that can be used by a tabular Decision Tree. It may include
features unavailable to the final dashboard.

### Tier B: PhiUSIIL-Supplied URL-Oriented Features

This tier represents supplied PhiUSIIL columns that appear related to URL
structure or URL text, while still preserving provenance labels such as
reference-dependent or uncertain.

### Tier C: PhiUSIIL-Supplied Directly Reproducible Raw-URL Features

This tier includes supplied PhiUSIIL columns whose semantics can be defended as
directly reconstructible from a raw URL string without hidden corpora,
webpage access, or network queries.

### Tier D: Independently Re-Extracted Raw-URL Features

This tier uses the project's own URL-text feature extractor. It represents the
deployment-realistic feature set used by the Streamlit dashboard.

## Planned Validation Protocols

The planned validation protocols are:

1. Random stratified train/validation/test split, matching the completed
   software project.
2. Registrable-domain-disjoint split, where domains are separated across
   evaluation partitions to test generalization beyond memorized domains.
3. External raw-URL dataset evaluation without retraining.

The current research batch defines the protocol, audits provenance, and
measures feature fidelity only. It does not yet run tiered model experiments,
domain-disjoint evaluation, or external-dataset evaluation.

## Main Controlled Experiment

The main planned experiment is:

```text
same dataset
same Decision Tree family
same evaluation metrics
different feature availability and provenance
```

This design isolates the role of feature provenance more clearly than a study
that changes both features and classifier families at the same time.

## Threats To Validity

- Feature definitions may be ambiguous or incompletely documented.
- A feature can be directly computable in principle but still not exactly
  match the original dataset implementation.
- Registrable-domain parsing can be imperfect without a public suffix list.
- External datasets may use different collection policies or label quality.
- PhiUSIIL may contain dataset-specific patterns that do not generalize.
- Decision Tree feature importance can be unstable when correlated features
  are present.
- High accuracy does not guarantee security in real-world deployment.
