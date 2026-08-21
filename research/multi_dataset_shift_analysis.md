# Multi-Dataset Class-Conditional Shift Analysis

## Scope

This post-hoc diagnostic compares the fixed Tier E lexical feature space across PhiUSIIL, URL-Phish, and LegitPhish. It uses only local feature matrices derived from URL strings; no URL was opened, requested, resolved, or contacted.

## Similarity Summary

| Semantic class | External dataset | Mean KS | Median KS | Max KS | Rank |
| --- | --- | ---: | ---: | ---: | ---: |
| legitimate | LegitPhish | 0.004445 | 0.002042 | 0.015956 | 1 |
| legitimate | URL-Phish | 0.173850 | 0.020020 | 0.889860 | 2 |
| phishing | URL-Phish | 0.112336 | 0.089140 | 0.426983 | 1 |
| phishing | LegitPhish | 0.358168 | 0.355834 | 0.764369 | 2 |

Lower average KS indicates greater lexical similarity to the matching PhiUSIIL class. By that criterion, LegitPhish is more similar to PhiUSIIL legitimate URLs, while URL-Phish is more similar to PhiUSIIL phishing URLs.

## Top Legitimate-Class Shifts

PhiUSIIL legitimate vs URL-Phish benign:
- path_length: KS=0.890, internal_mean=0.000, external_mean=4.605
- number_of_slashes: KS=0.890, internal_mean=2.000, external_mean=3.148
- uses_https_text: KS=0.649, internal_mean=1.000, external_mean=0.351
- special_character_count: KS=0.619, internal_mean=5.245, external_mean=6.671
- letter_ratio: KS=0.420, internal_mean=0.800, external_mean=0.754

PhiUSIIL legitimate vs LegitPhish legitimate:
- path_length: KS=0.016, internal_mean=0.000, external_mean=0.487
- number_of_slashes: KS=0.016, internal_mean=2.000, external_mean=2.037
- special_character_count: KS=0.014, internal_mean=5.245, external_mean=5.320
- url_length: KS=0.012, internal_mean=27.229, external_mean=27.681
- number_of_letters: KS=0.011, internal_mean=21.933, external_mean=22.280

## Top Phishing-Class Shifts

PhiUSIIL phishing vs URL-Phish phishing:
- uses_https_text: KS=0.427, internal_mean=0.487, external_mean=0.914
- path_length: KS=0.321, internal_mean=8.725, external_mean=17.153
- number_of_slashes: KS=0.321, internal_mean=3.019, external_mean=3.617
- number_of_subdomains: KS=0.184, internal_mean=1.157, external_mean=0.742
- number_of_dots: KS=0.169, internal_mean=2.385, external_mean=1.927

PhiUSIIL phishing vs LegitPhish phishing:
- domain_is_ip: KS=0.764, internal_mean=0.006, external_mean=0.770
- number_of_digits: KS=0.734, internal_mean=4.338, external_mean=13.477
- letter_ratio: KS=0.727, internal_mean=0.747, external_mean=0.374
- path_length: KS=0.722, internal_mean=8.725, external_mean=12.686
- digit_ratio: KS=0.719, internal_mean=0.064, external_mean=0.382

## PhiUSIIL vs LegitPhish Origin Diagnostics

- legitimate_only_phiusiil_vs_legitphish_origin: accuracy=0.507903, AUC=0.508291, top features=number_of_slashes, digit_ratio, letter_ratio, special_character_count, has_suspicious_keyword
- phishing_only_phiusiil_vs_legitphish_origin: accuracy=0.952679, AUC=0.990815, top features=domain_is_ip, number_of_underscores, path_length, url_length, uses_https_text

These origin trees are diagnostic only. They estimate whether a shallow classifier can separate dataset source within a fixed semantic class, and they are not phishing-detection models.
