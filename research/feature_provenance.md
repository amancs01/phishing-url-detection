# PhiUSIIL Feature Provenance Audit

## Purpose

This audit records whether each PhiUSIIL column can be used in a
deployment-realistic model that receives only a raw URL string. The audit is
intentionally conservative: a feature is marked directly reproducible only
when it can be recomputed from local URL text without webpage access, network
operations, or hidden reference statistics.

No model training is performed in this step.

## Evidence Used

- Local raw dataset schema: `data/raw/phiusil_raw.csv`
- Local schema report: `results/dataset_schema.json`
- Existing local feature-selection notes: `docs/dataset_schema.md` and
  `docs/url_feature_selection.md`
- Project extractor contract: `src/feature_extractor.py` and
  `src/feature_definitions.py`
- UCI and Mendeley dataset descriptions, which state that PhiUSIIL features
  were extracted from webpage source code and URL information, and that
  `URLSimilarityIndex`, `CharContinuationRate`, `TLDLegitimateProb`, and
  `URLCharProb` are derived from existing features.

## Category Definitions

- `A identifier/label/non-model`: source text, labels, or metadata that should
  not be treated as numerical deployment features.
- `B directly computable raw URL text`: features that can be computed from
  the submitted URL string using local parsing and character counting only.
- `C URL-derived but external/reference/unavailable stats`: URL-related
  features that appear to require reference distributions, label frequencies,
  similarity corpora, or other unavailable state.
- `D webpage/content-derived`: features requiring HTML, title text, redirects,
  page resources, forms, scripts, rendering behavior, or link analysis.
- `E uncertain/needs verification`: features whose source is not adequately
  specified by available local definitions.

## Summary Counts

| Provenance category | Count |
| --- | ---: |
| A identifier/label/non-model | 2 |
| B directly computable raw URL text | 20 |
| C URL-derived but external/reference/unavailable stats | 1 |
| D webpage/content-derived | 26 |
| E uncertain/needs verification | 6 |
| Total audited columns | 55 |

## Directly Computable Raw-URL Columns

These supplied PhiUSIIL columns are plausible raw-URL-text features:

`URLLength`, `Domain`, `DomainLength`, `IsDomainIP`, `TLD`, `TLDLength`,
`NoOfSubDomain`, `HasObfuscation`, `NoOfObfuscatedChar`,
`ObfuscationRatio`, `NoOfLettersInURL`, `LetterRatioInURL`,
`NoOfDegitsInURL`, `DegitRatioInURL`, `NoOfEqualsInURL`,
`NoOfQMarkInURL`, `NoOfAmpersandInURL`, `NoOfOtherSpecialCharsInURL`,
`SpacialCharRatioInURL`, and `IsHTTPS`.

This classification means the feature concept is computable from URL text. It
does not yet mean the project's extractor exactly reproduces the original
PhiUSIIL implementation.

## Scrutinized Derived Or Ambiguous Columns

`URLSimilarityIndex` is URL-related but not accepted as directly reproducible.
The available documentation does not specify the comparison reference,
similarity formula, or preprocessing.

`CharContinuationRate` is also documented as derived, but the formula and any
reference statistics are not available locally.

`TLDLegitimateProb` is classified as reference-dependent because a TLD
legitimacy probability cannot be known from one submitted URL string alone.

`URLCharProb` is uncertain because the probability model or reference corpus is
not available.

`URLTitleMatchScore` is webpage/content-derived because it requires title text
from page content in addition to URL text.

`Bank`, `Pay`, and `Crypto` are left uncertain because the names suggest
keyword indicators, but available definitions do not prove whether the keyword
search used URL text, webpage content, or both.

## Deployment Model Implication

The current dashboard model does not use supplied PhiUSIIL feature columns at
inference time. It uses the project's independently extracted 26 URL-text
features from `src/feature_definitions.py`.

Therefore `included_in_deployment_model` is marked `false` for every original
PhiUSIIL column. Later fidelity analysis maps comparable PhiUSIIL columns to
the project's deployment features without treating the supplied columns as the
production feature source.

## Safety Note

The audit uses only local files and static documentation. It does not open,
visit, request, resolve, ping, or otherwise contact any URL from the dataset.
