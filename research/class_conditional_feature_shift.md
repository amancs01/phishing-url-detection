# Post-Hoc Diagnostic Analysis: Class-Conditional Feature Shift

## Purpose

This post-hoc diagnostic analysis separates feature shift by semantic class.
The earlier overall feature-shift ranking mixed phishing and legitimate rows
from datasets with different class prevalence. Here, the same Tier E feature
extractor is compared under two class-conditional views:

- PhiUSIIL legitimate versus URL-Phish benign
- PhiUSIIL phishing versus URL-Phish phishing

No model is retrained, no threshold is changed, and no URL is contacted.

## Method

Both datasets use the existing Tier E feature names and extractor. PhiUSIIL
uses the project label convention `0 = phishing`, `1 = legitimate`; URL-Phish
labels were already normalized into the same convention. For each feature and
comparison, the analysis records row counts, mean, median, standard deviation,
10th/25th/75th/90th percentiles, KS statistic, KS p-value, mean difference,
and median difference. Binary features additionally report the proportion of
rows where the feature equals 1.

KS statistics are descriptive distribution-shift indicators only. They are not
causal evidence.

## Summary

The class-conditional shift is much larger for the legitimate/benign class
than for the phishing/phishing class. Mean top-10 KS statistic is 0.4305 for
PhiUSIIL legitimate versus URL-Phish benign and 0.2076 for PhiUSIIL phishing
versus URL-Phish phishing.

This aligns with the external validation result: phishing recall remained high,
but benign specificity collapsed because most URL-Phish benign rows were
predicted as phishing.

## Top Legitimate/Benign Shifts

| Rank | Feature | KS statistic | PhiUSIIL legitimate mean | URL-Phish benign mean | External - source mean |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `path_length` | 0.889860 | 0.000000 | 4.604890 | +4.604890 |
| 2 | `number_of_slashes` | 0.889860 | 2.000000 | 3.148250 | +1.148250 |
| 3 | `uses_https_text` | 0.649070 | 1.000000 | 0.350930 | -0.649070 |
| 4 | `special_character_count` | 0.618764 | 5.244865 | 6.670650 | +1.425785 |
| 5 | `letter_ratio` | 0.420388 | 0.799957 | 0.754285 | -0.045671 |
| 6 | `domain_length` | 0.245360 | 19.228610 | 16.755600 | -2.473010 |
| 7 | `number_of_letters` | 0.189713 | 21.933148 | 22.259790 | +0.326642 |
| 8 | `number_of_subdomains` | 0.141020 | 1.161661 | 1.099110 | -0.062551 |
| 9 | `number_of_dots` | 0.137190 | 2.161661 | 2.185790 | +0.024129 |
| 10 | `url_length` | 0.123633 | 27.228610 | 29.076060 | +1.847450 |

## Top Phishing/Phishing Shifts

| Rank | Feature | KS statistic | PhiUSIIL phishing mean | URL-Phish phishing mean | External - source mean |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | `uses_https_text` | 0.426983 | 0.487354 | 0.914337 | +0.426983 |
| 2 | `path_length` | 0.321266 | 8.725256 | 17.153373 | +8.428117 |
| 3 | `number_of_slashes` | 0.321257 | 3.019208 | 3.617289 | +0.598081 |
| 4 | `number_of_subdomains` | 0.184028 | 1.156699 | 0.741988 | -0.414711 |
| 5 | `number_of_dots` | 0.169284 | 2.384695 | 1.927289 | -0.457405 |
| 6 | `domain_length` | 0.155488 | 24.461647 | 21.319639 | -3.142009 |
| 7 | `number_of_hyphens` | 0.129562 | 0.706989 | 0.937410 | +0.230421 |
| 8 | `special_character_count` | 0.126702 | 7.651246 | 8.996024 | +1.344778 |
| 9 | `url_length` | 0.121272 | 46.238774 | 56.304699 | +10.065925 |
| 10 | `number_of_letters` | 0.120656 | 34.249255 | 41.555120 | +7.305866 |

## HTTPS Shift

| Comparison | PhiUSIIL proportion HTTPS | URL-Phish proportion HTTPS | Absolute difference |
| --- | ---: | ---: | ---: |
| Legitimate vs benign | 1.000000 | 0.350930 | 64.907 pp |
| Phishing vs phishing | 0.487354 | 0.914337 | 42.698 pp |

HTTPS text usage shifts far more in the legitimate/benign class than in the
phishing class.

## Path-Length Shift

| Comparison | PhiUSIIL mean | URL-Phish mean | PhiUSIIL median | URL-Phish median |
| --- | ---: | ---: | ---: | ---: |
| Legitimate vs benign | 0.000000 | 4.604890 | 0.000000 | 1.000000 |
| Phishing vs phishing | 8.725256 | 17.153373 | 1.000000 | 6.000000 |

Path structure shifts in both classes, but the legitimate/benign comparison
has the larger KS statistic.

## Interpretation

The evidence strongly supports class-conditional covariate shift, especially
among legitimate/benign URLs. This is consistent with the observed external
failure mode: URL-Phish phishing rows remain mostly detectable, while benign
rows often resemble feature regions that the PhiUSIIL-trained tree treats as
phishing.

This diagnostic does not prove concept shift and does not prove that any single
feature caused the failure. It shows that `P(X | Y)` differs substantially
between datasets under the project's frozen Tier E feature representation.

## Safety Statement

All computations used local feature matrices. No URL from PhiUSIIL or
URL-Phish was opened, requested, resolved, pinged, scraped, or contacted.
