# PhiUSIIL Feature Reconstruction Diagnostics

## Purpose

This report investigates why several URL-text features were directly
computable in principle but did not exactly match the existing project
extractor. The production extractor was not changed. Candidate
definitions were tested in a research-only diagnostics script.

No URL was opened, requested, resolved, pinged, or contacted.

## Candidate Representations Tested

- `A_full_stripped_raw_url`: full stripped URL string.
- `B_scheme_prefix_removed`: stripped URL after removing only `http://`
  or `https://` style scheme prefixes.
- `B2_scheme_and_www_prefix_removed`: scheme removal plus leading
  `www.` removal when present.
- `C_hostname_path_query`: locally parsed hostname, path, and query.
- `C2_hostname_without_www_path_query`: locally parsed hostname after
  leading `www.` removal, path, and query.
- `D_netloc_path_query`: locally parsed netloc, path, and query.
- `_other_special`: alternate special-character count that excludes
  common URL structural separators from "other special" characters.

## Confirmed By Evidence

- The original production `url_length` comparison matched only 20.630% exactly, with modal supplied-minus-reconstructed delta -1.
- Scheme removal does not explain the `URLLength` mismatch. After removing only the scheme prefix, exact match is 0.000% with MAE 6.986904 and modal delta 7.
- The best tested `URLLength` candidate remains `A_full_stripped_raw_url` with 20.630% exact match and modal delta -1.
- For `http` rows under scheme removal, exact match was 0.000% with modal delta 6.
- For `https` rows under scheme removal, exact match was 0.000% with modal delta 7.

Best candidate rows by feature:

| Feature | Best candidate | Exact % | MAE | Pearson | Modal delta |
| --- | --- | ---: | ---: | ---: | ---: |
| `DegitRatioInURL` | `A_full_stripped_raw_url` | 79.227 | 0.000439 | 0.999629 | 0 |
| `LetterRatioInURL` | `B_scheme_prefix_removed` | 0.028 | 0.322615 | 0.332821 | -0 |
| `NoOfDegitsInURL` | `A_full_stripped_raw_url` | 99.486 | 0.005161 | 0.999981 | 0 |
| `NoOfLettersInURL` | `B2_scheme_and_www_prefix_removed` | 26.728 | 0.749465 | 0.999789 | -1 |
| `NoOfOtherSpecialCharsInURL` | `B2_scheme_and_www_prefix_removed` | 91.514 | 0.185911 | 0.973848 | 0 |
| `SpacialCharRatioInURL` | `B2_scheme_and_www_prefix_removed_other_special` | 0.044 | 0.052260 | 0.628654 | 0 |
| `URLLength` | `A_full_stripped_raw_url` | 20.630 | 0.793859 | 0.999953 | -1 |

## Likely

- The letter-count mismatch is partly reduced by excluding common prefix material such as scheme text and leading `www.`, but the best tested candidate still leaves many residual mismatches. The best tested candidate for `NoOfLettersInURL` is `B2_scheme_and_www_prefix_removed` with 26.728% exact match.
- The special-character mismatch is likely explained by a narrower definition of "other special" characters. The best tested candidate for `NoOfOtherSpecialCharsInURL` is `B2_scheme_and_www_prefix_removed` with 91.514% exact match.
- Prefix removal explains part of the character-count behavior,
  especially special-character counts, but residual mismatches
  remain for malformed, unusual, or differently normalized URL
  strings.

## Unresolved

- The original PhiUSIIL source code or formal feature formulas were
  not available in the project files, so this report does not claim
  bit-for-bit discovery of the original implementation.
- `NoOfAmpersandInURL` and a small subset of query-character rows still
  show discrepancies, likely due to URL encoding or preprocessing
  differences that are not fully specified.
- `SpacialCharRatioInURL` remains spelling-preserved from the dataset
  and depends on the same unresolved special-character convention.

## Safety Statement

All operations were local string parsing and aggregation. No dataset
URL was contacted.
