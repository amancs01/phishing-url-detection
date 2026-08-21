# Cross-Dataset Overlap Audit

## Scope

This audit compares PhiUSIIL against URL-Phish and LegitPhish using local URL strings only. It reports aggregate overlap counts for exact stripped URLs, stripped-lower normalized URLs, and offline registrable-domain keys. It does not list overlapping URLs or domains.

## Pairwise Overlap

| External dataset | Exact shared URLs | Normalized shared URLs | Shared registrable domains | Exact cross-label conflicts | Normalized cross-label conflicts | Domain cross-label conflicts |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| URL-Phish | 595 | 595 | 7,149 | 0 | 0 | 97 |
| LegitPhish | 36,935 | 36,935 | 36,515 | 0 | 0 | 41 |

## LegitPhish Seen/Unseen-Domain Composition

| Segment | Total | Phishing | Legitimate | Phishing proportion | Legitimate proportion | Predicted phishing | Predicted legitimate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Seen in PhiUSIIL | 37,840 | 688 | 37,152 | 0.018182 | 0.981818 | 929 | 36,911 |
| Unseen in PhiUSIIL | 63,378 | 62,990 | 388 | 0.993878 | 0.006122 | 63,378 | 0 |

## Unseen-Domain Metric Note

The prior unseen-domain ROC-AUC of 0.5 was a valid two-class calculation, not a single-class fallback: the subset contained both phishing and legitimate rows, but the frozen model assigned all unseen-domain rows to the phishing class.

The unseen-domain subset is extremely class-skewed toward phishing. Its high phishing F1 coexists with ROC-AUC and balanced accuracy of 0.5 because the model predicts every row as phishing, yielding phishing recall of 1.0 and legitimate specificity of 0.0.

## Safety Statement

All overlap keys were computed from local strings with local parsing only; no URL was opened, requested, resolved, scraped, or contacted.
