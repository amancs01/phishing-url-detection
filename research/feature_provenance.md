# PhiUSIIL Feature Provenance Audit

## Purpose

This audit records whether each PhiUSIIL column can be used in a
deployment-realistic model that receives only a raw URL string. The final
taxonomy is conservative: a feature enters the direct-reproducible tier only
when it can be computed from one URL string without webpage access, network
operations, or hidden reference statistics.

No model training is performed in this taxonomy step.

## Evidence Used

- Local raw dataset schema: `data/raw/phiusil_raw.csv`
- Local schema report: `results/dataset_schema.json`
- Existing local feature-selection notes: `docs/dataset_schema.md` and
  `docs/url_feature_selection.md`
- Project extractor contract: `src/feature_extractor.py` and
  `src/feature_definitions.py`
- Empirical reconstruction diagnostics:
  `results/feature_delta_diagnostics.csv` and
  `research/feature_reconstruction_diagnostics.md`
- Official UCI and Mendeley dataset descriptions, which state that PhiUSIIL
  features were extracted from webpage source code and URL information, and
  that `CharContinuationRate`, `URLTitleMatchScore`, `URLCharProb`, and
  `TLDLegitimateProb` are derived from existing features.

## Category Definitions

- `A identifier/label/non-model`: source text, labels, or metadata that should
  not be treated as numerical deployment features.
- `B directly computable raw URL text`: features that can be computed from
  the submitted URL string using local parsing and character counting only.
- `C URL-derived but external/reference/unavailable stats`: URL-related
  features that appear to require reference distributions, similarity
  conventions, probability models, or other unavailable state.
- `D webpage/content-derived`: features requiring HTML, title text, redirects,
  page resources, forms, scripts, rendering behavior, content keywords, or
  link analysis.
- `E uncertain/needs verification`: features whose source is not adequately
  specified by available local definitions.

## Final Summary Counts

| Provenance category | Count |
| --- | ---: |
| A identifier/label/non-model | 2 |
| B directly computable raw URL text | 20 |
| C URL-derived but external/reference/unavailable stats | 3 |
| D webpage/content-derived | 29 |
| E uncertain/needs verification | 1 |
| Total audited columns | 55 |

## Resolved Review Features

`URLSimilarityIndex` is now classified as URL-derived but
reference-dependent or definition-dependent. The official metadata documents a
similarity-oriented derived feature, but the comparison reference and formula
are not available from one submitted URL.

`TLDLegitimateProb` remains reference-dependent because a TLD legitimacy
probability requires a corpus distribution or prior, not only one URL string.

`URLCharProb` is now classified as URL-derived but reference-dependent because
the probability model or reference distribution is unavailable.

`URLTitleMatchScore` remains webpage/content-derived because title text is
not available without webpage content.

`Bank`, `Pay`, and `Crypto` are classified as webpage/content-derived for
this study. They appear in the content-oriented block of the dataset, and no
official URL-only rule is specified. This is not a leakage claim; it is a
deployment-availability classification.

`CharContinuationRate` remains uncertain. The official metadata says it is a
derived feature, but the formula is not specified enough to prove whether it
is directly computable from one URL string or needs a reference convention.
It is excluded from deployment-reproducible tiers.

## Important Distinction

Directly URL-computable does not mean bit-for-bit reproduction of PhiUSIIL's
original implementation. The reconstruction diagnostics showed that several
concepts are computable from URL text but still differ from the supplied
values because PhiUSIIL appears to use undocumented preprocessing or counting
conventions.

## Locked Benchmark Tiers

### Tier A: Full Benchmark

All usable numerical PhiUSIIL model features excluding labels, identifiers,
raw text columns, and obvious non-model fields.

Count: 50

Feature list:

`URLLength`, `DomainLength`, `IsDomainIP`, `URLSimilarityIndex`,
`CharContinuationRate`, `TLDLegitimateProb`, `URLCharProb`, `TLDLength`,
`NoOfSubDomain`, `HasObfuscation`, `NoOfObfuscatedChar`,
`ObfuscationRatio`, `NoOfLettersInURL`, `LetterRatioInURL`,
`NoOfDegitsInURL`, `DegitRatioInURL`, `NoOfEqualsInURL`,
`NoOfQMarkInURL`, `NoOfAmpersandInURL`, `NoOfOtherSpecialCharsInURL`,
`SpacialCharRatioInURL`, `IsHTTPS`, `LineOfCode`, `LargestLineLength`,
`HasTitle`, `DomainTitleMatchScore`, `URLTitleMatchScore`, `HasFavicon`,
`Robots`, `IsResponsive`, `NoOfURLRedirect`, `NoOfSelfRedirect`,
`HasDescription`, `NoOfPopup`, `NoOfiFrame`, `HasExternalFormSubmit`,
`HasSocialNet`, `HasSubmitButton`, `HasHiddenFields`, `HasPasswordField`,
`Bank`, `Pay`, `Crypto`, `HasCopyrightInfo`, `NoOfImage`, `NoOfCSS`,
`NoOfJS`, `NoOfSelfRef`, `NoOfEmptyRef`, and `NoOfExternalRef`.

### Tier B: Supplied URL-Oriented

All supplied numerical features whose source is URL-related, including
documented URL-derived reference/probability attributes. This tier keeps
reference-dependent URL attributes because it represents a supplied benchmark
condition, not deployment availability.

Count: 22

Feature list:

`URLLength`, `DomainLength`, `IsDomainIP`, `URLSimilarityIndex`,
`CharContinuationRate`, `TLDLegitimateProb`, `URLCharProb`, `TLDLength`,
`NoOfSubDomain`, `HasObfuscation`, `NoOfObfuscatedChar`,
`ObfuscationRatio`, `NoOfLettersInURL`, `LetterRatioInURL`,
`NoOfDegitsInURL`, `DegitRatioInURL`, `NoOfEqualsInURL`,
`NoOfQMarkInURL`, `NoOfAmpersandInURL`, `NoOfOtherSpecialCharsInURL`,
`SpacialCharRatioInURL`, and `IsHTTPS`.

### Tier C: Supplied Direct-Reproducible

Only supplied PhiUSIIL numerical features that are defensibly computable
directly from one raw URL without webpage access or external/reference
corpora.

Count: 18

Feature list:

`URLLength`, `DomainLength`, `IsDomainIP`, `TLDLength`, `NoOfSubDomain`,
`HasObfuscation`, `NoOfObfuscatedChar`, `ObfuscationRatio`,
`NoOfLettersInURL`, `LetterRatioInURL`, `NoOfDegitsInURL`,
`DegitRatioInURL`, `NoOfEqualsInURL`, `NoOfQMarkInURL`,
`NoOfAmpersandInURL`, `NoOfOtherSpecialCharsInURL`,
`SpacialCharRatioInURL`, and `IsHTTPS`.

### Tier D-Matched: Independently Reconstructed

Research-specific local reconstructions of the Tier C feature concepts where
a faithful semantic mapping is possible. These are not production extractor
features and do not modify the dashboard pipeline.

Count: 18

Feature list:

`d_url_length`, `d_domain_length`, `d_is_domain_ip`, `d_tld_length`,
`d_number_of_subdomains`, `d_has_obfuscation`,
`d_number_of_obfuscated_chars`, `d_obfuscation_ratio`,
`d_number_of_letters`, `d_letter_ratio`, `d_number_of_digits`,
`d_digit_ratio`, `d_number_of_equal_signs`,
`d_number_of_question_marks`, `d_number_of_ampersands`,
`d_number_of_other_special_chars`, `d_special_char_ratio`, and
`d_is_https`.

### Tier E: Deployment-Extended

The project's existing 26-feature custom safe URL extractor. Tier E is the
practical deployment condition, but it is not a direct supplied-versus-
reconstructed fidelity comparison because it contains additional custom
features beyond Tier C.

Count: 26

Feature list:

`url_length`, `domain_length`, `path_length`, `query_length`,
`number_of_dots`, `number_of_hyphens`, `number_of_underscores`,
`number_of_slashes`, `number_of_question_marks`, `number_of_equal_signs`,
`number_of_at_symbols`, `number_of_ampersands`,
`number_of_percent_symbols`, `number_of_digits`, `number_of_letters`,
`digit_ratio`, `letter_ratio`, `special_character_count`,
`number_of_subdomains`, `domain_is_ip`, `uses_https_text`, `has_port`,
`number_of_query_parameters`, `suspicious_keyword_count`,
`has_suspicious_keyword`, and `known_shortener_domain`.

## Deployment Model Implication

The current dashboard model still uses only Tier E features generated by the
project's production extractor. No supplied PhiUSIIL column is used directly
at inference time.

## Safety Note

The audit uses only local files, local URL parsing, aggregate diagnostics, and
static documentation. It does not open, visit, request, resolve, ping, or
otherwise contact any URL from the dataset.
