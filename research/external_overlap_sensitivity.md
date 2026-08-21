# Post-Hoc Diagnostic Analysis: External Overlap And Deduplication Sensitivity

## Purpose

This secondary post-hoc diagnostic analysis checks whether the primary
URL-Phish external result is sensitive to exact duplicate URLs or cross-dataset
registrable-domain overlap. It does not replace the primary external
evaluation.

No model is retrained, no threshold is changed, and no URL is contacted.

## Part A: Exact-URL Deduplication

Before deduplication, exact duplicate URL values were checked for conflicting
labels. No conflicting duplicate URL values were found.

| Diagnostic | Value |
| --- | ---: |
| Raw external rows | 116,600 |
| Duplicate full rows | 1,369 |
| Duplicate URL rows | 1,369 |
| Conflicting duplicate URL values | 0 |
| Rows with conflicting duplicate URL | 0 |
| Deduplicated rows | 115,231 |
| Deduplicated phishing rows | 16,590 |
| Deduplicated legitimate rows | 98,641 |

Deduplicated external metrics:

| Metric | Primary external | Deduplicated | Difference |
| --- | ---: | ---: | ---: |
| Accuracy | 0.196509 | 0.198263 | +0.001753 |
| Phishing precision | 0.149206 | 0.150917 | +0.001711 |
| Phishing recall | 0.987590 | 0.987583 | -0.000007 |
| Phishing F1 | 0.259245 | 0.261824 | +0.002579 |
| ROC-AUC | 0.524568 | 0.524726 | +0.000158 |
| Balanced accuracy | 0.526390 | 0.526547 | +0.000156 |

Deduplication does not materially alter the core conclusion. External benign
specificity remains very low and phishing recall remains high.

## Part B: Cross-Dataset Registrable-Domain Overlap

Registrable domains were extracted with the existing offline `publicsuffix2`
utility. No DNS, WHOIS, socket, request, SSL, browser automation, or webpage
lookup was performed.

| Diagnostic | Value |
| --- | ---: |
| URL-Phish registrable domains | 91,683 |
| Domains also present in PhiUSIIL | 7,149 |
| Domains unseen in PhiUSIIL | 84,534 |
| Overlap percentage | 7.798% |

External metrics by domain-overlap segment:

| Segment | Rows | Phishing rows | Legitimate rows | Accuracy | Precision | Recall | F1 | ROC-AUC | Balanced accuracy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Seen in PhiUSIIL | 22,326 | 9,436 | 12,890 | 0.481815 | 0.448778 | 0.990250 | 0.617642 | 0.548833 | 0.549935 |
| Unseen in PhiUSIIL | 94,274 | 7,164 | 87,110 | 0.128943 | 0.079165 | 0.984087 | 0.146542 | 0.519199 | 0.521351 |

The seen-domain segment performs better than the unseen-domain segment, but
both retain the same qualitative failure mode: high phishing recall and low
benign specificity. This does not show that domain overlap caused the failure.
Most external registrable domains are unseen in PhiUSIIL, so simple domain
overlap is not a sufficient explanation for the external result.

## Part C: Source Metadata

URL-Phish Version 2 does not contain reliable source/category metadata such as
education, government, ranked commercial, or other source labels. This part was
therefore skipped. The analysis does not infer source category from URL text.

## Interpretation

Exact-URL duplicates are not driving the external result. Removing duplicates
leaves the same pattern: high phishing recall and very low benign specificity.

Registrable-domain overlap alone does not explain the failure. Most URL-Phish
registrable domains are unseen in PhiUSIIL. The seen-domain segment performs
better, but it still has low benign specificity, and the unseen-domain segment
still catches most phishing rows while overpredicting phishing on benign rows.
This supports the broader diagnostic story that the external failure is
associated with feature-distribution shift, especially in benign URL structure,
rather than a simple duplicate or domain overlap artifact.

## Safety Statement

All URL and domain operations used local strings and offline public suffix
parsing. No URL from PhiUSIIL or URL-Phish was opened, requested, resolved,
pinged, scraped, or contacted.
