"""Prepare LegitPhish external validation data with local URL parsing only."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import (
    LEGITPHISH_DATASET_SUMMARY_FILE,
    LEGITPHISH_DOI,
    LEGITPHISH_EXTERNAL_MATRIX_FILE,
    LEGITPHISH_RAW_FILE,
    LEGITPHISH_VERSION,
)
from src.feature_definitions import FEATURE_NAMES
from src.feature_extractor import extract_url_features
from src.prepare_external_data import TARGET_COLUMN


LEGITPHISH_URL_COLUMN = "URL"
LEGITPHISH_TARGET_COLUMN = "ClassLabel"
LEGITPHISH_LABEL_MEANINGS = {
    0: "phishing",
    1: "legitimate",
}


def load_legitphish_dataframe(raw_file: Path = LEGITPHISH_RAW_FILE) -> pd.DataFrame:
    """Load the official LegitPhish CSV from local ignored storage."""

    if not raw_file.exists():
        raise FileNotFoundError(
            f"LegitPhish raw CSV not found at {raw_file}. Download Version 2 "
            "from the official Mendeley dataset before preparing features."
        )

    return pd.read_csv(raw_file)


def validate_legitphish_schema(data: pd.DataFrame) -> None:
    """Validate required LegitPhish source columns and label convention."""

    missing_columns = [
        column
        for column in [LEGITPHISH_URL_COLUMN, LEGITPHISH_TARGET_COLUMN]
        if column not in data
    ]

    if missing_columns:
        raise ValueError(f"Missing required LegitPhish columns: {missing_columns}")

    label_values = set(
        data[LEGITPHISH_TARGET_COLUMN]
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )

    if label_values != set(LEGITPHISH_LABEL_MEANINGS):
        raise ValueError(
            f"Expected LegitPhish labels {sorted(LEGITPHISH_LABEL_MEANINGS)}, "
            f"found {sorted(label_values)}."
        )


def analysis_rows(data: pd.DataFrame) -> pd.DataFrame:
    """Return rows with usable URL and label fields."""

    validate_legitphish_schema(data)
    usable = data[
        data[LEGITPHISH_URL_COLUMN].notna()
        & data[LEGITPHISH_TARGET_COLUMN].notna()
    ].copy()
    usable[LEGITPHISH_TARGET_COLUMN] = usable[LEGITPHISH_TARGET_COLUMN].astype(int)
    return usable


def conflicting_duplicate_urls(data: pd.DataFrame) -> set[str]:
    """Return exact URL strings that appear with conflicting labels."""

    usable = analysis_rows(data)
    label_counts = usable.groupby(LEGITPHISH_URL_COLUMN)[LEGITPHISH_TARGET_COLUMN].nunique()
    return set(label_counts[label_counts > 1].index.tolist())


def build_legitphish_feature_matrix(data: pd.DataFrame) -> pd.DataFrame:
    """Build the Tier E external matrix from raw LegitPhish URL text only."""

    usable = analysis_rows(data)
    feature_rows = [
        extract_url_features(url_text)
        for url_text in usable[LEGITPHISH_URL_COLUMN].astype(str).tolist()
    ]
    features = pd.DataFrame(feature_rows, columns=FEATURE_NAMES)
    features[TARGET_COLUMN] = usable[LEGITPHISH_TARGET_COLUMN].astype(int).to_numpy()
    validate_legitphish_feature_matrix(features)
    return features


def validate_legitphish_feature_matrix(matrix: pd.DataFrame) -> None:
    """Validate the saved LegitPhish matrix contract."""

    if list(matrix.columns) != FEATURE_NAMES + [TARGET_COLUMN]:
        raise ValueError("LegitPhish feature matrix columns do not match FEATURE_NAMES.")

    if matrix[FEATURE_NAMES].isna().any().any():
        raise ValueError("LegitPhish feature matrix contains missing feature values.")

    non_numeric = [
        column
        for column in FEATURE_NAMES
        if not pd.api.types.is_numeric_dtype(matrix[column])
    ]

    if non_numeric:
        raise ValueError(f"LegitPhish feature columns must be numerical: {non_numeric}")

    label_values = set(matrix[TARGET_COLUMN].dropna().astype(int).unique().tolist())

    if label_values != set(LEGITPHISH_LABEL_MEANINGS):
        raise ValueError(f"Unexpected LegitPhish target classes: {sorted(label_values)}")


def summarize_legitphish_dataset(data: pd.DataFrame, matrix: pd.DataFrame) -> dict[str, Any]:
    """Create compact LegitPhish metadata without raw URLs or domains."""

    usable = analysis_rows(data)
    class_counts = usable[LEGITPHISH_TARGET_COLUMN].value_counts().to_dict()
    conflicts = conflicting_duplicate_urls(data)

    return {
        "dataset_name": "LegitPhish Dataset",
        "dataset_version": LEGITPHISH_VERSION,
        "doi": LEGITPHISH_DOI,
        "source": "Official Mendeley Data Version 2 CSV",
        "raw_rows": int(len(data)),
        "analysis_rows": int(len(usable)),
        "dropped_rows": {
            "missing_url_or_label": int(len(data) - len(usable)),
        },
        "url_column": LEGITPHISH_URL_COLUMN,
        "target_column": LEGITPHISH_TARGET_COLUMN,
        "target_convention": {
            "0": "phishing",
            "1": "legitimate",
        },
        "class_counts": {
            "phishing_label_0": int(class_counts.get(0, 0)),
            "legitimate_label_1": int(class_counts.get(1, 0)),
        },
        "missing_diagnostics": {
            "url_missing": int(data[LEGITPHISH_URL_COLUMN].isna().sum()),
            "label_missing": int(data[LEGITPHISH_TARGET_COLUMN].isna().sum()),
            "any_missing_source_row": int(data.isna().any(axis=1).sum()),
            "any_missing_matrix_row": int(matrix.isna().any(axis=1).sum()),
        },
        "duplicate_diagnostics": {
            "duplicate_rows": int(data.duplicated().sum()),
            "duplicate_url_rows": int(data[LEGITPHISH_URL_COLUMN].duplicated().sum()),
            "conflicting_duplicate_url_values": int(len(conflicts)),
            "rows_with_conflicting_duplicate_url": int(
                data[LEGITPHISH_URL_COLUMN].isin(conflicts).sum()
            ),
        },
        "feature_count": len(FEATURE_NAMES),
        "feature_names": FEATURE_NAMES,
        "used_source_columns_for_features": [LEGITPHISH_URL_COLUMN],
        "ignored_legitphish_supplied_feature_columns": [
            column
            for column in data.columns
            if column not in {LEGITPHISH_URL_COLUMN, LEGITPHISH_TARGET_COLUMN}
        ],
        "label_inversion_applied": False,
        "safety_statement": (
            "LegitPhish URL strings were parsed locally with extract_url_features; "
            "no dataset URL was opened, requested, resolved, or contacted."
        ),
    }


def prepare_legitphish_data(
    raw_file: Path = LEGITPHISH_RAW_FILE,
    matrix_file: Path = LEGITPHISH_EXTERNAL_MATRIX_FILE,
    summary_file: Path = LEGITPHISH_DATASET_SUMMARY_FILE,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Prepare the ignored LegitPhish matrix and committed compact summary."""

    data = load_legitphish_dataframe(raw_file)
    matrix = build_legitphish_feature_matrix(data)
    summary = summarize_legitphish_dataset(data, matrix)

    matrix_file.parent.mkdir(parents=True, exist_ok=True)
    matrix.to_csv(matrix_file, index=False)

    summary_file.parent.mkdir(parents=True, exist_ok=True)
    with summary_file.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)
        file.write("\n")

    return matrix, summary


def main() -> None:
    """Prepare LegitPhish external validation features."""

    matrix, summary = prepare_legitphish_data()
    print(f"Prepared LegitPhish matrix rows: {len(matrix)}")
    print(f"Saved ignored matrix: {LEGITPHISH_EXTERNAL_MATRIX_FILE}")
    print(f"Saved summary: {LEGITPHISH_DATASET_SUMMARY_FILE}")
    print(
        {
            "raw_rows": summary["raw_rows"],
            "analysis_rows": summary["analysis_rows"],
            "phishing": summary["class_counts"]["phishing_label_0"],
            "legitimate": summary["class_counts"]["legitimate_label_1"],
            "duplicate_url_rows": summary["duplicate_diagnostics"]["duplicate_url_rows"],
            "conflicting_duplicate_url_values": summary["duplicate_diagnostics"][
                "conflicting_duplicate_url_values"
            ],
        }
    )


if __name__ == "__main__":
    main()
