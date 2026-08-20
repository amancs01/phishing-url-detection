"""Build controlled feature tiers for benchmark-vs-reproducible experiments.

The builders in this module use only local dataframe columns and local URL
string parsing. They never open, request, resolve, ping, or contact URLs.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pandas as pd
from sklearn.model_selection import train_test_split

from src.config import RANDOM_STATE, RAW_DATA_FILE, RESULTS_DIRECTORY
from src.feature_definitions import FEATURE_NAMES
from src.feature_extractor import count_letters, count_digits, count_subdomains
from src.prepare_data import find_url_column
from src.url_utils import (
    get_hostname,
    hostname_is_ip_address,
    strip_url,
    uses_https_scheme,
)


TARGET_COLUMN = "label"
RESEARCH_SPLIT_INDICES_FILE = RESULTS_DIRECTORY / "research_split_indices.json"
RESEARCH_TIER_SUMMARY_FILE = RESULTS_DIRECTORY / "research_tier_summary.json"
SPLIT_NAMES = ("train", "validation", "test")


TIER_A_FEATURES = [
    "URLLength",
    "DomainLength",
    "IsDomainIP",
    "URLSimilarityIndex",
    "CharContinuationRate",
    "TLDLegitimateProb",
    "URLCharProb",
    "TLDLength",
    "NoOfSubDomain",
    "HasObfuscation",
    "NoOfObfuscatedChar",
    "ObfuscationRatio",
    "NoOfLettersInURL",
    "LetterRatioInURL",
    "NoOfDegitsInURL",
    "DegitRatioInURL",
    "NoOfEqualsInURL",
    "NoOfQMarkInURL",
    "NoOfAmpersandInURL",
    "NoOfOtherSpecialCharsInURL",
    "SpacialCharRatioInURL",
    "IsHTTPS",
    "LineOfCode",
    "LargestLineLength",
    "HasTitle",
    "DomainTitleMatchScore",
    "URLTitleMatchScore",
    "HasFavicon",
    "Robots",
    "IsResponsive",
    "NoOfURLRedirect",
    "NoOfSelfRedirect",
    "HasDescription",
    "NoOfPopup",
    "NoOfiFrame",
    "HasExternalFormSubmit",
    "HasSocialNet",
    "HasSubmitButton",
    "HasHiddenFields",
    "HasPasswordField",
    "Bank",
    "Pay",
    "Crypto",
    "HasCopyrightInfo",
    "NoOfImage",
    "NoOfCSS",
    "NoOfJS",
    "NoOfSelfRef",
    "NoOfEmptyRef",
    "NoOfExternalRef",
]

TIER_B_FEATURES = [
    "URLLength",
    "DomainLength",
    "IsDomainIP",
    "URLSimilarityIndex",
    "CharContinuationRate",
    "TLDLegitimateProb",
    "URLCharProb",
    "TLDLength",
    "NoOfSubDomain",
    "HasObfuscation",
    "NoOfObfuscatedChar",
    "ObfuscationRatio",
    "NoOfLettersInURL",
    "LetterRatioInURL",
    "NoOfDegitsInURL",
    "DegitRatioInURL",
    "NoOfEqualsInURL",
    "NoOfQMarkInURL",
    "NoOfAmpersandInURL",
    "NoOfOtherSpecialCharsInURL",
    "SpacialCharRatioInURL",
    "IsHTTPS",
]

TIER_C_FEATURES = [
    "URLLength",
    "DomainLength",
    "IsDomainIP",
    "TLDLength",
    "NoOfSubDomain",
    "HasObfuscation",
    "NoOfObfuscatedChar",
    "ObfuscationRatio",
    "NoOfLettersInURL",
    "LetterRatioInURL",
    "NoOfDegitsInURL",
    "DegitRatioInURL",
    "NoOfEqualsInURL",
    "NoOfQMarkInURL",
    "NoOfAmpersandInURL",
    "NoOfOtherSpecialCharsInURL",
    "SpacialCharRatioInURL",
    "IsHTTPS",
]

TIER_D_MATCHED_FEATURES = [
    "d_url_length",
    "d_domain_length",
    "d_is_domain_ip",
    "d_tld_length",
    "d_number_of_subdomains",
    "d_has_obfuscation",
    "d_number_of_obfuscated_chars",
    "d_obfuscation_ratio",
    "d_number_of_letters",
    "d_letter_ratio",
    "d_number_of_digits",
    "d_digit_ratio",
    "d_number_of_equal_signs",
    "d_number_of_question_marks",
    "d_number_of_ampersands",
    "d_number_of_other_special_chars",
    "d_special_char_ratio",
    "d_is_https",
]

TIER_E_FEATURES = FEATURE_NAMES
TIER_FEATURES = {
    "A": TIER_A_FEATURES,
    "B": TIER_B_FEATURES,
    "C": TIER_C_FEATURES,
    "D-matched": TIER_D_MATCHED_FEATURES,
    "E": TIER_E_FEATURES,
}
OBFUSCATED_CHARACTER_PATTERN = re.compile(r"%[0-9A-Fa-f]{2}")


@dataclass(frozen=True)
class ResearchTiers:
    """Container for controlled feature matrices and labels."""

    features: dict[str, pd.DataFrame]
    target: pd.Series
    split_indices: dict[str, list[int]]


def safe_ratio(part: int, whole: int) -> float:
    """Return part / whole, or zero for empty strings."""

    if whole == 0:
        return 0.0

    return part / whole


def remove_scheme_and_www_prefix(url: str) -> str:
    """Remove an explicit scheme and leading www. for compatibility counts."""

    stripped = strip_url(url)
    without_scheme = re.sub(r"^[A-Za-z][A-Za-z0-9+.-]*://", "", stripped, count=1)

    if without_scheme.lower().startswith("www."):
        return without_scheme[4:]

    return without_scheme


def tld_length(hostname: str) -> int:
    """Return length of the final hostname label."""

    labels = [label for label in hostname.split(".") if label]

    if not labels:
        return 0

    return len(labels[-1])


def count_obfuscated_characters(url: str) -> int:
    """Count percent-encoded byte-like obfuscation markers in URL text."""

    return len(OBFUSCATED_CHARACTER_PATTERN.findall(strip_url(url)))


def count_other_special_characters(text: str) -> int:
    """Count non-alphanumeric characters excluding common URL separators."""

    excluded = {":", "/", ".", "?", "=", "&"}
    return sum(
        not character.isalnum()
        and not character.isspace()
        and character not in excluded
        for character in text
    )


def build_tier_d_matched_features(urls: pd.Series) -> pd.DataFrame:
    """Build research-specific reconstructions of Tier C feature concepts."""

    records: list[dict[str, float | int]] = []

    for url in urls:
        stripped = strip_url(url)
        compatibility_text = remove_scheme_and_www_prefix(url)
        hostname = get_hostname(stripped)
        url_length = len(stripped)
        obfuscated_chars = count_obfuscated_characters(stripped)
        letter_count = count_letters(compatibility_text)
        digit_count = count_digits(stripped)
        other_special_count = count_other_special_characters(compatibility_text)

        records.append(
            {
                "d_url_length": url_length,
                "d_domain_length": len(hostname),
                "d_is_domain_ip": int(hostname_is_ip_address(hostname)),
                "d_tld_length": tld_length(hostname),
                "d_number_of_subdomains": count_subdomains(hostname),
                "d_has_obfuscation": int(obfuscated_chars > 0),
                "d_number_of_obfuscated_chars": obfuscated_chars,
                "d_obfuscation_ratio": safe_ratio(obfuscated_chars, url_length),
                "d_number_of_letters": letter_count,
                "d_letter_ratio": safe_ratio(letter_count, url_length),
                "d_number_of_digits": digit_count,
                "d_digit_ratio": safe_ratio(digit_count, url_length),
                "d_number_of_equal_signs": stripped.count("="),
                "d_number_of_question_marks": stripped.count("?"),
                "d_number_of_ampersands": stripped.count("&"),
                "d_number_of_other_special_chars": other_special_count,
                "d_special_char_ratio": safe_ratio(other_special_count, url_length),
                "d_is_https": int(uses_https_scheme(stripped)),
            }
        )

    return pd.DataFrame(records, columns=TIER_D_MATCHED_FEATURES)


def build_tier_e_features(urls: pd.Series) -> pd.DataFrame:
    """Build the production deployment-extended feature matrix."""

    from src.feature_extractor import extract_url_features

    return pd.DataFrame(
        [extract_url_features(url) for url in urls],
        columns=TIER_E_FEATURES,
    )


def build_split_indices(target: pd.Series) -> dict[str, list[int]]:
    """Build one deterministic 70/15/15 stratified split assignment."""

    all_indices = target.index.to_numpy()
    train_indices, holdout_indices = train_test_split(
        all_indices,
        test_size=0.30,
        random_state=RANDOM_STATE,
        stratify=target,
    )
    validation_indices, test_indices = train_test_split(
        holdout_indices,
        test_size=0.50,
        random_state=RANDOM_STATE,
        stratify=target.loc[holdout_indices],
    )

    return {
        "train": sorted(int(index) for index in train_indices),
        "validation": sorted(int(index) for index in validation_indices),
        "test": sorted(int(index) for index in test_indices),
    }


def validate_feature_matrix(
    matrix: pd.DataFrame,
    target: pd.Series,
    tier_name: str,
) -> None:
    """Validate one feature tier matrix."""

    if len(matrix) != len(target):
        raise ValueError(f"Tier {tier_name} row count does not match target.")

    if TARGET_COLUMN in matrix.columns:
        raise ValueError(f"Tier {tier_name} accidentally includes target column.")

    if "URL" in matrix.columns or "Domain" in matrix.columns or "Title" in matrix.columns:
        raise ValueError(f"Tier {tier_name} includes raw text columns.")

    if matrix.isna().sum().sum() != 0:
        raise ValueError(f"Tier {tier_name} contains missing values.")

    non_numeric_columns = [
        column
        for column in matrix.columns
        if not pd.api.types.is_numeric_dtype(matrix[column])
    ]

    if non_numeric_columns:
        raise ValueError(
            f"Tier {tier_name} has non-numeric columns: {non_numeric_columns}"
        )


def validate_split_indices(
    split_indices: dict[str, list[int]],
    expected_indices: set[int],
) -> None:
    """Validate split coverage and exclusivity."""

    observed: list[int] = []

    for split_name in SPLIT_NAMES:
        if split_name not in split_indices:
            raise ValueError(f"Missing split: {split_name}")
        observed.extend(split_indices[split_name])

    if len(observed) != len(set(observed)):
        raise ValueError("Split indices overlap.")

    if set(observed) != expected_indices:
        raise ValueError("Split indices do not cover exactly the dataset rows.")


def build_research_tiers(raw_data_file: Path = RAW_DATA_FILE) -> ResearchTiers:
    """Build all controlled research feature tiers."""

    raw_dataframe = pd.read_csv(raw_data_file)
    url_column = find_url_column(raw_dataframe)
    target = raw_dataframe[TARGET_COLUMN].astype(int)

    features = {
        "A": raw_dataframe[TIER_A_FEATURES].copy(),
        "B": raw_dataframe[TIER_B_FEATURES].copy(),
        "C": raw_dataframe[TIER_C_FEATURES].copy(),
        "D-matched": build_tier_d_matched_features(raw_dataframe[url_column]),
        "E": build_tier_e_features(raw_dataframe[url_column]),
    }
    split_indices = build_split_indices(target)

    validate_split_indices(split_indices, set(target.index.tolist()))

    for tier_name, matrix in features.items():
        validate_feature_matrix(matrix, target, tier_name)

    return ResearchTiers(features=features, target=target, split_indices=split_indices)


def build_summary(tiers: ResearchTiers) -> dict[str, object]:
    """Build compact summary metadata for the research tiers."""

    split_counts = {
        split_name: len(indices)
        for split_name, indices in tiers.split_indices.items()
    }
    split_label_counts = {
        split_name: tiers.target.loc[indices].value_counts().sort_index().to_dict()
        for split_name, indices in tiers.split_indices.items()
    }

    return {
        "random_state": RANDOM_STATE,
        "target_column": TARGET_COLUMN,
        "row_count": int(len(tiers.target)),
        "target_value_counts": tiers.target.value_counts().sort_index().to_dict(),
        "split_counts": split_counts,
        "split_label_counts": split_label_counts,
        "tiers": {
            tier_name: {
                "feature_count": int(matrix.shape[1]),
                "feature_names": matrix.columns.tolist(),
                "row_count": int(matrix.shape[0]),
                "has_missing_values": bool(matrix.isna().sum().sum() != 0),
                "all_numeric": bool(
                    all(pd.api.types.is_numeric_dtype(matrix[column]) for column in matrix)
                ),
            }
            for tier_name, matrix in tiers.features.items()
        },
        "controls": {
            "same_rows_all_tiers": True,
            "same_labels_all_tiers": True,
            "same_split_assignment_all_tiers": True,
            "raw_url_not_used_as_model_feature": True,
            "full_tier_matrices_committed": False,
        },
        "safety_statement": (
            "Feature tiers were built using local dataframe values and local "
            "URL text parsing only; no URL was contacted."
        ),
    }


def save_research_tier_artifacts(tiers: ResearchTiers) -> dict[str, object]:
    """Save split indices and summary metadata."""

    RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    summary = build_summary(tiers)

    with RESEARCH_SPLIT_INDICES_FILE.open("w", encoding="utf-8") as file:
        json.dump(tiers.split_indices, file)
        file.write("\n")

    with RESEARCH_TIER_SUMMARY_FILE.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)
        file.write("\n")

    return summary


def main() -> None:
    """Build and save controlled research tier metadata."""

    tiers = build_research_tiers()
    summary = save_research_tier_artifacts(tiers)

    print(f"Rows: {summary['row_count']:,}")
    print(f"Split counts: {summary['split_counts']}")
    for tier_name, tier_summary in summary["tiers"].items():
        print(f"Tier {tier_name}: {tier_summary['feature_count']} features")
    print(f"Saved: {RESEARCH_SPLIT_INDICES_FILE}")
    print(f"Saved: {RESEARCH_TIER_SUMMARY_FILE}")


if __name__ == "__main__":
    main()
