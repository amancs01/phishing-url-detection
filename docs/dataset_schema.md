# Dataset Schema

This document summarizes the actual schema and validation results produced by:

- `src/inspect_data.py`
- `src/validate_data.py`

The scripts read only the local file `data/raw/phiusil_raw.csv`.

## Dataset Dimensions

- Rows: 235,795
- Columns: 55
- Feature columns before target removal: 54
- Target column: `label`

## Target Labels

The target column is `label`.

| Label | Meaning | Count |
| --- | --- | ---: |
| `0` | Phishing | 100,945 |
| `1` | Legitimate | 134,850 |

The validation report found only the expected target values `0` and `1`.
There are no missing target values.

## Identifier and Text Columns

The dataset includes the following important identifier or text fields:

| Column | Notes |
| --- | --- |
| `URL` | Full URL text. This is safe to parse as text, but raw phishing URLs should not be displayed directly. |
| `Domain` | Domain text extracted from the URL. This appears URL-derived. |
| `TLD` | Top-level domain text. This appears URL-derived. |
| `Title` | Page title text. This appears webpage/content-derived and cannot be recreated safely without visiting the page. |
| `label` | Binary target class. |

## Numeric Feature Columns

The numeric columns reported by pandas are:

`URLLength`, `DomainLength`, `IsDomainIP`, `URLSimilarityIndex`,
`CharContinuationRate`, `TLDLegitimateProb`, `URLCharProb`, `TLDLength`,
`NoOfSubDomain`, `HasObfuscation`, `NoOfObfuscatedChar`, `ObfuscationRatio`,
`NoOfLettersInURL`, `LetterRatioInURL`, `NoOfDegitsInURL`,
`DegitRatioInURL`, `NoOfEqualsInURL`, `NoOfQMarkInURL`,
`NoOfAmpersandInURL`, `NoOfOtherSpecialCharsInURL`,
`SpacialCharRatioInURL`, `IsHTTPS`, `LineOfCode`, `LargestLineLength`,
`HasTitle`, `DomainTitleMatchScore`, `URLTitleMatchScore`, `HasFavicon`,
`Robots`, `IsResponsive`, `NoOfURLRedirect`, `NoOfSelfRedirect`,
`HasDescription`, `NoOfPopup`, `NoOfiFrame`, `HasExternalFormSubmit`,
`HasSocialNet`, `HasSubmitButton`, `HasHiddenFields`, `HasPasswordField`,
`Bank`, `Pay`, `Crypto`, `HasCopyrightInfo`, `NoOfImage`, `NoOfCSS`,
`NoOfJS`, `NoOfSelfRef`, `NoOfEmptyRef`, `NoOfExternalRef`, and `label`.

## Features That Appear URL-Text-Derived

These columns appear to be safely reproducible from URL text or its parsed
parts:

- `URL`
- `URLLength`
- `Domain`
- `DomainLength`
- `IsDomainIP`
- `TLD`
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

These columns may be derived from URL text, but their exact definitions need
further verification before they can be used in the final dashboard model:

- `URLSimilarityIndex`
- `CharContinuationRate`
- `TLDLegitimateProb`
- `URLCharProb`

## Features That Appear Webpage or Content-Derived

These columns appear to depend on webpage HTML, page content, page behavior, or
links collected from the webpage:

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
- `HasCopyrightInfo`
- `NoOfImage`
- `NoOfCSS`
- `NoOfJS`
- `NoOfSelfRef`
- `NoOfEmptyRef`
- `NoOfExternalRef`

The columns `Bank`, `Pay`, and `Crypto` are keyword-style indicators, but the
column names alone do not prove whether the keywords came from URL text, page
content, or both. They require further verification before final feature
selection.

## Why Webpage-Dependent Features Are Excluded Later

The final Streamlit dashboard must classify a user-submitted URL without
opening, visiting, requesting, downloading from, pinging, resolving, or
otherwise connecting to that URL. Webpage-dependent features cannot be used in
that final prediction system because they would require live website access or
stored page content that the dashboard will not have.

Using only URL-text-derived features also keeps the training data consistent
with the final application: every feature used during training must be
recreatable from a plain URL string entered by the user.

## Missing Values and Duplicates

Validation results:

- Missing values: 0
- Duplicate full rows: 0
- Duplicate URL values: 425 duplicated URL texts
- Rows with duplicate URL text: 850
- Constant columns: none
- Duplicate column names: none

No rows were deleted during validation. These results only describe the current
data quality.
