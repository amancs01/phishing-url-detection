# Feature Fidelity Analysis

## Purpose

This analysis answers the first part of the deployment-realism question: when a
PhiUSIIL feature appears computable from raw URL text, does the project's
independent extractor reproduce the supplied dataset values?

The audit compares supplied PhiUSIIL columns with the project's current
deployment extractor. It does not tune, retrain, or evaluate any model.

## Inputs And Outputs

Input dataset:

- `data/raw/phiusil_raw.csv`
- Rows compared: 235,795

Mapping file:

- `research/feature_mapping.json`

Generated outputs:

- `results/feature_fidelity.csv`
- `results/feature_fidelity_summary.json`
- `results/feature_fidelity_mismatch_samples.csv`
- `reports/figures/feature_fidelity_exact_match.png`
- `reports/figures/feature_fidelity_error.png`

The mismatch sample includes only row index, label, supplied value,
reconstructed value, and absolute error. It does not include raw URLs.

## Mapped Features

The audit compares 13 supplied PhiUSIIL fields against the project's
deployment extractor:

| Supplied PhiUSIIL feature | Reconstructed project feature | Type |
| --- | --- | --- |
| `URLLength` | `url_length` | discrete |
| `DomainLength` | `domain_length` | discrete |
| `IsDomainIP` | `domain_is_ip` | discrete |
| `NoOfSubDomain` | `number_of_subdomains` | discrete |
| `NoOfLettersInURL` | `number_of_letters` | discrete |
| `LetterRatioInURL` | `letter_ratio` | continuous |
| `NoOfDegitsInURL` | `number_of_digits` | discrete |
| `DegitRatioInURL` | `digit_ratio` | continuous |
| `NoOfEqualsInURL` | `number_of_equal_signs` | discrete |
| `NoOfQMarkInURL` | `number_of_question_marks` | discrete |
| `NoOfAmpersandInURL` | `number_of_ampersands` | discrete |
| `NoOfOtherSpecialCharsInURL` | `special_character_count` | discrete |
| `IsHTTPS` | `uses_https_text` | discrete |

Features such as `TLDLength`, `HasObfuscation`, `NoOfObfuscatedChar`,
`ObfuscationRatio`, and `SpacialCharRatioInURL` are directly computable in
principle, but they were excluded from this fidelity mapping because the
current deployment extractor does not expose one-to-one feature names for
them.

## Fidelity Results

| Supplied feature | Exact match % | Near match % | MAE | Pearson corr |
| --- | ---: | ---: | ---: | ---: |
| `URLLength` | 20.630 | 20.630 | 0.793859 | 0.999953 |
| `DomainLength` | 99.985 | 99.985 | 0.001497 | 0.999835 |
| `IsDomainIP` | 99.987 | 99.987 | 0.000127 | 0.976144 |
| `NoOfSubDomain` | 99.739 | 99.739 | 0.005221 | 0.985611 |
| `NoOfLettersInURL` | 0.000 | 0.000 | 7.776815 | 0.998260 |
| `LetterRatioInURL` | 0.000 | 0.001 | 0.261444 | 0.506183 |
| `NoOfDegitsInURL` | 99.486 | 99.486 | 0.005161 | 0.999981 |
| `DegitRatioInURL` | 79.227 | 92.024 | 0.000439 | 0.999629 |
| `NoOfEqualsInURL` | 99.894 | 99.894 | 0.001056 | 0.999400 |
| `NoOfQMarkInURL` | 99.995 | 99.995 | 0.000051 | 0.999321 |
| `NoOfAmpersandInURL` | 98.655 | 98.655 | 0.045637 | 0.238837 |
| `NoOfOtherSpecialCharsInURL` | 0.000 | 0.000 | 3.934850 | 0.962965 |
| `IsHTTPS` | 99.791 | 99.791 | 0.002091 | 0.993895 |

Mean exact match across mapped features: 69.030%.

Mean near match across mapped features: 70.014%.

## Highest Agreement

The strongest exact-match features were:

1. `NoOfQMarkInURL` -> `number_of_question_marks`: 99.995%
2. `IsDomainIP` -> `domain_is_ip`: 99.987%
3. `DomainLength` -> `domain_length`: 99.985%
4. `NoOfEqualsInURL` -> `number_of_equal_signs`: 99.894%
5. `IsHTTPS` -> `uses_https_text`: 99.791%

These results support the hypothesis that simple URL structure indicators can
be independently reconstructed with high fidelity.

## Surprising Disagreements

`URLLength` matched exactly for only 20.630% of rows, despite an extremely high
Pearson correlation of 0.999953 and a median absolute error of 1.0. This
suggests a systematic preprocessing difference, such as whether a trailing
slash, scheme normalization, or stored canonical form was counted.

`NoOfLettersInURL` and `LetterRatioInURL` had 0% exact match. The mismatch
sample shows that the supplied letter counts are often lower than the project
extractor's full stripped-URL counts. A likely reason is that PhiUSIIL may
count letters in a normalized URL component or exclude scheme characters such
as `https`.

`NoOfOtherSpecialCharsInURL` also had 0% exact match. The project extractor's
`special_character_count` counts all non-letter, non-digit, non-whitespace
characters in the full stripped URL, while PhiUSIIL's "other special chars"
appears to use a narrower definition.

`NoOfAmpersandInURL` had high exact match, but low Pearson correlation. This
can happen when a rare-character feature is mostly zero and disagreements are
concentrated in a small subset of rows.

These disagreements do not mean the deployment extractor is wrong. They show
that "directly computable" is different from "exactly reproduces the original
dataset implementation."

## Excluded From Fidelity Mapping

The following directly computable or partly URL-oriented features were not
mapped because the current deployment extractor does not expose an exact
one-to-one feature:

- `TLDLength`
- `HasObfuscation`
- `NoOfObfuscatedChar`
- `ObfuscationRatio`
- `SpacialCharRatioInURL`

The following were excluded because they require reference statistics,
webpage content, or unavailable definitions:

- `URLSimilarityIndex`
- `CharContinuationRate`
- `TLDLegitimateProb`
- `URLCharProb`
- `LineOfCode`
- `LargestLineLength`
- `HasTitle`
- `Title`
- `DomainTitleMatchScore`
- `URLTitleMatchScore`
- `HasFavicon`
- `Robots`
- `IsResponsive`
- `NoOfURLRedirect`
- `NoOfSelfRedirect`
- `HasDescription`
- `NoOfPopup`
- `NoOfiFrame`
- `HasExternalFormSubmit`
- `HasSocialNet`
- `HasSubmitButton`
- `HasHiddenFields`
- `HasPasswordField`
- `Bank`
- `Pay`
- `Crypto`
- `HasCopyrightInfo`
- `NoOfImage`
- `NoOfCSS`
- `NoOfJS`
- `NoOfSelfRef`
- `NoOfEmptyRef`
- `NoOfExternalRef`

## Tier C Candidate Feature List

Tier C means supplied PhiUSIIL numerical features whose concepts are
defensible as directly reproducible from raw URL text. This list is for future
experiments only; no model is trained in this batch.

Exact Tier C candidate list:

- `URLLength`
- `DomainLength`
- `IsDomainIP`
- `TLDLength`
- `NoOfSubDomain`
- `HasObfuscation`
- `NoOfObfuscatedChar`
- `ObfuscationRatio`
- `NoOfLettersInURL`
- `LetterRatioInURL`
- `NoOfDegitsInURL`
- `DegitRatioInURL`
- `NoOfEqualsInURL`
- `NoOfQMarkInURL`
- `NoOfAmpersandInURL`
- `NoOfOtherSpecialCharsInURL`
- `SpacialCharRatioInURL`
- `IsHTTPS`

`Domain` and `TLD` are directly derivable text metadata, but they are excluded
from Tier C because Tier C is a numerical Decision Tree feature tier.

## Tier D Candidate Feature List

Tier D means the project's independently re-extracted deployment feature set.
It is exactly the `FEATURE_NAMES` list in `src/feature_definitions.py`:

- `url_length`
- `domain_length`
- `path_length`
- `query_length`
- `number_of_dots`
- `number_of_hyphens`
- `number_of_underscores`
- `number_of_slashes`
- `number_of_question_marks`
- `number_of_equal_signs`
- `number_of_at_symbols`
- `number_of_ampersands`
- `number_of_percent_symbols`
- `number_of_digits`
- `number_of_letters`
- `digit_ratio`
- `letter_ratio`
- `special_character_count`
- `number_of_subdomains`
- `domain_is_ip`
- `uses_https_text`
- `has_port`
- `number_of_query_parameters`
- `suspicious_keyword_count`
- `has_suspicious_keyword`
- `known_shortener_domain`

## Implications

The audit supports a careful experimental design. Future benchmark comparisons
should not assume that all URL-looking supplied columns are equivalent to
deployment features. Some raw-URL concepts reproduce almost exactly; others
appear to depend on undocumented preprocessing choices.

The next modeling stage should therefore compare:

- supplied full benchmark features,
- supplied reproducible Tier C features, and
- independently extracted Tier D features.

This separation keeps the research question centered on feature provenance and
deployment realism rather than only on benchmark accuracy.

## Safety Statement

The fidelity script parses URL strings locally using project code. It does not
open, visit, request, resolve, ping, scrape, or otherwise contact any dataset
URL.
