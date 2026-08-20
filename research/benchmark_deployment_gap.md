# Benchmark To Deployment Performance Gap

## Purpose

This report quantifies the first controlled benchmark-versus-reproducible
feature experiment. It compares PhiUSIIL supplied benchmark features with
features that are defensibly reproducible from raw URL text.

The experiment does not perform domain-disjoint splitting or external-dataset
testing. Those remain future work.

## Experimental Controls

- Same rows across all tiers: 235,795
- Same deterministic split assignment across all tiers
- Same labels across all tiers
- Split seed: 42
- Split sizes: 165,056 train, 35,369 validation, 35,370 test
- Label convention: `0 = phishing`, `1 = legitimate`
- Phishing precision, recall, and F1 use class `0` as the positive class
- Test data were not used for model selection
- No URL was opened, requested, resolved, pinged, or contacted

## Feature Tiers

| Tier | Meaning | Feature count |
| --- | --- | ---: |
| A | Full usable numerical PhiUSIIL benchmark features | 50 |
| B | Supplied URL-oriented features, including URL-derived reference attributes | 22 |
| C | Supplied directly raw-URL-computable PhiUSIIL features | 18 |
| D-matched | Independently reconstructed equivalents of Tier C concepts | 18 |
| E | Existing deployment-extended project extractor | 26 |

The primary supplied-versus-reconstructed comparison is Tier C versus
Tier D-matched. Tier E is reported separately because it contains additional
custom deployment features.

## Model Tracks

### Track 1: Fixed Tree

The fixed-tree track uses the same pre-declared Decision Tree configuration
for every tier:

```text
criterion = entropy
max_depth = 10
min_samples_leaf = 1
min_samples_split = 2
ccp_alpha = 0.0
random_state = 42
```

This is the primary track for isolating feature-set and provenance effects.

### Track 2: Equal Tuning Protocol

The equal-tuning track applies the same modest search protocol independently
to each tier's training split:

```text
criterion = [gini, entropy]
max_depth = [6, 10, 14, None]
min_samples_leaf = [1, 5]
min_samples_split = [2]
ccp_alpha = [0.0]
scoring = phishing F1 with pos_label=0
cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
```

This track estimates what a Decision Tree can achieve under equal optimization
effort. It is not used to choose the fixed-tree configuration.

## Performance Table

| Tier | Track | Test accuracy | Phishing recall | Phishing F1 | ROC-AUC | Depth | Leaves |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A | fixed | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 4 | 5 |
| B | fixed | 0.999859 | 0.999736 | 0.999835 | 0.999883 | 10 | 26 |
| C | fixed | 0.996155 | 0.992669 | 0.995496 | 0.997923 | 10 | 154 |
| D-matched | fixed | 0.994430 | 0.988113 | 0.993460 | 0.996919 | 10 | 152 |
| E | fixed | 0.995731 | 0.990622 | 0.994992 | 0.997996 | 10 | 72 |
| A | tuned | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 4 | 5 |
| B | tuned | 0.999887 | 0.999736 | 0.999868 | 0.999866 | 6 | 8 |
| C | tuned | 0.997258 | 0.994585 | 0.996790 | 0.997080 | 24 | 496 |
| D-matched | tuned | 0.996862 | 0.994122 | 0.996327 | 0.996843 | 24 | 564 |
| E | tuned | 0.995731 | 0.990622 | 0.994992 | 0.997996 | 10 | 72 |

## Bootstrap Confidence Intervals

Confidence intervals use 1,000 percentile bootstrap samples over held-out test
prediction rows. Models are not retrained during bootstrap resampling.

### Fixed Tree

| Tier | Metric | Observed | 95% CI |
| --- | --- | ---: | --- |
| A | accuracy | 1.000000 | [1.000000, 1.000000] |
| A | phishing recall | 1.000000 | [1.000000, 1.000000] |
| A | phishing F1 | 1.000000 | [1.000000, 1.000000] |
| B | accuracy | 0.999859 | [0.999717, 0.999972] |
| B | phishing recall | 0.999736 | [0.999470, 0.999934] |
| B | phishing F1 | 0.999835 | [0.999671, 0.999967] |
| C | accuracy | 0.996155 | [0.995561, 0.996777] |
| C | phishing recall | 0.992669 | [0.991256, 0.993989] |
| C | phishing F1 | 0.995496 | [0.994713, 0.996231] |
| D-matched | accuracy | 0.994430 | [0.993638, 0.995222] |
| D-matched | phishing recall | 0.988113 | [0.986325, 0.989694] |
| D-matched | phishing F1 | 0.993460 | [0.992508, 0.994355] |
| E | accuracy | 0.995731 | [0.995052, 0.996381] |
| E | phishing recall | 0.990622 | [0.989095, 0.992095] |
| E | phishing F1 | 0.994992 | [0.994189, 0.995757] |

## Pairwise Gaps

Positive values mean the first tier scored higher than the second tier.

### Fixed Tree Percentage-Point Differences

| Comparison | Metric | Difference |
| --- | --- | ---: |
| A vs C | accuracy | +0.385 pp |
| A vs C | phishing recall | +0.733 pp |
| A vs C | phishing F1 | +0.450 pp |
| C vs D-matched | accuracy | +0.172 pp |
| C vs D-matched | phishing recall | +0.456 pp |
| C vs D-matched | phishing F1 | +0.204 pp |
| A vs D-matched | accuracy | +0.557 pp |
| A vs D-matched | phishing recall | +1.189 pp |
| A vs D-matched | phishing F1 | +0.654 pp |
| D-matched vs E | accuracy | -0.130 pp |
| D-matched vs E | phishing recall | -0.251 pp |
| D-matched vs E | phishing F1 | -0.153 pp |

### Tuned Tree Percentage-Point Differences

| Comparison | Metric | Difference |
| --- | --- | ---: |
| A vs C | accuracy | +0.274 pp |
| A vs C | phishing recall | +0.542 pp |
| A vs C | phishing F1 | +0.321 pp |
| C vs D-matched | accuracy | +0.040 pp |
| C vs D-matched | phishing recall | +0.046 pp |
| C vs D-matched | phishing F1 | +0.046 pp |
| A vs D-matched | accuracy | +0.314 pp |
| A vs D-matched | phishing recall | +0.588 pp |
| A vs D-matched | phishing F1 | +0.367 pp |
| D-matched vs E | accuracy | +0.113 pp |
| D-matched vs E | phishing recall | +0.350 pp |
| D-matched vs E | phishing F1 | +0.133 pp |

## Interpretation

Tier A achieved perfect performance on the random held-out test split in both
tracks. This is a striking result and should be treated cautiously. It may
reflect highly predictive webpage/content features, dataset-specific
regularities, or benchmark construction effects. The current experiment shows
the performance level under the benchmark split; it does not prove real-world
generalization.

Removing webpage/content features but retaining URL-oriented supplied features
still produced very high performance in Tier B. In the fixed track, Tier B
missed only 4 phishing rows and 1 legitimate row on the test split.

Removing reference-dependent and insufficiently specified URL attributes from
Tier B to Tier C produced a larger drop. In the fixed track, phishing F1 fell
from 0.999835 in Tier B to 0.995496 in Tier C.

The strongest supplied-versus-reconstructed comparison is Tier C versus
Tier D-matched. In the fixed track, Tier D-matched had a phishing F1 score
0.204 percentage points lower than Tier C and phishing recall 0.456
percentage points lower. Under equal tuning, the same gap was much smaller:
0.046 percentage points for phishing F1 and 0.046 percentage points for
phishing recall.

Tier E, the practical deployment-extended extractor, should not be interpreted
as a direct reconstruction test because it contains additional custom
features. In the fixed track, Tier E outperformed D-matched by 0.153
percentage points in phishing F1 and used a smaller tree than D-matched
because its feature set includes deployment-oriented features not present in
Tier C.

## Tree Complexity

The full Tier A tree was extremely small: depth 4 with 5 leaves. That supports
the idea that a small number of full-benchmark supplied features almost
perfectly separate the random split.

Tier C and Tier D-matched required much larger fixed trees, both at max depth
10 with more than 150 leaves. Under equal tuning, both selected unrestricted
depth and grew to 496 and 564 leaves respectively. This suggests the
raw-URL-only concept set needs more complex decision boundaries than the full
benchmark feature set.

Tier E reached depth 10 with only 72 leaves and matched the existing project
model behavior. Its lower complexity relative to D-matched is a practical
benefit, but it is not evidence that reconstruction itself improved
performance.

## Practical Implications

The experiment supports a nuanced benchmark-to-deployment story. Full
benchmark results are excellent, but much of the deployment-relevant analysis
depends on whether the model can use features available from one submitted URL
string. The reproducible URL-only tiers still perform strongly, but the
performance is measurably lower than the full supplied benchmark condition.

For a dashboard that must not contact URLs, Tier E remains the practical
deployment condition. For a fair supplied-versus-reconstructed research
comparison, Tier C versus Tier D-matched is the correct contrast.

## Limitations

- This is still a random split experiment, not domain-disjoint evaluation.
- No external raw-URL dataset is tested in this batch.
- Some PhiUSIIL feature formulas remain insufficiently specified.
- Tier D-matched is semantic reconstruction, not proven bit-for-bit
  reproduction of the original PhiUSIIL implementation.
- The perfect Tier A result should be verified later under stricter validation
  protocols before making broad generalization claims.

## Safety Statement

All experiments used local feature matrices and saved prediction rows. No
dataset URL was opened, requested, resolved, pinged, scraped, or otherwise
contacted.
