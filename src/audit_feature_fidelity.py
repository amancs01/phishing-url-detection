"""Audit fidelity between supplied PhiUSIIL features and local extraction.

The script treats dataset URLs as inert text. It never opens, requests,
resolves, pings, or otherwise contacts any URL.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.config import PROJECT_ROOT, RAW_DATA_FILE, RESULTS_DIRECTORY
from src.feature_definitions import FEATURE_NAMES
from src.feature_extractor import extract_url_features
from src.prepare_data import find_url_column


DEFAULT_MAPPING_FILE = PROJECT_ROOT / "research" / "feature_mapping.json"
FIDELITY_RESULTS_FILE = RESULTS_DIRECTORY / "feature_fidelity.csv"
FIDELITY_SUMMARY_FILE = RESULTS_DIRECTORY / "feature_fidelity_summary.json"
FIDELITY_MISMATCH_SAMPLE_FILE = RESULTS_DIRECTORY / "feature_fidelity_mismatch_samples.csv"
TARGET_COLUMN = "label"
REQUIRED_MAPPING_KEYS = {
    "supplied_feature",
    "reconstructed_feature",
    "feature_type",
    "near_match_tolerance",
}
REQUIRED_AUDIT_COLUMNS = [
    "supplied_feature",
    "reconstructed_feature",
    "feature_type",
    "compared_rows",
    "exact_match_count",
    "exact_match_percentage",
    "near_match_count",
    "near_match_percentage",
    "mismatch_count",
    "mae",
    "median_absolute_error",
    "pearson_correlation",
    "near_match_tolerance",
]


def load_feature_mapping(mapping_file: Path = DEFAULT_MAPPING_FILE) -> list[dict[str, Any]]:
    """Load the audited feature mapping JSON."""

    with mapping_file.open(encoding="utf-8") as file:
        mappings = json.load(file)

    if not isinstance(mappings, list) or not mappings:
        raise ValueError("Feature mapping must be a non-empty list.")

    return mappings


def validate_mappings(
    mappings: list[dict[str, Any]], supplied_columns: list[str]
) -> None:
    """Validate mapping records against supplied and extractor feature names."""

    supplied_column_set = set(supplied_columns)
    extractor_feature_set = set(FEATURE_NAMES)

    for index, mapping in enumerate(mappings):
        missing_keys = REQUIRED_MAPPING_KEYS - set(mapping)
        if missing_keys:
            raise ValueError(
                f"Mapping at index {index} is missing keys: {sorted(missing_keys)}"
            )

        supplied_feature = mapping["supplied_feature"]
        reconstructed_feature = mapping.get(
            "current_extractor_feature", mapping["reconstructed_feature"]
        )
        feature_type = mapping["feature_type"]

        if supplied_feature not in supplied_column_set:
            raise ValueError(
                f"Mapped supplied feature is not in dataset columns: {supplied_feature}"
            )

        if reconstructed_feature not in extractor_feature_set:
            raise ValueError(
                "Mapped reconstructed feature is not produced by extractor: "
                f"{reconstructed_feature}"
            )

        if feature_type not in {"discrete", "continuous"}:
            raise ValueError(
                f"Mapping for {supplied_feature} has invalid feature_type: {feature_type}"
            )


def current_fidelity_mappings(mappings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return mapping records that target the production extractor."""

    filtered_mappings: list[dict[str, Any]] = []

    for mapping in mappings:
        if not mapping.get("current_fidelity_audit", True):
            continue

        current_feature = mapping.get(
            "current_extractor_feature", mapping["reconstructed_feature"]
        )

        if current_feature is None:
            continue

        filtered_mapping = mapping.copy()
        filtered_mapping["reconstructed_feature"] = current_feature
        filtered_mappings.append(filtered_mapping)

    if not filtered_mappings:
        raise ValueError("No current extractor mappings are available.")

    return filtered_mappings


def build_reconstructed_features(urls: pd.Series) -> pd.DataFrame:
    """Extract project deployment features from URL text only."""

    feature_rows = [extract_url_features(url) for url in urls]
    return pd.DataFrame(feature_rows, columns=FEATURE_NAMES)


def _safe_pearson_correlation(supplied: pd.Series, reconstructed: pd.Series) -> float | None:
    """Return Pearson correlation, or None when one side is constant."""

    if supplied.nunique(dropna=True) <= 1 or reconstructed.nunique(dropna=True) <= 1:
        return None

    correlation = supplied.corr(reconstructed, method="pearson")

    if pd.isna(correlation):
        return None

    return float(correlation)


def compute_feature_fidelity(
    supplied_dataframe: pd.DataFrame,
    reconstructed_dataframe: pd.DataFrame,
    mappings: list[dict[str, Any]],
) -> pd.DataFrame:
    """Compute per-feature fidelity statistics for mapped columns."""

    records: list[dict[str, Any]] = []

    for mapping in mappings:
        supplied_feature = mapping["supplied_feature"]
        reconstructed_feature = mapping["reconstructed_feature"]
        feature_type = mapping["feature_type"]
        tolerance = float(mapping["near_match_tolerance"])

        supplied_values = pd.to_numeric(supplied_dataframe[supplied_feature])
        reconstructed_values = pd.to_numeric(
            reconstructed_dataframe[reconstructed_feature]
        )
        absolute_error = (supplied_values - reconstructed_values).abs()
        exact_matches = supplied_values == reconstructed_values
        near_matches = absolute_error <= tolerance
        compared_rows = int(len(supplied_values))

        records.append(
            {
                "supplied_feature": supplied_feature,
                "reconstructed_feature": reconstructed_feature,
                "feature_type": feature_type,
                "compared_rows": compared_rows,
                "exact_match_count": int(exact_matches.sum()),
                "exact_match_percentage": float(exact_matches.mean() * 100),
                "near_match_count": int(near_matches.sum()),
                "near_match_percentage": float(near_matches.mean() * 100),
                "mismatch_count": int((~exact_matches).sum()),
                "mae": float(absolute_error.mean()),
                "median_absolute_error": float(absolute_error.median()),
                "pearson_correlation": _safe_pearson_correlation(
                    supplied_values, reconstructed_values
                ),
                "near_match_tolerance": tolerance,
            }
        )

    return pd.DataFrame(records, columns=REQUIRED_AUDIT_COLUMNS)


def build_mismatch_samples(
    supplied_dataframe: pd.DataFrame,
    reconstructed_dataframe: pd.DataFrame,
    mappings: list[dict[str, Any]],
    max_samples_per_feature: int = 5,
) -> pd.DataFrame:
    """Build safe mismatch samples without raw URL text."""

    sample_records: list[dict[str, Any]] = []

    for mapping in mappings:
        supplied_feature = mapping["supplied_feature"]
        reconstructed_feature = mapping["reconstructed_feature"]

        supplied_values = pd.to_numeric(supplied_dataframe[supplied_feature])
        reconstructed_values = pd.to_numeric(
            reconstructed_dataframe[reconstructed_feature]
        )
        mismatch_mask = supplied_values != reconstructed_values
        mismatch_indices = supplied_dataframe.index[mismatch_mask][:max_samples_per_feature]

        for row_index in mismatch_indices:
            supplied_value = supplied_values.loc[row_index]
            reconstructed_value = reconstructed_values.loc[row_index]
            sample_records.append(
                {
                    "row_index": int(row_index),
                    "label": int(supplied_dataframe.loc[row_index, TARGET_COLUMN]),
                    "supplied_feature": supplied_feature,
                    "reconstructed_feature": reconstructed_feature,
                    "supplied_value": float(supplied_value),
                    "reconstructed_value": float(reconstructed_value),
                    "absolute_error": float(abs(supplied_value - reconstructed_value)),
                }
            )

    return pd.DataFrame(
        sample_records,
        columns=[
            "row_index",
            "label",
            "supplied_feature",
            "reconstructed_feature",
            "supplied_value",
            "reconstructed_value",
            "absolute_error",
        ],
    )


def build_summary(audit_table: pd.DataFrame, row_count: int) -> dict[str, Any]:
    """Build a compact JSON summary of the fidelity audit."""

    exact_rates = audit_table.set_index("supplied_feature")[
        "exact_match_percentage"
    ].to_dict()
    near_rates = audit_table.set_index("supplied_feature")[
        "near_match_percentage"
    ].to_dict()

    return {
        "row_count": int(row_count),
        "mapped_feature_count": int(len(audit_table)),
        "mapped_features": audit_table[
            ["supplied_feature", "reconstructed_feature", "feature_type"]
        ].to_dict(orient="records"),
        "mean_exact_match_percentage": float(
            audit_table["exact_match_percentage"].mean()
        ),
        "mean_near_match_percentage": float(
            audit_table["near_match_percentage"].mean()
        ),
        "highest_exact_match_features": audit_table.sort_values(
            ["exact_match_percentage", "supplied_feature"],
            ascending=[False, True],
        )
        .head(5)["supplied_feature"]
        .tolist(),
        "lowest_exact_match_features": audit_table.sort_values(
            ["exact_match_percentage", "supplied_feature"],
            ascending=[True, True],
        )
        .head(5)["supplied_feature"]
        .tolist(),
        "exact_match_percentage_by_feature": exact_rates,
        "near_match_percentage_by_feature": near_rates,
        "safety_statement": (
            "URLs were parsed as local text only; no dataset URL was opened, "
            "requested, resolved, pinged, or otherwise contacted."
        ),
    }


def run_feature_fidelity_audit(
    raw_data_file: Path = RAW_DATA_FILE,
    mapping_file: Path = DEFAULT_MAPPING_FILE,
) -> tuple[pd.DataFrame, dict[str, Any], pd.DataFrame]:
    """Run the full feature-fidelity audit and return output objects."""

    raw_dataframe = pd.read_csv(raw_data_file)
    mappings = current_fidelity_mappings(load_feature_mapping(mapping_file))
    validate_mappings(mappings, raw_dataframe.columns.tolist())

    url_column = find_url_column(raw_dataframe)
    reconstructed_dataframe = build_reconstructed_features(raw_dataframe[url_column])

    audit_table = compute_feature_fidelity(
        raw_dataframe, reconstructed_dataframe, mappings
    )
    mismatch_samples = build_mismatch_samples(
        raw_dataframe, reconstructed_dataframe, mappings
    )
    summary = build_summary(audit_table, len(raw_dataframe))

    return audit_table, summary, mismatch_samples


def save_audit_outputs(
    audit_table: pd.DataFrame,
    summary: dict[str, Any],
    mismatch_samples: pd.DataFrame,
) -> None:
    """Save fidelity outputs to the results directory."""

    RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    audit_table.to_csv(FIDELITY_RESULTS_FILE, index=False)
    mismatch_samples.to_csv(FIDELITY_MISMATCH_SAMPLE_FILE, index=False)

    with FIDELITY_SUMMARY_FILE.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)
        file.write("\n")


def main() -> None:
    """Run the feature-fidelity audit from the command line."""

    audit_table, summary, mismatch_samples = run_feature_fidelity_audit()
    save_audit_outputs(audit_table, summary, mismatch_samples)

    print(f"Audited rows: {summary['row_count']:,}")
    print(f"Mapped features: {summary['mapped_feature_count']}")
    print(f"Saved: {FIDELITY_RESULTS_FILE}")
    print(f"Saved: {FIDELITY_SUMMARY_FILE}")
    print(f"Saved: {FIDELITY_MISMATCH_SAMPLE_FILE}")


if __name__ == "__main__":
    main()
