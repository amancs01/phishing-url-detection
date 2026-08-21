"""Prepare URL-Phish external validation data with local URL parsing only."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import (
    EXTERNAL_DATASET_SUMMARY_FILE,
    URL_PHISH_DOI,
    URL_PHISH_EXTERNAL_MATRIX_FILE,
    URL_PHISH_RAW_FILE,
    URL_PHISH_VERSION,
)
from src.feature_definitions import FEATURE_NAMES
from src.feature_extractor import extract_url_features


URL_COLUMN = "url"
LABEL_COLUMN = "label"
TARGET_COLUMN = "target"
URL_PHISH_LABEL_MAPPING = {
    1: 0,
    0: 1,
}
PROJECT_LABEL_MEANINGS = {
    0: "phishing",
    1: "legitimate",
}


def load_url_phish_dataframe(raw_file: Path = URL_PHISH_RAW_FILE) -> pd.DataFrame:
    """Load the official URL-Phish CSV from local ignored storage."""

    if not raw_file.exists():
        raise FileNotFoundError(
            f"URL-Phish raw CSV not found at {raw_file}. Download Version 2 "
            "from the official Mendeley dataset before preparing features."
        )

    return pd.read_csv(raw_file)


def validate_url_phish_schema(data: pd.DataFrame) -> None:
    """Validate that required URL-Phish source columns are available."""

    missing_columns = [column for column in [URL_COLUMN, LABEL_COLUMN] if column not in data]

    if missing_columns:
        raise ValueError(f"Missing required URL-Phish columns: {missing_columns}")

    class_values = set(data[LABEL_COLUMN].dropna().astype(int).unique().tolist())

    if class_values != set(URL_PHISH_LABEL_MAPPING):
        raise ValueError(
            f"Expected URL-Phish labels {sorted(URL_PHISH_LABEL_MAPPING)}, "
            f"found {sorted(class_values)}."
        )


def normalize_url_phish_labels(labels: pd.Series) -> pd.Series:
    """Map URL-Phish labels into the project convention."""

    normalized = labels.astype(int).map(URL_PHISH_LABEL_MAPPING)

    if normalized.isna().any():
        bad_values = sorted(labels[normalized.isna()].dropna().unique().tolist())
        raise ValueError(f"Unexpected URL-Phish label values: {bad_values}")

    return normalized.astype(int)


def build_external_feature_matrix(data: pd.DataFrame) -> pd.DataFrame:
    """Build the Tier E external feature matrix from raw URL text only."""

    validate_url_phish_schema(data)
    feature_rows = [
        extract_url_features(url_text)
        for url_text in data[URL_COLUMN].astype(str).tolist()
    ]
    features = pd.DataFrame(feature_rows, columns=FEATURE_NAMES)
    features[TARGET_COLUMN] = normalize_url_phish_labels(data[LABEL_COLUMN]).to_numpy()
    validate_external_feature_matrix(features)
    return features


def validate_external_feature_matrix(matrix: pd.DataFrame) -> None:
    """Validate the saved external matrix contract."""

    expected_columns = FEATURE_NAMES + [TARGET_COLUMN]

    if list(matrix.columns) != expected_columns:
        raise ValueError("External feature matrix columns do not match FEATURE_NAMES.")

    if matrix[FEATURE_NAMES].isna().any().any():
        raise ValueError("External feature matrix contains missing feature values.")

    non_numeric = [
        column
        for column in FEATURE_NAMES
        if not pd.api.types.is_numeric_dtype(matrix[column])
    ]

    if non_numeric:
        raise ValueError(f"External feature columns must be numerical: {non_numeric}")

    class_values = set(matrix[TARGET_COLUMN].dropna().astype(int).unique().tolist())

    if class_values != set(PROJECT_LABEL_MEANINGS):
        raise ValueError(f"Unexpected normalized target classes: {sorted(class_values)}")


def summarize_external_dataset(data: pd.DataFrame, matrix: pd.DataFrame) -> dict[str, Any]:
    """Create compact metadata without raw URLs or domain names."""

    url_missing = int(data[URL_COLUMN].isna().sum())
    label_missing = int(data[LABEL_COLUMN].isna().sum())
    url_phish_counts = data[LABEL_COLUMN].astype(int).value_counts().to_dict()
    normalized_counts = matrix[TARGET_COLUMN].astype(int).value_counts().to_dict()

    return {
        "dataset_name": "URL-Phish: A Feature-Engineered Dataset for Phishing Detection",
        "dataset_version": URL_PHISH_VERSION,
        "doi": URL_PHISH_DOI,
        "source": "Official Mendeley Data Version 2 CSV",
        "total_rows": int(len(data)),
        "url_column": URL_COLUMN,
        "label_column": LABEL_COLUMN,
        "url_phish_label_semantics": {
            "0": "benign",
            "1": "phishing",
        },
        "project_label_semantics": {
            "0": "phishing",
            "1": "legitimate",
        },
        "label_mapping": {
            "url_phish_1": "project_0_phishing",
            "url_phish_0": "project_1_legitimate",
        },
        "url_phish_class_counts": {
            "benign_label_0": int(url_phish_counts.get(0, 0)),
            "phishing_label_1": int(url_phish_counts.get(1, 0)),
        },
        "normalized_project_class_counts": {
            "phishing_label_0": int(normalized_counts.get(0, 0)),
            "legitimate_label_1": int(normalized_counts.get(1, 0)),
        },
        "benign_count": int(url_phish_counts.get(0, 0)),
        "phishing_count": int(url_phish_counts.get(1, 0)),
        "missing_rows": {
            "url_missing": url_missing,
            "label_missing": label_missing,
            "any_missing_in_source_row": int(data.isna().any(axis=1).sum()),
            "any_missing_in_external_matrix_row": int(matrix.isna().any(axis=1).sum()),
        },
        "duplicate_rows": int(data.duplicated().sum()),
        "duplicate_url_rows": int(data[URL_COLUMN].duplicated().sum()),
        "feature_count": len(FEATURE_NAMES),
        "feature_names": FEATURE_NAMES,
        "used_source_columns_for_features": [URL_COLUMN],
        "ignored_url_phish_supplied_feature_columns": [
            column
            for column in data.columns
            if column not in {URL_COLUMN, LABEL_COLUMN}
        ],
        "safety_statement": (
            "External URL strings were parsed locally with extract_url_features; "
            "no dataset URL was opened, requested, resolved, or contacted."
        ),
    }


def prepare_external_data(
    raw_file: Path = URL_PHISH_RAW_FILE,
    matrix_file: Path = URL_PHISH_EXTERNAL_MATRIX_FILE,
    summary_file: Path = EXTERNAL_DATASET_SUMMARY_FILE,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Prepare the ignored external matrix and committed compact summary."""

    data = load_url_phish_dataframe(raw_file)
    matrix = build_external_feature_matrix(data)
    summary = summarize_external_dataset(data, matrix)

    matrix_file.parent.mkdir(parents=True, exist_ok=True)
    matrix.to_csv(matrix_file, index=False)

    summary_file.parent.mkdir(parents=True, exist_ok=True)
    with summary_file.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)
        file.write("\n")

    return matrix, summary


def main() -> None:
    """Prepare URL-Phish external validation features."""

    matrix, summary = prepare_external_data()
    print(f"Prepared external matrix rows: {len(matrix)}")
    print(f"Saved ignored matrix: {URL_PHISH_EXTERNAL_MATRIX_FILE}")
    print(f"Saved summary: {EXTERNAL_DATASET_SUMMARY_FILE}")
    print(
        {
            "total_rows": summary["total_rows"],
            "benign_count": summary["benign_count"],
            "phishing_count": summary["phishing_count"],
            "duplicate_url_rows": summary["duplicate_url_rows"],
        }
    )


if __name__ == "__main__":
    main()
