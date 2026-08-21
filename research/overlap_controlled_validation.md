# Overlap-Controlled External Validation

## Scope

This sensitivity analysis keeps the frozen PhiUSIIL Tier E Decision Tree fixed. It does not retrain, retune, recalibrate, change thresholds, or replace the primary external results.

## Subset Metrics

| Dataset | Subset | Rows | Phishing | Legitimate | Accuracy | Precision | Recall | F1 | Specificity | Balanced accuracy | ROC-AUC | PR-AUC |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LegitPhish | full_primary_reference | 101,218 | 63,678 | 37,540 | 0.993786 | 0.990219 | 1.000000 | 0.995085 | 0.983245 | 0.991622 | 0.991929 | 0.990573 |
| LegitPhish | remove_exact_urls_present_in_phiusiil | 64,283 | 63,678 | 605 | 0.990588 | 0.990588 | 1.000000 | 0.995272 | 0.000000 | 0.500000 | 0.500000 | 0.990588 |
| LegitPhish | remove_normalized_urls_present_in_phiusiil | 64,283 | 63,678 | 605 | 0.990588 | 0.990588 | 1.000000 | 0.995272 | 0.000000 | 0.500000 | 0.500000 | 0.990588 |
| LegitPhish | unseen_registrable_domain | 63,378 | 62,990 | 388 | 0.993878 | 0.993878 | 1.000000 | 0.996930 | 0.000000 | 0.500000 | 0.500000 | 0.993878 |
| URL-Phish | full_primary_reference | 116,600 | 16,600 | 100,000 | 0.196509 | 0.149206 | 0.987590 | 0.259245 | 0.065190 | 0.526390 | 0.524568 | 0.148627 |
| URL-Phish | remove_exact_urls_present_in_phiusiil | 115,996 | 16,600 | 99,396 | 0.192334 | 0.149207 | 0.987590 | 0.259247 | 0.059519 | 0.523555 | 0.521688 | 0.148629 |

## Interpretation

The full rows remain historical primary references. Overlap-controlled subsets test whether external performance persists after removing direct URL overlap with PhiUSIIL.

For any subset containing only one observed class, two-class metrics are marked undefined instead of assigning a numeric fallback.

## Safety Statement

All subset keys were computed from local strings with local parsing only; no URL was opened, requested, resolved, scraped, or contacted.
